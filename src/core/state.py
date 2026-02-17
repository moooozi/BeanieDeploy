"""
Application state management.
Replaces the global variable chaos with proper state management.
"""

import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.settings import get_config
from models.check import DoneChecks
from models.install_options import InstallOptions
from models.kickstart import KickstartConfig
from models.partition import PartitioningOptions
from models.spin import Spin
from models.types import IPLocaleInfo
from services.disk import (
    Partition,
    get_efi_partition,
    get_windows_partition,
)
from services.download import fetch_json
from services.privilege_manager import elevated


class InstallerStatus(Enum):
    """Installation status enumeration."""

    NOT_STARTED = "not_started"
    CHECKING = "checking"
    READY = "ready"
    DOWNLOADING = "downloading"
    INSTALLING = "installing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SpinState:
    """State related to spin version selection."""

    supported_version: str
    use_dummy: bool = False

    is_using_untested: bool = False

    _latest_version: str = ""
    _raw_spins_data: list[dict] = field(default_factory=list)
    _accepted_spins: list[Spin] = field(default_factory=list)
    _all_spins: list[Spin] = field(default_factory=list)
    _live_os_installer_spin: Spin | None = None

    @property
    def latest_version(self) -> str:
        """Get latest version."""
        if not self._latest_version:
            self.load_spins_info()
        return self._latest_version

    @property
    def raw_spins_data(self) -> list[dict]:
        """Get raw spins data."""
        if not self._raw_spins_data:
            self.load_spins_info()
        return self._raw_spins_data

    @property
    def accepted_spins(self) -> list[Spin]:
        """Get accepted spins."""
        if not self._accepted_spins:
            self.set_accepted_spins()
        return self._accepted_spins

    @property
    def all_spins(self) -> list[Spin]:
        """Get all spins."""
        if not self._all_spins:
            self.load_spins_info()
        return self._all_spins

    @property
    def live_os_installer_spin(self) -> Spin | None:
        for spin in self._accepted_spins:
            if spin.is_base_netinstall:
                return spin
        return None

    def load_spins_info(self):
        from services.spin_manager import parse_spins

        try:
            if self.use_dummy:
                import offline_data

                self._raw_spins_data = offline_data.get_fallback_offline_spin_data()
            else:
                url = get_config().urls.available_spins_list
                data = fetch_json(url)
                self._raw_spins_data = data
            parsed_spins, latest_version = parse_spins(self._raw_spins_data)
            self._latest_version = latest_version
            self._all_spins = parsed_spins
        except Exception as e:
            msg = f"Failed to fetch spins: {e}"
            logging.exception(msg)

    def set_accepted_spins(self, version: str | None = None):
        """Set accepted spins based on version."""
        if version is None:
            if self.is_using_untested:
                version = self.latest_version
            else:
                version = self.supported_version
        spins = [spin for spin in self.all_spins if spin.version == version]
        for spin in spins:
            if spin.is_base_netinstall:
                self._live_os_installer_spin = spin
                break
        if self._live_os_installer_spin:
            self._accepted_spins = spins
        else:
            # strip liveos images if no netinstall found
            spins = [spin for spin in spins if not spin.is_live_img]


@dataclass
class CompatibilityState:
    """State related to system compatibility checks."""

    use_dummy: bool

    done_checks: DoneChecks | None = None
    _ip_locale: IPLocaleInfo | None = None
    skip_check: bool = False

    @property
    def ip_locale(self) -> IPLocaleInfo | None:
        """Get IP locale information."""
        if self._ip_locale is None:
            if self.use_dummy:
                import offline_data

                self._ip_locale = offline_data.DEFAULT_IP_LOCALE
            else:
                self.update_ip_locale()
        return self._ip_locale

    def update_ip_locale(self):
        url = get_config().urls.fedora_geo_ip
        data = fetch_json(url)
        self._ip_locale = IPLocaleInfo(
            country_code=data["country_code"], time_zone=data["time_zone"]
        )


