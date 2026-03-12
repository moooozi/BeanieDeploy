from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, NamedTuple

import vgkit as vgk

from core.settings import ConfigManager, get_config
from core.state import get_state

if TYPE_CHECKING:
    from collections.abc import Callable

    from core.navigation_conditions import PageCondition


class PageValidationResult(NamedTuple):
    """Result of page validation."""

    is_valid: bool
    error_message: str | None = None


@dataclass
class ButtonConfig:
    """Configuration for a navigation button."""

    text: str | None = None
    command: Callable | None = None
    visible: bool = True
    state: str = "normal"


@dataclass
class NavigationEntry:
    """Configuration for a page's position in the navigation flow."""

    conditions: list[PageCondition] = field(default_factory=list)
    special: bool = False
    next: Callable[[], type[Page] | None] | None = None
    previous: Callable[[], type[Page] | None] | None = None


class Page(vgk.Frame, ABC):
    """
    Base class for all application pages.

    Pages own their UI configuration (title, button settings).
    The PageManager reads these when showing a page and subscribes
    to changes via a callback for live updates.

    For translations, import and use _() directly from multilingual module.
    """

    @property
    def _ui(self):
        """Get UI configuration."""
        return self.app_config.ui

    @property
    def page_name(self) -> str:
        """Page name derived from class name."""
        return type(self).__name__

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.initiated: bool = False
        self.destroy_on_next: bool = False

        # Page-owned UI config — PageManager reads these when (re-)showing
        self.page_title: str | None = None
        self.primary_button_config: ButtonConfig | None = None
        self.secondary_button_config: ButtonConfig | None = None

        # Config-change callback — set by PageManager for live updates
        self.config_changed_callback: Callable[[], None] | None = None

        # Shared singletons
        self.app_config: ConfigManager = get_config()
        self.state = get_state()

        # Set by PageManager.add_page — used only for navigation
        self.page_manager: Any = None

    # ── Config setters (auto-notify PageManager on live updates) ──────

    def set_page_title(self, text: str):
        """Set this page's title. Applied immediately if the page is visible."""
        self.page_title = text
        self._notify_config_change()

    def set_primary_button_config(
        self,
        text: str | None = None,
        command: Callable | None = None,
        visible: bool = True,
        state: str = "normal",
    ):
        """Set this page's primary button configuration."""
        self.primary_button_config = ButtonConfig(text, command, visible, state)
        self._notify_config_change()

    def set_secondary_button_config(
        self,
        text: str | None = None,
        command: Callable | None = None,
        visible: bool = True,
    ):
        """Set this page's secondary button configuration."""
        self.secondary_button_config = ButtonConfig(text, command, visible)
        self._notify_config_change()

    def _notify_config_change(self):
        """Fire the config-change callback if the page is already initialized.

        During init_page(), setters store config without triggering UI updates.
        After init completes, subsequent calls apply changes live.
        """
        if self.initiated and self.config_changed_callback:
            self.config_changed_callback()

    # ── Lifecycle hooks (override in subclasses) ──────────────────────

    @abstractmethod
    def init_page(self):
        """Initialize the page layout and widgets."""

    def on_show(self):
        """Called when the page is shown."""

    def on_hide(self):
        """Called when the page is hidden."""

    def on_next(self):
        """Called when user clicks next and validation passes."""

    def on_previous(self):
        """Called when user clicks previous."""

    # ── Validation ────────────────────────────────────────────────────

    def validate_input(self) -> PageValidationResult:
        """Validate the current page input. Override for page-specific validation."""
        return PageValidationResult(True)

    def show_validation_error(self, message: str):
        """Show a validation error to the user."""
        logging.warning(f"Validation error on {self.page_name}: {message}")

    # ── Navigation ────────────────────────────────────────────────────

    def next_action(self) -> bool:
        """Run validation then on_next. Returns True if navigation should proceed."""
        result = self.validate_input()
        if not result.is_valid:
            if result.error_message:
                self.show_validation_error(result.error_message)
            return False
        self.on_next()
        return True

    def previous_action(self) -> bool:
        """Run on_previous. Returns True if navigation should proceed."""
        self.on_previous()
        return True

    def navigate_next(self):
        """Navigate to the next page (validates first)."""
        if self.page_manager and self.next_action():
            self.page_manager.navigate_forward(type(self))

    def navigate_previous(self):
        """Navigate to the previous page."""
        if self.page_manager and self.previous_action():
            self.page_manager.navigate_backward(type(self))

    def reinitialize(self):
        """Reinitialize the page."""
        for widget in self.winfo_children():
            widget.destroy()
        self.initiated = False
        self.init_page()
        self.initiated = True


# Type alias — defined after Page to avoid forward-reference issues
NavigationFlow = dict[type[Page], NavigationEntry]
