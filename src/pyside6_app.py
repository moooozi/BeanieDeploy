from typing import Optional
from PySide6.QtWidgets import QApplication, QMessageBox

from core.navigation_conditions import SkipCheckDisabledCondition
import dummy
from models.pyside6_page_manager import PySide6PageManager
from models.installation_context import InstallationContext
from services.spin_manager import parse_spins
from templates.pyside6_application import PySide6Application
from config.settings import get_config
from core.state import get_state, get_state_manager
from utils.logging import get_logger

# Import PySide6 page classes
from pages.pyside6_page_1 import PySide6Page1
from pages.pyside6_page_autoinst2 import PySide6PageAutoinst2
from pages.pyside6_page_check import PySide6PageCheck
from pages.pyside6_page_error import PySide6PageError
from pages.pyside6_page_install_method import PySide6PageInstallMethod


class PySide6MainApp(PySide6Application):
    """
    Main PySide6 application class.
    
    Simplified compared to CustomTkinter version because:
    - Qt handles window management better
    - No need for custom grid layouts (Qt has better layout managers)
    - Built-in message box support
    - Better error handling
    """
    
    def __init__(
        self,
        skip_check: bool = False,
        done_checks=None,
        installation_context: Optional[InstallationContext] = None,
        playground: bool = False,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        
        # Get system components
        self.config = get_config()
        self.state_manager = get_state_manager()
        self.logger = get_logger(__name__)
        
        # Create page manager
        self.page_manager = PySide6PageManager(self)
        self.setCentralWidget(self.page_manager)
        
        # Connect page manager signals
        self.page_manager.navigation_error.connect(self._show_navigation_error)
        self.page_manager.page_changed.connect(self._on_page_changed)
        
        # Configure navigation flow and automatically add pages
        self._configure_navigation_flow()
        self._add_pages_from_navigation_flow()
        
        # Handle initialization parameters
        self._handle_initialization_parameters(skip_check, done_checks, installation_context)

    def _configure_navigation_flow(self):
        """Configure the navigation flow for the page manager."""
        from core.navigation_conditions import (
            AutoInstallCondition,
        )
        
        # Configure navigation flow with PySide6 page classes
        # As we create more PySide6 pages, we'll uncomment them here
        navigation_flow = {
            PySide6PageCheck: {"conditions": [SkipCheckDisabledCondition()]},
            PySide6Page1: {},
            PySide6PageInstallMethod: {},
            PySide6PageAutoinst2: {
                "conditions": [AutoInstallCondition()]
            },
            # TODO: Add remaining pages as they're created
            # PySide6PageAutoinstAddition1: {
            #     "conditions": [AutoInstallCondition()]
            # },
            # PySide6PageAutoinstAddition2: {
            #     "conditions": [AutoInstallCondition()]
            # },
            # PySide6PageAutoinstAddition3: {
            #     "conditions": [AutoInstallCondition(), UserAccountRequiredCondition()]
            # },
            # PySide6PageVerify: {
            #     "conditions": [CustomInstallCondition()]
            # },
            # PySide6PageInstalling: {},
            # PySide6PageRestartRequired: {},
            # Special pages not in main flow
            PySide6PageError: {"special": True}
        }
        
        self.page_manager.configure_navigation_flow(navigation_flow)

    def _add_pages_from_navigation_flow(self):
        """
        Automatically add all pages from the navigation flow.
        This eliminates the need to manually add each page and keeps everything in sync.
        """
        # Get the navigation flow that was just configured
        navigation_flow = self.page_manager._navigation_flow
        
        if not navigation_flow:
            self.logger.warning("No navigation flow configured, cannot add pages")
            return
        
        # Extract all page classes from the navigation flow
        page_classes = set(navigation_flow.keys())
        
        # Add special pages that might be referenced in custom navigation functions
        # Note: We'll add more special pages as we create PySide6 versions of them
        # special_pages = {PySide6PagePlayground}  # Add when created
        # page_classes.update(special_pages)
        
        # Add each page to the page manager
        for page_class in page_classes:
            try:
                self.page_manager.add_page(page_class)
                self.logger.debug(f"Added page: {page_class.__name__}")
            except Exception as e:
                self.logger.error(f"Failed to add page {page_class.__name__}: {e}")
        
        self.logger.info(f"Successfully added {len(page_classes)} pages from navigation flow")

    def _handle_initialization_parameters(
        self, 
        skip_check: bool, 
        done_checks, 
        installation_context: Optional[InstallationContext]
    ):
        """Handle initialization parameters."""
        playground = False  # TODO: Get from config or args when needed
        
        if playground:
            # TODO: Show playground page when PySide6PagePlayground is created
            self.logger.info("Playground mode requested but not yet implemented")
        
        if installation_context:
            # Configure installation page when it exists
            self.logger.info("Installation context provided - will configure installation page")
            # TODO: Uncomment when PySide6PageInstalling is created
            # self.page_manager.configure_page(PySide6PageInstalling, 
            #                                lambda page: page.set_installation_context(installation_context))
            # return self.page_manager.show_page(PySide6PageInstalling)
        if done_checks:
            # Set done checks through the specific page type
            self.logger.info("Done checks provided")
            self.page_manager.configure_page(PySide6PageCheck,
                                           lambda page: page.set_done_checks(done_checks))


        if skip_check:
            self.logger.info("Skipping checks - using dummy data")
            _, all_spins = parse_spins(dummy.DUMMY_ALL_SPINS)
            get_state().compatibility.accepted_spins = all_spins
            get_state().compatibility.ip_locale = dummy.DUMMY_IP_LOCALE
            print("Using dummy data for all spins")
            
        # Show the first page
        if not self.page_manager.current_page:
            return self.page_manager.start()

    def _show_navigation_error(self, message: str):
        """Show navigation error to user."""
        QMessageBox.warning(self, "Navigation Error", message)

    def _on_page_changed(self, page_name: str):
        """Handle page change event."""
        self.logger.info(f"Page changed to: {page_name}")
        # Update window title if needed
        self.setWindowTitle(f"BeanieDeploy - {page_name}")


def create_pyside6_app() -> QApplication:
    """Create and configure the PySide6 application."""
    app = QApplication([])
    
    # Set application properties
    app.setApplicationName("BeanieDeploy")
    app.setApplicationVersion("0.94-Beta")
    app.setOrganizationName("BeanieDeploy")
    
    # Qt automatically handles dark mode based on system settings
    # No need for custom dark mode detection like in CustomTkinter
    
    return app