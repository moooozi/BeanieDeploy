from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt
from typing import Optional, Callable
from pyside6_templates import FONT_MEDIUM


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
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        title_label.setWordWrap(True)
        title_label.setContentsMargins(0, 30, 0, 0)  # Add top margin (e.g., 30px)
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
