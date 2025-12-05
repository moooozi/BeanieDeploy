import logging
import threading
from typing import Any

import dummy
from config.settings import get_config
from core.compatibility_logic import filter_spins
from core.navigation_conditions import SkipCheckDisabledCondition
from core.state import IPLocaleInfo, get_state, get_state_manager
from models.page_manager import PageManager
from models.types import NavigationFlow, SpinDictList
from pages.page_1 import Page1
from pages.page_autoinst2 import PageAutoinst2
from pages.page_autoinst_addition_1 import PageAutoinstAddition1
from pages.page_autoinst_addition_2 import PageAutoinstAddition2
from pages.page_check import PageCheck
from pages.page_error import PageError
from pages.page_install_method import PageInstallMethod
from pages.page_installing import PageInstalling
from pages.page_playground import PagePlayground
from pages.page_restart_required import PageRestartRequired
from pages.page_verify import PageVerify
from services.download import DownloadService
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
        self.download_service = DownloadService(self.config)

        # Add observer for state changes
        self.app_state.add_observer(self._on_state_change)

        threading.Thread(target=self._fetch_spins, daemon=True).start()
        threading.Thread(target=self._fetch_ip_locale, daemon=True).start()

        # Create page manager with integrated navigation
        self.page_manager = PageManager(self)
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

    def _on_state_change(self, change_type: str, **_kwargs) -> None:
        """Handle state changes."""
        logging.info(f"State change detected: {change_type}")
        if change_type == "error_occurred":
            logging.info("Scheduling navigation to error page")

            self.after(0, lambda: self.page_manager.show_page(PageError))

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
        self.app_state.compatibility.ip_locale = IPLocaleInfo(
            country_code=data["country_code"], time_zone=data["time_zone"]
        )

    def _fetch_spins(self):
        try:
            data = self.download_service.fetch_json(
                self.config.urls.available_spins_list
            )
            self.after(0, self._on_spin_promise_complete, data)
        except Exception as e:
            msg = f"Failed to fetch spins: {e}"
            logging.exception(msg)
            # Set error in state (will auto-navigate to error page)
            self.app_state.set_error_messages([msg])

    def _fetch_ip_locale(self):
        try:
            data = self.download_service.fetch_json(self.config.urls.fedora_geo_ip)
            self.after(0, self._update_ip_locale, data)
        except Exception as e:
            logging.error(f"Failed to fetch IP locale: {e}")
            # Non-critical - just log and continue
