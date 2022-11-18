import tkinter as tk
import tkinter.ttk as ttk
import ctypes
from gui_functions import detect_darkmode_in_windows
import globals as GV
WIDTH = 750
HEIGHT = 500
MINWIDTH = 650
MINHEIGHT = 450
MAXWIDTH = WIDTH + 300
MAXHEIGHT = HEIGHT + 100
WIDTH_OFFSET = 400
HEIGHT_OFFSET = 400
TOP_FRAME_HEIGHT = 80
LEFT_FRAME_WIDTH = 0
COLOR_MODE = 'dark' if detect_darkmode_in_windows() else 'light'

FONTS_large = ("Ariel", 24)
FONTS_medium = ("Ariel Bold", 16)
FONTS_small = ("Ariel", 13)
FONTS_smaller = ("Ariel", 10)
FONTS_tiny = ("Ariel", 9)

tkinter_background_color = '#856ff8'
color_red = '#e81123'
color_blue = '#0067b8'
top_background_color = '#e6e6e6'


def apply_theme(theme, tkinter):
    global tkinter_background_color, color_red, color_blue, top_background_color, left_background_color
    if theme == 'light':
        tkinter_background_color = '#856ff8'
        color_red = '#e81123'
        color_blue = '#0067b8'
        top_background_color = '#e6e6e6'
    elif theme == 'dark':
        tkinter_background_color = '#856ff8'
        color_red = '#ff4a4a'
        color_blue = '#3aa9ff'
        top_background_color = '#2b2b2b'
        # force Windows black borders for Windows 11
        tkinter.update()
        set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
        get_parent = ctypes.windll.user32.GetParent
        hwnd = get_parent(tkinter.winfo_id())
        rendering_policy = 20
        value = 2
        value = ctypes.c_int(value)
        set_window_attribute(hwnd, rendering_policy, ctypes.byref(value),
                             ctypes.sizeof(value))
    tkinter.tk.call("set_theme", theme)
    tkinter.update()


def init_tkinter(title, icon=None):
    tkinter = tk.Tk()
    tkinter.title(title)

    #windll.shcore.SetProcessDpiAwareness(1)
    dpi_factor = ctypes.windll.user32.GetDpiForSystem()/96

    tkinter.geometry(str("%sx%s+%s+%s" % (WIDTH, HEIGHT, WIDTH_OFFSET, HEIGHT_OFFSET)))
    tkinter.minsize(MINWIDTH, MINHEIGHT)
    tkinter.maxsize(int(MAXWIDTH * dpi_factor), int(MAXHEIGHT * dpi_factor))
    tkinter.iconbitmap(icon)
    tkinter.tk.call("source", GV.PATH.CURRENT_DIR + '/resources/style/theme/azure.tcl')
    tkinter.tk.call('tk', 'scaling', 1.4)
    apply_theme(COLOR_MODE, tkinter)
    #tkinter.resizable(False, False)
    ''' 
    '''
    return tkinter


def build_main_gui_frames(parent, left_frame_img_path=None, top_frame_height=TOP_FRAME_HEIGHT,
                          left_frame_width=LEFT_FRAME_WIDTH):
    """
    Used to build or rebuild the main frames after language change to a language with different direction
    (see function right_to_left_lang)
    """
    top_frame = tk.Frame(parent, height=top_frame_height, width=MINWIDTH, background=top_background_color)
    left_frame = tk.Frame(parent, width=left_frame_width, height=MINHEIGHT)
    mid_frame = tk.Frame(parent, height=MINHEIGHT - top_frame_height,)

    top_frame.pack(fill="x", side='top')
    top_frame.pack_propagate(False)
    #left_frame.pack(fill="y", side=GV.UI.DI_VAR['l'])
    #left_frame.pack_propagate(False)
    mid_frame.pack(fill="both", expand=True, padx=20, pady=(20, 20))
    mid_frame.pack_propagate(False)
    return top_frame, mid_frame, left_frame


def generic_page_layout(parent, title=None, primary_btn_txt=None, primary_btn_command=None, secondary_btn_txt=None,
                        secondary_btn_command=None):
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
    frame.pack(fill='both', expand=1, pady=(10, 10), padx=(10, 0))
    return frame


