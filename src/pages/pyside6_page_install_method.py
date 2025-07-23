from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QMessageBox, QWidget, QLineEdit, QFrame
from PySide6.QtCore import Qt, Signal
from typing import Optional
import os

from models.pyside6_page import PySide6Page, PageValidationResult
from pyside6_templates import GenericPageLayout, MultiRadioButtons
from compatibility_checks import CheckType
from models.data_units import DataUnit
from sys import argv

class PySide6PageInstallMethod(PySide6Page):
    """
    PySide6 version of PageInstallMethod - Installation Method Selection Page.
    
    Full port of the CustomTkinter version with:
    - Dual-boot size entry and validation
    - Dynamic UI showing/hiding based on selection
    - Warning messages about file backup
    - Complete space calculation logic
    """
    
    def __init__(self, parent: Optional[QWidget], page_name: str):
        super().__init__(parent, page_name)
        self.selected_method: Optional[str] = None
        self.dualboot_size: float = 0.0
        self.max_size: float = 0.0
        self.min_size: float = 0.0
        
        # UI components
        self.page_layout: Optional[GenericPageLayout] = None
        self.radio_group: Optional[MultiRadioButtons] = None
        self.options_frame: Optional[QFrame] = None
        self.warning_label: Optional[QLabel] = None
        self.size_label_pre: Optional[QLabel] = None
        self.size_entry: Optional[QLineEdit] = None
        self.size_label_post: Optional[QLabel] = None

    def init_page(self):
        """Initialize the page layout and widgets."""
        print("Initializing PageInstallMethod (Installation Method Selection)")
        
        try:
            # Get selected spin from state
            selected_spin = self.state.installation.selected_spin
            if not selected_spin:
                print("No spin selected when initializing install method page")
                self._show_error("No distribution selected")
                return

            # Store selected spin name for comparison
            self.selected_spin_name = selected_spin.name

            # Create the main page layout
            title_text = self.LN.windows_question % selected_spin.name
            self.page_layout = GenericPageLayout(
                self,
                title=title_text,
                primary_btn_txt=self.LN.btn_next,
                primary_btn_command=self.navigate_next,
                secondary_btn_txt=self.LN.btn_back,
                secondary_btn_command=self.navigate_previous,
            )
            
            # Set up the main layout
            main_layout = QVBoxLayout(self)
            main_layout.addWidget(self.page_layout)
            
            # Calculate space requirements and availability
            self._calculate_space_requirements(selected_spin)
            
            # Create install method options
            install_methods_dict = self._create_install_method_options(selected_spin)
            
            # Create the radio button group
            self.radio_group = MultiRadioButtons(
                self.page_layout.content_frame,
                items=install_methods_dict,
                validation_callback=self._on_method_selection_changed
            )
            
            # Connect selection signal
            self.radio_group.selection_changed.connect(self._on_method_selected)
            self.page_layout.content_layout.addWidget(self.radio_group)
            
            # Create dynamic options frame (initially hidden)
            self._create_options_frame()
            
            # Set default selection
            self._set_default_selection(selected_spin)
            
            # Initial update of options display
            self._update_options_display()
            
            # Connect button state changes to the page layout
            self.button_state_changed.connect(self._on_button_state_changed)
            
            print("PageInstallMethod initialized successfully")
            
        except Exception as e:
            print(f"Error initializing PageInstallMethod: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _calculate_space_requirements(self, selected_spin):
        """Calculate space requirements and availability."""
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

        # Check space availability
        done_checks = self.state.compatibility.done_checks
        if "--skip_check" not in argv and done_checks is not None:
            resizable_result = done_checks.checks[CheckType.RESIZABLE].result
            
            # Handle case where resizable check returned None or failed
            if resizable_result is None:
                print("Resizable partition check returned None - assuming no space available")
                self.dualboot_space_available = False
                self.replace_win_space_available = False
                self.max_size = 0
            else:
                self.dualboot_space_available = (resizable_result > space_dualboot)
                self.replace_win_space_available = (resizable_result > space_clean)
                
                # Convert string size to bytes for arithmetic operation
                selected_spin_size_bytes = DataUnit.from_string(selected_spin.size).bytes
                
                # Calculate max_size
                self.max_size = DataUnit.from_bytes(
                    resizable_result
                    - selected_spin_size_bytes
                    - self.app_config.app.additional_failsafe_space.bytes_value
                ).to_gigabytes()
                self.max_size = round(self.max_size, 2)
        else:
            self.dualboot_space_available = True
            self.replace_win_space_available = True
            self.max_size = 9999

        # Calculate minimum size for dual boot
        self.min_size = DataUnit.from_bytes(
            self.app_config.app.dualboot_required_space.bytes_value
        ).to_gigabytes()

    def _create_install_method_options(self, selected_spin) -> dict:
        """Create installation method options dictionary."""
        is_auto_installable = selected_spin.is_auto_installable
        
        # Determine default method
        default = "custom" if not is_auto_installable else "replace_win"
        self.selected_method = default

        # Create error messages
        dualboot_error_msg = ""
        replace_win_error_msg = ""
        
        if not is_auto_installable:
            dualboot_error_msg = self.LN.warn_not_available
            replace_win_error_msg = self.LN.warn_not_available
        else:
            if not self.dualboot_space_available:
                dualboot_error_msg = self.LN.warn_space
            if not self.replace_win_space_available:
                replace_win_error_msg = self.LN.warn_space

        return {
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

    def _create_options_frame(self):
        """Create the dynamic options frame for dual-boot size and warnings."""
        self.options_frame = QFrame()
        self.options_frame.setMaximumHeight(300)
        self.page_layout.content_layout.addWidget(self.options_frame)
        
        # Create layout for options frame
        options_layout = QVBoxLayout(self.options_frame)
        options_layout.setContentsMargins(10, 10, 10, 10)
        
        # Warning label for file backup (replace_win mode)
        self.warning_label = QLabel()
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet("color: red; font-size: 12px;")
        options_layout.addWidget(self.warning_label)
        
        # Dual-boot size controls
        size_widget = QWidget()
        size_layout = QHBoxLayout(size_widget)
        size_layout.setContentsMargins(0, 0, 0, 0)
        
        self.size_label_pre = QLabel()
        self.size_label_pre.setStyleSheet("font-size: 12px;")
        size_layout.addWidget(self.size_label_pre)
        
        self.size_entry = QLineEdit()
        self.size_entry.setMaximumWidth(100)
        self.size_entry.textChanged.connect(self._on_dualboot_size_change)
        size_layout.addWidget(self.size_entry)
        
        self.size_label_post = QLabel()
        self.size_label_post.setStyleSheet("color: blue; font-size: 12px;")
        size_layout.addWidget(self.size_label_post)
        
        size_layout.addStretch()
        options_layout.addWidget(size_widget)
        
        # Initially hide the frame
        self.options_frame.hide()

    def _set_default_selection(self, selected_spin):
        """Set the default installation method selection."""
        is_auto_installable = selected_spin.is_auto_installable
        default = "custom" if not is_auto_installable else "replace_win"
        
        if self.radio_group:
            self.radio_group.set_selected_key(default)
            self.selected_method = default

    def _on_method_selected(self, method_key: str):
        """Handle installation method selection."""
        self.selected_method = method_key
        print(f"Selected installation method: {method_key}")
        
        # Update the options display
        self._update_options_display()
        
        # Update button states
        self.update_button_states()

    def _update_options_display(self):
        """Update the display of additional options based on selected method."""
        if not self.selected_method or not self.options_frame:
            if self.options_frame:
                self.options_frame.hide()
            return
        
        # Hide all options first
        if self.warning_label:
            self.warning_label.hide()
        if self.size_label_pre:
            self.size_label_pre.hide()
        if self.size_entry:
            self.size_entry.hide()
        if self.size_label_post:
            self.size_label_post.hide()
        
        if self.selected_method == "dualboot":
            # Show dual-boot size controls
            selected_spin = self.state.installation.selected_spin
            if selected_spin and self.size_label_pre and self.size_label_post:
                self.size_label_pre.setText(
                    self.LN.dualboot_size_txt % selected_spin.name
                )
                self.size_label_post.setText(
                    f"({self.min_size}GB - {self.max_size}GB)"
                )
                
            if self.size_label_pre:
                self.size_label_pre.show()
            if self.size_entry:
                self.size_entry.show()
            if self.size_label_post:
                self.size_label_post.show()
            self.options_frame.show()
            
        elif self.selected_method == "replace_win":
            # Show backup warning
            if self.warning_label:
                sys_drive = self._get_sys_drive_letter()
                self.warning_label.setText(
                    self.LN.warn_backup_files_txt % f"{sys_drive}:\\"
                )
                self.warning_label.show()
            self.options_frame.show()
            
        else:
            # Hide options frame for custom install
            self.options_frame.hide()

    def _on_dualboot_size_change(self):
        """Handle changes to dual-boot size entry."""
        if not self.size_entry:
            return
            
        text = self.size_entry.text()
        try:
            if text.strip():
                self.dualboot_size = float(text)
            else:
                self.dualboot_size = 0.0
        except ValueError:
            self.dualboot_size = 0.0
        
        # Update button states based on validation
        self.update_button_states()

    def _on_method_selection_changed(self):
        """Handle validation when selection changes."""
        self.update_button_states()

    def _get_sys_drive_letter(self):
        """Get the system drive letter."""
        return os.environ.get('SYSTEMDRIVE', 'C:').replace(':', '')

    def _show_error(self, message: str):
        """Show error message."""
        error_label = QLabel(message)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("color: red; font-weight: bold;")
        
        layout = QVBoxLayout(self)
        layout.addWidget(error_label)

    def validate_input(self) -> PageValidationResult:
        """Validate the selected install method and options."""
        if not self.selected_method:
            return PageValidationResult(
                False, 
                "Please select an installation method to continue."
            )
        
        # Check if selected method is available (no error message)
        if self.radio_group:
            selected_option = self.radio_group._items.get(self.selected_method)
            if selected_option and selected_option.error:
                return PageValidationResult(False, selected_option.error)
        
        # Validate dual boot size if needed
        if self.selected_method == "dualboot":
            if not self.size_entry or not self.size_entry.text().strip():
                return PageValidationResult(False, "Dual boot size is required")
            
            try:
                size_value = float(self.size_entry.text())
                if size_value < self.min_size or size_value > self.max_size:
                    return PageValidationResult(
                        False, 
                        f"Dual boot size must be between {self.min_size}GB and {self.max_size}GB"
                    )
            except ValueError:
                return PageValidationResult(False, "Dual boot size must be a valid number")
        
        return PageValidationResult(True)

    def on_next(self):
        """Handle next button action."""
        if self.selected_method:
            print(f"Proceeding with installation method: {self.selected_method}")
            
            # Update state with install method
            self.state.installation.install_options.partition_method = self.selected_method
            
            if self.selected_method == "dualboot":
                # Save dual boot size
                if self.size_entry and self.size_entry.text().strip():
                    size = DataUnit.from_gigabytes(float(self.size_entry.text()))
                    if not self.state.installation.partition:
                        from models.partition import Partition
                        self.state.installation.partition = Partition()
                    self.state.installation.partition.shrink_space = size.bytes
            elif self.selected_method == "custom":
                # Reset partition settings for custom install
                if self.state.installation.partition:
                    self.state.installation.partition.shrink_space = 0
                    self.state.installation.partition.boot_part_size = 0
                    self.state.installation.partition.efi_part_size = 0

    def on_show(self):
        """Always reinitialize the page when shown to ensure state is fresh."""
        print("Reinitializing install method page on show")
        # Clear all child widgets to avoid stale UI
        for widget in self.findChildren(QWidget):
            widget.deleteLater()
        self._initiated = False
        self.init_page()
        self._initiated = True

    def show_validation_error(self, message: str):
        """Show validation error to user."""
        QMessageBox.warning(self, "Validation Error", message)

    def _on_button_state_changed(self, next_enabled: bool, previous_enabled: bool):
        """Handle button state changes by updating the page layout buttons."""
        if self.page_layout:
            self.page_layout.set_button_states(next_enabled, previous_enabled)
