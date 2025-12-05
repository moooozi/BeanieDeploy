import logging

import customtkinter as ctk

from models.page import Page, PageValidationResult
from multilingual import _
from templates.generic_page_layout import GenericPageLayout


class PagePlayground(Page):
    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)

    def init_page(self):
        page_layout = GenericPageLayout(
            self,
            "Hello, this is a playground page!",
            secondary_btn_txt=_("btn.quit"),
            secondary_btn_command=lambda: self._quit_application(),
        )
        self.page_frame = page_layout.content_frame

        playground_label = ctk.CTkSimpleLabel(
            self.page_frame,
            text="This is a label",
            justify=self._ui.di.l,
            pady=5,
        )
        playground_label.grid(row=0, column=0, pady=10)

        self.progressbar = ctk.CTkProgressBar(self.page_frame, mode="determinate")
        self.progressbar.grid(row=1, column=0, pady=10)
        self.progressbar.set(0)

        # Start the progress animation
        self.start_progress_animation()

    def start_progress_animation(self):
        """Start a non-blocking progress animation."""
        self.progress_value = 0
        self.animate_progress()

    def animate_progress(self):
        """Animate the progress bar without blocking the UI."""
        if self.progress_value <= 1.0:
            self.progressbar.set(self.progress_value)
            self.progress_value += 0.01
            # Schedule the next update in 50ms (non-blocking)
            self.after(50, self.animate_progress)
        else:
            # Reset and restart
            self.progress_value = 0
            self.after(1000, self.animate_progress)  # Wait 1 second then restart

    def validate_input(self) -> PageValidationResult:
        """Playground page doesn't require validation."""
        return PageValidationResult(True)

    def _quit_application(self):
        """Quit the application."""
        logging.info("User quit from playground page")

        raise SystemExit(0)