def open_popup(parent, x_size: int = None, y_size: int = None,):
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
    geometry = "%dx%d+%d+%d" % (x_size, y_size, x_position + (x_app_size - x_size) / 2 + 20, y_position + (y_app_size - y_size) / 2 + 20)
    pop.geometry(geometry)
    #pop.protocol("WM_DELETE_WINDOW", False)
    pop.overrideredirect(True)
    pop.focus_set()
    pop.grab_set()
    border_frame.pack(expand=1, fill='both', pady=5, padx=5)
    pop_frame = tk.Frame(border_frame)
    pop_frame.pack(expand=1, fill='both', padx=10, pady=(20, 10))

    return pop, pop_frame


def input_pop_up(parent, title_txt=None, msg_txt=None, primary_btn_str=None, secondary_btn_str=None,):
    x_size = 600
    y_size = int(len(msg_txt) / 2.8 + 180 + 13 * msg_txt.count('\n'))
    pop, pop_frame = open_popup(parent, x_size, y_size)
    pop_var = tk.IntVar(pop)
    msg_font = FONTS_small
    if msg_txt:
        add_text_label(pop_frame, msg_txt, msg_font, pady=10)

    generic_page_layout(pop_frame, title_txt, primary_btn_str, lambda *args: validate_pop_input(1),
                        secondary_btn_str, lambda *args: validate_pop_input(0))

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
    btn_next.pack(anchor=GV.UI.DI_VAR['se'], side=GV.UI.DI_VAR['r'], ipadx=22, padx=0)
    return btn_next


def add_secondary_btn(parent, text, command):
    """
    a preset for adding a tkinter button. Used for the likes of "Back", "Cancel" and "Abort" buttons
    :return: tkinter button object
    """
    btn_back = ttk.Button(parent, text=text, command=command)
    btn_back.pack(anchor=GV.UI.DI_VAR['se'], side=GV.UI.DI_VAR['r'], padx=12, ipadx=8)
    return btn_back


def add_page_title(parent, text, pady=(0, 15)):
    title = ttk.Label(parent, wraplength=GV.UI.width, justify=GV.UI.DI_VAR['l'], text=text, font=FONTS_medium)
    title.pack(pady=pady,)
    return title


def add_radio_btn(parent, text, var, value, command=None, is_disabled=None, ipady=5, side=None, pack=True):
    radio = ttk.Radiobutton(parent, text=text, variable=var, value=value)
    if pack:
        radio.pack(ipady=ipady, side=side)
    if command: radio.configure(command=command)
    if is_disabled: radio.configure(state='disabled')
    return radio


def add_check_btn(parent, text, var, command=None, is_disabled=None, pady=5, pack=True, switch=False):
    check = ttk.Checkbutton(parent, text=text, variable=var, onvalue=True, offvalue=False)
    if switch: check.configure(style='Switch.TCheckbutton')
    if pack: check.pack(ipady=5, pady=pady)
    if command: check.configure(command=command)
    if is_disabled: check.configure(state='disabled')
    return check


def add_text_label(parent, text=None, font=FONTS_small, var=None, pady=20, padx=0, foreground=None):
    """
    a preset for tkinter text label that packs by default
    :return: the tkinter label "ttk.Label" object
    """
    if (not var and text) or (var and not text):
        label = ttk.Label(parent, wraplength=GV.UI.width, justify=GV.UI.DI_VAR['l'],
                          text=text, textvariable=var, foreground=foreground, font=font)
    else: return -1
    label.pack(pady=pady, padx=padx, )
    return label


def add_lang_list(parent, var, languages):
    lang_list = ttk.Combobox(parent, name="language", textvariable=var, background=top_background_color)
    lang_list['values'] = tuple(languages)
    lang_list['state'] = 'readonly'
    lang_list.set('English')
    lang_list.pack(side='left', padx=30)
    return lang_list


def add_frame_container(parent, fill='both'):
    frame = ttk.Frame(parent, width=MINWIDTH)
    frame.pack(expand=1, fill=fill, padx=0, pady=0)

    return frame


def add_progress_bar(parent, length=MINWIDTH - LEFT_FRAME_WIDTH):
    progressbar = ttk.Progressbar(parent, orient='horizontal', length=length, mode='determinate')
    progressbar.pack(pady=25)
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
    if tracers_list:
        return 'tracer exists'
    else:
        var.trace_add(mode=mode, callback=cb)


