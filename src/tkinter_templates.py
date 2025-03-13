import multiprocessing
import queue
from tkinter import ttk
import customtkinter as ctk
import ctypes
from gui_functions import detect_darkmode_in_windows
import globals as GV
import multilingual

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
DARK_MODE = detect_darkmode_in_windows()


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


def dark_decorations(ye_or_nah, tkinter):
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


def dark_theme(ye_or_nah, tkinter):
    global tkinter_background_color, color_red, color_blue, color_green, top_background_color
    if not ye_or_nah:
        color_mode = "light"
        tkinter_background_color = "#856ff8"
        color_red = "#e81123"
        color_blue = "#0067b8"
        color_green = "#008009"
        top_background_color = "#e6e6e6"
    else:
        color_mode = "dark"
        tkinter_background_color = "#856ff8"
        color_red = "#ff4a4a"
        color_blue = "#3aa9ff"
        color_green = "#5dd25e"
        top_background_color = "#6b6b6b"
    dark_decorations(ye_or_nah, tkinter)
    tkinter.update()


def add_frame_container(parent, **kwargs):
    frame = ctk.CTkFrame(
        parent,
        width=MINWIDTH,
        bg_color="transparent",
        fg_color="transparent",
        corner_radius=0,
        border_width=0,
    )
    frame.pack(**kwargs)
    return frame


def open_popup(
    parent,
    x_size: int = None,
    y_size: int = None,
):
    """
    Pops up window to get input from user and freezes the main GUI while waiting for response
    :param y_size: window height in pixels
    :param x_size: window width in pixels
    :param parent: the parent for the CustomTkinter Toplevel
    :return:
    """
    pop = ctk.CTkToplevel(parent)
    border_frame = ctk.CTkFrame(pop, fg_color="gray", corner_radius=1)
    x_position = parent.winfo_x()
    y_position = parent.winfo_y()
    x_app_size = parent.winfo_width()
    y_app_size = parent.winfo_height()
    #  position the pop-up window at the center of its parent
    geometry = "%dx%d+%d+%d" % (
        x_size,
        y_size,
        x_position + (x_app_size - x_size) / 2 + 20,
        y_position + (y_app_size - y_size) / 2 + 20,
    )
    pop.geometry(geometry)
    dark_theme(DARK_MODE, pop)
    # pop.protocol("WM_DELETE_WINDOW", False)
    pop.focus_set()
    pop.grab_set()
    border_frame.pack(expand=1, fill="both", pady=5, padx=5)
    pop_frame = ctk.CTkFrame(border_frame)
    pop_frame.pack(expand=1, fill="both", padx=10, pady=(20, 10))

    return pop, pop_frame


def input_pop_up(
    parent,
    title_txt=None,
    msg_txt=None,
    primary_btn_str=None,
    secondary_btn_str=None,
):
    x_size = 600
    y_size = int(len(msg_txt) / 2.8 + 180 + 13 * msg_txt.count("\n"))
    pop, pop_frame = open_popup(parent, x_size, y_size)
    pop_var = ctk.IntVar(pop)
    msg_font = FONTS_smaller
    layout_frame = generic_page_layout(
        pop_frame,
        title_txt,
        primary_btn_str,
        lambda *args: validate_pop_input(1),
        secondary_btn_str,
        lambda *args: validate_pop_input(0),
        title_pady=5,
    )
    if msg_txt:
        add_text_label(layout_frame, msg_txt, msg_font, pady=10)

    def validate_pop_input(inputted):
        pop_var.set(inputted)
        pop.destroy()

    pop.wait_window()
    return pop_var.get()


def add_check_btn(
    parent, text, var, command=None, is_disabled=None, pady=5, pack=True, switch=False
):
    check = ctk.CTkCheckBox(
        parent, text=text, variable=var, onvalue=True, offvalue=False, width=99
    )
    if switch:
        check.configure(style="Switch.TCheckbutton")
    if pack:
        check.pack(ipady=5, pady=pady)
    if command:
        check.configure(command=command)
    if is_disabled:
        check.configure(state="disabled")
    return check


def add_text_label(
    parent,
    text=None,
    font=FONTS_small,
    var=None,
    pady=20,
    padx=0,
    foreground=None,
    anchor=None,
    pack=True,
):
    """
    a preset for CustomTkinter text label that packs by default
    :return: the CustomTkinter label "ctk.CTkLabel" object
    """
    if (not var and text) or (var and not text):
        label = ctk.CTkLabel(
            parent,
            wraplength=GV.MAX_WIDTH,
            justify=multilingual.get_di_var().l,
            text=text,
            textvariable=var,
            text_color=foreground,
            font=font,
        )
    else:
        return -1
    if pack:
        label.pack(pady=pady, padx=padx, anchor=anchor)
    return label


def add_lang_list(parent, var, languages):
    lang_list = ctk.CTkComboBox(
        parent, name="language", textvariable=var, fg_color=top_background_color
    )
    lang_list["values"] = tuple(languages)
    lang_list["state"] = "readonly"
    lang_list.set("English")
    lang_list.pack(side="left", padx=30)
    return lang_list


def add_progress_bar(
    parent,
):
    progressbar = ctk.CTkProgressBar(
        parent,
        orientation="horizontal",
        mode="determinate",
    )
    progressbar.pack(pady=(0, 20), fill="both")
    return progressbar


def flush_frame(frame):
    """removes all elements inside the middle frame, which contains all page-specific content"""
    GV.MAX_WIDTH = frame.winfo_width()
    for widget in frame.winfo_children():
        widget.destroy()


def var_tracer(var, mode, cb):
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
