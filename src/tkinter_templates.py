import multiprocessing
import queue
import subprocess
from tkinter import ttk
import customtkinter as ctk
import ctypes
from gui_functions import detect_darkmode_in_windows
import globals as GV
import resources.style.theme.svtheme.sv_ttk as sv_ttk
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
    # sv_ttk.set_theme(color_mode)
    tkinter.update()


class Application(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # windll.shcore.SetProcessDpiAwareness(1)
        dpi_factor = get_dpi_scaling_factor()
        self.geometry(str("%sx%s+%s+%s" % (WIDTH, HEIGHT, WIDTH_OFFSET, HEIGHT_OFFSET)))
        self.minsize(MINWIDTH, MINHEIGHT)
        self.maxsize(int(MAXWIDTH * dpi_factor), int(MAXHEIGHT * dpi_factor))
        self.iconbitmap(GV.PATH.APP_ICON)

        # ctk.tk.call('tk', 'scaling', 1.4)
        # ctk.resizable(False, False)

        # top_frame.grid_propagate(False)

        dark_theme(DARK_MODE, self)

        ####
        ###Treeview Customisation (theme colors are selected)
        bg_color = self._apply_appearance_mode(
            ctk.ThemeManager.theme["CTkFrame"]["fg_color"]
        )
        text_color = self._apply_appearance_mode(
            ctk.ThemeManager.theme["CTkLabel"]["text_color"]
        )
        selected_color = self._apply_appearance_mode(
            ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        )

        treestyle = ttk.Style()
        treestyle.theme_use("default")
        treestyle.configure(
            "Treeview",
            background=bg_color,
            foreground=text_color,
            fieldbackground=bg_color,
            borderwidth=0,
        )
        treestyle.map(
            "Treeview",
            background=[("selected", bg_color)],
            foreground=[("selected", selected_color)],
        )
        self.bind("<<TreeviewSelect>>", lambda event: self.focus_set())

    def wait_and_handle_queue_output(
        self,
        output_queue: multiprocessing.Queue,
        callback,
        frequency=100,
        retry_count=0,
    ):
        try:
            while not output_queue.empty():
                output = output_queue.get_nowait()
                callback(output)
        except queue.Empty:
            if retry_count:
                self.after(
                    frequency,
                    self.wait_and_handle_queue_output,
                    output_queue,
                    callback,
                    frequency,
                    retry_count - 1,
                )


def build_main_gui_frames(
    parent,
    left_frame_img_path=None,
    top_frame_height=TOP_FRAME_HEIGHT,
    left_frame_width=LEFT_FRAME_WIDTH,
):
    """
    Used to build or rebuild the main frames after language change to a language with different direction
    (see function right_to_left_lang)
    """

    # top_frame.pack_propagate(False)
    # dark_mode_var = ctk.BooleanVar(parent, DARK_MODE)
    # add_check_btn(top_frame, "Dark Mode", dark_mode_var, lambda *args: dark_theme(dark_mode_var.get(), parent), switch=True)
    # left_frame.pack(fill="y", side=multilingual.DI_VAR['l'])
    # left_frame.pack_propagate(False)


def generic_page_layout(
    parent,
    title=None,
    primary_btn_txt=None,
    primary_btn_command=None,
    secondary_btn_txt=None,
    secondary_btn_command=None,
    title_pady=20,
):
    if title:
        add_page_title(parent, title)
    if primary_btn_txt or secondary_btn_txt:
        bottom_frame = ctk.CTkFrame(
            parent, height=34, bg_color="transparent", fg_color="transparent"
        )
        bottom_frame.grid(row=2, column=0, sticky="ew")
        bottom_frame.grid_propagate(False)
        if primary_btn_txt:
            add_primary_btn(bottom_frame, primary_btn_txt, primary_btn_command)
        if secondary_btn_txt:
            add_secondary_btn(bottom_frame, secondary_btn_txt, secondary_btn_command)
    frame = ctk.CTkFrame(
        parent,
        bg_color="transparent",
        fg_color="transparent",
    )
    frame.grid(row=1, column=0, pady=title_pady, padx=(20, 20), sticky="nsew")

    parent.grid_columnconfigure(0, weight=1)
    parent.grid_rowconfigure(1, weight=1)
    parent.grid_rowconfigure(2, weight=0)
    # Set a specific size for the frame
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


def add_primary_btn(parent, text, command):
    """
    a preset for adding a CustomTkinter button. Used for the likes of "Next" and "Install" buttons
    :return: CustomTkinter button object
    """
    btn_next = ctk.CTkButton(parent, text=text, command=command)
    btn_next.pack(
        anchor=multilingual.get_di_var().se,
        side=multilingual.get_di_var().r,
        ipadx=22,
        padx=0,
    )
    return btn_next


def add_secondary_btn(parent, text, command):
    """
    a preset for adding a CustomTkinter button. Used for the likes of "Back", "Cancel" and "Abort" buttons
    :return: CustomTkinter button object
    """
    btn_back = ctk.CTkButton(parent, text=text, command=command)
    btn_back.pack(
        anchor=multilingual.get_di_var().se,
        side=multilingual.get_di_var().r,
        padx=12,
        ipadx=8,
    )
    return btn_back


def add_multi_radio_buttons(parent, items: dict, var, validate_func=None):
    frame = add_frame_container(parent, fill="x", expand=1)
    advanced_frame = ctk.CTkFrame(  # advanced options frame
        frame,
        bg_color="transparent",
        fg_color="transparent",
    )

    def show_advanced_options():
        advanced_frame.grid(row=len(items), column=0, sticky="w")
        show_advanced_label.grid_remove()

    show_advanced_label = ctk.CTkLabel(
        frame,
        text="Show advanced options",
        font=FONTS_smaller,
        text_color=color_blue,
        cursor="hand2",
    )
    if any(items[item].get("advanced", False) for item in items):
        show_advanced_label.grid(ipady=5, row=len(items) + 1, column=0, sticky="w")
        show_advanced_label.bind("<Button-1>", lambda e: show_advanced_options())

    for index, item in enumerate(items.keys()):
        target_frame = advanced_frame if items[item].get("advanced", False) else frame
        button = add_radio_btn(
            target_frame,
            items[item]["name"],
            var,
            item,
            command=lambda: validate_func(),
            pack=False,
        )
        button.grid(ipady=5, row=index, column=0, sticky="nwe")
        if "error" in items[item] and items[item]["error"]:
            button.configure(state="disabled")
            ctk.CTkLabel(
                target_frame,
                justify="center",
                text=items[item]["error"],
                font=FONTS_smaller,
                text_color=color_red,
            ).grid(ipadx=5, row=index, column=1, sticky=multilingual.get_di_var().w)
            if var.get() == item:
                var.set("")
        elif "description" in items[item] and items[item]["description"]:
            ctk.CTkLabel(
                target_frame,
                justify="center",
                text=items[item]["description"],
                font=FONTS_tiny,
                text_color=color_blue,
            ).grid(ipadx=5, row=index, column=1, sticky=multilingual.get_di_var().w)
    frame.grid_columnconfigure(0, weight=1)
    advanced_frame.grid_columnconfigure(0, weight=1)

    return frame


def add_page_title(parent, text, pady=(0, 5)):
    title = ctk.CTkLabel(
        parent,
        wraplength=GV.UI.width,
        justify=multilingual.get_di_var().l,
        text=text,
        font=FONTS_medium,
    )
    title.grid(
        row=0,
        column=0,
        pady=pady,
        padx=0,
        sticky="",
    )
    return title


def add_radio_btn(
    parent,
    text,
    var,
    value,
    command=None,
    is_disabled=None,
    ipady=5,
    side=None,
    pack=True,
):
    radio = ctk.CTkRadioButton(
        parent,
        text=text,
        variable=var,
        value=value,
    )
    if pack:
        radio.pack(ipady=ipady, side=side, fill="x")
    if command:
        radio.configure(command=command)
    if is_disabled:
        radio.configure(state="disabled")
    return radio


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
            wraplength=GV.UI.width,
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


def stylize(parent, theme_dir, theme_name):
    style = ctk.CTkStyle(parent)
    parent.tk.call("source", theme_dir)
    style.theme_use(theme_name)
    style.configure("Accent.TButton", text_color="white")
    style.configure("Togglebutton", text_color="white")


def init_frame(frame):
    """removes all elements inside the middle frame, which contains all page-specific content"""
    GV.UI.width = frame.winfo_width()
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


class InfoFrameRaster:
    def __init__(self, parent, title=""):
        self.info_frame = ctk.CTkFrame(parent)
        self.labels = {}
        if title:
            add_text_label(
                self.info_frame,
                title,
                anchor=multilingual.get_di_var().w,
                pady=5,
                padx=4,
                foreground=color_green,
                font=FONTS_smaller,
            )

    def add_label(self, key, text=""):
        label = ctk.CTkLabel(
            self.info_frame, text=text, anchor=multilingual.get_di_var().w
        )
        label.pack(fill="x", pady=2, padx=10)
        self.labels[key] = label

    def update_label(self, key, text):
        if key in self.labels:
            self.labels[key].configure(text=text)
        else:
            raise KeyError(f"Label with key '{key}' does not exist.")

    def flush_labels(self):
        for label in self.labels.values():
            label.pack_forget()
        self.labels.clear()

    def pack(self, **kwargs):
        self.info_frame.pack(**kwargs)
