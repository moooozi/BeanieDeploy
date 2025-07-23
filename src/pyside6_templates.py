from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QCheckBox, QButtonGroup, QRadioButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from typing import Dict, Any, Optional, Callable

# Application constants (Qt handles DPI scaling automatically)
WINDOW_WIDTH = 850
WINDOW_HEIGHT = 580
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 530

# Font configurations (Qt will handle DPI scaling)
FONT_LARGE = QFont("Arial", 18, QFont.Weight.Bold)
FONT_MEDIUM = QFont("Arial", 12, QFont.Weight.Bold) 
FONT_SMALL = QFont("Arial", 10)
FONT_SMALLER = QFont("Arial", 9)


class GenericPageLayout(QWidget):
    """
    Generic page layout that provides consistent structure for all pages.
    
    Simplified compared to CustomTkinter version since Qt handles:
    - DPI scaling automatically
    - Better theme support
    - Built-in layout management
    """
    
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        title: Optional[str] = None,
        primary_btn_txt: Optional[str] = None,
        primary_btn_command: Optional[Callable] = None,
        secondary_btn_txt: Optional[str] = None,
        secondary_btn_command: Optional[Callable] = None,
    ):
        super().__init__(parent)
        
        self.title = title
        self.primary_btn_txt = primary_btn_txt
        self.primary_btn_command = primary_btn_command
        self.secondary_btn_txt = secondary_btn_txt
        self.secondary_btn_command = secondary_btn_command
        
        # Store button references for state management
        self.primary_btn: Optional[QPushButton] = None
        self.secondary_btn: Optional[QPushButton] = None
        
        self._setup_ui()

    def _setup_ui(self):
        """Set up the page layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Add title if provided
        if self.title:
            self._add_title(layout)
        
        # Content frame - this is what pages will add their content to
        self.content_frame = QWidget()
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.content_frame, 1)  # Takes up most space
        
        # Button bar at bottom
        if self.primary_btn_txt or self.secondary_btn_txt:
            self._add_button_bar(layout)

    def _add_title(self, layout: QVBoxLayout):
        """Add the page title."""
        title_label = QLabel(self.title)
        title_label.setFont(FONT_MEDIUM)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

    def _add_button_bar(self, layout: QVBoxLayout):
        """Add the button bar at the bottom."""
        button_frame = QWidget()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add stretch to push buttons to the right
        button_layout.addStretch()
        
        # Secondary button (Back, Cancel, etc.)
        if self.secondary_btn_txt:
            self.secondary_btn = QPushButton(self.secondary_btn_txt)
            if self.secondary_btn_command:
                self.secondary_btn.clicked.connect(self.secondary_btn_command)
            button_layout.addWidget(self.secondary_btn)
        
        # Primary button (Next, Install, etc.)
        if self.primary_btn_txt:
            self.primary_btn = QPushButton(self.primary_btn_txt)
            self.primary_btn.setDefault(True)  # Make it the default button
            if self.primary_btn_command:
                self.primary_btn.clicked.connect(self.primary_btn_command)
            button_layout.addWidget(self.primary_btn)
        
        layout.addWidget(button_frame)

    def set_button_states(self, primary_enabled: bool = True, secondary_enabled: bool = True):
        """Update the enabled state of navigation buttons."""
        if self.primary_btn:
            self.primary_btn.setEnabled(primary_enabled)
        if self.secondary_btn:
            self.secondary_btn.setEnabled(secondary_enabled)


class CheckButton(QCheckBox):
    """
    Custom checkbox with simplified interface compared to CustomTkinter version.
    Qt handles styling and DPI automatically.
    """
    
    def __init__(self, parent: Optional[QWidget] = None, text: str = "", checked: bool = False):
        super().__init__(text, parent)
        self.setChecked(checked)


class RadioButtonItem:
    """Data class representing a single radio button item configuration."""
    
    def __init__(self, name: str, description: str = "", error: str = "", advanced: bool = False):
        self.name = name
        self.description = description
        self.error = error
        self.advanced = advanced
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RadioButtonItem':
        """Create a RadioButtonItem from a dictionary."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            error=data.get("error", ""),
            advanced=data.get("advanced", False)
        )