@dataclass
class InstallationState:
    """State related to the installation process."""

    status: InstallerStatus = InstallerStatus.NOT_STARTED
    install_options: InstallOptions = field(default_factory=InstallOptions)
    kickstart: KickstartConfig | None = None
    partition: PartitioningOptions | None = None
    selected_spin: Spin | None = None
    tmp_part: Partition | None = None
    # Cached partition info
    _windows_partition: Partition | None = None
    _efi_partition: Partition | None = None
    _windows_partition_fetched: bool = False
    _efi_partition_fetched: bool = False

    @property
    def windows_partition(self) -> Partition:
        """Get Windows partition info, fetching and caching if needed.

        Raises RuntimeError if the WMI query fails.  The failure is cached
        so subsequent accesses raise immediately without re-querying.
        """
        if not self._windows_partition_fetched:
            self._windows_partition_fetched = True
            try:
                self._windows_partition = get_windows_partition()
            except Exception:
                logging.exception("Failed to query Windows partition")
        if self._windows_partition is None:
            msg = "Windows partition could not be determined"
            raise RuntimeError(msg)
        return self._windows_partition

    @property
    def efi_partition(self) -> Partition:
        """Get EFI partition info, fetching and caching if needed.

        Raises RuntimeError if the WMI query fails.  The failure is cached
        so subsequent accesses raise immediately without re-querying.
        """
        if not self._efi_partition_fetched:
            self._efi_partition_fetched = True
            try:
                self._efi_partition = elevated.call(get_efi_partition)
            except Exception:
                logging.exception("Failed to query EFI partition")
        if self._efi_partition is None:
            msg = "EFI partition could not be determined"
            raise RuntimeError(msg)
        return self._efi_partition


@dataclass
class UserState:
    """State related to user information and preferences."""

    selected_language: str = "English"
    tmp_partition_letter: str = ""


@dataclass
class ErrorState:
    """State related to error handling."""

    has_error: bool = False
    error_messages: list[str] = field(default_factory=list)
    category: str = "generic"


@dataclass
class ApplicationState:
    """Complete application state."""

    installation: InstallationState = field(default_factory=InstallationState)
    user: UserState = field(default_factory=UserState)
    error: ErrorState = field(default_factory=ErrorState)

    is_release_mode: bool = getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")

    compatibility: CompatibilityState = field(init=False)
    spins: SpinState = field(init=False)

    # Additional runtime state
    _observers: list[Callable] = field(default_factory=list, init=False)

    def __post_init__(self):
        use_dummy = not self.is_release_mode
        supported_version = get_config().app.supported_version
        self.compatibility = CompatibilityState(use_dummy=use_dummy)
        self.spins = SpinState(supported_version=supported_version, use_dummy=use_dummy)

    def add_observer(self, observer: Callable) -> None:
        """Add an observer to be notified of state changes."""
        self._observers.append(observer)

    def remove_observer(self, observer: Callable) -> None:
        """Remove an observer."""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify_observers(self, change_type: str, **kwargs) -> None:
        """Notify all observers of a state change."""
        logging.info(f"Notifying {len(self._observers)} observers of {change_type}")
        for observer in self._observers:
            try:
                observer(change_type, **kwargs)
            except Exception as e:
                logging.error(f"Error in observer: {e}")

    def update_installer_status(self, status: InstallerStatus) -> None:
        """Update the installer status and notify observers."""
        old_status = self.installation.status
        self.installation.status = status
        self.notify_observers(
            "installer_status_changed", old_status=old_status, new_status=status
        )

    def set_selected_spin(self, spin: Spin) -> None:
        """Set the selected spin and notify observers."""
        old_spin = self.installation.selected_spin
        self.installation.selected_spin = spin
        self.notify_observers("selected_spin_changed", old_spin=old_spin, new_spin=spin)

    def update_compatibility_checks(self, done_checks: Any) -> None:
        """Update compatibility check results."""
        self.compatibility.done_checks = done_checks
        self.notify_observers("compatibility_checks_updated", done_checks=done_checks)

    def set_error_messages(
        self, messages: list[str], category: str = "generic"
    ) -> None:
        """Set error messages and category, and notify observers."""
        logging.info(f"Setting error messages: {messages}, category: {category}")
        self.error.has_error = True
        self.error.error_messages = messages
        self.error.category = category
        self.notify_observers("error_occurred", messages=messages, category=category)

    def clear_error(self) -> None:
        """Clear the current error state."""
        self.error.has_error = False
        self.error.error_messages = []
        self.error.category = "generic"
        self.notify_observers("error_cleared")


class StateManager:
    """Centralized state management."""

    def __init__(self):
        self._state = ApplicationState()

    @property
    def state(self) -> ApplicationState:
        """Get the current application state."""
        return self._state

    def reset(self) -> None:
        """Reset the state to initial values."""
        self._state = ApplicationState()

    def add_observer(self, observer: Callable) -> None:
        """Add a state observer."""
        self._state.add_observer(observer)

    def remove_observer(self, observer: Callable) -> None:
        """Remove a state observer."""
        self._state.remove_observer(observer)


# Global state manager instance
_state_manager: StateManager | None = None


def get_state_manager() -> StateManager:
    """Get the global state manager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager


def get_state() -> ApplicationState:
    """Get the current application state."""
    return get_state_manager().state


def set_state_manager(state_manager: StateManager) -> None:
    """Set the global state manager (for testing)."""
    global _state_manager
    _state_manager = state_manager
