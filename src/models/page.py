from abc import ABC, abstractmethod
from typing import Optional, Any
import multilingual
import customtkinter as ctk

from config.settings import get_config
from core.state import get_state
from utils.logging import get_logger


class PageValidationResult:
    """Result of page validation."""
    
    def __init__(self, is_valid: bool, error_message: Optional[str] = None):
        self.is_valid = is_valid
        self.error_message = error_message


class Page(ctk.CTkFrame, ABC):
    LN = multilingual.get_lang()
    DI_VAR = multilingual.get_di_var()

    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.page_name = page_name
        self._initiated = False
        
        # Initialize new systems
        self.config = get_config()
        self.state = get_state()
        self.logger = get_logger(f"pages.{page_name}")
        
        # Navigation will be set by page manager
        self._navigation_manager = None

    def set_navigation_manager(self, nav_manager):
        """Set the navigation manager for this page."""
        self._navigation_manager = nav_manager

    @abstractmethod
    def init_page(self):
        """Initialize the page layout and widgets."""
        pass

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
        """Navigate to the next page."""
        self.logger.info(f"navigate_next() called on {self.page_name}")
        
        if not self._navigation_manager:
            self.logger.error("No navigation manager set!")
            return
            
        self.logger.info("Calling next_action()")
        if self.next_action():
            self.logger.info("next_action() returned True, calling navigate_forward")
            result = self._navigation_manager.navigate_forward(
                self.page_name, 
                True
            )
            self.logger.info(f"navigate_forward result: success={result.success}, target={result.target_page}")
            if not result.success:
                self.logger.error(f"Navigation failed: {result.error_message}")
            else:
                self.logger.info(f"Navigation successful to {result.target_page}")
        else:
            self.logger.warning("next_action() returned False, not navigating")

    def navigate_previous(self):
        """Navigate to the previous page."""
        if self._navigation_manager and self.previous_action():
            result = self._navigation_manager.navigate_backward(self.page_name)
            if not result.success:
                self.logger.error(f"Navigation failed: {result.error_message}")

    def navigate_to(self, target_page: str):
        """Navigate directly to a specific page."""
        if self._navigation_manager:
            result = self._navigation_manager.navigate_to(target_page)
            if not result.success:
                self.logger.error(f"Navigation failed: {result.error_message}")

    def show_validation_error(self, message: str):
        """
        Show a validation error to the user.
        Override to implement custom error display.
        """
        self.logger.warning(f"Validation error: {message}")
        # Default implementation could show a popup or status message
        # For now, just log it

    def get_navigation_info(self):
        """Get navigation information for this page."""
        if self._navigation_manager:
            return self._navigation_manager.get_navigation_info(self.page_name)
        return None
