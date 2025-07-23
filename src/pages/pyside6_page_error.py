from PySide6.QtWidgets import QVBoxLayout, QLabel, QScrollArea, QWidget, QApplication
from PySide6.QtCore import Qt
from typing import Optional, List

from models.pyside6_page import PySide6Page, PageValidationResult
from pyside6_templates import GenericPageLayout


class PySide6PageError(PySide6Page):
    """
    PySide6 version of PageError - Error Display Page.
    
    Much simpler than the CustomTkinter version because:
    - Qt's built-in scrolling widgets
    - Better text handling and formatting
    - No need for custom info frames
    """
    
    def __init__(self, parent: Optional[QWidget], page_name: str):
        super().__init__(parent, page_name)
        self.errors: List[str] = []
        self.error_container: Optional[QWidget] = None

    def init_page(self):
        """Initialize the page layout and widgets."""
        self.logger.info("Initializing PageError (Error Display)")
        
        try:
            # Get app name from config
            app_name = self.app_config.app.name if hasattr(self.app_config.app, 'name') else "BeanieDeploy"
            
            # Create the main page layout
            page_layout = GenericPageLayout(
                self,
                title=self.LN.error_title % app_name,
                secondary_btn_txt=self.LN.btn_quit,
                secondary_btn_command=self._quit_application,
            )
            
            # Set up the main layout
            main_layout = QVBoxLayout(self)
            main_layout.addWidget(page_layout)
            
            # Error description
            error_desc = QLabel(self.LN.error_list)
            error_desc.setWordWrap(True)
            page_layout.content_layout.addWidget(error_desc)
            
            # Scroll area for errors
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            
            # Container for error messages
            self.error_container = QWidget()
            self.error_layout = QVBoxLayout(self.error_container)
            self.error_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            
            scroll_area.setWidget(self.error_container)
            page_layout.content_layout.addWidget(scroll_area)
            
            self.logger.info("PageError initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing PageError: {e}")
            import traceback
            traceback.print_exc()
            raise

    def set_errors(self, errors: List[str]):
        """Set the errors to display."""
        self.errors = errors
        
        # Initialize page if not already done
        if not self._initiated:
            self.init_page()
            self._initiated = True
        
        # Clear existing error messages
        if self.error_container and hasattr(self, 'error_layout'):
            # Remove all existing widgets
            for i in reversed(range(self.error_layout.count())):
                child = self.error_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)
        
        # Add new error messages
        for i, error in enumerate(self.errors):
            error_label = QLabel(f"• {error}")
            error_label.setWordWrap(True)
            error_label.setStyleSheet("""
                QLabel {
                    background-color: #ffebee;
                    border: 1px solid #f44336;
                    border-radius: 4px;
                    padding: 8px;
                    margin: 2px 0px;
                    color: #c62828;
                }
            """)
            self.error_layout.addWidget(error_label)
        
        self.logger.error(f"Displaying {len(errors)} errors to user")

    def _quit_application(self):
        """Quit the application."""
        self.logger.info("User chose to quit from error page")
        QApplication.quit()

    def validate_input(self) -> PageValidationResult:
        """Error page doesn't require validation."""
        return PageValidationResult(True)

    def show_validation_error(self, message: str):
        """Error page doesn't show validation errors."""
        pass  # Error page doesn't need validation error display
