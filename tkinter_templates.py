import tkinter as tk
import tkinter.ttk as ttk
import types

import globals as GV
MAXWIDTH = 800
MAXHEIGHT = 500
TOP_FRAME_HEIGHT = 100
LEFT_FRAME_WIDTH = 150

top_background = '#474747'
FONTS = types.SimpleNamespace()
FONTS.large = ("Ariel", 24)
FONTS.medium = ("Ariel Bold", 16)
FONTS.small = ("Ariel", 13)
FONTS.tiny = ("Ariel", 10)


def init_tkinter(title, icon=None):
    tkinter = tk.Tk()
    tkinter.title(title)
    tkinter.geometry(str("%sx%s" % (MAXWIDTH, MAXHEIGHT)))
    tkinter.iconbitmap(icon)
    tkinter.resizable(False, False)
    tkinter.option_add('*Font', 'Ariel 11')
    return tkinter


def build_main_gui_frames(parent, left_frame_img_path=None, top_frame_height=TOP_FRAME_HEIGHT,
                          left_frame_width=LEFT_FRAME_WIDTH):
    """
    Used to build or rebuild the main frames after language change to a language with different direction
    (see function right_to_left_lang)
    """
    top_frame = tk.Frame(parent, height=top_frame_height, width=MAXWIDTH, background=top_background)
    left_frame = ttk.Frame(parent, width=left_frame_width, height=MAXHEIGHT)
    mid_frame = ttk.Frame(parent, height=MAXHEIGHT - top_frame_height)

    top_frame.pack(fill="x", expand=1)
    top_frame.pack_propagate(False)
    left_frame.pack(fill="y", side=GV.UI.DI_VAR['l'])
    left_frame.pack_propagate(False)
    mid_frame.pack(fill="both", expand=1, padx=20, pady=20)
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
    #  position the pop up window at the center of its parent
    if x_size and y_size:
        geometry = "%dx%d+%d+%d" % (x_size, y_size, x_position + MAXWIDTH - x_size / 2, y_position + y_size/2 + 25)
        msg_font = FONTS.tiny
    else:
        if len(msg_txt) > 120:
            x_size = 600
            y_size = 300
            geometry = "%dx%d+%d+%d" % (x_size, y_size, x_position+MAXWIDTH-x_size/2, y_position+y_size/2 + 25)
            msg_font = FONTS.tiny
        else:
            x_size = 600
            y_size = 250
            geometry = "%dx%d+%d+%d" % (x_size, y_size, x_position+MAXWIDTH/2-x_size/2, y_position+MAXHEIGHT/2-y_size/2 + 25)
            msg_font = FONTS.small

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
    btn_next = ttk.Button(parent, text=text, style="Accentbutton", command=command)
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


def add_page_title(parent, text, pady=(25, 40)):
    title = ttk.Label(parent, wraplength=540, justify=GV.UI.DI_VAR['l'], text=text, font=FONTS.medium)
    title.pack(pady=pady, anchor=GV.UI.DI_VAR['w'])
    return title


def add_radio_btn(parent, text, var, value, command=None, is_disabled=None, ipady=5, side=None, pack=True):
    radio = ttk.Radiobutton(parent, text=text, variable=var, value=value)
    if pack:
        radio.pack(anchor=GV.UI.DI_VAR['w'], ipady=ipady, side=side)
    if command: radio.configure(command=command)
    if is_disabled: radio.configure(state='disabled')
    return radio


def add_check_btn(parent, text, var, command=None, is_disabled=None, pady=5, pack=True):
    check = ttk.Checkbutton(parent, text=text, variable=var, onvalue=True, offvalue=False)
    if pack: check.pack(anchor=GV.UI.DI_VAR['w'], ipady=5, pady=pady)
    if command: check.configure(command=command)
    if is_disabled: check.configure(state='disabled')
    return check


def add_text_label(parent, text=None, font=FONTS.small, var=None, pady=20, padx=0, foreground=None):
    """
    a preset for tkinter text label that packs by default
    :return: the tkinter label "ttk.Label" object
    """
    if (not var and text) or (var and not text):
        label = ttk.Label(parent, wraplength=540, justify=GV.UI.DI_VAR['l'],
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


def add_progress_bar(parent, lenth=MAXWIDTH-LEFT_FRAME_WIDTH):
    progressbar = ttk.Progressbar(parent, orient='horizontal', length=lenth, mode='determinate')
    progressbar.pack(pady=25)


def stylize(parent, theme_dir, theme_name):
    style = ttk.Style(parent)
    parent.tk.call('source', theme_dir)
    style.theme_use(theme_name)
    style.configure("Accentbutton", foreground='white')
    style.configure("Togglebutton", foreground='white')


def clear_frame(frame):
    """removes all elements inside the middle frame, which contains all page-specific content"""
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


