import ctypes
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
WIDTH_OFFSET = _ui_config.width_offset
HEIGHT_OFFSET = _ui_config.height_offset
TOP_FRAME_HEIGHT = _ui_config.top_frame_height
LEFT_FRAME_WIDTH = _ui_config.left_frame_width
DARK_MODE = True


def get_dpi_scaling_factor():
    return ctypes.windll.user32.GetDpiForSystem() / 96


dpi_scaling_factor = _ui_config.dpi_scaling_factor
# print("DPI scaling factor: ", dpi_scaling_factor)
FONTS_large = _ui_config.font_large
FONTS_medium = _ui_config.font_medium
FONTS_small = _ui_config.font_small
FONTS_smaller = _ui_config.font_smaller
FONTS_tiny = _ui_config.font_tiny

# Initialize color variables with default values
tkinter_background_color = _ui_config.color_background
color_red = _ui_config.color_red
color_blue = _ui_config.color_blue
color_green = _ui_config.color_green
top_background_color = "#e6e6e6"


def dark_decorations(ye_or_nah: bool, tkinter: ctk.CTk) -> None:
    # force Windows black borders for Windows 11
    tkinter.update()
    set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
    get_parent = ctypes.windll.user32.GetParent
    hwnd = get_parent(tkinter.winfo_id())
    rendering_policy = 20 if ye_or_nah else 0
    value = ctypes.c_int(2)
    set_window_attribute(
        hwnd, rendering_policy, ctypes.byref(value), ctypes.sizeof(value)
    )


def dark_theme(ye_or_nah: bool, tkinter: ctk.CTk) -> None:
    global \
        tkinter_background_color, \
        color_red, \
        color_blue, \
        color_green, \
        top_background_color
    if not ye_or_nah:
        tkinter_background_color = "#856ff8"
        color_red = "#e81123"
        color_blue = "#0067b8"
        color_green = "#008009"
        top_background_color = "#e6e6e6"
    else:
        tkinter_background_color = "#856ff8"
        color_red = "#ff4a4a"
        color_blue = "#3aa9ff"
        color_green = "#5dd25e"
        top_background_color = "#6b6b6b"
    dark_decorations(ye_or_nah, tkinter)
    tkinter.update()


class FrameContainer(ctk.CTkFrame):
    """Custom transparent frame container with predefined styling."""

    def __init__(self, parent: Any, **kwargs: Any) -> None:
        super().__init__(
            parent,
            width=MINWIDTH,
            bg_color="transparent",
            fg_color="transparent",
            corner_radius=0,
            border_width=0,
            **kwargs,
        )


class TextLabel(ctk.CTkLabel):
    """Custom text label with predefined styling and smart configuration."""

    def __init__(
        self,
        parent: Any,
        text: str | None = None,
        font: Any = FONTS_small,
        var: Any | None = None,
        foreground: str | None = None,
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
            text_color=foreground,
            font=font,
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
            fg_color=top_background_color,
            **kwargs,
        )

        self.configure(values=tuple(languages))
        self.configure(state="readonly")
        self.set("English")


def flush_frame(frame: ctk.CTkFrame) -> None:
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
