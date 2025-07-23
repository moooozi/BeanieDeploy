from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout
from PySide6.QtCore import Signal
from typing import TYPE_CHECKING, Dict, Optional, Type, TypeVar, Any, Callable

from models.pyside6_page import PySide6Page
from utils.logging import get_logger

# Type variable for page types
TPage = TypeVar('TPage', bound=PySide6Page)

if TYPE_CHECKING:
    from models.pyside6_page import PySide6Page


class PySide6PageManager(QWidget):
    """
    PySide6 implementation of the page manager.
    
    Manages navigation between pages in a Qt application using QStackedWidget.
    Provides the same functionality as the CustomTkinter PageManager but leverages
    Qt's built-in navigation and layout systems.
    """
    
    # Signals
    page_changed = Signal(str)  # Emitted when page changes
    navigation_error = Signal(str)  # Emitted on navigation errors
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.pages: Dict[Type[PySide6Page], PySide6Page] = {}
        self.current_page: Optional[PySide6Page] = None
        self.logger = get_logger(__name__)
        
        # Navigation flow will be configured externally
        self._navigation_flow: Dict[Type[PySide6Page], Any] = {}
        self._page_configurators: Dict[Type[PySide6Page], Callable] = {}
        
        # Set up the UI
        self._setup_ui()

    def _setup_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create the stacked widget for page navigation
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

    def configure_navigation_flow(self, navigation_flow: Dict[Type[PySide6Page], Any]):
        """Configure the navigation flow from external source."""
        self._navigation_flow = navigation_flow
        self.logger.debug("Navigation flow configured externally")

    def configure_page(self, page_class: Type[PySide6Page], configurator: Callable):
        """Configure a specific page with a callback function."""
        self._page_configurators[page_class] = configurator

    def add_page(self, page_class: Type[PySide6Page]) -> PySide6Page:
        """Add a page to the manager."""
        if page_class in self.pages:
            self.logger.warning(f"Page {page_class.__name__} already exists")
            return self.pages[page_class]
        
        # Create page instance
        page_instance = page_class(self, page_class.__name__)
        page_instance.set_page_manager(self)
        
        # Connect navigation signals
        page_instance.navigate_next_requested.connect(self._handle_next_navigation)
        page_instance.navigate_previous_requested.connect(self._handle_previous_navigation)
        page_instance.validation_error.connect(self._handle_validation_error)
        
        # Add to stacked widget
        self.stacked_widget.addWidget(page_instance)
        
        # Store page
        self.pages[page_class] = page_instance
        
        self.logger.debug(f"Added page: {page_class.__name__}")
        return page_instance

    def show_page(self, page_class: Type[PySide6Page]) -> bool:
        """Show a specific page."""
        if page_class not in self.pages:
            self.logger.error(f"Page {page_class.__name__} not found")
            return False
        
        page_instance = self.pages[page_class]
        
        # Configure page if configurator exists
        if page_class in self._page_configurators:
            self._page_configurators[page_class](page_instance)
        
        # Initialize page if not already done
        if not page_instance._initiated:
            page_instance.init_page()
            page_instance._initiated = True
        
        # Hide current page
        if self.current_page:
            self.current_page.on_hide()
        
        # Show new page
        self.stacked_widget.setCurrentWidget(page_instance)
        self.current_page = page_instance
        page_instance.on_show()
        
        self.page_changed.emit(page_class.__name__)
        self.logger.info(f"Switched to page: {page_class.__name__}")
        return True

    def get_next_page(self, current_page_class: Type[PySide6Page]) -> Optional[Type[PySide6Page]]:
        """Get the next page in the flow, automatically skipping disabled pages."""
        if not self._navigation_flow:
            self.logger.warning("Navigation flow not configured")
            return None
            
        # Get the ordered list of pages from the dictionary keys
        page_order = list(self._navigation_flow.keys())
        
        # Check for custom next navigation first
        page_config = self._navigation_flow.get(current_page_class, {})
        if "next" in page_config:
            custom_next = page_config["next"]
            if callable(custom_next):
                next_page = custom_next()
                if next_page and isinstance(next_page, type):
                    return self._find_next_enabled_page_from(next_page, page_order)
            return None
        
        # Find current page in the order
        try:
            current_index = page_order.index(current_page_class)
        except ValueError:
            self.logger.warning(f"Page {current_page_class.__name__} not found in page order")
            return None
        
        # Find next enabled page
        for i in range(current_index + 1, len(page_order)):
            candidate_page = page_order[i]
            if self._is_page_enabled(candidate_page):
                return candidate_page
            else:
                self.logger.info(f"Skipping page {candidate_page.__name__} due to condition")
        
        return None

    def get_previous_page(self, current_page_class: Type[PySide6Page]) -> Optional[Type[PySide6Page]]:
        """Get the previous page in the flow, automatically skipping disabled pages."""
        if not self._navigation_flow:
            self.logger.warning("Navigation flow not configured")
            return None
            
        # Get the ordered list of pages from the dictionary keys
        page_order = list(self._navigation_flow.keys())
        self.logger.debug(f"get_previous_page called from {current_page_class.__name__}")
        
        # Check for custom previous navigation first
        page_config = self._navigation_flow.get(current_page_class, {})
        if "previous" in page_config:
            custom_prev = page_config["previous"]
            if callable(custom_prev):
                prev_page = custom_prev()
                if prev_page and isinstance(prev_page, type):
                    self.logger.debug(f"Using custom previous: {prev_page.__name__}")
                    return self._find_previous_enabled_page_from(prev_page, page_order)
            return None
        
        # Find current page in the order
        try:
            current_index = page_order.index(current_page_class)
        except ValueError:
            self.logger.warning(f"Page {current_page_class.__name__} not found in page order")
            return None
        
        self.logger.debug(f"Current page index: {current_index}")
        
        # Find previous enabled page
        for i in range(current_index - 1, -1, -1):
            candidate_page = page_order[i]
            self.logger.debug(f"Checking previous candidate: {candidate_page.__name__}")
            if self._is_page_enabled(candidate_page):
                self.logger.debug(f"Found enabled previous page: {candidate_page.__name__}")
                return candidate_page
            else:
                self.logger.info(f"Skipping page {candidate_page.__name__} due to condition")
        
        self.logger.debug("No previous page found")
        return None

    def _find_next_enabled_page_from(self, start_page: Type[PySide6Page], page_order: list) -> Optional[Type[PySide6Page]]:
        """Find the next enabled page starting from a specific page."""
        try:
            start_index = page_order.index(start_page)
        except ValueError:
            return None
        
        # Check if the start page itself is enabled
        if self._is_page_enabled(start_page):
            return start_page
        
        # Find next enabled page
        for i in range(start_index + 1, len(page_order)):
            candidate_page = page_order[i]
            if self._is_page_enabled(candidate_page):
                return candidate_page
        
        return None

    def _find_previous_enabled_page_from(self, start_page: Type[PySide6Page], page_order: list) -> Optional[Type[PySide6Page]]:
        """Find the previous enabled page starting from a specific page."""
        try:
            start_index = page_order.index(start_page)
        except ValueError:
            return None
        
        # Check if the start page itself is enabled
        if self._is_page_enabled(start_page):
            return start_page
        
        # Find previous enabled page
        for i in range(start_index - 1, -1, -1):
            candidate_page = page_order[i]
            if self._is_page_enabled(candidate_page):
                return candidate_page
        
        return None

    def _is_page_enabled(self, page_class: Type[PySide6Page]) -> bool:
        """Check if a page is enabled based on its conditions."""
        page_config = self._navigation_flow.get(page_class, {})
        conditions = page_config.get("conditions", [])
        
        # If no conditions, page is enabled
        if not conditions:
            return True
        
        # All conditions must be satisfied
        for condition in conditions:
            if not condition.is_satisfied():
                return False
        
        return True

    def _handle_next_navigation(self):
        """Handle next navigation request from current page with validation."""
        if not self.current_page:
            return
        
        self.logger.info(f"DEBUG: Navigation request from {self.current_page.page_name}")
        
        # SAFETY MECHANISM: Validate page input before allowing navigation
        validation_result = self.current_page.validate_input()
        self.logger.info(f"DEBUG: Validation result - valid: {validation_result.is_valid}, message: {validation_result.error_message}")
        
        if not validation_result.is_valid:
            self.logger.warning(f"Navigation blocked - validation failed: {validation_result.error_message}")
            if validation_result.error_message:
                self.current_page.show_validation_error(validation_result.error_message)
            return
        
        # Execute page-specific next action
        self.logger.info("DEBUG: Validation passed, calling next_action")
        if not self.current_page.next_action():
            self.logger.warning("Navigation blocked - page next_action returned False")
            return
        
        current_page_class = type(self.current_page)
        next_page_class = self.get_next_page(current_page_class)
        
        if next_page_class:
            self.logger.info(f"DEBUG: Navigating from {current_page_class.__name__} to {next_page_class.__name__}")
            self.show_page(next_page_class)
        else:
            self.logger.info("No next page available")

    def _handle_previous_navigation(self):
        """Handle previous navigation request from current page."""
        if not self.current_page:
            return
        
        current_page_class = type(self.current_page)
        previous_page_class = self.get_previous_page(current_page_class)
        
        if previous_page_class:
            self.show_page(previous_page_class)
        else:
            self.logger.info("No previous page available")

    def _handle_validation_error(self, message: str):
        """Handle validation error from a page."""
        self.navigation_error.emit(message)
        # In a real application, you might show a message box or status message here
