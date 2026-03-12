import logging

import vgkit as vgk

from core.settings import get_config
from models.page import ButtonConfig, NavigationEntry, Page


class PageManager:
    def __init__(self, container):
        self.container = container
        self.pages: dict[type[Page], Page] = {}
        self.current_page: Page | None = None
        self._navigation_flow: dict[type[Page], NavigationEntry] = {}

        # Shared UI widgets
        ui = get_config().ui
        self._ui = ui

        self._title_label = vgk.Label(
            container, text="", font=ui.fonts.medium, wraplength="self"
        )
        self._title_label.grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(ui.margin_title_top, 0),
        )

        self._primary_button = vgk.Button(
            container, text="", command=self._default_next, mode="round"
        )
        self._primary_button.grid(
            row=2,
            column=2,
            ipadx=15,
            padx=(0, ui.margin_side),
            pady=(0, ui.margin_bottom),
        )

        self._secondary_button = vgk.Button(
            container,
            text="",
            command=self._default_previous,
            style="secondary",
            mode="round",
        )
        self._secondary_button.grid(
            row=2,
            column=1,
            padx=12,
            pady=(0, ui.margin_bottom),
        )
        self._secondary_button.grid_remove()

        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

    # ── Default button handlers ───────────────────────────────────────

    def _default_next(self):
        if self.current_page:
            self.current_page.navigate_next()

    def _default_previous(self):
        if self.current_page:
            self.current_page.navigate_previous()

    # ── Navigation flow ───────────────────────────────────────────────

    def configure_navigation_flow(self, flow: dict[type[Page], NavigationEntry]):
        """Set the navigation flow (ordered mapping of page classes to config)."""
        self._navigation_flow = flow

    def get_next_page(self, current: type[Page]) -> type[Page] | None:
        """Get the next enabled page from *current*."""
        return self._get_neighbor(current, direction=1)

    def get_previous_page(self, current: type[Page]) -> type[Page] | None:
        """Get the previous enabled page from *current*."""
        return self._get_neighbor(current, direction=-1)

    def _get_neighbor(self, current: type[Page], direction: int) -> type[Page] | None:
        """Find the next (direction=1) or previous (direction=-1) enabled page."""
        if not self._navigation_flow:
            return None

        page_order = list(self._navigation_flow.keys())
        entry = self._navigation_flow.get(current)

        # Custom navigation override
        if entry:
            custom = entry.next if direction > 0 else entry.previous
            if custom:
                target = custom()
                if target and isinstance(target, type):
                    return self._find_enabled_page(target, page_order, direction)
                return None

        # Linear search from current position
        try:
            idx = page_order.index(current)
        except ValueError:
            return None

        end = len(page_order) if direction > 0 else -1
        for i in range(idx + direction, end, direction):
            if self._is_page_enabled(page_order[i]):
                return page_order[i]
        return None

    def _find_enabled_page(
        self,
        start: type[Page],
        page_order: list[type[Page]],
        direction: int,
    ) -> type[Page] | None:
        """Starting at *start*, find the first enabled page in *direction*."""
        try:
            start_idx = page_order.index(start)
        except ValueError:
            return start if self._is_page_enabled(start) else None

        if self._is_page_enabled(start):
            return start

        end = len(page_order) if direction > 0 else -1
        for i in range(start_idx + direction, end, direction):
            if self._is_page_enabled(page_order[i]):
                return page_order[i]
        return None

    def _is_page_enabled(self, page_class: type[Page]) -> bool:
        """Check if a page is enabled (not special, all conditions met)."""
        entry = self._navigation_flow.get(page_class, NavigationEntry())
        if entry.special:
            return False
        return all(c.is_enabled() for c in entry.conditions)

    # ── Navigation actions ────────────────────────────────────────────

    def navigate_forward(self, current_class: type[Page]) -> bool:
        """Navigate to the next page, destroying current if flagged."""
        next_page = self.get_next_page(current_class)
        if not next_page:
            return False

        current = self.pages.get(current_class)
        should_destroy = current is not None and current.destroy_on_next
        self.show_page(next_page)
        if should_destroy:
            self._destroy_page(current_class)
        return True

    def navigate_backward(self, current_class: type[Page]) -> bool:
        """Navigate to the previous page."""
        prev_page = self.get_previous_page(current_class)
        if not prev_page:
            return False
        self.show_page(prev_page)
        return True

    def _destroy_page(self, page_class: type[Page]):
        """Remove and destroy a page widget."""
        page = self.pages.pop(page_class, None)
        if page:
            page.destroy()
        logging.debug(f"Destroyed page: {page_class.__name__}")

    # ── Page management ───────────────────────────────────────────────

    def add_page(self, page_class: type[Page], *args, **kwargs):
        """Instantiate a page, wire it up, and add it to the container."""
        page = page_class(self.container, *args, **kwargs)

        # Wire navigation and config-change callback
        page.page_manager = self  # noqa: page_manager is declared as Any in Page
        page.config_changed_callback = self._apply_current_page_config

        self.pages[page_class] = page
        page.grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="nsew",
            padx=self._ui.margin_side,
            pady=(self._ui.margin_title_bottom, self._ui.margin_button_bar),
        )

    def show_page(self, page_class: type[Page]):
        """Show a specific page (initializes on first visit)."""
        if page_class not in self.pages:
            msg = f"Page '{page_class.__name__}' not found"
            raise ValueError(msg)

        page = self.pages[page_class]

        if self.current_page:
            self.current_page.on_hide()

        self.current_page = page

        # First-time initialization
        if not page.initiated:
            page.init_page()
            page.initiated = True

        # Raise and notify
        page.tkraise()
        page.on_show()

        # Apply page config AFTER init_page + on_show have set their values
        self._apply_current_page_config()
        logging.info(f"Showing page: {page_class.__name__}")

    def start(self):
        """Show the first enabled page in the navigation flow."""
        for page_class in self._navigation_flow:
            if self._is_page_enabled(page_class):
                self.show_page(page_class)
                return
        logging.warning("No enabled page found to start navigation")

    # ── Config application (reads page-owned attrs) ───────────────────

    def _apply_current_page_config(self):
        """Read the current page's config attrs and apply them to shared widgets."""
        page = self.current_page
        if not page:
            return

        from multilingual import _

        # Title
        if page.page_title is not None:
            self._title_label.configure(text=page.page_title)

        # Primary button
        primary = page.primary_button_config or ButtonConfig(text=_("btn.next"))
        self._apply_button(self._primary_button, primary, self._default_next)

        # Secondary button
        if page.secondary_button_config is not None:
            self._apply_button(
                self._secondary_button,
                page.secondary_button_config,
                self._default_previous,
            )
        else:
            has_prev = self.get_previous_page(type(page)) is not None
            self._apply_button(
                self._secondary_button,
                ButtonConfig(text=_("btn.back"), visible=has_prev),
                self._default_previous,
            )

    @staticmethod
    def _apply_button(widget, config: ButtonConfig, default_command):
        """Apply a ButtonConfig to a widget."""
        if config.text is not None:
            widget.configure(text=config.text)
        widget.configure(command=config.command or default_command)
        widget.configure(state=config.state)
        if config.visible:
            widget.grid()
        else:
            widget.grid_remove()
