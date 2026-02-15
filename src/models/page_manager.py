import logging
from typing import Any, TypeVar

import vgkit as vgk

from core.settings import get_config
from models.page import Page

# Type variable for page types
TPage = TypeVar("TPage", bound=Page)


class PageManager:
    def __init__(self, container):
        self.container = container
        self.pages: dict[type[Page], Page] = {}
        self.current_page: Page | None = None

        # Navigation flow will be configured externally
        self._navigation_flow: dict[type[Page], Any] = {}

        # Store page-specific titles
        self.page_titles: dict[type[Page], str] = {}

        # Store page-specific button settings
        self.page_primary_buttons: dict[type[Page], dict[str, Any]] = {}
        self.page_secondary_buttons: dict[type[Page], dict[str, Any]] = {}

        # Create shared UI elements
        self.ui_config = get_config().ui
        self.title_label = vgk.Label(
            self.container, text="", font=self.ui_config.fonts.medium, wraplength="self"
        )
        self.title_label.grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(self.ui_config.margin_title_top, 0),
        )

        self.primary_button = vgk.Button(
            self.container, text="", command=self._default_next, mode="round"
        )
        self.primary_button.grid(
            row=2,
            column=2,
            ipadx=15,
            padx=(0, self.ui_config.margin_side),
            pady=(0, self.ui_config.margin_bottom),
        )

        self.secondary_button = vgk.Button(
            self.container,
            text="",
            command=self._default_previous,
            style="secondary",
            mode="round",
        )
        self.secondary_button.grid(
            row=2, column=1, padx=12, pady=(0, self.ui_config.margin_bottom)
        )
        self.secondary_button.grid_remove()  # Hide by default

        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(1, weight=1)

    def _default_next(self):
        """Default next action: navigate to next page with validation."""
        if self.current_page:
            self.current_page.navigate_next()

    def _default_previous(self):
        """Default previous action: navigate to previous page."""
        if self.current_page:
            self.current_page.navigate_previous()

    def set_title(self, text: str):
        """Set the title text."""
        self.title_label.configure(text=text)
        if self.current_page:
            self.page_titles[type(self.current_page)] = text

    def set_primary_button(
        self,
        text: str | None = None,
        command=None,
        visible: bool = True,
        state: str = "normal",
    ):
        """Set primary button properties."""
        if text is not None:
            self.primary_button.configure(text=text)
        if command is not None:
            self.primary_button.configure(command=command)
        self.primary_button.configure(state=state)
        if visible:
            self.primary_button.grid()
        else:
            self.primary_button.grid_remove()
        if self.current_page:
            self.page_primary_buttons[type(self.current_page)] = {
                "text": text,
                "command": command,
                "visible": visible,
                "state": state,
            }

    def set_secondary_button(
        self, text: str | None = None, command=None, visible: bool = True
    ):
        """Set secondary button properties."""
        if text is not None:
            self.secondary_button.configure(text=text)
        if command is not None:
            self.secondary_button.configure(command=command)
        if visible:
            self.secondary_button.grid()
        else:
            self.secondary_button.grid_remove()
        if self.current_page:
            self.page_secondary_buttons[type(self.current_page)] = {
                "text": text,
                "command": command,
                "visible": visible,
            }

    def configure_navigation_flow(self, navigation_flow: dict[type[Page], Any]):
        """Configure the navigation flow from external source."""
        self._navigation_flow = navigation_flow
        logging.debug("Navigation flow configured externally")

    def get_next_page(self, current_page_class: type[Page]) -> type[Page] | None:
        """Get the next page in the flow, automatically skipping disabled pages."""
        if not self._navigation_flow:
            logging.warning("Navigation flow not configured")
            return None

        # Get the ordered list of pages from the dictionary keys
        page_order = list(self._navigation_flow.keys())

        # Check for custom next navigation first
        page_config = self._navigation_flow.get(current_page_class, {})
        if "next" in page_config:
            custom_next = page_config["next"]
            if callable(custom_next):
                next_page = custom_next()
                if next_page and isinstance(next_page, type):
                    return self._find_next_enabled_page_from(next_page, page_order)
            return None

        # Find current page in the order
        try:
            current_index = page_order.index(current_page_class)
        except ValueError:
            logging.warning(
                f"Page {current_page_class.__name__} not found in page order"
            )
            return None

        # Find next enabled page
        for i in range(current_index + 1, len(page_order)):
            candidate_page = page_order[i]
            if self._is_page_enabled(candidate_page):
                return candidate_page
            logging.info(f"Skipping page {candidate_page.__name__} due to condition")

        return None

    def get_previous_page(self, current_page_class: type[Page]) -> type[Page] | None:
        """Get the previous page in the flow, automatically skipping disabled pages."""
        if not self._navigation_flow:
            logging.warning("Navigation flow not configured")
            return None

        # Get the ordered list of pages from the dictionary keys
        page_order = list(self._navigation_flow.keys())
        logging.debug(f"get_previous_page called from {current_page_class.__name__}")

        # Check for custom previous navigation first
        page_config = self._navigation_flow.get(current_page_class, {})
        if "previous" in page_config:
            custom_prev = page_config["previous"]
            if callable(custom_prev):
                prev_page = custom_prev()
                if prev_page and isinstance(prev_page, type):
                    logging.debug(f"Using custom previous: {prev_page.__name__}")
                    return self._find_previous_enabled_page_from(prev_page, page_order)
            return None

        # Find current page in the order
        try:
            current_index = page_order.index(current_page_class)
        except ValueError:
            logging.warning(
                f"Page {current_page_class.__name__} not found in page order"
            )
            return None

        logging.debug(f"Current page index: {current_index}")

        # Find previous enabled page
        for i in range(current_index - 1, -1, -1):
            candidate_page = page_order[i]
            logging.debug(f"Checking previous candidate: {candidate_page.__name__}")
            if self._is_page_enabled(candidate_page):
                logging.info(f"Found previous enabled page: {candidate_page.__name__}")
                return candidate_page
            logging.info(f"Skipping page {candidate_page.__name__} due to condition")

        logging.debug("No previous page found")
        return None

    def _is_page_enabled(self, page_class: type[Page]) -> bool:
        """Check if a page is enabled based on its conditions."""
        page_config = self._navigation_flow.get(page_class, {})

        # Skip special pages in normal flow
        if page_config.get("special", False):
            logging.debug(f"Page {page_class.__name__} is marked as special, skipping")
            return False

        # Check all conditions
        conditions = page_config.get("conditions", [])
        for condition in conditions:
            if not condition.is_enabled():
                logging.info(
                    f"Page {page_class.__name__} disabled by condition {condition.__class__.__name__}"
                )
                return False

        logging.debug(f"Page {page_class.__name__} is enabled")
        return True  # Enabled if no conditions or all conditions pass

    def _find_next_enabled_page_from(
        self, start_page: type[Page], page_order: list
    ) -> type[Page] | None:
        """Find the next enabled page starting from a given page."""
        try:
            start_index = page_order.index(start_page)
        except ValueError:
            return start_page if self._is_page_enabled(start_page) else None

        # Check if the start page itself is enabled
        if self._is_page_enabled(start_page):
            return start_page

        # Find next enabled page after start_page
        for i in range(start_index + 1, len(page_order)):
            candidate_page = page_order[i]
            if self._is_page_enabled(candidate_page):
                return candidate_page
            logging.info(f"Skipping page {candidate_page.__name__} due to condition")

        return None

    def _find_previous_enabled_page_from(
        self, start_page: type[Page], page_order: list
    ) -> type[Page] | None:
        """Find the previous enabled page starting from a given page."""
        try:
            start_index = page_order.index(start_page)
        except ValueError:
            return start_page if self._is_page_enabled(start_page) else None

        # Check if the start page itself is enabled
        if self._is_page_enabled(start_page):
            return start_page

        # Find previous enabled page before start_page
        for i in range(start_index - 1, -1, -1):
            candidate_page = page_order[i]
            if self._is_page_enabled(candidate_page):
                return candidate_page
            logging.info(f"Skipping page {candidate_page.__name__} due to condition")

        return None

    def navigate_forward(self, current_page_class: type[Page]) -> bool:
        """Navigate to the next page."""
        next_page = self.get_next_page(current_page_class)
        if next_page:
            self.show_page(next_page)
            return True
        return False

    def navigate_backward(self, current_page_class: type[Page]) -> bool:
        """Navigate to the previous page."""
        previous_page = self.get_previous_page(current_page_class)
        if previous_page:
            self.show_page(previous_page)
            return True
        return False

    def add_page(self, page_class: type[Page], *args, **kwargs):
        """Add a page to the manager."""
        page_name = page_class.__name__
        page = page_class(
            self.container,
            page_name,
            *args,
            **kwargs,
        )

        # Set up navigation for the page
        page.set_page_manager(self)

        self.pages[page_class] = page
        page.grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="nsew",
            padx=self.ui_config.margin_side,
            pady=(
                self.ui_config.margin_title_bottom,
                self.ui_config.margin_button_bar,
            ),
        )

    def show_page(self, page_class: type[Page]):
        """Show a specific page."""

        page_name = page_class.__name__

        if page_class not in self.pages:
            error_msg = f"Page '{page_name}' not found"
            raise ValueError(error_msg)

        page = self.pages[page_class]

        # Hide current page
        if self.current_page:
            self.current_page.on_hide()

        self.current_page = page

        # Set default button states
        from multilingual import _

        # Set page-specific title if stored
        if page_class in self.page_titles:
            self.title_label.configure(text=self.page_titles[page_class])

        # Apply page-specific button settings if stored
        if page_class in self.page_primary_buttons:
            settings = self.page_primary_buttons[page_class]
            self.set_primary_button(**settings)
        else:
            self.set_primary_button(_("btn.next"))

        if page_class in self.page_secondary_buttons:
            settings = self.page_secondary_buttons[page_class]
            self.set_secondary_button(**settings)
        else:
            has_previous = self.get_previous_page(page_class) is not None
            self.set_secondary_button(_("btn.back"), visible=has_previous)

        # Initialize page if needed
        if not page._initiated:  # noqa: SLF001
            logging.debug(f"Initializing page: {page_name}")
            page.init_page()
            page._initiated = True  # noqa: SLF001

        # Show new page
        page.tkraise()
        page.on_show()

        logging.info(f"Showing page: {page_name}")

    def get_current_page(self) -> Page | None:
        """Get the currently active page."""
        return self.current_page

    def get_current_page_name(self) -> str | None:
        """Get the name of the currently active page."""
        return self.current_page.page_name if self.current_page else None

    def get_current_page_class(self) -> type[Page] | None:
        """Get the class type of the currently active page."""
        return type(self.current_page) if self.current_page else None

    def reset_page(self, page_class: type[Page]):
        """Reset a page to uninitialized state."""
        if page_class in self.pages:
            self.pages[page_class]._initiated = False  # noqa: SLF001
            logging.debug(f"Reset page: {page_class.__name__}")

    def get_navigation_info(self) -> dict | None:
        """Get navigation information for the current page."""
        if self.current_page:
            current_page_class = type(self.current_page)
            next_page = self.get_next_page(current_page_class)
            previous_page = self.get_previous_page(current_page_class)

            return {
                "current": current_page_class.__name__,
                "next": next_page.__name__ if next_page else None,
                "previous": previous_page.__name__ if previous_page else None,
                "can_go_forward": next_page is not None,
                "can_go_backward": previous_page is not None,
            }
        return None

    def get_page(self, page_class: type[TPage]) -> TPage | None:
        """
        Get a page instance by its class type.
        This is a type-safe alternative to dictionary access.

        Args:
            page_class: The class type of the page to retrieve

        Returns:
            The page instance if found, None otherwise
        """
        for page in self.pages.values():
            if isinstance(page, page_class):
                return page
        return None

    def get_page_by_name(self, page_class: type[TPage]) -> TPage | None:
        """
        Get a page instance by class type with type safety.

        Args:
            page_class: The expected class type for validation

        Returns:
            The page instance if found and of correct type, None otherwise
        """
        page = self.pages.get(page_class)
        if page and isinstance(page, page_class):
            return page
        return None

    def configure_page(self, page_class: type[TPage], configure_func) -> bool:
        """
        Type-safe method to configure a page.

        Args:
            page_class: The class type of the page to configure
            configure_func: Function to call with the page instance

        Returns:
            True if page was found and configured, False otherwise
        """
        page = self.get_page(page_class)
        if page:
            configure_func(page)
            return True
        return False

    def get_navigation_flow(self) -> dict[type[Page], Any]:
        """
        Get the configured navigation flow.

        Returns:
            Dictionary mapping page classes to their navigation configuration
        """
        return self._navigation_flow or {}

    def start(self):
        """
        Show the first enabled page in the navigation flow.
        """
        if not self._navigation_flow:
            logging.warning("Navigation flow not configured")
            return

        page_order = list(self._navigation_flow.keys())
        for page_class in page_order:
            if self._is_page_enabled(page_class):
                self.show_page(page_class)
                logging.info(f"Started navigation with page: {page_class.__name__}")
                return
        logging.warning("No enabled page found to start navigation")
