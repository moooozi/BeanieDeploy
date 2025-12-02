import tkinter as tk
from collections.abc import Callable
from typing import Any

import customtkinter as ctk

import multilingual
from config.settings import get_config

# Get UI config
_ui_config = get_config().ui

WIDTH = _ui_config.width
HEIGHT = _ui_config.height
MINWIDTH = _ui_config.min_width
MINHEIGHT = _ui_config.min_height
MAXWIDTH = _ui_config.max_width
MAXHEIGHT = _ui_config.max_height
TOP_FRAME_HEIGHT = _ui_config.top_frame_height
LEFT_FRAME_WIDTH = _ui_config.left_frame_width
colors = _ui_config.colors


FONTS_large = _ui_config.font_large
FONTS_medium = _ui_config.font_medium
FONTS_small = _ui_config.font_small
FONTS_smaller = _ui_config.font_smaller
FONTS_tiny = _ui_config.font_tiny


class FrameContainer(ctk.CTkContainer):
    """Custom transparent frame container with predefined styling."""

    def __init__(self, parent: Any, **kwargs: Any) -> None:
        super().__init__(
            parent,
            width=MINWIDTH,
            **kwargs,
        )


class TextLabel(ctk.CTkSimpleLabel):
    """Custom text label with predefined styling and smart configuration."""

    def __init__(
        self,
        parent: Any,
        text: str | None = None,
        font: Any = FONTS_small,
        var: Any | None = None,
        **kwargs: Any,
    ) -> None:
        # Validate that either text or var is provided, but not both
        if not ((text is None) ^ (var is None)):
            msg = "Either 'text' or 'var' must be provided, but not both"
            raise ValueError(msg)

        config = get_config()

        # Set default values for text and textvariable to avoid None issues
        text_value = text if text is not None else ""
        var_value = var if var is not None else None

        super().__init__(
            parent,
            wraplength=config.ui.max_width,
            justify=multilingual.get_di_var().l,
            text=text_value,
            textvariable=var_value,
            font=font,
            bg_color="transparent",
            pady=5,
            **kwargs,
        )


class LanguageComboBox(ctk.CTkComboBox):
    """Custom language selection combobox with predefined styling."""

    def __init__(
        self, parent: Any, variable: Any, languages: list[str], **kwargs: Any
    ) -> None:
        super().__init__(
            parent,
            name="language",
            textvariable=variable,
            **kwargs,
        )

        self.configure(values=tuple(languages))
        self.configure(state="readonly")
        self.set("English")


def flush_frame(frame: tk.Widget) -> None:
    """removes all elements inside the middle frame, which contains all page-specific content"""
    for widget in frame.winfo_children():
        widget.destroy()


def var_tracer(var: Any, mode: str, cb: Callable[..., Any]) -> None:
    """
    add CustomTkinter variable tracer if no tracer exists
    :param var: CustomTkinter variable
    :param mode: CustomTkinter tracer mode (see trace_add docs)
    :param cb: the callback function
    """
    tracers_list = var.trace_info()
    for tracer in tracers_list:
        var.trace_remove(*tracer)
    var.trace_add(mode=mode, callback=cb)
