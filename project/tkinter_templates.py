import tkinter as tk
import tkinter.ttk as ttk

import globals as GV
WIDTH = 850
HEIGHT = 550
MINWIDTH = 850
MINHEIGHT = 550
WIDTH_OFFSET = 400
HEIGHT_OFFSET = 400
TOP_FRAME_HEIGHT = 100
LEFT_FRAME_WIDTH = 150
light_red = '#ff4a4a'
light_blue = '#3aa9ff'
top_background = '#474747'
left_background = '#303030'
FONTS_large = ("Ariel", 24)
FONTS_medium = ("Ariel Bold", 16)
FONTS_small = ("Ariel", 13)
FONTS_smaller = ("Ariel", 10)
FONTS_tiny = ("Ariel", 9)


def init_tkinter(title, icon=None):
    tkinter = tk.Tk()
    tkinter.title(title)
    tkinter.geometry(str("%sx%s+%s+%s" % (WIDTH, HEIGHT, WIDTH_OFFSET, HEIGHT_OFFSET)))
    tkinter.minsize(MINWIDTH, MINHEIGHT)
    tkinter.iconbitmap(icon)
    #tkinter.resizable(False, False)
    tkinter.option_add('*Font', 'Ariel 11')
    ''' # force Windows black borders for Windows 11
    import ctypes
    tkinter.update()
    dwmwa_use_immersive_dark_mode = 20
    set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
    get_parent = ctypes.windll.user32.GetParent
    hwnd = get_parent(tkinter.winfo_id())
    rendering_policy = dwmwa_use_immersive_dark_mode
    value = 2
    value = ctypes.c_int(value)
    set_window_attribute(hwnd, rendering_policy, ctypes.byref(value),
                         ctypes.sizeof(value))
    '''
    return tkinter


def build_main_gui_frames(parent, left_frame_img_path=None, top_frame_height=TOP_FRAME_HEIGHT,
                          left_frame_width=LEFT_FRAME_WIDTH):
    """
    Used to build or rebuild the main frames after language change to a language with different direction
    (see function right_to_left_lang)
    """
    top_frame = tk.Frame(parent, height=top_frame_height, width=MINWIDTH, background=top_background)
    left_frame = tk.Frame(parent, width=left_frame_width, height=MINHEIGHT, background=left_background)
    mid_frame = ttk.Frame(parent, height=MINHEIGHT - top_frame_height)

    top_frame.pack(fill="x", side='top')
    top_frame.pack_propagate(False)
    left_frame.pack(fill="y", side=GV.UI.DI_VAR['l'])
    left_frame.pack_propagate(False)
    mid_frame.pack(fill="both", expand=True, padx=20, pady=20)
    mid_frame.pack_propagate(False)
    return top_frame, mid_frame, left_frame


def generic_page_layout(parent, title, primary_btn_txt=None, primary_btn_command=None, secondary_btn_txt=None,
                        secondary_btn_command=None):
    add_page_title(parent, title)
    if primary_btn_txt or secondary_btn_txt:
        bottom_frame = tk.Frame(parent, height=34)
        bottom_frame.pack(side='bottom', fill='x')
        bottom_frame.pack_propagate(False)
        if primary_btn_txt:
            add_primary_btn(bottom_frame, primary_btn_txt, primary_btn_command)
        if secondary_btn_txt:
            add_secondary_btn(bottom_frame, secondary_btn_txt, secondary_btn_command)
    frame = add_frame_container(parent)
    return frame


