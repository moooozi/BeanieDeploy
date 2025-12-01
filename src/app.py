import logging
import threading
from typing import Any

import requests

import dummy
from config.settings import get_config
from core.compatibility_logic import filter_spins
from core.navigation_conditions import SkipCheckDisabledCondition
from core.state import get_state, get_state_manager
from models.page_manager import PageManager
from models.types import NavigationFlow, SpinDictList
from pages.page_1 import Page1
from pages.page_autoinst2 import PageAutoinst2
from pages.page_autoinst_addition_1 import PageAutoinstAddition1
from pages.page_autoinst_addition_2 import PageAutoinstAddition2
from pages.page_check import PageCheck
from pages.page_error import PageError
from pages.page_install_failed import PageInstallFailed
from pages.page_install_method import PageInstallMethod
from pages.page_installing import PageInstalling
from pages.page_playground import PagePlayground
from pages.page_restart_required import PageRestartRequired
from pages.page_verify import PageVerify
from services.spin_manager import parse_spins
from templates.application import Application


class MainApp(Application):
    def __init__(
        self,
        skip_check: bool = False,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)

        # Get system components
        self.config = get_config()
        self.state_manager = get_state_manager()
        self.app_state = get_state()

        threading.Thread(target=self._fetch_spins, daemon=True).start()
        threading.Thread(target=self._fetch_ip_locale, daemon=True).start()

        # Create page manager with integrated navigation
        self.page_manager = PageManager(
            self, fg_color="transparent", bg_color="transparent"
        )
        self.page_manager.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Configure navigation flow and automatically add pages
        self._configure_navigation_flow()
        self._add_pages_from_navigation_flow()
        # Handle initialization parameters using new state system
        playground = False

        if playground:
            return self.page_manager.show_page(PagePlayground)

        if skip_check:
            logging.info("Skipping checks - using dummy data")
            all_spins = parse_spins(dummy.get_dummy_spin_data())
            get_state().compatibility.accepted_spins = all_spins
            get_state().compatibility.ip_locale = dummy.DUMMY_IP_LOCALE
            logging.info("Using dummy data")

        # Show the first page in self._navigation_flow if no page is currently shown
        if not self.page_manager.current_page:
            # Show the first page in self._navigation_flow
            return self.page_manager.start()
        return None

    def _configure_navigation_flow(self):
        """Configure the navigation flow for the page manager."""
        from core.navigation_conditions import (
            AutoInstallCondition,
        )

        navigation_flow: NavigationFlow = {
            PageCheck: {"conditions": [SkipCheckDisabledCondition()]},
            Page1: {},
            PageInstallMethod: {},
            PageAutoinst2: {"conditions": [AutoInstallCondition()]},
            PageAutoinstAddition1: {"conditions": [AutoInstallCondition()]},
            PageAutoinstAddition2: {"conditions": [AutoInstallCondition()]},
            PageVerify: {},
            PageInstalling: {},
            PageRestartRequired: {},
            # Special pages not in main flow
            PageError: {"special": True},
            PageInstallFailed: {"special": True},
        }

        self.page_manager.configure_navigation_flow(navigation_flow)

    def _add_pages_from_navigation_flow(self):
        """
        Automatically add all pages from the navigation flow.
        This eliminates the need to manually add each page and keeps everything in sync.
        """
        # Get the navigation flow that was just configured
        navigation_flow = self.page_manager.get_navigation_flow()

        if not navigation_flow:
            logging.warning("No navigation flow configured, cannot add pages")
            return

        # Extract all page classes from the navigation flow
        page_classes = set(navigation_flow.keys())

        # Add special pages that might be referenced in custom navigation functions
        # These could be referenced in "next" or "previous" callbacks
        special_pages = {PagePlayground}  # Add any other special pages here
        page_classes.update(special_pages)

        # Add each page to the page manager
        for page_class in page_classes:
            try:
                self.page_manager.add_page(page_class)
                logging.debug(f"Added page: {page_class.__name__}")
            except Exception as e:
                logging.error(f"Failed to add page {page_class.__name__}: {e}")

        logging.info(
            f"Successfully added {len(page_classes)} pages from navigation flow"
        )

    def _on_spin_promise_complete(self, spins: SpinDictList) -> None:
        """
        Callback for when the spins promise completes.
        Sets the available spins in the state.
        """
        parsed_spins = parse_spins(spins)
        self.app_state.compatibility.all_spins = parsed_spins
        filtered_result = filter_spins(self.app_state.compatibility.all_spins)
        self.app_state.compatibility.accepted_spins = filtered_result.spins
        if filtered_result.live_os_installer_index is not None:
            self.app_state.compatibility.live_os_installer_spin = (
                self.app_state.compatibility.accepted_spins[
                    filtered_result.live_os_installer_index
                ]
            )
        logging.info("About to navigate_next()")

    def _update_ip_locale(self, data):
        self.app_state.compatibility.ip_locale = data

    def _fetch_spins(self):
        url = self.config.urls.available_spins_list
        data = requests.get(url).json()
        self.after(0, self._on_spin_promise_complete, data)

    def _fetch_ip_locale(self):
        url = self.config.urls.fedora_geo_ip
        data = requests.get(url).json()
        self.after(0, self._update_ip_locale, data)
