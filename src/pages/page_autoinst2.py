import logging
import tkinter as tk

import customtkinter as ctk

from models.page import Page, PageValidationResult
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
            logging.error("No spin selected when initializing auto-install page")
            return

        self.page_manager.set_title(
            _("windows.question") % {"distro_name": selected_spin.name}
        )

        page_frame = self
        frame_checkboxes = ctk.CTkContainer(
            page_frame,
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
        check_wifi.grid(ipady=5, pady=(5, 0), row=0, column=0, sticky=self._ui.di.w)

        check_encrypt = ctk.CTkCheckBox(
            frame_checkboxes,
            text=_("encrypted.root"),
            variable=self.enable_encryption_toggle_var,
            command=lambda: self.show_encrypt_options(
                self.enable_encryption_toggle_var
            ),
            onvalue=True,
            offvalue=False,
            width=99,
        )
        check_encrypt.grid(ipady=5, row=2, column=0, sticky=self._ui.di.w)

        self.encrypt_pass_note = ctk.CTkSimpleLabel(
            frame_checkboxes,
            text=f"ⓘ {_('encrypt.reminder.txt')}",
            font=self._ui.fonts.smaller,
            text_color=self._ui.colors.primary,
        )
        self.encrypt_pass_note.grid(
            pady=5, padx=(0, 0), row=2, column=1, sticky=self._ui.di.w
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
            kickstart.partitioning.is_encrypted = (
                self.enable_encryption_toggle_var.get()
            )

        if install_options:
            install_options.export_wifi = self.export_wifi_toggle_var.get()

        logging.info(
            f"Auto-install settings: encryption={kickstart.partitioning.is_encrypted if kickstart else False}, wifi_export={install_options.export_wifi if install_options else False}"
        )
