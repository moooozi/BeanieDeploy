from typing import Optional
from models.page_manager import PageManager
from models.installation_context import InstallationContext
from pages.page_autoinst2 import PageAutoinst2
from pages.page_check import PageCheck
from pages.page_error import PageError
from pages.page_install_method import PageInstallMethod
from pages.page_installing import PageInstalling
from pages.page_1 import Page1
from pages.page_autoinst_addition_1 import PageAutoinstAddition1
from pages.page_autoinst_addition_2 import PageAutoinstAddition2
from pages.page_autoinst_addition_3 import PageAutoinstAddition3
from pages.page_playground import PagePlayground
from pages.page_verify import PageVerify
from pages.page_restart_required import PageRestartRequired
from templates.application import Application
from config.settings import get_config
from core.state import get_state_manager
from utils.logging import get_logger


class MainApp(Application):
    def __init__(
        self,
        skip_check: bool = False,
        done_checks=None,
        installation_context: Optional[InstallationContext] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        
        # Get system components
        self.config = get_config()
        self.state_manager = get_state_manager()
        self.logger = get_logger(__name__)
        
        # Create page manager with integrated navigation
        self.page_manager = PageManager(
            self, fg_color="transparent", bg_color="transparent"
        )
        self.page_manager.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Configure navigation flow
        self._configure_navigation_flow()

        # Add all pages with their new constructor signature
        self.page_manager.add_page(PageError)
        self.page_manager.add_page(PageCheck)
        self.page_manager.add_page(Page1)
        self.page_manager.add_page(PageInstallMethod)
        self.page_manager.add_page(PageAutoinstAddition1)
        self.page_manager.add_page(PageAutoinstAddition2)
        self.page_manager.add_page(PageAutoinstAddition3)
        self.page_manager.add_page(PageAutoinst2)
        self.page_manager.add_page(PageVerify)
        self.page_manager.add_page(PageInstalling)
        self.page_manager.add_page(PageRestartRequired)
        self.page_manager.add_page(PagePlayground)

        # Handle initialization parameters using new state system
        playground = False

        if playground:
            return self.page_manager.show_page(PagePlayground)
        
        if installation_context:
            # Set installation context through the specific page type
            self.page_manager.configure_page(PageInstalling, 
                                           lambda page: page.set_installation_context(installation_context))
            return self.page_manager.show_page(PageInstalling)
        
        if skip_check:
            # Set skip check flag through the specific page type
            self.page_manager.configure_page(PageCheck,
                                           lambda page: page.set_skip_check(skip_check))
            
        if done_checks:
            # Set done checks through the specific page type
            self.page_manager.configure_page(PageCheck,
                                           lambda page: page.set_done_checks(done_checks))
            
        # Start with the check page only if no page is currently shown
        if not self.page_manager.current_page:
            return self.page_manager.show_page(PageCheck)

    def _configure_navigation_flow(self):
        """Configure the navigation flow for the page manager."""
        from typing import Dict, Type, Any
        from models.page import Page
        from core.navigation_conditions import UserAccountRequiredCondition, AutoInstallCondition
        from core.state import get_state
        
        def determine_install_method_next() -> Type[Page]:
            """Dynamically determine next page based on install method."""
            state = get_state()
            partition_method = state.installation.install_options.partition_method
            
            if partition_method == "custom":
                return PageVerify
            else:
                return PageAutoinst2  # Default to auto-install flow
        
        navigation_flow: Dict[Type[Page], Any] = {
            PageCheck: {},
            Page1: {},
            PageInstallMethod: {
                "next": determine_install_method_next
            },
            PageAutoinst2: {
                "conditions": [AutoInstallCondition()]
            },
            PageAutoinstAddition1: {
                "conditions": [AutoInstallCondition()]
            },
            PageAutoinstAddition2: {
                "conditions": [AutoInstallCondition()]
            },
            PageAutoinstAddition3: {
                "conditions": [AutoInstallCondition(), UserAccountRequiredCondition()]
            },
            PageVerify: {},
            PageInstalling: {},
            PageRestartRequired: {},
            # Special pages not in main flow
            PageError: {"special": True}
        }
        
        self.page_manager.configure_navigation_flow(navigation_flow)
