from models.page_manager import PageManager
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
        skip_check=False,
        done_checks=None,
        install_args=None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        
        # Get system components
        self.config = get_config()
        self.state_manager = get_state_manager()
        self.logger = get_logger(__name__)
        
        # Create page manager with new navigation system
        self.page_manager = PageManager(
            self, fg_color="transparent", bg_color="transparent"
        )
        self.page_manager.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Add all pages with their new constructor signature
        self.page_manager.add_page("PageError", PageError)
        self.page_manager.add_page("PageCheck", PageCheck)
        self.page_manager.add_page("Page1", Page1)
        self.page_manager.add_page("PageInstallMethod", PageInstallMethod)
        self.page_manager.add_page("PageAutoinstAddition1", PageAutoinstAddition1)
        self.page_manager.add_page("PageAutoinstAddition2", PageAutoinstAddition2)
        self.page_manager.add_page("PageAutoinstAddition3", PageAutoinstAddition3)
        self.page_manager.add_page("PageAutoinst2", PageAutoinst2)
        self.page_manager.add_page("PageVerify", PageVerify)
        self.page_manager.add_page("PageInstalling", PageInstalling)
        self.page_manager.add_page("PageRestartRequired", PageRestartRequired)
        self.page_manager.add_page("PagePlayground", PagePlayground)

        # Handle initialization parameters using new state system
        playground = False

        if playground:
            return self.page_manager.show_page("PagePlayground")
        
        if install_args:
            # Set installer args through the new state system or page directly
            self.page_manager.pages["PageInstalling"].set_installer_args(install_args)
            return self.page_manager.show_page("PageInstalling")
        
        if skip_check:
            # Set skip check flag through the page
            self.page_manager.pages["PageCheck"].set_skip_check(skip_check)
            
        if done_checks:
            # Set done checks through the page
            self.page_manager.pages["PageCheck"].set_done_checks(done_checks)
            
        # Start with the check page only if no page is currently shown
        if not self.page_manager.current_page_name:
            return self.page_manager.show_page("PageCheck")
