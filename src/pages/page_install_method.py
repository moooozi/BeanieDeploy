import logging
import tkinter as tk
from sys import argv

import vgkit as vgk

from compatibility_checks import CheckType
from models.data_units import DataUnit
from models.page import Page, PageValidationResult
from models.partition import PartitioningMethod
from multilingual import _
from templates.multi_radio_buttons import MultiRadioButtons


class PageInstallMethod(Page):
    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)
        self.install_method_var = tk.StringVar(parent)
        self.dualboot_size_var = tk.StringVar(parent)

    def init_page(self):
        # Get selected spin from state
        selected_spin = self.state.installation.selected_spin
        if not selected_spin:
            logging.error("No spin selected when initializing install method page")
            return

        self.page_manager.set_title(
            _("windows.question") % {"distro_name": selected_spin.name}
        )
        # Primary and secondary buttons use defaults
        self.columnconfigure(0, weight=1)

        self.selected_spin_name = selected_spin.name

        # Calculate space requirements using config
        # Get partition size, defaulting to 0 if partition is None
        partition_size = (
            self.state.installation.partition.tmp_part_size
            if self.state.installation.partition
            else 0
        )

        space_dualboot = (
            self.app_config.app.dualboot_required_space.bytes_value
            + self.app_config.app.linux_boot_partition_size.bytes_value
            + self.app_config.app.additional_failsafe_space.bytes_value
            + partition_size * 2
        )
        space_clean = (
            self.app_config.app.linux_boot_partition_size.bytes_value
            + self.app_config.app.additional_failsafe_space.bytes_value
            + partition_size * 2
        )

        done_checks = self.state.compatibility.done_checks
        if "--skip_check" not in argv and done_checks is not None:
            has_dualboot_space = (
                done_checks.checks[CheckType.RESIZABLE].result > space_dualboot
            )
            has_space = done_checks.checks[CheckType.RESIZABLE].result > space_clean
            # Convert string size to bytes for arithmetic operation
            # Spin size is already in bytes
            selected_spin_size_bytes = selected_spin.size
            max_size_bytes = (
                done_checks.checks[CheckType.RESIZABLE].result
                - selected_spin_size_bytes
                - self.app_config.app.additional_failsafe_space.bytes_value
            )
        else:
            has_dualboot_space = True
            has_space = True
            max_size_bytes = DataUnit.from_gibibytes(9999).bytes

        max_size_gb = DataUnit(max_size_bytes).gigabytes

        is_auto_installable = selected_spin.is_auto_installable

        default = (
            PartitioningMethod.CUSTOM.value
            if not is_auto_installable
            else PartitioningMethod.CLEAN_DISK.value
        )
        self.install_method_var.set(default)

        dualboot_error_msg = ""
        replace_win_error_msg = ""
        clean_disk_error_msg = ""
        if not is_auto_installable:
            dualboot_error_msg = _("warn.not.available")
            replace_win_error_msg = _("warn.not.available")
            clean_disk_error_msg = _("warn.not.available")
        else:
            if not has_dualboot_space:
                dualboot_error_msg = _("warn.space")
            if not has_space:
                clean_disk_error_msg = _("warn.space")
                replace_win_error_msg = _("warn.space")

        install_methods_dict = {
            PartitioningMethod.DUALBOOT.value: {
                "name": _("install.option.dualboot") + f" ({_('warn.experimental')})",
                "error": dualboot_error_msg,
                "advanced": True,
            },
            PartitioningMethod.CLEAN_DISK.value: {
                "name": _("install.option.clean_disk"),
                "error": clean_disk_error_msg,
                "advanced": False,
            },
            PartitioningMethod.REPLACE_WIN.value: {
                "name": _("install.option.replace_win"),
                "error": replace_win_error_msg,
                "advanced": False,
            },
            PartitioningMethod.CUSTOM.value: {
                "name": _("install.option.custom"),
                "advanced": True,
            },
        }

        radio_buttons = MultiRadioButtons(
            self,
            items=install_methods_dict,
            variable=self.install_method_var,
            validation_callback=lambda: self.show_more_widgets_if_needed(),
            advanced_options_txt=_("show.advanced.options"),
        )
        radio_buttons.grid(row=0, column=0, sticky="ew")

        min_size_gb = DataUnit(
            self.app_config.app.dualboot_required_space.bytes_value
        ).gigabytes
        self.conditional_frame = vgk.Frame(self)
        self.conditional_frame.grid(row=1, column=0, sticky="we")
        self.rowconfigure(0, weight=5, uniform="a")
        self.rowconfigure(1, weight=1, uniform="a")
        self.conditional_frame.columnconfigure(0, weight=1)

        win_drive_letter = self.state.installation.windows_partition.drive_letter
        self.warn_backup_sys_drive_files = vgk.Label(
            self.conditional_frame,
            text=_("warn.backup.system_drive") % {"drive": f"{win_drive_letter}:\\"},
            font=self._ui.fonts.smaller,
            text_color=self._ui.colors.red,
            justify=self._ui.di.l,
            pady=5,
        )
        self.warn_backup_device = vgk.Label(
            self.conditional_frame,
            text=_("warn.backup.device"),
            font=self._ui.fonts.smaller,
            text_color=self._ui.colors.red,
            justify=self._ui.di.l,
            pady=5,
        )
        self.size_dualboot_txt_pre = vgk.Label(
            self.conditional_frame,
            text=_("dualboot.size.txt") % {"distro_name": selected_spin.name},
            font=self._ui.fonts.smaller,
            justify=self._ui.di.l,
            pady=5,
        )
        self.size_dualboot_entry = vgk.Entry(
            self.conditional_frame,
            width=100,
            textvariable=self.dualboot_size_var,
        )
        validation_func = self.register(
            lambda x: x.replace(".", "", 1).isdigit()
            and min_size_gb <= float(x) <= max_size_gb
        )
        self.size_dualboot_entry.configure(
            validate="none", validatecommand=(validation_func, "%P")
        )
        # Format size range using humanize for clarity
        min_size_txt = self.app_config.app.dualboot_required_space.to_gibibytes()
        max_size_txt = DataUnit(max_size_bytes).to_gibibytes()
        size_range_text = f"({min_size_txt}GiB - {max_size_txt}GiB)"
        self.size_dualboot_txt_post = vgk.Label(
            self.conditional_frame,
            text=size_range_text,
            font=self._ui.fonts.smaller,
            text_color=self._ui.colors.primary,
            justify=self._ui.di.l,
            pady=5,
        )

        self.update_idletasks()
        self.show_more_widgets_if_needed()  # GUI bugfix

    def _on_dualboot_size_change(self):
        """Called when dualboot size changes."""
        # Could implement real-time validation feedback here if needed

    def show_more_widgets_if_needed(self):
        """Show/hide additional widgets based on selected install method."""
        self.warn_backup_sys_drive_files.grid_forget()
        self.warn_backup_device.grid_forget()
        self.size_dualboot_txt_pre.grid_forget()
        self.size_dualboot_entry.grid_forget()
        self.size_dualboot_txt_post.grid_forget()

        if self.install_method_var.get() == PartitioningMethod.DUALBOOT.value:
            self.size_dualboot_txt_pre.grid(column=0, row=0, sticky=self._ui.di.w)
            self.size_dualboot_entry.grid(padx=5, column=1, row=0)
            self.size_dualboot_txt_post.grid(column=2, row=0, sticky=self._ui.di.w)
        elif self.install_method_var.get() == PartitioningMethod.REPLACE_WIN.value:
            self.warn_backup_sys_drive_files.grid(column=0, row=0, sticky=self._ui.di.w)
        elif self.install_method_var.get() == PartitioningMethod.CLEAN_DISK.value:
            self.warn_backup_device.grid(column=0, row=0, sticky=self._ui.di.w)

    def validate_input(self) -> PageValidationResult:
        """Validate the selected install method and options."""
        method = self.install_method_var.get()

        # Validate dual boot size if needed
        if method == PartitioningMethod.DUALBOOT.value:
            try:
                size_str = self.dualboot_size_var.get().strip()
                if not size_str:
                    return PageValidationResult(False, "Dual boot size is required")

                size_value = float(size_str)
                if size_value <= 0:
                    return PageValidationResult(
                        False, "Dual boot size must be positive"
                    )

            except ValueError:
                return PageValidationResult(
                    False, "Dual boot size must be a valid number"
                )

        return PageValidationResult(True)

    def on_next(self):
        """Save the install method selection to state."""
        method = self.install_method_var.get()
        # Update state with install method
        self.state.installation.install_options.partition_method = PartitioningMethod(
            method
        )

        if method == PartitioningMethod.DUALBOOT.value:
            # Save dual boot size
            size = DataUnit.from_gigabytes(float(self.dualboot_size_var.get()))
            if not self.state.installation.partition:
                from models.partition import PartitioningOptions

                self.state.installation.partition = PartitioningOptions()
            self.state.installation.partition.shrink_space = size.bytes
        elif method == PartitioningMethod.CUSTOM.value:
            # Reset partition settings for custom install
            if self.state.installation.partition:
                self.state.installation.partition.shrink_space = 0
                self.state.installation.partition.boot_part_size = 0

        logging.info(f"Install method selected: {method}")

    def on_show(self):
        """Called when page is shown - reinitialize if spin changed."""
        if hasattr(self, "selected_spin_name"):
            current_spin = self.state.installation.selected_spin
            if current_spin and self.selected_spin_name != current_spin.name:
                logging.info("Spin changed, reinitializing page")
                # Clear the frame and reinitialize
                for widget in self.winfo_children():
                    widget.destroy()
                self._initiated = False
                self.init_page()
                self._initiated = True
