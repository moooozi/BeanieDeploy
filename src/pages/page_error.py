import logging

from models.page import Page, PageValidationResult
from multilingual import _
from templates.generic_page_layout import GenericPageLayout
from templates.info_frame import InfoFrame
from tkinter_templates import TextLabel


class PageError(Page):
    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)
        self.errors: list[str] = []

    def init_page(self):
        # Get app name from config
        app_name = (
            self.app_config.app.name
            if hasattr(self.app_config.app, "name")
            else "BeanieDeploy"
        )

        page_layout = GenericPageLayout(
            self,
            _("error.title") % {"app_name": app_name},
            secondary_btn_txt=_("btn.quit"),
            secondary_btn_command=lambda: self._quit_application(),
        )
        self.page_frame = page_layout.content_frame

        error_label = TextLabel(self.page_frame, text=_("error.list"))
        error_label.pack(pady=10)

        self.info_frame_raster = InfoFrame(self.page_frame)
        self.info_frame_raster.pack(fill="x", pady=5, padx=10)

    def set_errors(self, errors):
        """Set the errors to display and initialize the page."""
        self.init_page()
        self._initiated = True
        self.errors = errors
        self.info_frame_raster.flush_labels()

        for i, error in enumerate(self.errors):
            self.info_frame_raster.add_label(f"error_{i}", error)

        logging.error(f"Displaying {len(errors)} errors to user")

    def validate_input(self) -> PageValidationResult:
        """Error page doesn't require validation."""
        return PageValidationResult(True)

    def _quit_application(self):
        """Quit the application."""
        logging.info("User chose to quit from error page")
        import sys

        sys.exit(1)
