import logging
import tkinter as tk

from models.page import Page, PageValidationResult
from multilingual import _
from templates.generic_page_layout import GenericPageLayout
from tkinter_templates import FONTS_small, FONTS_smaller, TextLabel, colors


class PageRestartRequired(Page):
    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)
        self.restarting_text_var = tk.StringVar()

    def init_page(self):
        page_frame = GenericPageLayout(
            self,
            _("finished.title"),
            _("btn.restart.now"),
            lambda: self._restart_now(),
            _("btn.restart.later"),
            lambda: self._quit_application(),
        )

        finished_label = TextLabel(
            page_frame.content_frame, text=_("finished.text"), font=FONTS_smaller
        )
        finished_label.pack(pady=10)

        restarting_label = TextLabel(
            page_frame.content_frame,
            var=self.restarting_text_var,
            font=FONTS_small,
            text_color=colors.primary,
        )
        restarting_label.pack(pady=10)

        # Check if auto restart is enabled
        install_options = self.state.installation.install_options
        if install_options and install_options.auto_restart:
            self.countdown_to_restart(10)

    def countdown_to_restart(self, time):
        """Countdown timer for auto restart."""
        time -= 1
        if time > 0:
            self.restarting_text_var.set(
                _("finished.text.restarting.now") % {"seconds": int(time)}
            )
            self.after(1000, self.countdown_to_restart, time)
        else:
            self._restart_now()

    def validate_input(self) -> PageValidationResult:
        """Restart page doesn't require validation."""
        return PageValidationResult(True)

    def _restart_now(self):
        """Restart the system now."""
        logging.info("User chose to restart now")
        # This should integrate with your system restart function
        # For now, just quit the application
        self._quit_and_restart()

    def _quit_application(self):
        """Quit the application without restarting."""
        logging.info("User chose to restart later")

        raise SystemExit(0)

    def _quit_and_restart(self):
        """Quit application and restart Windows."""
        import subprocess

        try:
            # Restart Windows
            subprocess.run(["shutdown", "/r", "/t", "0"], check=True)
        except Exception as e:
            logging.error(f"Failed to restart system: {e}")
            raise SystemExit(0) from e
