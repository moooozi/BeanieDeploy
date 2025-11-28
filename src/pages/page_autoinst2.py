from templates.generic_page_layout import GenericPageLayout
from models.page import Page, PageValidationResult
import tkinter as tk
import customtkinter as ctk
from tkinter_templates import FONTS_smaller, color_blue
from multilingual import _


class PageAutoinst2(Page):
    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)
        
        # Initialize kickstart if it doesn't exist
        if not self.state.installation.kickstart:
            from models.kickstart import KickstartConfig
            self.state.installation.kickstart = KickstartConfig()
            
        # Initialize install options if it doesn't exist  
        if not self.state.installation.install_options:
            from models.install_options import InstallOptions
            self.state.installation.install_options = InstallOptions()
        
        kickstart = self.state.installation.kickstart
        install_options = self.state.installation.install_options
        
        self.enable_encryption_toggle_var = tk.BooleanVar(
            parent, kickstart.partitioning.is_encrypted if kickstart else False
        )
        self.export_wifi_toggle_var = tk.BooleanVar(
            parent, install_options.export_wifi if install_options else False
        )

    def init_page(self):
        # Get selected spin from state
        selected_spin = self.state.installation.selected_spin
        if not selected_spin:
            self.logger.error("No spin selected when initializing auto-install page")
            return
            
        page_layout = GenericPageLayout(
            self,
            _("windows.question") % {"distro_name": selected_spin.name},
            _("btn.next"),
            lambda: self.navigate_next(),
            _("btn.back"),
            lambda: self.navigate_previous(),
        )
        page_frame = page_layout.content_frame
        frame_checkboxes = ctk.CTkFrame(
            page_frame,
            bg_color="transparent",
            fg_color="transparent",
            corner_radius=0,
            border_width=0,
        )
        frame_checkboxes.grid(row=0, column=0, sticky="ew")
        page_frame.grid_columnconfigure(0, weight=1)
        page_frame.grid_rowconfigure(0, weight=1)

        
        check_wifi = ctk.CTkCheckBox(
            frame_checkboxes,
            text=_("add.import.wifi") % {"distro_name": selected_spin.name},
            variable=self.export_wifi_toggle_var,
            onvalue=True,
            offvalue=False,
            width=99,
        )
        check_wifi.grid(ipady=5, pady=(5, 0), row=0, column=0, sticky=self.DI_VAR.w)

        check_encrypt = ctk.CTkCheckBox(
            frame_checkboxes,
            text=_("encrypted.root"),
            variable=self.enable_encryption_toggle_var,
            command=lambda: self.show_encrypt_options(self.enable_encryption_toggle_var),
            onvalue=True,
            offvalue=False,
            width=99,
        )
        check_encrypt.grid(ipady=5, row=2, column=0, sticky=self.DI_VAR.w)

        # Get max width from config instead of global
        max_width = self.app_config.ui.max_width if hasattr(self.app_config.ui, 'max_width') else 400
        
        self.encrypt_pass_note = ctk.CTkLabel(
            frame_checkboxes,
            wraplength=max_width,
            justify=self.DI_VAR.l,
            text=_("encrypt.reminder.txt"),
            font=FONTS_smaller,
            text_color=color_blue,
        )
        self.encrypt_pass_note.grid(
            pady=5, padx=(0, 0), row=2, column=1, sticky=self.DI_VAR.w
        )
        self.encrypt_pass_note.grid_remove()

        self.show_encrypt_options(self.enable_encryption_toggle_var)

    def show_encrypt_options(self, var):
        """Show/hide encryption reminder based on checkbox state."""
        if var.get():
            self.encrypt_pass_note.grid()
        else:
            self.encrypt_pass_note.grid_remove()

    def validate_input(self) -> PageValidationResult:
        """Validate the auto-install settings."""
        # Auto-install settings are always valid since they're just checkboxes
        return PageValidationResult(True)

    def on_next(self):
        """Save the auto-install settings to state."""
        kickstart = self.state.installation.kickstart
        install_options = self.state.installation.install_options
        
        if kickstart:
            kickstart.partitioning.is_encrypted = self.enable_encryption_toggle_var.get()
            
        if install_options:
            install_options.export_wifi = self.export_wifi_toggle_var.get()
            
        self.logger.info(f"Auto-install settings: encryption={kickstart.partitioning.is_encrypted if kickstart else False}, wifi_export={install_options.export_wifi if install_options else False}")
