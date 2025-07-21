import customtkinter as ctk
from compatibility_checks import CheckType
from models.data_units import DataUnit
from templates.generic_page_layout import GenericPageLayout
from templates.multi_radio_buttons import MultiRadioButtons
import tkinter_templates as tkt
from models.page import Page, PageValidationResult
import tkinter as tk
from sys import argv


class PageInstallMethod(Page):
    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)
        self.install_method_var = tk.StringVar(parent)
        self.dualboot_size_var = tk.StringVar(parent)

    def init_page(self):
        # Get selected spin from state
        selected_spin = self.state.installation.selected_spin
        if not selected_spin:
            self.logger.error("No spin selected when initializing install method page")
            return

        page_layout = GenericPageLayout(
            self,
            self.LN.windows_question % selected_spin.name,
            self.LN.btn_next,
            lambda: self.navigate_next(),
            self.LN.btn_back,
            lambda: self.navigate_previous(),
        )
        page_frame = page_layout.content_frame

        self.selected_spin_name = selected_spin.name

        # Calculate space requirements using config
        space_dualboot = (
            self.config.app.dualboot_required_space.bytes_value
            + self.config.app.linux_boot_partition_size.bytes_value
            + self.config.app.additional_failsafe_space.bytes_value
            + self.state.installation.partition.tmp_part_size * 2
        )
        space_clean = (
            self.config.app.linux_boot_partition_size.bytes_value
            + self.config.app.additional_failsafe_space.bytes_value
            + self.state.installation.partition.tmp_part_size * 2
        )

        if "--skip_check" not in argv:
            done_checks = self.state.compatibility.done_checks
            dualboot_space_available = (
                done_checks.checks[CheckType.RESIZABLE].result > space_dualboot
            )
            replace_win_space_available = (
                done_checks.checks[CheckType.RESIZABLE].result > space_clean
            )
            max_size = DataUnit.from_bytes(
                done_checks.checks[CheckType.RESIZABLE].result
                - selected_spin.size
                - self.config.app.additional_failsafe_space.bytes_value
            ).to_gigabytes()
            max_size = round(max_size, 2)
        else:
            dualboot_space_available = True
            replace_win_space_available = True
            max_size = 9999

        is_auto_installable = selected_spin.is_auto_installable

        default = "custom" if not is_auto_installable else "replace_win"
        self.install_method_var.set(default)

        dualboot_error_msg = ""
        replace_win_error_msg = ""
        if not is_auto_installable:
            dualboot_error_msg = self.LN.warn_not_available
            replace_win_error_msg = self.LN.warn_not_available
        else:
            if not dualboot_space_available:
                dualboot_error_msg = self.LN.warn_space
            if not replace_win_space_available:
                replace_win_error_msg = self.LN.warn_space

        install_methods_dict = {
            "dualboot": {
                "name": self.LN.windows_options["dualboot"],
                "error": dualboot_error_msg,
                "advanced": True,
            },
            "replace_win": {
                "name": self.LN.windows_options["replace_win"],
                "error": replace_win_error_msg,
                "advanced": False,
            },
            "custom": {
                "name": self.LN.windows_options["custom"],
                "advanced": True,
            },
        }

        radio_buttons = MultiRadioButtons(
            page_frame,
            install_methods_dict,
            self.install_method_var,
            lambda: self.show_more_options_if_needed(),
        )
        radio_buttons.pack(expand=1, fill="x")

        min_size = DataUnit.from_bytes(self.config.app.dualboot_required_space.bytes_value).to_gigabytes()
        self.entry1_frame = ctk.CTkFrame(page_frame, height=300)
        self.entry1_frame.pack_propagate(False)
        self.entry1_frame.pack(
            fill="both",
            side="bottom",
        )

        self.warn_backup_sys_drive_files = tkt.add_text_label(
            self.entry1_frame,
            text=self.LN.warn_backup_files_txt % f"{self._get_sys_drive_letter()}:\\",
            font=tkt.FONTS_smaller,
            foreground=tkt.color_red,
            pack=False,
        )
        self.size_dualboot_txt_pre = tkt.add_text_label(
            self.entry1_frame,
            text=self.LN.dualboot_size_txt % selected_spin.name,
            font=tkt.FONTS_smaller,
            pack=False,
        )
        self.size_dualboot_entry = ctk.CTkEntry(
            self.entry1_frame,
            width=10,
            textvariable=self.dualboot_size_var,
        )
        validation_func = self.register(
            lambda x: x.replace(".", "", 1).isdigit()
            and min_size <= float(x) <= max_size
        )
        self.size_dualboot_entry.configure(
            validate="none", validatecommand=(validation_func, "%P")
        )
        self.size_dualboot_txt_post = tkt.add_text_label(
            self.entry1_frame,
            text="(%sGB - %sGB)" % (min_size, max_size),
            font=tkt.FONTS_smaller,
            foreground=tkt.color_blue,
            pack=False,
        )
        tkt.var_tracer(
            self.dualboot_size_var,
            "write",
            lambda *args: self.size_dualboot_entry.validate(),
        )

        self.update_idletasks()
        self.show_more_options_if_needed()  # GUI bugfix

    def show_more_options_if_needed(self):
        """Show/hide additional options based on selected install method."""
        self.warn_backup_sys_drive_files.grid_forget()
        self.size_dualboot_txt_pre.grid_forget()
        self.size_dualboot_entry.grid_forget()
        self.size_dualboot_txt_post.grid_forget()
        
        if self.install_method_var.get() == "dualboot":
            self.size_dualboot_txt_pre.grid(
                pady=5, padx=(10, 0), column=0, row=0, sticky=self.DI_VAR.w
            )
            self.size_dualboot_entry.grid(pady=5, padx=5, column=1, row=0)
            self.size_dualboot_txt_post.grid(
                pady=5, padx=(0, 0), column=2, row=0, sticky=self.DI_VAR.w
            )
        elif self.install_method_var.get() == "replace_win":
            self.warn_backup_sys_drive_files.grid(
                pady=5, padx=(10, 0), column=0, row=0, sticky=self.DI_VAR.w
            )

    def validate_input(self) -> PageValidationResult:
        """Validate the selected install method and options."""
        method = self.install_method_var.get()
        
        # Check if method is available
        available_methods = self._get_available_install_methods()
        if method not in available_methods:
            return PageValidationResult(False, "Selected install method is not available")
        
        # Validate dual boot size if needed
        if method == "dualboot":
            if not self.size_dualboot_entry.validate():
                return PageValidationResult(False, "Invalid dual boot size")
            
            syntax_invalid = "invalid" in self.size_dualboot_entry.state()
            if syntax_invalid:
                return PageValidationResult(False, "Dual boot size is invalid")
        
        return PageValidationResult(True)

    def on_next(self):
        """Save the install method selection to state."""
        method = self.install_method_var.get()
        
        # Update state with install method
        self.state.installation.install_options.partition_method = method
        
        if method == "dualboot":
            # Save dual boot size
            size = DataUnit.from_gigabytes(float(self.dualboot_size_var.get()))
            self.state.installation.partition.shrink_space = size.bytes
        elif method == "custom":
            # Reset partition settings for custom install
            if self.state.installation.partition:
                self.state.installation.partition.shrink_space = 0
                self.state.installation.partition.boot_part_size = 0
                self.state.installation.partition.efi_part_size = 0
        
        self.logger.info(f"Install method selected: {method}")

    def on_show(self):
        """Called when page is shown - reinitialize if spin changed."""
        if hasattr(self, 'selected_spin_name'):
            current_spin = self.state.installation.selected_spin
            if current_spin and self.selected_spin_name != current_spin.name:
                self.logger.info("Spin changed, reinitializing page")
                # Clear the frame and reinitialize
                for widget in self.winfo_children():
                    widget.destroy()
                self._initiated = False
                self.init_page()
                self._initiated = True

    def _get_available_install_methods(self):
        """Get list of available install methods based on current state."""
        # This would typically come from your compatibility checks or state
        # For now, return a basic list
        return ["dualboot", "replace_win", "custom"]

    def _get_sys_drive_letter(self):
        """Get the system drive letter."""
        # This should be moved to a utility function
        import os
        return os.environ.get('SYSTEMDRIVE', 'C:').replace(':', '')
