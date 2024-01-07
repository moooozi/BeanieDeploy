import tkinter as tk
import tkinter.ttk as ttk
import ctypes
from gui_functions import detect_darkmode_in_windows
import globals as GV
import resources.style.theme.svtheme.sv_ttk as sv_ttk
import multilingual

WIDTH = 850
HEIGHT = 580
MINWIDTH = WIDTH -50
MINHEIGHT = HEIGHT - 50
MAXWIDTH = WIDTH + 300
MAXHEIGHT = HEIGHT + 200
WIDTH_OFFSET = 400
HEIGHT_OFFSET = 400
TOP_FRAME_HEIGHT = 80
LEFT_FRAME_WIDTH = 0
DARK_MODE = detect_darkmode_in_windows()

FONTS_large = ("Ariel", 24)
FONTS_medium = ("Ariel Bold", 16)
FONTS_small = ("Ariel", 13)
FONTS_smaller = ("Ariel", 12)
FONTS_tiny = ("Ariel", 11)

tkinter_background_color = ''
color_red = ''
color_blue = ''
color_green = ''
top_background_color = ''


def dark_decorations(ye_or_nah, tkinter):
    # force Windows black borders for Windows 11
    tkinter.update()
    set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
    get_parent = ctypes.windll.user32.GetParent
    hwnd = get_parent(tkinter.winfo_id())
    rendering_policy = 20 if ye_or_nah else 0
    value = 2
    value = ctypes.c_int(value)
    set_window_attribute(hwnd, rendering_policy, ctypes.byref(value),
                         ctypes.sizeof(value))


def dark_theme(ye_or_nah, tkinter):
    global tkinter_background_color, color_red, color_blue, color_green, top_background_color
    if not ye_or_nah:
        color_mode = 'light'
        tkinter_background_color = '#856ff8'
        color_red = '#e81123'
        color_blue = '#0067b8'
        color_green = '#008009'
        top_background_color = '#e6e6e6'
    else:
        color_mode = 'dark'
        tkinter_background_color = '#856ff8'
        color_red = '#ff4a4a'
        color_blue = '#3aa9ff'
        color_green = '#5dd25e'
        top_background_color = '#2b2b2b'
    dark_decorations(ye_or_nah, tkinter)
    sv_ttk.set_theme(color_mode)
    tkinter.update()


def init_tkinter(title, icon=None):
    tkinter = tk.Tk()
    tkinter.title(title)
    # windll.shcore.SetProcessDpiAwareness(1)
    dpi_factor = ctypes.windll.user32.GetDpiForSystem() / 96

    tkinter.geometry(str("%sx%s+%s+%s" % (WIDTH, HEIGHT, WIDTH_OFFSET, HEIGHT_OFFSET)))
    tkinter.minsize(MINWIDTH, MINHEIGHT)
    tkinter.maxsize(int(MAXWIDTH * dpi_factor), int(MAXHEIGHT * dpi_factor))
    tkinter.iconbitmap(icon)
    #tkinter.tk.call('tk', 'scaling', 1.4)
    dark_theme(DARK_MODE, tkinter)
    # tkinter.resizable(False, False)

    return tkinter


def build_main_gui_frames(parent, left_frame_img_path=None, top_frame_height=TOP_FRAME_HEIGHT,
                          left_frame_width=LEFT_FRAME_WIDTH):
    """
    Used to build or rebuild the main frames after language change to a language with different direction
    (see function right_to_left_lang)
    """
    top_frame = tk.Frame(parent, height=top_frame_height, width=MINWIDTH, background=top_background_color)
    left_frame = tk.Frame(parent, width=left_frame_width, height=MINHEIGHT)
    mid_frame = tk.Frame(parent, height=MINHEIGHT - top_frame_height, )

    top_frame.pack(fill="x", side='top')
    top_frame.pack_propagate(False)
    # dark_mode_var = tk.BooleanVar(parent, DARK_MODE)
    # add_check_btn(top_frame, "Dark Mode", dark_mode_var, lambda *args: dark_theme(dark_mode_var.get(), parent), switch=True)
    # left_frame.pack(fill="y", side=multilingual.DI_VAR['l'])
    # left_frame.pack_propagate(False)
    mid_frame.pack(fill="both", expand=True, padx=20, pady=(20, 20))
    mid_frame.pack_propagate(False)
    return top_frame, mid_frame, left_frame


