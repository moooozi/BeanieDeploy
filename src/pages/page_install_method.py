import contextlib
import logging
import tkinter as tk
from sys import argv

import vgkit as vgk

from compatibility_checks import CheckType
from models.kickstart import KickstartConfig
from models.page import Page, PageValidationResult
from models.partition import PartitioningMethod
from multilingual import _
from pages.page_user_info import get_full_name, get_username
from templates.multi_radio_buttons import MultiRadioButtons


class PageInstallMethod(Page):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.install_method_var = tk.StringVar(parent)

        self.enable_encryption_toggle_var = tk.BooleanVar(parent)

    def init_page(self):
        # Get selected spin from state
        selected_spin = self.state.installation.selected_spin
        if not selected_spin:
            logging.error("No spin selected when initializing install method page")
            return

        self.set_page_title(_("windows.question") % {"distro_name": selected_spin.name})
        self.columnconfigure(0, weight=1)

        self.selected_spin_name = selected_spin.name

        # Calculate space requirements using config
        # Get partition size, defaulting to 0 if partition is None
        partition_size = (
            self.state.installation.partition.tmp_part_size
            if self.state.installation.partition
            else 0
        )

        space_clean = (
            self.app_config.app.linux_boot_partition_size.bytes_value
            + self.app_config.app.additional_failsafe_space.bytes_value
            + partition_size * 2
        )

        done_checks = self.state.compatibility.done_checks
        if "--skip_check" not in argv and done_checks is not None:
            has_space = done_checks.checks[CheckType.RESIZABLE].result > space_clean
        else:
            has_space = True

        is_auto_installable = selected_spin.is_auto_installable

        default = (
            PartitioningMethod.CUSTOM.value
            if not is_auto_installable
            else PartitioningMethod.CLEAN_DISK.value
        )
        self.install_method_var.set(default)

        clean_disk_error_msg = ""
        if not is_auto_installable:
            clean_disk_error_msg = _("warn.not.available")
        else:
            if not has_space:
                clean_disk_error_msg = _("warn.space")

        install_methods_dict = {
            PartitioningMethod.CLEAN_DISK.value: {
                "name": _("install.option.clean_disk"),
                "error": clean_disk_error_msg,
                "description": _("install.option.clean_disk.desc"),
                "advanced": False,
            },
            PartitioningMethod.CUSTOM.value: {
                "name": _("install.option.custom"),
                "description": _("install.option.custom.desc"),
                "advanced": True,
            },
        }

        radio_buttons = MultiRadioButtons(
            self,
            items=install_methods_dict,
            variable=self.install_method_var,
            validation_callback=self.show_more_widgets_if_needed,
            advanced_options_txt=_("show.advanced.options"),
        )
        radio_buttons.grid(row=0, column=0, sticky="ew")

        self.method_options_frame = vgk.Frame(self)
        self.method_options_frame.grid(row=1, column=0, sticky="we")
        self.rowconfigure(0, weight=3, uniform="a")
        self.rowconfigure(1, weight=1, uniform="a")

        # Encryption checkbox
        self.check_encrypt_frame = vgk.Frame(self.method_options_frame)
        self.check_encrypt_frame.grid(row=0, column=0, pady=5, sticky="w")
        self.check_encrypt = vgk.CheckBox(
            self.check_encrypt_frame,
            text=_("encrypted.root"),
            variable=self.enable_encryption_toggle_var,
            command=self.update_encrypt_note_visiblity,
            onvalue=True,
            offvalue=False,
            width=99,
        )
        self.check_encrypt.grid(ipady=5, row=0, column=0, sticky=self._ui.di.w)

        self.encrypt_pass_note = vgk.Label(
            self.check_encrypt_frame,
            text=f"ⓘ {_('encrypt.reminder.txt')}",
            font=self._ui.fonts.tiny,
            text_color=self._ui.colors.primary,
        )
        self.encrypt_pass_note.grid(padx=10, row=0, column=1, sticky=self._ui.di.w)
        self.update_encrypt_note_visiblity()

        # Warning label for destructive options
        self.warning_label = vgk.Label(
            self.method_options_frame,
            text="",
            font=self._ui.fonts.smaller,
            text_color=self._ui.colors.red,
            justify=self._ui.di.l,
            pady=5,
        )
        self.warning_label.grid(row=3, column=0, sticky=self._ui.di.w)
        # Update warning based on install method
        self._warning_trace_id = self.install_method_var.trace_add(
            "write", self.update_warning_label
        )

        self.update_idletasks()
        self.show_more_widgets_if_needed()
        self.update_warning_label()

    def update_warning_label(self, *_args):
        # print args for debugging
        method = self.install_method_var.get()
        if method == PartitioningMethod.CLEAN_DISK.value:
            self.warning_label.configure(text=_("warn.backup.device"))
        else:
            self.warning_label.configure(text="")

    def update_encrypt_note_visiblity(self):
        """Show/hide encryption reminder based on checkbox state."""
        if self.enable_encryption_toggle_var.get():
            self.encrypt_pass_note.grid()
        else:
            self.encrypt_pass_note.grid_remove()

    def show_more_widgets_if_needed(self):
        """Show/hide additional widgets based on selected install method."""
        method = self.install_method_var.get()
        # Hide all method-specific widgets first
        self.warning_label.grid_remove()

        # Hide checkboxes for custom install (they don't make sense)
        if method == PartitioningMethod.CUSTOM.value:
            self.check_encrypt_frame.grid_remove()
        else:
            self.check_encrypt_frame.grid()

        # Show method-specific widgets
        if method == PartitioningMethod.CLEAN_DISK.value:
            self.warning_label.grid()

    def validate_input(self) -> PageValidationResult:
        """Validate the selected install method and options."""
        return PageValidationResult(True)

    def on_next(self):
        """Save the install method selection to state."""
        method = self.install_method_var.get()
        logging.info(f"Install method selected: {method}")
        # Update state with install method
        self.state.installation.install_options.partition_method = PartitioningMethod(
            method
        )
        self.state.installation.partition.shrink_space = 0

        if method == PartitioningMethod.CUSTOM.value:
            # Unset Kickstart partitioning settings for custom install
            self.state.installation.kickstart = None
        else:
            # Ensure Kickstart partitioning settings exist for non-custom installs
            if not self.state.installation.kickstart:
                self.state.installation.kickstart = KickstartConfig()

            kickstart = self.state.installation.kickstart
            selected_spin = self.state.installation.selected_spin
            kickstart.should_use_native_firstboot = (
                selected_spin is not None and selected_spin.desktop == "GNOME"
            )
            kickstart.user_username = get_username()
            kickstart.user_full_name = get_full_name()
            partitioning = self.state.installation.kickstart.partitioning
            is_encrypted = self.enable_encryption_toggle_var.get()
            logging.info(f"Encryption enabled: {is_encrypted}")
            partitioning.is_encrypted = is_encrypted

    def on_show(self):
        """Called when page is shown - reinitialize if spin changed."""
        if self.selected_spin_name:
            current_spin = self.state.installation.selected_spin
            if current_spin and self.selected_spin_name != current_spin.name:
                logging.info("Spin changed, reinitializing page")
                # Remove trace before destroying widgets to avoid callbacks on dead widgets
                with contextlib.suppress(Exception):
                    self.install_method_var.trace_remove(
                        "write", self._warning_trace_id
                    )
                # Clear the frame and reinitialize
                for widget in self.winfo_children():
                    widget.destroy()
                self.initiated = False
                self.init_page()
                self.initiated = True
