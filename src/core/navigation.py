"""
Navigation system for the application.
Handles page flow, conditional navigation, and page state management.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Callable, Any
from enum import Enum

from core.state import get_state
from config.settings import get_config
from utils.logging import get_logger


class NavigationDirection(Enum):
    """Navigation direction enumeration."""
    FORWARD = "forward"
    BACKWARD = "backward"


class NavigationResult:
    """Result of a navigation attempt."""
    
    def __init__(self, success: bool, target_page: Optional[str] = None, 
                 error_message: Optional[str] = None):
        self.success = success
        self.target_page = target_page
        self.error_message = error_message


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
        selected_spin = state.installation.selected_spin
        return selected_spin and selected_spin.is_auto_installable


class NetInstallCondition(PageCondition):
    """Condition for net install detection."""
    
    def is_enabled(self) -> bool:
        state = get_state()
        selected_spin = state.installation.selected_spin
        return selected_spin and selected_spin.is_base_netinstall


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


class NavigationFlow:
    """Defines the navigation flow between pages."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._flow_map = self._build_flow_map()
    
    def _build_flow_map(self) -> Dict[str, Dict[str, Any]]:
        """Build the navigation flow map."""
        return {
            "PageCheck": {
                "next": "Page1",
                "previous": None,
                "conditions": [],
            },
            "Page1": {
                "next": "PageInstallMethod",
                "previous": "PageCheck",
                "conditions": [],
            },
            "PageInstallMethod": {
                "next": self._determine_install_method_next,
                "previous": "Page1",
                "conditions": [],
            },
            "PageAutoinst2": {
                "next": "PageAutoinstAddition1",
                "previous": "PageInstallMethod",
                "conditions": [AutoInstallCondition()],
            },
            "PageAutoinstAddition1": {
                "next": "PageAutoinstAddition2",
                "previous": "PageAutoinst2",
                "conditions": [AutoInstallCondition()],
            },
            "PageAutoinstAddition2": {
                "next": "PageAutoinstAddition3",
                "previous": "PageAutoinstAddition1",
                "conditions": [AutoInstallCondition()],
            },
            "PageAutoinstAddition3": {
                "next": "PageVerify",
                "previous": "PageAutoinstAddition2",
                "conditions": [AutoInstallCondition()],
            },
            "PageVerify": {
                "next": "PageInstalling",
                "previous": self._determine_verify_previous,
                "conditions": [],
            },
            "PageInstalling": {
                "next": "PageRestartRequired",
                "previous": None,  # Can't go back during installation
                "conditions": [],
            },
            "PageRestartRequired": {
                "next": None,
                "previous": None,
                "conditions": [],
            },
            "PageError": {
                "next": None,
                "previous": None,
                "conditions": [],
            }
        }
    
    def _determine_install_method_next(self) -> str:
        """Dynamically determine next page based on install method."""
        state = get_state()
        partition_method = state.installation.install_options.partition_method
        
        if partition_method == "custom":
            return "PageVerify"
        elif partition_method in ["dualboot", "replace_win"]:
            return "PageAutoinst2"
        else:
            return "PageAutoinst2"  # Default to auto-install flow
    
    def _determine_verify_previous(self) -> str:
        """Dynamically determine previous page for verify page."""
        state = get_state()
        partition_method = state.installation.install_options.partition_method
        
        if partition_method == "custom":
            return "PageInstallMethod"
        else:
            return "PageAutoinstAddition3"
    
    def get_next_page(self, current_page: str) -> Optional[str]:
        """Get the next page in the flow."""
        flow_entry = self._flow_map.get(current_page)
        if not flow_entry:
            return None
        
        next_page = flow_entry["next"]
        if callable(next_page):
            next_page = next_page()
        
        # Check if next page is enabled
        if next_page and not self._is_page_enabled(next_page):
            # Skip to the next page after the disabled one
            return self.get_next_page(next_page)
        
        return next_page
    
    def get_previous_page(self, current_page: str) -> Optional[str]:
        """Get the previous page in the flow."""
        flow_entry = self._flow_map.get(current_page)
        if not flow_entry:
            return None
        
        previous_page = flow_entry["previous"]
        if callable(previous_page):
            previous_page = previous_page()
        
        # Check if previous page is enabled
        if previous_page and not self._is_page_enabled(previous_page):
            # Skip to the previous page before the disabled one
            return self.get_previous_page(previous_page)
        
        return previous_page
    
    def _is_page_enabled(self, page_name: str) -> bool:
        """Check if a page is enabled based on its conditions."""
        flow_entry = self._flow_map.get(page_name)
        if not flow_entry:
            return False
        
        conditions = flow_entry.get("conditions", [])
        return all(condition.is_enabled() for condition in conditions)
    
    def can_navigate_to(self, target_page: str) -> bool:
        """Check if navigation to a specific page is allowed."""
        return self._is_page_enabled(target_page)


