import tkinter as tk
from tkinter import ttk

MAXWIDTH = 800
MAXHEIGHT = 500
top_background = '#474747'
FONTS = {
    'large': ("Ariel", 24),
    'medium': ("Ariel Bold", 15),
    'small': ("Ariel", 12),
    'tiny': ("Ariel", 10)
}


def init_tkinter(title, icon=None):
    tkinter = tk.Tk()
    tkinter.title(title)
    tkinter.geometry(str("%sx%s" % (MAXWIDTH, MAXHEIGHT)))
    tkinter.iconbitmap(icon)
    tkinter.resizable(False, False)
    tkinter.option_add('*Font', 'Ariel 11')
    return tkinter


def open_popup(parent, title_txt, msg_txt, primary_btn_str=None, secondary_btn_str=None, is_entry=None, regex=None):
    """
Pops up window to get input from user and freezes the main GUI while waiting for response
    :param is_entry: typing input? or just a yes-no-like question
    :param parent: the parent for the Tkinter Toplevel
    :param secondary_btn_str: the string text for the secondary button
    :param primary_btn_str: the string text for the primary button
    :type regex: Pattern[str]
    :param title_txt: the title for the popup in big font
    :param msg_txt: the smaller text beneath the title
    :return:
    """
    from multilingual import DI_VAR
    pop = tk.Toplevel(parent)
    border_frame = tk.Frame(pop, highlightbackground="gray", highlightthickness=1)
    pop_frame = tk.Frame(border_frame)
    pop_var = tk.IntVar(pop)
    x_position = parent.winfo_x()
    y_position = parent.winfo_y()
    if len(msg_txt) > 120:
        geometry = "600x300+%d+%d" % (x_position+125, y_position+125)
        msg_font = FONTS['tiny']
    else:
        geometry = "600x250+%d+%d" % (x_position+125, y_position+160)
        msg_font = FONTS['small']
    pop.geometry(geometry)
    pop.overrideredirect(True)
    pop.focus_set()
    pop.grab_set()
    border_frame.pack(expand=1, fill='both', pady=5, padx=5)
    pop_frame.pack(expand=1, fill='both', pady=5, padx=10)
    title = ttk.Label(pop_frame, wraplength=600, font=('Mistral 18 bold'), justify=DI_VAR['l'], text=title_txt)
    title.pack(pady=20, anchor=DI_VAR['w'])
    msg = ttk.Label(pop_frame, wraplength=600, justify=DI_VAR['l'], text=msg_txt, font=msg_font)
    msg.pack(pady=10, anchor=DI_VAR['w'])
    if is_entry:
        temp_frame = ttk.Frame(pop_frame)
        temp_frame.pack(fill='x', pady=(20, 0))
        entry_var = tk.StringVar(pop)
        entry = ttk.Entry(temp_frame, width=20, textvariable=entry_var)
        entry.pack(padx=(20, 10), anchor=DI_VAR['w'], side=DI_VAR['l'])
        if regex:
            from functions import validate_with_regex
            entry_var.trace_add('write', lambda *args: validate_with_regex(var=entry_var, regex=regex, mode='fix'))
        entry_suffix = ttk.Label(temp_frame, text='GB', font=msg_font)
        entry_suffix.pack(anchor=DI_VAR['w'], side=DI_VAR['l'])
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
    from multilingual import DI_VAR
    btn_next = ttk.Button(parent, text=text, style="Accentbutton", command=command)
    btn_next.pack(anchor=DI_VAR['se'], side=DI_VAR['r'], ipadx=15, padx=10)


def add_secondary_btn(parent, text, command):
    from multilingual import DI_VAR
    btn_back = ttk.Button(parent, text=text, command=command)
    btn_back.pack(anchor=DI_VAR['se'], side=DI_VAR['r'], padx=5)


def add_page_title(parent, text, pady=35):
    from multilingual import DI_VAR
    title = ttk.Label(parent, wraplength=540, justify=DI_VAR['l'], text=text, font=FONTS['medium'])
    title.pack(pady=pady, anchor=DI_VAR['w'])


def add_radio_btn(parent, text, var, value, command=None, is_disabled=None):
    from multilingual import DI_VAR

    radio = ttk.Radiobutton(parent, text=text, variable=var, value=value)
    radio.pack(anchor=DI_VAR['w'], ipady=5)
    if command: radio.configure(command=command)
    if is_disabled: radio.configure(state='disabled')
    return radio


def add_check_btn(parent, text, var, command=None, is_disabled=None, pady=30):
    from multilingual import DI_VAR
    check = ttk.Checkbutton(parent, text=text, variable=var, onvalue=1, offvalue=0)
    check.pack(anchor=DI_VAR['w'], ipady=5, pady=pady)
    if command: check.configure(command=command)
    if is_disabled: check.configure(state='disabled')
    return check


def build_main_gui_frames(parent, main_title_var, mode='build', left_frame_img_path=None,
                          top_frame_height=100, left_frame_width=200):
    """Used to build or rebuild the main frames after language change to a language with different direction
(see function right_to_left_lang)"""
    from multilingual import DI_VAR
    if mode == 'rebuild': clear_frame(parent)
    top_frame = tk.Frame(parent, height=top_frame_height, width=MAXWIDTH, background=top_background)
    top_frame.pack(fill="x", expand=1)
    top_frame.pack_propagate(False)
    top_title = ttk.Label(top_frame, justify='center', textvariable=main_title_var, font=FONTS['large'], background=top_background)
    top_title.pack(anchor='center', side='left', padx=15)

    left_frame = ttk.Frame(parent, width=left_frame_width, height=MAXHEIGHT)
    left_frame.pack(fill="y", side=DI_VAR['l'])
    left_frame.pack_propagate(False)
    if left_frame_img_path:
        left_frame_label = ttk.Label(left_frame, image=tk.PhotoImage(file=left_frame_img_path))
        left_frame_label.pack(side='bottom')
    mid_frame = ttk.Frame(parent, height=MAXHEIGHT - top_frame_height)
    mid_frame.pack(fill="both", expand=1, padx=15, pady=20)
    mid_frame.pack_propagate(False)
    return top_frame, mid_frame, left_frame


def add_lang_list(parent, var, languages):
    from multilingual import DI_VAR
    lang_list = ttk.Combobox(parent, name="language", textvariable=var, background=top_background)
    lang_list['values'] = tuple(languages)
    lang_list['state'] = 'readonly'
    lang_list.set('English')
    lang_list.pack(anchor=DI_VAR['w'], side='left', padx=30)
    return lang_list


def stylize(parent, theme_dir):
    style = ttk.Style(parent)
    parent.tk.call('source', theme_dir)
    style.theme_use('azure')
    style.configure("Accentbutton", foreground='white')
    style.configure("Togglebutton", foreground='white')


def clear_frame(frame):
    """removes all elements inside the middle frame, which contains all page-specific content"""
    for widgets in frame.winfo_children():
        widgets.destroy()


