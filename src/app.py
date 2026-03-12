import logging
from typing import Any

from core.navigation_conditions import (
    ReleaseModeCondition,
    SkipCheckDisabledCondition,
)
from core.settings import get_config
from core.state import get_state, get_state_manager
from models.page import NavigationEntry
from models.page_manager import PageManager
from pages.page_1 import Page1
from pages.page_autoinst_addition_1 import PageAutoinstAddition1
from pages.page_autoinst_addition_2 import PageAutoinstAddition2
from pages.page_check import PageCheck
from pages.page_disclaimer import PageDisclaimer
from pages.page_error import PageError
from pages.page_install_method import PageInstallMethod
from pages.page_installing import PageInstalling
from pages.page_playground import PagePlayground
from pages.page_restart_required import PageRestartRequired
from pages.page_verify import PageVerify
from templates.application import Application


class MainApp(Application):
    def __init__(
        self,
        skip_check: bool = False,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)

        self.state_manager = get_state_manager()
        self.app_state = get_state()
        self.app_config = get_config()
        self.app_state.add_observer(self._on_state_change)

        self.page_manager = PageManager(self)
        self._setup_navigation()

        playground = False
        if playground:
            return self.page_manager.show_page(PagePlayground)

        if skip_check:
            logging.info("Skipping checks")

        if not self.page_manager.current_page:
            return self.page_manager.start()
        return None

    def _on_state_change(self, change_type: str, **_kwargs) -> None:
        """Handle state changes."""
        if change_type == "error_occurred":
            self.after(0, lambda: self.page_manager.show_page(PageError))

    def _setup_navigation(self):
        """Configure navigation flow and register all pages."""
        from core.navigation_conditions import AutoInstallCondition

        navigation_flow = {
            PageDisclaimer: NavigationEntry(conditions=[ReleaseModeCondition()]),
            PageCheck: NavigationEntry(conditions=[SkipCheckDisabledCondition()]),
            Page1: NavigationEntry(),
            PageInstallMethod: NavigationEntry(),
            PageAutoinstAddition1: NavigationEntry(conditions=[AutoInstallCondition()]),
            PageAutoinstAddition2: NavigationEntry(conditions=[AutoInstallCondition()]),
            PageVerify: NavigationEntry(),
            PageInstalling: NavigationEntry(),
            PageRestartRequired: NavigationEntry(),
            PageError: NavigationEntry(special=True),
        }

        self.page_manager.configure_navigation_flow(navigation_flow)

        for page_class in [*navigation_flow, PagePlayground]:
            self.page_manager.add_page(page_class)
