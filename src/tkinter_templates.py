import customtkinter as ctk
import ctypes
from config.settings import get_config
import multilingual
from typing import Any, Optional, Callable, List

WIDTH = 850
HEIGHT = 580
MINWIDTH = WIDTH - 50
MINHEIGHT = HEIGHT - 50
MAXWIDTH = WIDTH + 600
MAXHEIGHT = HEIGHT + 200
WIDTH_OFFSET = 400
HEIGHT_OFFSET = 400
TOP_FRAME_HEIGHT = 80
LEFT_FRAME_WIDTH = 0
DARK_MODE = True


def get_dpi_scaling_factor():
    return ctypes.windll.user32.GetDpiForSystem() / 96


dpi_scaling_factor = 1.35
# print("DPI scaling factor: ", dpi_scaling_factor)
FONTS_large = ("Ariel", int(24 * dpi_scaling_factor))
FONTS_medium = ("Ariel Bold", int(16 * dpi_scaling_factor))
FONTS_small = ("Ariel", int(13 * dpi_scaling_factor))
FONTS_smaller = ("Ariel", int(12 * dpi_scaling_factor))
FONTS_tiny = ("Ariel", int(11 * dpi_scaling_factor))

# Initialize color variables with default values
tkinter_background_color = "#856ff8"
color_red = "#e81123"
color_blue = "#0067b8"
color_green = "#008009"
top_background_color = "#e6e6e6"


def dark_decorations(ye_or_nah: bool, tkinter: ctk.CTk) -> None:
    # force Windows black borders for Windows 11
    tkinter.update()
    set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
    get_parent = ctypes.windll.user32.GetParent
    hwnd = get_parent(tkinter.winfo_id())
    rendering_policy = 20 if ye_or_nah else 0
    value = 2
    value = ctypes.c_int(value)
    set_window_attribute(
        hwnd, rendering_policy, ctypes.byref(value), ctypes.sizeof(value)
    )


def dark_theme(ye_or_nah: bool, tkinter: ctk.CTk) -> None:
    global tkinter_background_color, color_red, color_blue, color_green, top_background_color
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
            **kwargs
        )


class TextLabel(ctk.CTkLabel):
    """Custom text label with predefined styling and smart configuration."""

    def __init__(
        self,
        parent: Any,
        text: Optional[str] = None,
        font: Any = FONTS_small,
        var: Optional[Any] = None,
        foreground: Optional[str] = None,
        **kwargs: Any
    ) -> None:

        # Validate that either text or var is provided, but not both
        if not ((text is None) ^ (var is None)):
            raise ValueError("Either 'text' or 'var' must be provided, but not both")

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
            **kwargs
        )


class LanguageComboBox(ctk.CTkComboBox):
    """Custom language selection combobox with predefined styling."""

    def __init__(
        self, parent: Any, variable: Any, languages: List[str], **kwargs: Any
    ) -> None:
        super().__init__(
            parent,
            name="language",
            textvariable=variable,
            fg_color=top_background_color,
            **kwargs
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
