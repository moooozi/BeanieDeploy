from templates.generic_page_layout import GenericPageLayout
from templates.info_frame import InfoFrame
from models.page import Page, PageValidationResult
from tkinter_templates import TextLabel, FONTS_small
from multilingual import _


class PageInstallFailed(Page):
    """
    Page shown when installation fails after cleanup.
    
    This page informs the user that the installation failed and cleanup was completed.
    """
    
    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)
        self.error_message = ""

    def init_page(self):
        """Initialize the installation failed page."""
        page_layout = GenericPageLayout(
            self,
            _("install.failed.title"),
            primary_btn_txt=_("btn.quit"),
            primary_btn_command=lambda: self._quit_application(),
        )
        self.page_frame = page_layout.content_frame
        
        # Detailed error info
        if self.error_message:
            info_frame = InfoFrame(self.page_frame)
            info_frame.pack(fill="x", pady=5, padx=10)
            info_frame.add_label("error_details", f"Error: {self.error_message}")
        
        # Additional help text
        help_label = TextLabel(
            self.page_frame,
            text=_("install.failed.help"),
            font=FONTS_small
        )
        help_label.pack(pady=(20, 10))

    def set_error_message(self, error_message: str):
        """Set the error message to display."""
        self.error_message = error_message
        if hasattr(self, '_initiated') and self._initiated:
            # Re-initialize if already shown
            self.init_page()

    def validate_input(self) -> PageValidationResult:
        """Installation failed page doesn't require validation."""
        return PageValidationResult(True)

    def _retry_installation(self):
        """Retry the installation by going back to the beginning."""
        self.logger.info("User chose to retry installation")
        # Navigate back to the first page
        from pages.page_1 import Page1
        self.navigate_to(Page1)

    def _quit_application(self):
        """Quit the application."""
        self.logger.info("User chose to quit from installation failed page")
        import sys
        sys.exit(1)
