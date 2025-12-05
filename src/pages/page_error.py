import logging

import customtkinter as ctk

from models.page import Page, PageValidationResult
from multilingual import _
from templates.generic_page_layout import GenericPageLayout
from templates.info_frame import InfoFrame


class PageError(Page):
    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)
        self.errors: list[str] = []
        self.logged_errors: list[str] = []
        self.category = "generic"

        # Set up logging handler to collect error messages
        class ErrorCollectingHandler(logging.Handler):
            def __init__(self, error_list):
                super().__init__()
                self.error_list = error_list

            def emit(self, record):
                if record.levelno >= logging.ERROR:
                    self.error_list.append(record.getMessage())

        self.error_handler = ErrorCollectingHandler(self.logged_errors)
        logging.getLogger().addHandler(self.error_handler)

    def init_page(self):
        # Determine title based on category
        app_name = self.app_config.app.name

        if self.state.error.has_error:
            self.category = self.state.error.category
            self.errors = self.state.error.error_messages
        else:
            self.errors = (
                self.logged_errors[:] if self.logged_errors else [_("error.generic")]
            )

        if self.category == "compatibility":
            title = _("error.title.compatibility") % {"app_name": app_name}
            subtitle = _("error.subtitle.compatibility")
        elif self.category == "installation":
            title = _("error.title.installation")
            subtitle = _("error.subtitle.installation")
        else:
            title = _("error.title.generic")
            subtitle = _("error.subtitle.generic")

        page_layout = GenericPageLayout(
            self,
            title,
            secondary_btn_txt=_("btn.quit"),
            secondary_btn_command=lambda: self._quit_application(),
        )
        self.page_frame = page_layout.content_frame
        self.page_frame.columnconfigure(0, weight=1)
        self.page_frame.rowconfigure(1, weight=1)

        # Subtitle
        subtitle_key = f"error.subtitle.{self.category}"
        subtitle = _(subtitle_key)
        subtitle_label = ctk.CTkSimpleLabel(
            self.page_frame,
            text=subtitle,
            justify=self._ui.di.l,
            wraplength="self",
            font=self._ui.fonts.small,
            pady=5,
        )
        subtitle_label.grid(row=0, column=0, pady=(10, 5), sticky="ew")

        self.info_frame_raster = InfoFrame(self.page_frame)
        self.info_frame_raster.grid(row=1, column=0, pady=5, padx=10, sticky="nsew")

        self._display_errors()

    def _display_errors(self):
        """Display the current errors in the UI."""
        self.info_frame_raster.flush_labels()
        for i, error in enumerate(self.errors):
            self.info_frame_raster.add_label(f"error_{i}", error)
        logging.error(f"Displaying {len(self.errors)} errors to user")

    def validate_input(self) -> PageValidationResult:
        """Error page doesn't require validation."""
        return PageValidationResult(True)

    def _quit_application(self):
        """Quit the application."""
        logging.info("Quitting from error page")
        exit_code = 1 if self.category == "installation" else 0
        raise SystemExit(exit_code)
