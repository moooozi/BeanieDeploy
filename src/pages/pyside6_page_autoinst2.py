from PySide6.QtWidgets import QVBoxLayout, QLabel, QMessageBox, QWidget, QCheckBox
from PySide6.QtCore import Qt
from typing import Optional

from models.pyside6_page import PySide6Page, PageValidationResult
from pyside6_templates import GenericPageLayout


class PySide6PageAutoinst2(PySide6Page):
    """
    PySide6 version of PageAutoinst2 - Auto Installation Options.
    
    Demonstrates how much simpler the PySide6 version is:
    - No need for custom CheckButton class (Qt's QCheckBox is better)
    - Better layout management with Qt's layout system
    - Built-in styling and theming
    - No DPI awareness code needed
    """
    
    def __init__(self, parent: Optional[QWidget], page_name: str):
        super().__init__(parent, page_name)
        
        # Initialize kickstart and install options if they don't exist
        if not self.state.installation.kickstart:
            from models.kickstart import Kickstart
            self.state.installation.kickstart = Kickstart()
            
        if not self.state.installation.install_options:
            from models.install_options import InstallOptions
            self.state.installation.install_options = InstallOptions()
        
        # Create checkboxes
        self.encryption_checkbox: Optional[QCheckBox] = None
        self.export_wifi_checkbox: Optional[QCheckBox] = None

    def init_page(self):
        """Initialize the page layout and widgets."""
        self.logger.info("Initializing PageAutoinst2 (Auto Install Options)")
        
        try:
            # Get selected spin from state
            selected_spin = self.state.installation.selected_spin
            if not selected_spin:
                self.logger.error("No spin selected when initializing auto-install page")
                self._show_error("No distribution selected")
                return
            
            # Create the main page layout with dynamic title
            title_text = self.LN.windows_question % selected_spin.name
            page_layout = GenericPageLayout(
                self,
                title=title_text,
                primary_btn_txt=self.LN.btn_next,
                primary_btn_command=self.navigate_next,
                secondary_btn_txt=self.LN.btn_back,
                secondary_btn_command=self.navigate_previous,
            )
            
            # Set up the main layout
            main_layout = QVBoxLayout(self)
            main_layout.addWidget(page_layout)
            
            # Create the options section
            self._create_options_section(page_layout)
            
            self.logger.info("PageAutoinst2 initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing PageAutoinst2: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _create_options_section(self, parent_layout):
        """Create the auto-installation options section."""
        
        # Get current state
        kickstart = self.state.installation.kickstart
        install_options = self.state.installation.install_options
        
        # Instructions label
        instructions = QLabel(
            "Configure auto-installation options:"
        )
        instructions.setWordWrap(True)
        parent_layout.content_layout.addWidget(instructions)
        
        # Options container
        options_container = QWidget()
        options_layout = QVBoxLayout(options_container)
        options_layout.setContentsMargins(20, 20, 20, 20)
        options_layout.setSpacing(15)
        
        # Encryption option
        self.encryption_checkbox = QCheckBox("Enable disk encryption")
        self.encryption_checkbox.setChecked(kickstart.is_encrypted if kickstart else False)
        self.encryption_checkbox.toggled.connect(self._on_encryption_toggled)
        
        # Add tooltip/description
        self.encryption_checkbox.setToolTip(
            "Encrypt the disk to protect your data. " +
            "You will need to enter a password each time you boot."
        )
        
        options_layout.addWidget(self.encryption_checkbox)
        
        # WiFi export option
        self.export_wifi_checkbox = QCheckBox("Export WiFi settings")
        self.export_wifi_checkbox.setChecked(install_options.export_wifi if install_options else False)
        self.export_wifi_checkbox.toggled.connect(self._on_export_wifi_toggled)
        
        # Add tooltip/description
        self.export_wifi_checkbox.setToolTip(
            "Export current WiFi settings to the new installation. " +
            "This will copy your saved networks and passwords."
        )
        
        options_layout.addWidget(self.export_wifi_checkbox)
        
        # Add some additional spacing
        options_layout.addStretch()
        
        parent_layout.content_layout.addWidget(options_container)

    def _on_encryption_toggled(self, checked: bool):
        """Handle encryption checkbox toggle."""
        self.logger.info(f"Encryption option toggled: {checked}")
        
        kickstart = self.state.installation.kickstart
        if kickstart:
            kickstart.is_encrypted = checked

    def _on_export_wifi_toggled(self, checked: bool):
        """Handle WiFi export checkbox toggle."""
        self.logger.info(f"WiFi export option toggled: {checked}")
        
        install_options = self.state.installation.install_options
        if install_options:
            install_options.export_wifi = checked

    def _show_error(self, message: str):
        """Show error message."""
        error_label = QLabel(message)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("color: red; font-weight: bold;")
        
        layout = QVBoxLayout(self)
        layout.addWidget(error_label)

    def validate_input(self) -> PageValidationResult:
        """Validate the page input."""
        # For this page, any selection is valid
        # The user can choose to enable or disable options
        return PageValidationResult(True)

    def on_next(self):
        """Handle next button action."""
        kickstart = self.state.installation.kickstart
        install_options = self.state.installation.install_options
        
        self.logger.info(
            f"Auto-install options: " +
            f"encryption={kickstart.is_encrypted if kickstart else False}, " +
            f"export_wifi={install_options.export_wifi if install_options else False}"
        )

    def show_validation_error(self, message: str):
        """Show validation error to user."""
        QMessageBox.warning(self, "Validation Error", message)
