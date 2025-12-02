from collections.abc import Callable
from typing import Any

from tkinter_templates import *


class RadioButtonItem:
    """Data class representing a single radio button item configuration."""

    def __init__(
        self, name: str, description: str = "", error: str = "", advanced: bool = False
    ):
        self.name = name
        self.description = description
        self.error = error
        self.advanced = advanced

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RadioButtonItem":
        """Create a RadioButtonItem from a dictionary."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            error=data.get("error", ""),
            advanced=data.get("advanced", False),
        )


class MultiRadioButtons(ctk.CTkFrame):
    """
    A customizable radio button group widget that supports advanced options,
    descriptions, and error states.

    Features:
    - Standard and advanced radio button options
    - Error state handling with disabled buttons
    - Descriptions for each option
    - Collapsible advanced options section
    """

    # UI Constants
    ADVANCED_OPTIONS_TEXT = "Show advanced options"
    AUTO_EXPAND_DELAY_MS = 2000
    GRID_PADDING = 5

    def __init__(
        self,
        parent,
        items: dict[str, dict[str, Any]],
        variable: ctk.Variable,
        validation_callback: Callable | None = None,
        *args,
        **kwargs,
    ):
        """
        Initialize the MultiRadioButtons widget.

        Args:
            parent: Parent widget
            items: Dictionary mapping item keys to their configuration
            variable: CTk variable to bind radio button selection to
            validation_callback: Optional callback function for validation
        """
        super().__init__(
            parent,
            *args,
            bg_color="transparent",
            fg_color="transparent",
            **kwargs,
        )

        # Core properties
        self._variable = variable
        self._validation_callback = validation_callback
        self._items = self._parse_items(items)

        # UI components
        self._radio_buttons: dict[str, ctk.CTkRadioButton] = {}
        self._advanced_frame: ctk.CTkFrame | None = None
        self._show_advanced_label: ctk.CTkSimpleLabel | None = None

        # Initialize the widget
        self._setup_ui()
        self._handle_initial_state()

    def _parse_items(
        self, items: dict[str, dict[str, Any]]
    ) -> dict[str, RadioButtonItem]:
        """Parse raw items dictionary into RadioButtonItem objects."""
        return {key: RadioButtonItem.from_dict(config) for key, config in items.items()}

    def _setup_ui(self) -> None:
        """Set up the complete user interface."""
        self._create_advanced_frame()
        self._create_advanced_toggle_if_needed()
        self._create_radio_buttons()
        self._configure_grid()

    def _create_advanced_frame(self) -> None:
        """Create the frame that will contain advanced options."""
        self._advanced_frame = ctk.CTkContainer(self)

    def _create_advanced_toggle_if_needed(self) -> None:
        """Create the 'Show advanced options' label if any items are marked as advanced."""
        if not self._has_advanced_options():
            return

        self._show_advanced_label = ctk.CTkSimpleLabel(
            self,
            text=self.ADVANCED_OPTIONS_TEXT,
            font=FONTS_smaller,
            text_color=colors.primary,
            cursor="hand2",
        )

        # Position the label after all items
        row_position = len(self._items) + 1
        self._show_advanced_label.grid(
            ipady=self.GRID_PADDING, row=row_position, column=0, sticky="w"
        )

        # Bind click event
        self._show_advanced_label.bind(
            "<Button-1>", lambda _: self._show_advanced_options()
        )

    def _create_radio_buttons(self) -> None:
        """Create all radio buttons with their associated labels."""
        for index, (item_key, item_config) in enumerate(self._items.items()):
            target_frame = self._get_target_frame(item_config)

            # Create and position radio button
            radio_button = self._create_radio_button(
                target_frame, item_config, item_key
            )
            radio_button.grid(
                ipady=self.GRID_PADDING, row=index, column=0, sticky="nwe"
            )
            self._radio_buttons[item_key] = radio_button

            # Create associated label (error or description)
            self._create_associated_label(target_frame, item_config, index)

    def _get_target_frame(self, item_config: RadioButtonItem):
        """Determine which frame should contain this radio button."""
        return self._advanced_frame if item_config.advanced else self

    def _create_radio_button(
        self, parent, item_config: RadioButtonItem, value: str
    ) -> ctk.CTkRadioButton:
        """Create a single radio button."""
        radio_button = ctk.CTkRadioButton(
            parent,
            text=item_config.name,
            variable=self._variable,
            value=value,
        )

        # Add validation callback if provided
        if self._validation_callback:
            radio_button.configure(command=self._validation_callback)

        # Handle error state
        if item_config.error:
            radio_button.configure(state="disabled")
            self._handle_error_state_selection(value)

        return radio_button

    def _create_associated_label(
        self, parent, item_config: RadioButtonItem, row: int
    ) -> None:
        """Create error or description label for the radio button."""
        if item_config.error:
            self._create_error_label(parent, item_config.error, row)
        elif item_config.description:
            self._create_description_label(parent, item_config.description, row)

    def _create_error_label(self, parent, error_text: str, row: int) -> None:
        """Create an error label for a disabled radio button."""
        error_label = ctk.CTkSimpleLabel(
            parent,
            justify="center",
            text=error_text,
            font=FONTS_smaller,
            text_color=colors.red,
        )
        error_label.grid(
            ipadx=self.GRID_PADDING,
            row=row,
            column=1,
            sticky=multilingual.get_di_var().w,
        )

    def _create_description_label(
        self, parent, description_text: str, row: int
    ) -> None:
        """Create a description label for a radio button."""
        description_label = ctk.CTkSimpleLabel(
            parent,
            justify="center",
            text=description_text,
            font=FONTS_tiny,
            text_color=colors.primary,
        )
        description_label.grid(
            ipadx=self.GRID_PADDING,
            row=row,
            column=1,
            sticky=multilingual.get_di_var().w,
        )

    def _configure_grid(self) -> None:
        """Configure grid weights for proper resizing."""
        self.grid_columnconfigure(0, weight=1)
        if self._advanced_frame:
            self._advanced_frame.grid_columnconfigure(0, weight=1)

    def _handle_initial_state(self) -> None:
        """Handle the initial state of the widget, including auto-expanding advanced options."""
        current_value = self._variable.get()
        if current_value in self._items:
            current_item = self._items[current_value]
            if current_item.advanced:
                # Auto-expand advanced options after a delay
                self.after(self.AUTO_EXPAND_DELAY_MS, self._show_advanced_options)

    def _handle_error_state_selection(self, item_key: str) -> None:
        """Clear selection if the currently selected item is in error state."""
        if self._variable.get() == item_key:
            self._variable.set("")

    def _has_advanced_options(self) -> bool:
        """Check if any items are marked as advanced."""
        return any(item.advanced for item in self._items.values())

    def _show_advanced_options(self) -> None:
        """Show the advanced options frame and hide the toggle label."""
        if self._advanced_frame and self._show_advanced_label:
            self._advanced_frame.grid(row=len(self._items), column=0, sticky="w")
            self._show_advanced_label.grid_forget()

    # Public API methods

    def get_selected_value(self) -> str:
        """Get the currently selected radio button value."""
        return self._variable.get()

    def set_selected_value(self, value: str) -> None:
        """Set the selected radio button value."""
        if value in self._items:
            self._variable.set(value)
        else:
            msg = f"Invalid value: {value}. Must be one of: {list(self._items.keys())}"
            raise ValueError(msg)

    def enable_item(self, item_key: str) -> None:
        """Enable a specific radio button."""
        if item_key in self._radio_buttons:
            self._radio_buttons[item_key].configure(state="normal")

    def disable_item(self, item_key: str) -> None:
        """Disable a specific radio button."""
        if item_key in self._radio_buttons:
            self._radio_buttons[item_key].configure(state="disabled")
            if self._variable.get() == item_key:
                self._variable.set("")
