import customtkinter as ctk
from typing import Dict, Optional

from models.page import Page
from core.navigation import NavigationManager, set_navigation_manager
from utils.logging import get_logger


class PageManager(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.pages: Dict[str, Page] = {}
        self.current_page_name: Optional[str] = None
        self.logger = get_logger(__name__)
        
        # Initialize navigation system
        self.navigation_manager = NavigationManager(self)
        set_navigation_manager(self.navigation_manager)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def add_page(self, page_name: str, page_class: Page, *args, **kwargs):
        """Add a page to the manager."""
        page = page_class(
            self,
            page_name,
            *args,
            fg_color="transparent",
            bg_color="transparent",
            **kwargs,
        )
        
        # Set up navigation for the page
        page.set_navigation_manager(self.navigation_manager)
        
        self.pages[page_name] = page
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(0, weight=1)
        page.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.logger.debug(f"Added page: {page_name}")

    def show_page(self, page_name: str):
        """Show a specific page."""
        import traceback
        print(f"🔧 PageManager.show_page called with: {page_name}")
        print(f"🔧 Call stack: {traceback.format_stack()[-2].strip()}")
            
        if page_name not in self.pages:
            error_msg = f"Page '{page_name}' not found"
            print(f"🔧 ERROR: {error_msg}")
            raise ValueError(error_msg)
        
        print(f"🔧 Page {page_name} found in pages dict")
        page = self.pages[page_name]
        
        # Hide current page
        if self.current_page_name and self.current_page_name in self.pages:
            print(f"🔧 Hiding current page: {self.current_page_name}")
            current_page = self.pages[self.current_page_name]
            current_page.on_hide()
        
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
        self.current_page_name = page_name
        
        print(f"🔧 PageManager.show_page completed for {page_name}")
        self.logger.info(f"Showing page: {page_name}")

    def get_current_page(self) -> Optional[Page]:
        """Get the currently active page."""
        if self.current_page_name:
            return self.pages.get(self.current_page_name)
        return None

    def get_current_page_name(self) -> Optional[str]:
        """Get the name of the currently active page."""
        return self.current_page_name

    def reset_page(self, page_name: str):
        """Reset a page to uninitialized state."""
        if page_name in self.pages:
            self.pages[page_name]._initiated = False
            self.logger.debug(f"Reset page: {page_name}")

    def get_navigation_info(self) -> Optional[dict]:
        """Get navigation information for the current page."""
        if self.current_page_name:
            return self.navigation_manager.get_navigation_info(self.current_page_name)
        return None


