"""
Application state management.
Replaces the global variable chaos with proper state management.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from enum import Enum

from models.install_options import InstallOptions
from models.kickstart import KickstartConfig
from models.partition import Partition
from models.spin import Spin
from models.check import DoneChecks
from services.partition import TemporaryPartition
from services.disk import PartitionInfo, get_windows_partition_info, get_efi_partition_info
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
class CompatibilityState:
    """State related to system compatibility checks."""
    
    done_checks: Optional[DoneChecks] = None
    ip_locale: Dict[str, Any] = field(default_factory=dict)
    all_spins: List[Spin] = field(default_factory=list)
    accepted_spins: List[Spin] = field(default_factory=list)
    live_os_installer_spin: Optional[Spin] = None
    skip_check: bool = False

@dataclass
class InstallationState:
    """State related to the installation process."""
    
    status: InstallerStatus = InstallerStatus.NOT_STARTED
    install_options: InstallOptions = field(default_factory=InstallOptions)
    kickstart: Optional[KickstartConfig] = None
    partition: Optional[Partition] = None
    selected_spin: Optional[Spin] = None
    tmp_part: Optional[TemporaryPartition] = None
    
    # Cached partition info
    _windows_partition_info: Optional[PartitionInfo] = None
    _efi_partition_info: Optional[PartitionInfo] = None
    
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
    error_message: str = ""
    error_details: str = ""


@dataclass
class ApplicationState:
    """Complete application state."""
    
    compatibility: CompatibilityState = field(default_factory=CompatibilityState)
    installation: InstallationState = field(default_factory=InstallationState)
    user: UserState = field(default_factory=UserState)
    error: ErrorState = field(default_factory=ErrorState)
    
    # Additional runtime state
    _observers: List[Callable] = field(default_factory=list, init=False)
    
    def add_observer(self, observer: Callable) -> None:
        """Add an observer to be notified of state changes."""
        self._observers.append(observer)
    
    def remove_observer(self, observer: Callable) -> None:
        """Remove an observer."""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify_observers(self, change_type: str, **kwargs) -> None:
        """Notify all observers of a state change."""
        for observer in self._observers:
            try:
                observer(change_type, **kwargs)
            except Exception:
                # Don't let observer errors crash the app
                pass
    
    def update_installer_status(self, status: InstallerStatus) -> None:
        """Update the installer status and notify observers."""
        old_status = self.installation.status
        self.installation.status = status
        self.notify_observers("installer_status_changed", 
                             old_status=old_status, new_status=status)
    
    def set_selected_spin(self, spin: Spin) -> None:
        """Set the selected spin and notify observers."""
        old_spin = self.installation.selected_spin
        self.installation.selected_spin = spin
        self.notify_observers("selected_spin_changed",
                             old_spin=old_spin, new_spin=spin)
    
    def update_compatibility_checks(self, done_checks: Any) -> None:
        """Update compatibility check results."""
        self.compatibility.done_checks = done_checks
        self.notify_observers("compatibility_checks_updated",
                             done_checks=done_checks)
    
    def set_spins_data(self, all_spins: List[Spin], accepted_spins: List[Spin]) -> None:
        """Set the spins data."""
        self.compatibility.all_spins = all_spins
        self.compatibility.accepted_spins = accepted_spins
        self.notify_observers("spins_data_updated",
                             all_spins=all_spins, accepted_spins=accepted_spins)
    
    def set_error_message(self, message: str, details: str = "") -> None:
        """Set an error message and notify observers."""
        self.error.has_error = True
        self.error.error_message = message
        self.error.error_details = details
        self.notify_observers("error_occurred", 
                             message=message, details=details)
    
    def clear_error(self) -> None:
        """Clear the current error state."""
        self.error.has_error = False
        self.error.error_message = ""
        self.error.error_details = ""
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
_state_manager: Optional[StateManager] = None


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
