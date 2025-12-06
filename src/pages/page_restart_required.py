import logging
import tkinter as tk

import customtkinter as ctk

from models.page import Page, PageValidationResult
from multilingual import _


class PageRestartRequired(Page):
    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)
        self.restarting_text_var = tk.StringVar()

    def init_page(self):
        self.page_manager.set_title(_("finished.title"))
        self.page_manager.set_primary_button(
            _("btn.restart.now"), command=lambda: self._restart_now()
        )
        self.page_manager.set_secondary_button(
            _("btn.restart.later"), command=lambda: self._quit_application()
        )

        page_frame = self

        finished_label = ctk.CTkSimpleLabel(
            page_frame,
            text=_("finished.text"),
            font=self._ui.fonts.smaller,
            justify=self._ui.di.l,
            pady=5,
        )
        finished_label.grid(row=0, column=0, pady=10)

        restarting_label = ctk.CTkSimpleLabel(
            page_frame,
            textvariable=self.restarting_text_var,
            font=self._ui.fonts.small,
            text_color=self._ui.colors.primary,
            justify=self._ui.di.l,
            pady=5,
        )
        restarting_label.grid(row=1, column=0, pady=10)

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