def open_popup(parent, title_txt, msg_txt, primary_btn_str=None, secondary_btn_str=None, is_entry=None, regex=None,
               x_size: int = None, y_size: int = None):
    """
    Pops up window to get input from user and freezes the main GUI while waiting for response
    :param y_size: window height in pixels
    :param x_size: window width in pixels
    :param is_entry: typing input? or just a yes-no-like question
    :param parent: the parent for the Tkinter Toplevel
    :param secondary_btn_str: the string text for the secondary button
    :param primary_btn_str: the string text for the primary button
    :type regex: Pattern[str]
    :param title_txt: the title for the popup in big font
    :param msg_txt: the smaller text beneath the title
    :return:
    """
    pop = tk.Toplevel(parent)
    border_frame = tk.Frame(pop, highlightbackground="gray", highlightthickness=1)
    pop_frame = tk.Frame(border_frame)
    pop_var = tk.IntVar(pop)
    x_position = parent.winfo_x()
    y_position = parent.winfo_y()
    #  position the pop-up window at the center of its parent
    msg_font = FONTS_small
    if not (x_size and y_size):
        x_size = 600
        y_size = int(len(msg_txt)/2.8 + 180 + 13*msg_txt.count('\n'))

    geometry = "%dx%d+%d+%d" % (x_size, y_size, x_position + (MINWIDTH - x_size) / 2 + 20, y_position + (MINHEIGHT - y_size) / 2 + 20)
    pop.geometry(geometry)
    pop.overrideredirect(True)
    pop.focus_set()
    pop.grab_set()
    border_frame.pack(expand=1, fill='both', pady=5, padx=5)
    pop_frame.pack(expand=1, fill='both', pady=5, padx=10)
    add_page_title(pop_frame, title_txt, 20)
    add_text_label(pop_frame, msg_txt, msg_font, pady=10)

    if is_entry:
        temp_frame = ttk.Frame(pop_frame)
        temp_frame.pack(fill='x', pady=(20, 0))
        entry_var = tk.StringVar(pop)
        entry = ttk.Entry(temp_frame, width=20, textvariable=entry_var)
        entry.pack(padx=(20, 10), anchor=GV.UI.DI_VAR['w'], side=GV.UI.DI_VAR['l'])
        if regex:
            from functions import validate_with_regex
            entry_var.trace_add('write', lambda *args: validate_with_regex(var=entry_var, regex=regex, mode='fix'))
        entry_suffix = ttk.Label(temp_frame, text='GB', font=msg_font)
        entry_suffix.pack(anchor=GV.UI.DI_VAR['w'], side=GV.UI.DI_VAR['l'])
    else:
        entry_var = None

    add_primary_btn(pop_frame, primary_btn_str, lambda *args: validate_pop_input(1))
    add_secondary_btn(pop_frame, secondary_btn_str, lambda *args: validate_pop_input(0))

    def validate_pop_input(inputted):
        pop_var.set(inputted)
        pop.destroy()
    pop.wait_window()
    if is_entry and pop_var.get() == 1:
        return entry_var.get()
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


def add_page_title(parent, text, pady=(20, 15)):
    title = ttk.Label(parent, wraplength=GV.UI.width, justify=GV.UI.DI_VAR['l'], text=text, font=FONTS_medium)
    title.pack(pady=pady, anchor=GV.UI.DI_VAR['w'])
    return title


def add_radio_btn(parent, text, var, value, command=None, is_disabled=None, ipady=5, side=None, pack=True):
    radio = ttk.Radiobutton(parent, text=text, variable=var, value=value)
    if pack:
        radio.pack(anchor=GV.UI.DI_VAR['w'], ipady=ipady, side=side)
    if command: radio.configure(command=command)
    if is_disabled: radio.configure(state='disabled')
    return radio


def add_check_btn(parent, text, var, command=None, is_disabled=None, pady=5, pack=True, switch=False):
    check = ttk.Checkbutton(parent, text=text, variable=var, onvalue=True, offvalue=False)
    if switch: check.configure(style='Switch.TCheckbutton')
    if pack: check.pack(anchor=GV.UI.DI_VAR['w'], ipady=5, pady=pady)
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
    label.pack(pady=pady, padx=padx, anchor=GV.UI.DI_VAR['w'])
    return label


def add_lang_list(parent, var, languages):
    lang_list = ttk.Combobox(parent, name="language", textvariable=var, background=top_background)
    lang_list['values'] = tuple(languages)
    lang_list['state'] = 'readonly'
    lang_list.set('English')
    lang_list.pack(anchor=GV.UI.DI_VAR['w'], side='left', padx=30)
    return lang_list


def add_frame_container(parent, padx=20, pady=20):
    frame = ttk.Frame(parent)
    padx_var = (padx, 0)
    if GV.UI.DI_VAR['w'] != 'w':  # if right-to-left language
        padx_var = (0, padx)
    frame.pack(fill="x", padx=padx_var, pady=(pady, 0))
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