class NavigationManager:
    """Manages page navigation and validation."""
    
    def __init__(self, page_manager):
        self.page_manager = page_manager
        self.flow = NavigationFlow()
        self.logger = get_logger(__name__)
        self._current_page: Optional[str] = None
    
    @property
    def current_page(self) -> Optional[str]:
        """Get the current page name."""
        return self._current_page
    
    def navigate_forward(self, current_page: str, 
                        validation_result: bool = True) -> NavigationResult:
        """Navigate to the next page."""
        self.logger.info(f"navigate_forward called: current_page={current_page}, validation_result={validation_result}")
        
        if not validation_result:
            self.logger.warning("Navigation blocked: validation failed")
            return NavigationResult(
                success=False, 
                error_message="Current page validation failed"
            )
        
        next_page = self.flow.get_next_page(current_page)
        self.logger.info(f"Next page determined: {next_page}")
        
        if not next_page:
            self.logger.error(f"No next page available for {current_page}")
            return NavigationResult(
                success=False, 
                error_message="No next page available"
            )
        
        self.logger.info(f"Calling _navigate_to({next_page})")
        return self._navigate_to(next_page)
    
    def navigate_backward(self, current_page: str) -> NavigationResult:
        """Navigate to the previous page."""
        previous_page = self.flow.get_previous_page(current_page)
        if not previous_page:
            return NavigationResult(
                success=False, 
                error_message="No previous page available"
            )
        
        return self._navigate_to(previous_page)
    
    def navigate_to(self, target_page: str) -> NavigationResult:
        """Navigate directly to a specific page."""
        if not self.flow.can_navigate_to(target_page):
            return NavigationResult(
                success=False, 
                error_message=f"Navigation to {target_page} is not allowed"
            )
        
        return self._navigate_to(target_page)
    
    def _navigate_to(self, target_page: str) -> NavigationResult:
        """Internal method to perform navigation."""
        self.logger.info(f"_navigate_to called with target_page: {target_page}")
        print(f"🔧 _navigate_to called with target_page: {target_page}")
        try:
            self.logger.info(f"Calling page_manager.show_page({target_page})")
            print(f"🔧 About to call page_manager.show_page({target_page})")
            self.page_manager.show_page(target_page)
            print(f"🔧 page_manager.show_page({target_page}) completed")
            self._current_page = target_page
            self.logger.info(f"Successfully navigated to page: {target_page}")
            print(f"🔧 Successfully navigated to page: {target_page}")
            return NavigationResult(success=True, target_page=target_page)
        except Exception as e:
            error_msg = f"Failed to navigate to {target_page}: {str(e)}"
            self.logger.error(error_msg)
            print(f"🔧 ERROR: Failed to navigate to {target_page}: {str(e)}")
            import traceback
            self.logger.error(f"Exception traceback: {traceback.format_exc()}")
            print(f"🔧 Exception traceback: {traceback.format_exc()}")
            return NavigationResult(success=False, error_message=error_msg)
    
    def get_navigation_info(self, current_page: str) -> Dict[str, Any]:
        """Get navigation information for a page."""
        return {
            "current": current_page,
            "next": self.flow.get_next_page(current_page),
            "previous": self.flow.get_previous_page(current_page),
            "can_go_forward": self.flow.get_next_page(current_page) is not None,
            "can_go_backward": self.flow.get_previous_page(current_page) is not None,
        }


# Global navigation manager instance
_navigation_manager: Optional[NavigationManager] = None


def get_navigation_manager() -> NavigationManager:
    """Get the global navigation manager instance."""
    global _navigation_manager
    if _navigation_manager is None:
        raise RuntimeError("Navigation manager not initialized. Call set_navigation_manager first.")
    return _navigation_manager


def set_navigation_manager(nav_manager: NavigationManager) -> None:
    """Set the global navigation manager."""
    global _navigation_manager
    _navigation_manager = nav_manager
