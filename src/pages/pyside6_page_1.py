from PySide6.QtWidgets import QVBoxLayout, QLabel, QMessageBox, QWidget
from PySide6.QtCore import Qt
from typing import Optional

from models.pyside6_page import PySide6Page, PageValidationResult
from templates.pyside6_generic_page_layout import GenericPageLayout
from templates.pyside6_multi_radio_buttons import MultiRadioButtons



class PySide6Page1(PySide6Page):
    """
    PySide6 version of Page1 - Distribution Selection Page.
    
    Much simpler than the CustomTkinter version because:
    - Qt handles DPI scaling automatically
    - No need for custom info frames (Qt has better tooltips/help text)
    - Built-in radio button groups with proper styling
    - Better layout management
    """
    
    def __init__(self, parent: Optional[QWidget], page_name: str):
        super().__init__(parent, page_name)
        self.selected_spin_key: Optional[str] = None
        self.spin_options = {}
        self.page_layout: Optional[GenericPageLayout] = None

    def init_page(self):
        """Initialize the page layout and widgets."""
        self.logger.info("Initializing Page1 (Distribution Selection)")
        
        try:
            # Create the main page layout
            self.page_layout = GenericPageLayout(
                self,
                title=self.LN.desktop_question,
                primary_btn_txt=self.LN.btn_next,
                primary_btn_command=self.navigate_next,
            )
            
            # Set up the main layout
            main_layout = QVBoxLayout(self)
            
            main_layout.addWidget(self.page_layout)
            
            # Get accepted spins from state
            accepted_spins = self.state.compatibility.accepted_spins
            if not accepted_spins:
                self._show_no_spins_available()
                return
            
            # Prepare spin options for radio buttons
            self._prepare_spin_options(accepted_spins)
            
            # Create and configure the radio button group
            self._create_radio_button_group(self.page_layout)
            
            # Set default selection to the first featured/default spin
            self._set_default_selection()
            
            # Update button states initially (Next should be disabled until selection)
            self.update_button_states()
            
            # Connect button state changes to the page layout
            self.button_state_changed.connect(self._on_button_state_changed)
            
            self.logger.info(f"Page1 initialized with {len(self.spin_options)} spin options")
            
        except Exception as e:
            self.logger.error(f"Error initializing Page1: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _prepare_spin_options(self, accepted_spins):
        """Prepare the spin options for the radio button group."""
        self.spin_options = {}
        
        for spin in accepted_spins:
            spin_key = f"{spin.name}_{spin.version}"
            spin_display_name = f"{spin.name} {spin.version}"
            
            # Get description from translations if available
            description = ""
            if hasattr(self.LN, 'distro_hint') and spin.name in self.LN.distro_hint:
                description = self.LN.distro_hint[spin.name]
            
            # Determine if this is an advanced option
            is_advanced = not (spin.is_default or spin.is_featured)
            
            self.spin_options[spin_key] = {
                "name": spin_display_name,
                "description": description,
                "error": "",  # No errors for valid spins
                "advanced": is_advanced,
                "spin_object": spin  # Store reference to the actual spin object
            }
    
    def _create_radio_button_group(self, parent_layout):
        """Create the radio button group for spin selection."""
        
        # Create the radio button group
        self.radio_group = MultiRadioButtons(
            parent_layout.content_frame,
            items=self.spin_options,
            validation_callback=self._on_spin_selection_changed
        )
        
        # Connect selection signal
        self.radio_group.selection_changed.connect(self._on_spin_selected)
        
        parent_layout.content_layout.addWidget(self.radio_group)
        
        # Set default selection to the first featured/default spin
        self._set_default_selection()

    def _set_default_selection(self):
        """Set default selection only if there's a clear default, otherwise leave unselected."""
        # Only auto-select if there's exactly one default spin
        default_spins = []
        for spin_key, spin_data in self.spin_options.items():
            spin_object = spin_data["spin_object"]
            if spin_object.is_default:
                default_spins.append((spin_key, spin_object))
        
        # Only auto-select if there's exactly one default
        if len(default_spins) == 1:
            spin_key, spin_object = default_spins[0]
            self.radio_group.set_selected_key(spin_key)
            self.selected_spin_key = spin_key
            
            # IMPORTANT: Update the state with the selected spin
            self.state.installation.selected_spin = spin_object
            
            self.logger.info(f"Auto-selected default spin: {spin_key}")
            self.logger.info(f"Updated state with auto-selected spin: {spin_object.name} {spin_object.version}")
        else:
            # No auto-selection - user must choose
            self.logger.info("No single default spin found - user must select manually")

    def _on_spin_selected(self, spin_key: str):
        """Handle spin selection."""
        self.logger.info(f"DEBUG: _on_spin_selected called with spin_key: {spin_key}")
        self.selected_spin_key = spin_key
        self.logger.info(f"Selected spin: {spin_key}")
        
        # Update state with selected spin
        if spin_key in self.spin_options:
            selected_spin = self.spin_options[spin_key]["spin_object"]
            self.state.installation.selected_spin = selected_spin
            self.logger.info(f"Updated state with selected spin: {selected_spin.name} {selected_spin.version}")
        
        # Update button states now that we have a selection
        self.logger.info("DEBUG: About to call update_button_states")
        self.update_button_states()
        self.logger.info("DEBUG: update_button_states completed")

    def _on_spin_selection_changed(self):
        """Handle validation when selection changes."""
        self.logger.info("DEBUG: _on_spin_selection_changed called")
        # Update button states when selection changes
        self.update_button_states()
        self.logger.info("DEBUG: _on_spin_selection_changed completed")

    def _show_no_spins_available(self):
        """Show error when no spins are available."""
        error_label = QLabel(
            "No compatible distributions found. Please check your system compatibility."
        )
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("color: red; font-weight: bold;")
        
        layout = QVBoxLayout(self)
        layout.addWidget(error_label)

    def validate_input(self) -> PageValidationResult:
        """Validate that a spin has been selected."""
        if not self.selected_spin_key:
            return PageValidationResult(
                False, 
                "Please select a distribution to continue."
            )
        
        return PageValidationResult(True)

    def on_next(self):
        """Handle next button action."""
        if self.selected_spin_key:
            self.logger.info(f"Proceeding with selected spin: {self.selected_spin_key}")
        
    def show_validation_error(self, message: str):
        """Show validation error to user."""
        QMessageBox.warning(self, "Validation Error", message)

    def _on_button_state_changed(self, next_enabled: bool, previous_enabled: bool):
        """Handle button state changes by updating the page layout buttons."""
        if self.page_layout:
            self.page_layout.set_button_states(next_enabled, previous_enabled)