class MultiRadioButtons(QWidget):
    """
    A customizable radio button group widget for PySide6.
    
    Much simpler than the CustomTkinter version since Qt provides:
    - Built-in QButtonGroup for exclusive selection
    - Better layout management
    - Automatic styling
    """
    
    # Signal emitted when selection changes
    selection_changed = Signal(str)  # Emits the selected key
    
    def __init__(
        self, 
        parent: Optional[QWidget] = None,
        items: Optional[Dict[str, Dict[str, Any]]] = None,
        validation_callback: Optional[Callable] = None,
    ):
        super().__init__(parent)
        
        self._validation_callback = validation_callback
        self._items = self._parse_items(items or {})
        
        # Button group for exclusive selection
        self._button_group = QButtonGroup(self)
        self._radio_buttons: Dict[str, QRadioButton] = {}
        
        # Track advanced options
        self._advanced_frame: Optional[QWidget] = None
        self._show_advanced_button: Optional[QPushButton] = None
        self._advanced_visible = False
        
        self._setup_ui()
        
        # Connect button group signal
        self._button_group.buttonClicked.connect(self._on_selection_changed)

    def _parse_items(self, items: Dict[str, Dict[str, Any]]) -> Dict[str, RadioButtonItem]:
        """Parse raw items dictionary into RadioButtonItem objects."""
        return {
            key: RadioButtonItem.from_dict(config) 
            for key, config in items.items()
        }

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Create standard options first
        standard_items = {k: v for k, v in self._items.items() if not v.advanced}
        self._create_radio_buttons(layout, standard_items)
        
        # Create advanced options if any exist
        advanced_items = {k: v for k, v in self._items.items() if v.advanced}
        if advanced_items:
            self._create_advanced_section(layout, advanced_items)

    def _create_radio_buttons(self, layout: QVBoxLayout, items: Dict[str, RadioButtonItem]):
        """Create radio buttons for the given items."""
        for key, item in items.items():
            radio_button = QRadioButton(item.name)
            
            # Disable if there's an error
            if item.error:
                radio_button.setEnabled(False)
                radio_button.setToolTip(item.error)
            
            # Add description as tooltip if available
            elif item.description:
                radio_button.setToolTip(item.description)
            
            # Store the key as user data
            radio_button.setProperty("item_key", key)
            
            self._radio_buttons[key] = radio_button
            self._button_group.addButton(radio_button)
            layout.addWidget(radio_button)

    def _create_advanced_section(self, layout: QVBoxLayout, advanced_items: Dict[str, RadioButtonItem]):
        """Create the collapsible advanced options section."""
        # Button to show/hide advanced options
        self._show_advanced_button = QPushButton("Show advanced options")
        self._show_advanced_button.clicked.connect(self._toggle_advanced_options)
        layout.addWidget(self._show_advanced_button)
        
        # Advanced options frame (initially hidden)
        self._advanced_frame = QWidget()
        advanced_layout = QVBoxLayout(self._advanced_frame)
        advanced_layout.setContentsMargins(20, 10, 0, 10)  # Indent advanced options
        
        self._create_radio_buttons(advanced_layout, advanced_items)
        
        self._advanced_frame.setVisible(False)
        layout.addWidget(self._advanced_frame)

    def _toggle_advanced_options(self):
        """Toggle visibility of advanced options."""
        self._advanced_visible = not self._advanced_visible
        
        if self._advanced_frame:
            self._advanced_frame.setVisible(self._advanced_visible)
        
        if self._show_advanced_button:
            text = "Hide advanced options" if self._advanced_visible else "Show advanced options"
            self._show_advanced_button.setText(text)

    def _on_selection_changed(self, button: QRadioButton):
        """Handle radio button selection change."""
        key = button.property("item_key")
        if key:
            self.selection_changed.emit(key)
            
            # Call validation callback if provided
            if self._validation_callback:
                self._validation_callback()

    def get_selected_key(self) -> Optional[str]:
        """Get the key of the currently selected radio button."""
        checked_button = self._button_group.checkedButton()
        if checked_button:
            return checked_button.property("item_key")
        return None

    def set_selected_key(self, key: str) -> bool:
        """Set the selected radio button by key."""
        if key in self._radio_buttons:
            self._radio_buttons[key].setChecked(True)
            return True
        return False

    def clear_selection(self):
        """Clear the current selection."""
        if self._button_group.checkedButton():
            self._button_group.setExclusive(False)
            self._button_group.checkedButton().setChecked(False)
            self._button_group.setExclusive(True)