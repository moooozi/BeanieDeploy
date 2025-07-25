"""
Page conditions for navigation logic.
Simple conditions that can be used by PageManager for conditional navigation.
"""
from abc import ABC, abstractmethod

from core.state import get_state


class PageCondition(ABC):
    """Abstract base class for page visibility/navigation conditions."""
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if this condition is met."""
        pass


class AutoInstallCondition(PageCondition):
    """Condition for auto-install related pages."""
    
    def is_enabled(self) -> bool:
        state = get_state()
        install_options = state.installation.install_options
        # Auto-install pages are enabled when partition method is NOT custom
        return install_options.partition_method != "custom"


class NetInstallCondition(PageCondition):
    """Condition for net install detection."""
    
    def is_enabled(self) -> bool:
        state = get_state()
        selected_spin = state.installation.selected_spin
        return bool(selected_spin and selected_spin.is_base_netinstall)


class DualBootCondition(PageCondition):
    """Condition for dual boot specific pages."""
    
    def is_enabled(self) -> bool:
        state = get_state()
        return state.installation.install_options.partition_method == "dualboot"


class CustomInstallCondition(PageCondition):
    """Condition for custom install method."""
    
    def is_enabled(self) -> bool:
        state = get_state()
        return state.installation.install_options.partition_method == "custom"



class SkipCheckDisabledCondition(PageCondition):
    """Condition to show PageCheck only if skip_check is False."""
    def is_enabled(self) -> bool:
        state = get_state()
        return not getattr(state.compatibility, 'skip_check', False)
