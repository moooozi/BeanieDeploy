from typing import Dict, Any, Optional, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QRadioButton, QButtonGroup, QLabel, QSizePolicy
)
from PySide6.QtCore import Signal, Qt


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
        self._button_group = QButtonGroup(self)
        self._radio_buttons: Dict[str, QRadioButton] = {}
        self._advanced_radio_buttons: Dict[str, QRadioButton] = {}  # Store advanced separately
        self._show_advanced_label: Optional[QLabel] = None
        self._setup_ui()
        self._button_group.buttonClicked.connect(self._on_selection_changed)

        # Prevent vertical stretching
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), QSizePolicy.Policy.Maximum)

    def _parse_items(self, items: Dict[str, Dict[str, Any]]) -> Dict[str, RadioButtonItem]:
        """Parse raw items dictionary into RadioButtonItem objects."""
        return {
            key: RadioButtonItem.from_dict(config) 
            for key, config in items.items()
        }

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        # Standard options
        standard_items = {k: v for k, v in self._items.items() if not v.advanced}
        self._create_radio_buttons(layout, standard_items, advanced=False)
        # Advanced options
        advanced_items = {k: v for k, v in self._items.items() if v.advanced}
        if advanced_items:
            self._show_advanced_label = QLabel('<a href="#">Show advanced options</a>')
            self._show_advanced_label.setTextFormat(Qt.TextFormat.RichText)
            self._show_advanced_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
            self._show_advanced_label.setCursor(Qt.CursorShape.PointingHandCursor)
            self._show_advanced_label.linkActivated.connect(self._show_advanced_options)
            layout.addWidget(self._show_advanced_label)
            self._create_radio_buttons(layout, advanced_items, advanced=True)

    def _create_radio_buttons(self, layout: QVBoxLayout, items: Dict[str, RadioButtonItem], advanced: bool):
        for key, item in items.items():
            radio_button = QRadioButton(item.name)
            if item.error:
                radio_button.setEnabled(False)
                radio_button.setToolTip(item.error)
            elif item.description:
                radio_button.setToolTip(item.description)
            radio_button.setProperty("item_key", key)
            radio_button.setVisible(not advanced)  # Hide advanced by default
            self._radio_buttons[key] = radio_button
            if advanced:
                self._advanced_radio_buttons[key] = radio_button
            self._button_group.addButton(radio_button)
            layout.addWidget(radio_button)

    def _show_advanced_options(self):
        """Show advanced options and hide the label forever."""
        for btn in self._advanced_radio_buttons.values():
            btn.setVisible(True)
        if self._show_advanced_label:
            self._show_advanced_label.hide()

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