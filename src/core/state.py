"""
Application state management.
Replaces the global variable chaos with proper state management.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from models.check import DoneChecks
from models.install_options import InstallOptions
from models.kickstart import KickstartConfig
from models.partition import Partition
from models.spin import Spin
from services.disk import (
    PartitionInfo,
    get_efi_partition_info,
    get_windows_partition_info,
)
from services.partition import TemporaryPartition
from services.privilege_manager import elevated


@dataclass(frozen=True)
class IPLocaleInfo:
    """IP-based locale information from Fedora's GeoIP service."""

    country_code: str
    time_zone: str
    # ip: str
    # city: str
    # region_name: str
    # region: str
    # postal_code: str
    # country_name: str
    # latitude: float
    # longitude: float
    # metro_code: int | None = None
    # dma_code: int | None = None
    # country_code3: str = ""


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
class SpinSelectionState:
    """State related to spin version selection."""

    latest_version: str = ""
    is_using_untested: bool = False
    raw_spins_data: list[dict] = field(default_factory=list)


@dataclass
class CompatibilityState:
    """State related to system compatibility checks."""

    done_checks: DoneChecks | None = None
    ip_locale: IPLocaleInfo | None = None
    all_spins: list[Spin] = field(default_factory=list)
    accepted_spins: list[Spin] = field(default_factory=list)
    live_os_installer_spin: Spin | None = None
    skip_check: bool = False


@dataclass
class InstallationState:
    """State related to the installation process."""

    status: InstallerStatus = InstallerStatus.NOT_STARTED
    install_options: InstallOptions = field(default_factory=InstallOptions)
    kickstart: KickstartConfig | None = None
    partition: Partition | None = None
    selected_spin: Spin | None = None
    tmp_part: TemporaryPartition | None = None

    # Cached partition info
    _windows_partition_info: PartitionInfo | None = None
    _efi_partition_info: PartitionInfo | None = None

    @property
    def windows_partition_info(self) -> PartitionInfo:
        """Get Windows partition info, fetching and caching if needed."""
        if self._windows_partition_info is None:
            self._windows_partition_info = get_windows_partition_info()
        return self._windows_partition_info

    @property
    def efi_partition_info(self) -> PartitionInfo:
        """Get EFI partition info, fetching and caching if needed."""
        if self._efi_partition_info is None:
            self._efi_partition_info = elevated.call(get_efi_partition_info)
        return self._efi_partition_info


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

    compatibility: CompatibilityState = field(default_factory=CompatibilityState)
    spin_selection: SpinSelectionState = field(default_factory=SpinSelectionState)
    installation: InstallationState = field(default_factory=InstallationState)
    user: UserState = field(default_factory=UserState)
    error: ErrorState = field(default_factory=ErrorState)

    # Additional runtime state
    _observers: list[Callable] = field(default_factory=list, init=False)

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

    def set_spins_data(self, all_spins: list[Spin], accepted_spins: list[Spin]) -> None:
        """Set the spins data."""
        self.compatibility.all_spins = all_spins
        self.compatibility.accepted_spins = accepted_spins
        self.notify_observers(
            "spins_data_updated", all_spins=all_spins, accepted_spins=accepted_spins
        )

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
