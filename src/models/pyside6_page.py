from abc import abstractmethod
from typing import Optional
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal
import multilingual

from config.settings import get_config, ConfigManager
from core.state import get_state
from utils.logging import get_logger


class PageValidationResult:
    """Result of page validation."""
    
    def __init__(self, is_valid: bool, error_message: Optional[str] = None):
        self.is_valid = is_valid
        self.error_message = error_message


class PySide6Page(QWidget):
    """
    Base class for all PySide6 pages in the application.
    
    This class provides the core functionality for pages including:
    - Navigation signals
    - Validation framework
    - State management integration
    - Configuration access
    
    Note: We don't inherit from ABC to avoid metaclass conflicts with Qt.
    Instead, we use abstractmethod decorators and document required methods.
    """
    
    # Signals for navigation
    navigate_next_requested = Signal()
    navigate_previous_requested = Signal()
    validation_error = Signal(str)
    button_state_changed = Signal(bool, bool)  # (next_enabled, previous_enabled)
    
    LN = multilingual.get_lang()
    DI_VAR = multilingual.get_di_var()

    def __init__(self, parent: Optional[QWidget], page_name: str):
        super().__init__(parent)
        self.page_name = page_name
        self._initiated = False
        
        # Initialize new systems
        self.app_config: ConfigManager = get_config()
        self.state = get_state()
        self.logger = get_logger(f"pages.{page_name}")
        
        self._page_manager = None

    def set_page_manager(self, page_manager):
        """Set the page manager for this page."""
        self._page_manager = page_manager

    @abstractmethod
    def init_page(self):
        """Initialize the page layout and widgets. MUST be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement init_page()")

    def validate_input(self) -> PageValidationResult:
        """
        Validate the current page input.
        Override this method to implement page-specific validation.
        """
        return PageValidationResult(True)

    def on_show(self):
        """Called when the page is shown."""
        pass

    def on_hide(self):
        """Called when the page is hidden."""
        pass

    def next_action(self) -> bool:
        """
        Handle next button action.
        Returns True if navigation should proceed, False otherwise.
        """
        validation_result = self.validate_input()
        if not validation_result.is_valid:
            if validation_result.error_message:
                self.show_validation_error(validation_result.error_message)
            return False
        
        # Perform any page-specific next actions
        self.on_next()
        return True

    def previous_action(self) -> bool:
        """
        Handle previous button action.
        Returns True if navigation should proceed, False otherwise.
        """
        # Perform any page-specific previous actions
        self.on_previous()
        return True

    def on_next(self):
        """
        Called when user clicks next and validation passes.
        Override to implement page-specific next logic.
        """
        pass

    def on_previous(self):
        """
        Called when user clicks previous.
        Override to implement page-specific previous logic.
        """
        pass

    def navigate_next(self):
        """Navigate to the next page with safety checks."""
        # The page manager will handle validation, so we just emit the request
        self.navigate_next_requested.emit()

    def navigate_previous(self):
        """Navigate to the previous page."""
        if self.previous_action():
            self.navigate_previous_requested.emit()

    def show_validation_error(self, message: str):
        """Show validation error to user."""
        self.validation_error.emit(message)
        self.logger.warning(f"Validation error on page {self.page_name}: {message}")

    def update_button_states(self):
        """Update navigation button states based on current validation."""
        self.logger.debug(f"DEBUG: update_button_states called for {self.page_name}")
        validation_result = self.validate_input()
        next_enabled = validation_result.is_valid
        
        # Previous button is usually always enabled (unless overridden)
        previous_enabled = self._is_previous_allowed()
        
        self.logger.debug(f"DEBUG: Button states - next_enabled: {next_enabled}, previous_enabled: {previous_enabled}")
        self.button_state_changed.emit(next_enabled, previous_enabled)

    def _is_previous_allowed(self) -> bool:
        """Check if previous navigation is allowed. Override in subclasses if needed."""
        return True
