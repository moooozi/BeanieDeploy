from templates.generic_page_layout import GenericPageLayout
from templates.info_frame import InfoFrame
from models.page import Page, PageValidationResult
import tkinter as tk
import customtkinter as ctk
from tkinter_templates import flush_frame
from multilingual import _
from config.settings import PartitioningMethod

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
            _("verify.question"),
            _("btn.install"),
            lambda: self.navigate_next(),
            _("btn.back"),
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
            
        review_sel = build_review_text(selected_spin, kickstart, install_options)

        self.info_frame_raster = InfoFrame(page_frame)

        for i, text in enumerate(review_sel):
            self.info_frame_raster.add_label(f"review_{i}", text)
        self.info_frame_raster.pack(side="top", fill="x", pady=10, padx=5)

        page_frame.columnconfigure(0, weight=1)
        page_frame.grid_rowconfigure(0, weight=3)

        check_restart = ctk.CTkCheckBox(
            page_frame,
            text=_("add.auto.restart"),
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


def build_review_text(selected_spin, kickstart, install_options):
    review_sel = []
    if kickstart and getattr(kickstart, 'partitioning', None) and kickstart.partitioning.method == PartitioningMethod.CUSTOM:
        review_sel.append(_("verify.no.autoinst") % {"distro_name": selected_spin.name})
    else:
        if kickstart and getattr(kickstart, 'partitioning', None) and kickstart.partitioning.method == PartitioningMethod.DUALBOOT:
            review_sel.append(_("verify.autoinst.dualboot") % {"distro_name": selected_spin.name})
            review_sel.append(_("verify.autoinst.keep.data"))
        elif kickstart and getattr(kickstart, 'partitioning', None) and kickstart.partitioning.method == PartitioningMethod.REPLACE_WIN:
            review_sel.append(_("verify.autoinst.replace.win") % {"distro_name": selected_spin.name})
            review_sel.append(_("verify.autoinst.rm.all"))
        if install_options and getattr(install_options, 'export_wifi', False):
            review_sel.append(_("verify.autoinst.wifi") % {"distro_name": selected_spin.name})
    return review_sel
