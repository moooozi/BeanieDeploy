from templates.generic_page_layout import GenericPageLayout
from models.page import Page, PageValidationResult
import tkinter as tk
from tkinter_templates import TextLabel, FONTS_smaller, FONTS_small, color_blue


class PageRestartRequired(Page):
    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)
        self.restarting_text_var = tk.StringVar()

    def init_page(self):
        page_frame = GenericPageLayout(
            self,
            self.LN.finished_title,
            self.LN.btn_restart_now,
            lambda: self._restart_now(),
            self.LN.btn_restart_later,
            lambda: self._quit_application(),
        )
        
        
        finished_label = TextLabel(
            page_frame, text=self.LN.finished_text, font=FONTS_smaller
        )
        finished_label.pack(pady=10)
        
        restarting_label = TextLabel(
            page_frame,
            var=self.restarting_text_var,
            font=FONTS_small,
            foreground=color_blue,
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
                self.LN.finished_text_restarting_now % (int(time))
            )
            self.after(1000, self.countdown_to_restart, time)
        else:
            self._restart_now()

    def validate_input(self) -> PageValidationResult:
        """Restart page doesn't require validation."""
        return PageValidationResult(True)

    def _restart_now(self):
        """Restart the system now."""
        self.logger.info("User chose to restart now")
        # This should integrate with your system restart function
        # For now, just quit the application
        self._quit_and_restart()

    def _quit_application(self):
        """Quit the application without restarting."""
        self.logger.info("User chose to restart later")
        import sys
        sys.exit(0)

    def _quit_and_restart(self):
        """Quit application and restart Windows."""
        import subprocess
        import sys
        try:
            # Restart Windows
            subprocess.run(["shutdown", "/r", "/t", "0"], check=True)
        except Exception as e:
            self.logger.error(f"Failed to restart system: {e}")
            sys.exit(0)
