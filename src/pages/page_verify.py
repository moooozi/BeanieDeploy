from templates.generic_page_layout import GenericPageLayout
from templates.info_frame import InfoFrame
from models.page import Page, PageValidationResult
import tkinter as tk
import customtkinter as ctk
from tkinter_templates import flush_frame

class PageVerify(Page):
    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)
        
        # Initialize install options if it doesn't exist
        if not self.state.installation.install_options:
            from models.install_options import InstallOptions
            self.state.installation.install_options = InstallOptions()
            
        install_options = self.state.installation.install_options
        self.auto_restart_toggle_var = tk.BooleanVar(
            parent, install_options.auto_restart if install_options else False
        )

    def init_page(self):
        page_layout = GenericPageLayout(
            self,
            self.LN.verify_question,
            self.LN.btn_install,
            lambda: self.navigate_next(),
            self.LN.btn_back,
            lambda: self.navigate_previous(),
        )
        page_frame = page_layout.content_frame
        
        # Get data from state
        selected_spin = self.state.installation.selected_spin
        kickstart = self.state.installation.kickstart
        install_options = self.state.installation.install_options
        
        if not selected_spin:
            self.logger.error("No spin selected when showing verify page")
            return
            
        from core.verify_logic import build_review_text
        review_sel = build_review_text(selected_spin, kickstart, install_options, self.LN)

        self.info_frame_raster = InfoFrame(page_frame)

        for i, text in enumerate(review_sel):
            self.info_frame_raster.add_label(f"review_{i}", text)
        self.info_frame_raster.pack(side="top", fill="x", pady=10, padx=5)

        page_frame.columnconfigure(0, weight=1)
        page_frame.grid_rowconfigure(0, weight=3)

        check_restart = ctk.CTkCheckBox(
            page_frame,
            text=self.LN.add_auto_restart,
            variable=self.auto_restart_toggle_var,
            onvalue=True,
            offvalue=False,
            width=99,
        )
        check_restart.pack(ipady=8, side="top", anchor="w")

    def validate_input(self) -> PageValidationResult:
        """Validate the installation settings."""
        # All verification settings are valid by default
        return PageValidationResult(True)

    def on_next(self):
        """Save final installation settings and prepare for installation."""
        install_options = self.state.installation.install_options
        if install_options:
            install_options.auto_restart = self.auto_restart_toggle_var.get()
            
        self.logger.info(f"Installation verified. Auto restart: {install_options.auto_restart if install_options else False}")

    def on_show(self):
        """Called when the page is shown - reinitialize to show current selections."""
        if self._initiated:
            flush_frame(self)
            self._initiated = False
            self.init_page()
            self._initiated = True
