import customtkinter as ctk
from typing import TYPE_CHECKING, Dict, Optional, Type, TypeVar, Any

from models.page import Page
from utils.logging import get_logger

# Type variable for page types
TPage = TypeVar('TPage', bound=Page)

if TYPE_CHECKING:
    from models.page import Page

class PageManager(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.pages: Dict[Type[Page], Page] = {}
        self.current_page: Optional[Page] = None
        self.logger = get_logger(__name__)
        
        # Navigation flow will be configured externally
        self._navigation_flow: Dict[Type[Page], Any] = {}
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def configure_navigation_flow(self, navigation_flow: Dict[Type[Page], Any]):
        """Configure the navigation flow from external source."""
        self._navigation_flow = navigation_flow
        self.logger.debug("Navigation flow configured externally")
    
    def get_next_page(self, current_page_class: Type[Page]) -> Optional[Type[Page]]:
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
    
    def get_previous_page(self, current_page_class: Type[Page]) -> Optional[Type[Page]]:
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
                self.logger.info(f"Found previous enabled page: {candidate_page.__name__}")
                return candidate_page
            else:
                self.logger.info(f"Skipping page {candidate_page.__name__} due to condition")
        
        self.logger.debug("No previous page found")
        return None
    
    def _is_page_enabled(self, page_class: Type[Page]) -> bool:
        """Check if a page is enabled based on its conditions."""
        page_config = self._navigation_flow.get(page_class, {})
        
        # Skip special pages in normal flow
        if page_config.get("special", False):
            self.logger.debug(f"Page {page_class.__name__} is marked as special, skipping")
            return False
        
        # Check all conditions
        conditions = page_config.get("conditions", [])
        for condition in conditions:
            if not condition.is_enabled():
                self.logger.info(f"Page {page_class.__name__} disabled by condition {condition.__class__.__name__}")
                return False
        
        self.logger.debug(f"Page {page_class.__name__} is enabled")
        return True  # Enabled if no conditions or all conditions pass
    
    def _find_next_enabled_page_from(self, start_page: Type[Page], page_order: list) -> Optional[Type[Page]]:
        """Find the next enabled page starting from a given page."""
        try:
            start_index = page_order.index(start_page)
        except ValueError:
            return start_page if self._is_page_enabled(start_page) else None
        
        # Check if the start page itself is enabled
        if self._is_page_enabled(start_page):
            return start_page
        
        # Find next enabled page after start_page
        for i in range(start_index + 1, len(page_order)):
            candidate_page = page_order[i]
            if self._is_page_enabled(candidate_page):
                return candidate_page
            else:
                self.logger.info(f"Skipping page {candidate_page.__name__} due to condition")
        
        return None
    
    def _find_previous_enabled_page_from(self, start_page: Type[Page], page_order: list) -> Optional[Type[Page]]:
        """Find the previous enabled page starting from a given page."""
        try:
            start_index = page_order.index(start_page)
        except ValueError:
            return start_page if self._is_page_enabled(start_page) else None
        
        # Check if the start page itself is enabled
        if self._is_page_enabled(start_page):
            return start_page
        
        # Find previous enabled page before start_page
        for i in range(start_index - 1, -1, -1):
            candidate_page = page_order[i]
            if self._is_page_enabled(candidate_page):
                return candidate_page
            else:
                self.logger.info(f"Skipping page {candidate_page.__name__} due to condition")
        
        return None

    def navigate_forward(self, current_page_class: Type[Page]) -> bool:
        """Navigate to the next page."""
        next_page = self.get_next_page(current_page_class)
        if next_page:
            self.show_page(next_page)
            return True
        return False

    def navigate_backward(self, current_page_class: Type[Page]) -> bool:
        """Navigate to the previous page."""
        previous_page = self.get_previous_page(current_page_class)
        if previous_page:
            self.show_page(previous_page)
            return True
        return False

    def add_page(self, page_class: Type[Page], *args, **kwargs):
        """Add a page to the manager."""
        page_name = page_class.__name__
        page = page_class(
            self,
            page_name,
            *args,
            fg_color="transparent",
            bg_color="transparent",
            **kwargs,
        )
        
        # Set up navigation for the page
        page.set_page_manager(self)
        
        self.pages[page_class] = page
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(0, weight=1)
        page.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.logger.debug(f"Added page: {page_name}")

    def show_page(self, page_class: Type[Page]):
        """Show a specific page."""
        import traceback
        page_name = page_class.__name__
        print(f"🔧 PageManager.show_page called with: {page_name}")
        print(f"🔧 Call stack: {traceback.format_stack()[-2].strip()}")
            
        if page_class not in self.pages:
            error_msg = f"Page '{page_name}' not found"
            print(f"🔧 ERROR: {error_msg}")
            raise ValueError(error_msg)
        
        print(f"🔧 Page {page_name} found in pages dict")
        page = self.pages[page_class]
        
        # Hide current page
        if self.current_page:
            print(f"🔧 Hiding current page: {self.current_page.page_name}")
            self.current_page.on_hide()
        
        # Initialize page if needed
        if not page._initiated:
            print(f"🔧 Page {page_name} not initiated, calling init_page()")
            self.logger.debug(f"Initializing page: {page_name}")
            page.init_page()
            page._initiated = True
        else:
            print(f"🔧 Page {page_name} already initiated")
        
        # Show new page
        print(f"🔧 Calling tkraise() on {page_name}")
        page.tkraise()
        print(f"🔧 Calling on_show() on {page_name}")
        page.on_show()
        self.current_page = page
        
        print(f"🔧 PageManager.show_page completed for {page_name}")
        self.logger.info(f"Showing page: {page_name}")

    def get_current_page(self) -> Optional[Page]:
        """Get the currently active page."""
        return self.current_page

    def get_current_page_name(self) -> Optional[str]:
        """Get the name of the currently active page."""
        return self.current_page.page_name if self.current_page else None

    def get_current_page_class(self) -> Optional[Type[Page]]:
        """Get the class type of the currently active page."""
        return type(self.current_page) if self.current_page else None

    def reset_page(self, page_class: Type[Page]):
        """Reset a page to uninitialized state."""
        if page_class in self.pages:
            self.pages[page_class]._initiated = False
            self.logger.debug(f"Reset page: {page_class.__name__}")

    def get_navigation_info(self) -> Optional[dict]:
        """Get navigation information for the current page."""
        if self.current_page:
            current_page_class = type(self.current_page)
            next_page = self.get_next_page(current_page_class)
            previous_page = self.get_previous_page(current_page_class)
            
            return {
                "current": current_page_class.__name__,
                "next": next_page.__name__ if next_page else None,
                "previous": previous_page.__name__ if previous_page else None,
                "can_go_forward": next_page is not None,
                "can_go_backward": previous_page is not None,
            }
        return None

    def get_page(self, page_class: Type[TPage]) -> Optional[TPage]:
        """
        Get a page instance by its class type.
        This is a type-safe alternative to dictionary access.
        
        Args:
            page_class: The class type of the page to retrieve
            
        Returns:
            The page instance if found, None otherwise
        """
        for page in self.pages.values():
            if isinstance(page, page_class):
                return page
        return None
    
    def get_page_by_name(self, page_name: str, page_class: Type[TPage]) -> Optional[TPage]:
        """
        Get a page instance by name with type safety.
        
        Args:
            page_name: The name of the page to retrieve (for backward compatibility)
            page_class: The expected class type for validation
            
        Returns:
            The page instance if found and of correct type, None otherwise
        """
        page = self.pages.get(page_class)
        if page and isinstance(page, page_class):
            return page
        return None
    
    def configure_page(self, page_class: Type[TPage], configure_func) -> bool:
        """
        Type-safe method to configure a page.
        
        Args:
            page_class: The class type of the page to configure
            configure_func: Function to call with the page instance
            
        Returns:
            True if page was found and configured, False otherwise
        """
        page = self.get_page(page_class)
        if page:
            configure_func(page)
            return True
        return False

    def start(self):
        """
        Show the first enabled page in the navigation flow.
        """
        if not self._navigation_flow:
            self.logger.warning("Navigation flow not configured")
            return

        page_order = list(self._navigation_flow.keys())
        for page_class in page_order:
            if self._is_page_enabled(page_class):
                print(f"Page {page_class.__name__} is enabled, starting navigation")
                self.show_page(page_class)
                self.logger.info(f"Started navigation with page: {page_class.__name__}")
                return
        self.logger.warning("No enabled page found to start navigation")


