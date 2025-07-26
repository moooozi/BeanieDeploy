from PySide6.QtWidgets import (
    QWidget,
    QCheckBox,
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
FONT_MEDIUM = QFont("Arial", 15, QFont.Weight.Bold)
FONT_SMALL = QFont("Arial", 12)
FONT_SMALLER = QFont("Arial", 10)




class CheckButton(QCheckBox):
    """
    Custom checkbox with simplified interface compared to CustomTkinter version.
    Qt handles styling and DPI automatically.
    """
    
    def __init__(self, parent: Optional[QWidget] = None, text: str = "", checked: bool = False):
        super().__init__(text, parent)
        self.setChecked(checked)