def generic_page_layout(parent, title=None, primary_btn_txt=None, primary_btn_command=None, secondary_btn_txt=None,
                        secondary_btn_command=None, title_pady=15):
    if title:
        add_page_title(parent, title)
    if primary_btn_txt or secondary_btn_txt:
        bottom_frame = tk.Frame(parent, height=34)
        bottom_frame.pack(side='bottom', fill='x')
        bottom_frame.pack_propagate(False)
        if primary_btn_txt:
            add_primary_btn(bottom_frame, primary_btn_txt, primary_btn_command)
        if secondary_btn_txt:
            add_secondary_btn(bottom_frame, secondary_btn_txt, secondary_btn_command)
    frame = ttk.Frame(parent)
    frame.pack(fill='both', expand=1, pady=title_pady, padx=(0, 0))
    return frame


def open_popup(parent, x_size: int = None, y_size: int = None, ):
    """
    Pops up window to get input from user and freezes the main GUI while waiting for response
    :param y_size: window height in pixels
    :param x_size: window width in pixels
    :param parent: the parent for the Tkinter Toplevel
    :return:
    """
    pop = tk.Toplevel(parent)
    border_frame = tk.Frame(pop, highlightbackground="gray", highlightthickness=1)
    x_position = parent.winfo_x()
    y_position = parent.winfo_y()
    x_app_size = parent.winfo_width()
    y_app_size = parent.winfo_height()
    #  position the pop-up window at the center of its parent
    geometry = "%dx%d+%d+%d" % (
    x_size, y_size, x_position + (x_app_size - x_size) / 2 + 20, y_position + (y_app_size - y_size) / 2 + 20)
    pop.geometry(geometry)
    dark_theme(DARK_MODE, pop)
    # pop.protocol("WM_DELETE_WINDOW", False)
    pop.focus_set()
    pop.grab_set()
    border_frame.pack(expand=1, fill='both', pady=5, padx=5)
    pop_frame = tk.Frame(border_frame)
    pop_frame.pack(expand=1, fill='both', padx=10, pady=(20, 10))

    return pop, pop_frame


def input_pop_up(parent, title_txt=None, msg_txt=None, primary_btn_str=None, secondary_btn_str=None, ):
    x_size = 600
    y_size = int(len(msg_txt) / 2.8 + 180 + 13 * msg_txt.count('\n'))
    pop, pop_frame = open_popup(parent, x_size, y_size)
    pop_var = tk.IntVar(pop)
    msg_font = FONTS_smaller
    layout_frame = generic_page_layout(pop_frame, title_txt, primary_btn_str, lambda *args: validate_pop_input(1),
                                       secondary_btn_str, lambda *args: validate_pop_input(0), title_pady=5)
    if msg_txt:
        add_text_label(layout_frame, msg_txt, msg_font, pady=10)

    def validate_pop_input(inputted):
        pop_var.set(inputted)
        pop.destroy()

    pop.wait_window()
    return pop_var.get()


def add_primary_btn(parent, text, command):
    """
    a preset for adding a tkinter button. Used for the likes of "Next" and "Install" buttons
    :return: tkinter button object
    """
    btn_next = ttk.Button(parent, text=text, style="Accent.TButton", command=command)
    btn_next.pack(anchor=multilingual.DI_VAR['se'], side=multilingual.DI_VAR['r'], ipadx=22, padx=0)
    return btn_next


def add_secondary_btn(parent, text, command):
    """
    a preset for adding a tkinter button. Used for the likes of "Back", "Cancel" and "Abort" buttons
    :return: tkinter button object
    """
    btn_back = ttk.Button(parent, text=text, command=command)
    btn_back.pack(anchor=multilingual.DI_VAR['se'], side=multilingual.DI_VAR['r'], padx=12, ipadx=8)
    return btn_back


