from PySide6.QtWidgets import (
    QVBoxLayout, QLabel, QLineEdit, QWidget, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from typing import Optional

from models.pyside6_page import PySide6Page, PageValidationResult
from templates.pyside6_generic_page_layout import GenericPageLayout
from templates.pyside6_multi_radio_buttons import MultiRadioButtons
from models.data_units import DataUnit
from compatibility_checks import CheckType

class PySide6PageInstallMethod(PySide6Page):
    button_state_changed = Signal(bool, bool)

    def __init__(self, parent: Optional[QWidget], page_name: str):
        super().__init__(parent, page_name)
        self.install_method_key: Optional[str] = None
        self.dualboot_size_str: str = ""
        self.install_methods_dict = {}
        self.page_layout: Optional[GenericPageLayout] = None
        self.size_entry: Optional[QLineEdit] = None

    def init_page(self):
        self.logger.info("Initializing Install Method Page (PySide6)")
        selected_spin = self.state.installation.selected_spin
        if not selected_spin:
            self.logger.error("No spin selected when initializing install method page")
            return

        self.page_layout = GenericPageLayout(
            self,
            title=self.LN.windows_question % selected_spin.name,
            primary_btn_txt=self.LN.btn_next,
            primary_btn_command=self.navigate_next,
            secondary_btn_txt=self.LN.btn_back,
            secondary_btn_command=self.navigate_previous,
        )

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.page_layout)

        # Calculate space requirements
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
        from sys import argv
        if "--skip_check" not in argv and done_checks is not None:
            dualboot_space_available = (
                int(done_checks.checks[CheckType.RESIZABLE].result) > space_dualboot
            )
            replace_win_space_available = (
                int(done_checks.checks[CheckType.RESIZABLE].result) > space_clean
            )
            selected_spin_size_bytes = DataUnit.from_string(selected_spin.size).bytes
            max_size = DataUnit.from_bytes(
                done_checks.checks[CheckType.RESIZABLE].result
                - selected_spin_size_bytes
                - self.app_config.app.additional_failsafe_space.bytes_value
            ).to_gigabytes()
            max_size = round(max_size, 2)
        else:
            dualboot_space_available = True
            replace_win_space_available = True
            max_size = 9999

        is_auto_installable = selected_spin.is_auto_installable
        default = "custom" if not is_auto_installable else "replace_win"
        self.install_method_key = default

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

        self.install_methods_dict = {
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

        # Radio buttons for install method selection
        self.radio_group = MultiRadioButtons(
            self.page_layout.content_frame,
            items=self.install_methods_dict,
            validation_callback=self._on_install_method_changed
        )
        self.radio_group.selection_changed.connect(self._on_method_selected)
        self.page_layout.content_layout.addWidget(self.radio_group)
        self.radio_group.set_selected_key(default)

        # Dualboot size entry
        min_size = DataUnit.from_bytes(self.app_config.app.dualboot_required_space.bytes_value).to_gigabytes()
        self.size_entry = QLineEdit(self.page_layout.content_frame)
        self.size_entry.setPlaceholderText(f"{min_size} - {max_size} GB")
        self.size_entry.textChanged.connect(self._on_dualboot_size_change)

        self.warn_backup_label = QLabel(
            self.LN.warn_backup_files_txt % f"{self._get_sys_drive_letter()}:\\"
        )
        self.warn_backup_label.setStyleSheet("color: red; font-size: small;")
        self.size_label_pre = QLabel(self.LN.dualboot_size_txt % selected_spin.name)
        self.size_label_post = QLabel(f"({min_size}GB - {max_size}GB)")
        self.size_label_post.setStyleSheet("color: blue; font-size: small;")

        self._show_more_options_if_needed()

    def _on_method_selected(self, method_key: str):
        self.install_method_key = method_key
        self._show_more_options_if_needed()
        self.update_button_states()

    def _on_install_method_changed(self):
        self.update_button_states()

    def _on_dualboot_size_change(self, text: str):
        self.dualboot_size_str = text
        self.update_button_states()

    def _show_more_options_if_needed(self):
        # Remove all widgets first
        layout = self.page_layout.content_layout
        for widget in [self.warn_backup_label, self.size_label_pre, self.size_entry, self.size_label_post]:
            layout.removeWidget(widget)
            widget.setParent(None)

        if self.install_method_key == "dualboot":
            layout.addWidget(self.size_label_pre)
            layout.addWidget(self.size_entry)
            layout.addWidget(self.size_label_post)
        elif self.install_method_key == "replace_win":
            layout.addWidget(self.warn_backup_label)

    def validate_input(self) -> PageValidationResult:
        method = self.install_method_key
        available_methods = self._get_available_install_methods()
        if method not in available_methods:
            return PageValidationResult(False, "Selected install method is not available")

        if method == "dualboot":
            size_str = self.dualboot_size_str.strip()
            if not size_str:
                return PageValidationResult(False, "Dual boot size is required")
            try:
                size_value = float(size_str)
                if size_value <= 0:
                    return PageValidationResult(False, "Dual boot size must be positive")
            except ValueError:
                return PageValidationResult(False, "Dual boot size must be a valid number")

        return PageValidationResult(True)

    def on_next(self):
        method = self.install_method_key
        self.state.installation.install_options.partition_method = method

        if method == "dualboot":
            size = DataUnit.from_gigabytes(float(self.dualboot_size_str))
            if not self.state.installation.partition:
                from models.partition import Partition
                self.state.installation.partition = Partition()
            self.state.installation.partition.shrink_space = size.bytes
        elif method == "custom":
            if self.state.installation.partition:
                self.state.installation.partition.shrink_space = 0
                self.state.installation.partition.boot_part_size = 0
                self.state.installation.partition.efi_part_size = 0

        self.logger.info(f"Install method selected: {method}")

    def on_show(self):
        if hasattr(self, 'selected_spin_name'):
            current_spin = self.state.installation.selected_spin
            if current_spin and self.selected_spin_name != current_spin.name:
                self.logger.info("Spin changed, reinitializing page")
                for widget in self.winfo_children():
                    widget.deleteLater()
                self._initiated = False
                self.init_page()
                self._initiated = True

    def _get_available_install_methods(self):
        return ["dualboot", "replace_win", "custom"]

    def _get_sys_drive_letter(self):
        import os
        return os.environ.get('SYSTEMDRIVE', 'C:').replace(':', '')

    def show_validation_error(self, message: str):
        QMessageBox.warning(self, "Validation Error", message)