def add_multi_radio_buttons(parent, items: dict, var, validate_func=None):
    frame = add_frame_container(parent, fill='x', expand=1)
    for index, item in enumerate(items.keys()):
        button = add_radio_btn(frame, items[item]["name"], var, item, command=lambda: validate_func(), pack=False)
        button.grid(ipady=5, row=index, column=0, sticky=multilingual.DI_VAR['nw'])
        if "error" in items[item] and items[item]["error"]:
            button.configure(state='disabled')
            ttk.Label(frame, wraplength=GV.UI.width, justify="center", text=items[item]["error"],
                      font=FONTS_smaller, foreground=color_red).grid(ipadx=5, row=index, column=1,
                                                                     sticky=multilingual.DI_VAR['w'])
            if var.get() == item:
                var.set("")
        elif "description" in items[item] and items[item]["description"]:
            ttk.Label(frame, wraplength=GV.UI.width, justify="center", text=items[item]["description"],
                      font=FONTS_tiny, foreground=color_blue).grid(ipadx=5, row=index, column=1,
                                                                   sticky=multilingual.DI_VAR['w'])
        frame.grid_columnconfigure(index, weight=1)
    #temp_frame = ttk.Label(frame,text="Yo wtf")
    #temp_frame.grid(row=index+1, rowspan=5, column=0, sticky=multilingual.DI_VAR['nw'])
    #temp_frame.grid_columnconfigure(index+1, weight=5)
    return frame


def add_page_title(parent, text, pady=(0, 5)):
    title = ttk.Label(parent, wraplength=GV.UI.width, justify=multilingual.DI_VAR['l'], text=text, font=FONTS_medium)
    title.pack(pady=pady, padx=0, fill='x', )
    return title


def add_radio_btn(parent, text, var, value, command=None, is_disabled=None, ipady=5, side=None, pack=True):
    radio = ttk.Radiobutton(parent, text=text, variable=var, value=value, width=99)
    if pack: radio.pack(ipady=ipady, side=side)
    if command: radio.configure(command=command)
    if is_disabled: radio.configure(state='disabled')
    return radio


def add_check_btn(parent, text, var, command=None, is_disabled=None, pady=5, pack=True, switch=False):
    check = ttk.Checkbutton(parent, text=text, variable=var, onvalue=True, offvalue=False, width=99)
    if switch: check.configure(style='Switch.TCheckbutton')
    if pack: check.pack(ipady=5, pady=pady)
    if command: check.configure(command=command)
    if is_disabled: check.configure(state='disabled')
    return check


def add_text_label(parent, text=None, font=FONTS_small, var=None, pady=20, padx=0, foreground=None, anchor=None,
                   pack=True):
    """
    a preset for tkinter text label that packs by default
    :return: the tkinter label "ttk.Label" object
    """
    if (not var and text) or (var and not text):
        label = ttk.Label(parent, wraplength=GV.UI.width, justify=multilingual.DI_VAR['l'],
                          text=text, textvariable=var, foreground=foreground, font=font)
    else:
        return -1
    if pack: label.pack(pady=pady, padx=padx, anchor=anchor)
    return label


def add_lang_list(parent, var, languages):
    lang_list = ttk.Combobox(parent, name="language", textvariable=var, background=top_background_color)
    lang_list['values'] = tuple(languages)
    lang_list['state'] = 'readonly'
    lang_list.set('English')
    lang_list.pack(side='left', padx=30)
    return lang_list


def add_frame_container(parent, **kwargs):
    frame = ttk.Frame(parent, width=MINWIDTH)
    frame.pack(**kwargs)
    return frame


def add_progress_bar(parent, ):
    progressbar = ttk.Progressbar(parent, orient='horizontal', length=MAXWIDTH, mode='determinate')
    progressbar.pack(pady=(0, 20))
    return progressbar


def stylize(parent, theme_dir, theme_name):
    style = ttk.Style(parent)
    parent.tk.call('source', theme_dir)
    style.theme_use(theme_name)
    style.configure("Accent.TButton", foreground='white')
    style.configure("Togglebutton", foreground='white')


def init_frame(frame):
    """removes all elements inside the middle frame, which contains all page-specific content"""
    GV.UI.width = frame.winfo_width()
    for widget in frame.winfo_children():
        widget.destroy()


def var_tracer(var, mode, cb):
    """
    add tkinter variable tracer if no tracer exists
    :param var: tkinter variable
    :param mode: tkinter tracer mode (see trace_add docs)
    :param cb: the callback function
    """
    tracers_list = var.trace_info()
    for tracer in tracers_list:
        var.trace_remove(*tracer)
    var.trace_add(mode=mode, callback=cb)
