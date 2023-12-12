import page_autoinst_addition_3
import tkinter.ttk as ttk
import autoinst
import libs.langtable as langtable
import page_autoinst_addition_1
import tkinter_templates as tkt
import globals as GV
import multilingual
import global_tk_vars as tk_var


def run(app):
    """the autoinstall page on which you choose your timezone and keyboard layout"""
    tkt.init_frame(app)
    global LN, DI_VAR
    LN = multilingual.get_lang()
    DI_VAR = multilingual.get_di_var()
    # *************************************************************************************************************
    page_frame = tkt.generic_page_layout(app, LN.title_autoinst3,
                                         LN.btn_next, lambda: next_btn_action(),
                                         LN.btn_back, lambda: page_autoinst_addition_1.run(app))


    # List of all keymaps, the more likely relevant keymaps (based on selected locale) will be listed first
    selected_locale_keymaps = langtable.list_keyboards(languageId=GV.KICKSTART.locale)
    #all_keymaps = selected_locale_keymaps +  [keyboard for keyboard in langtable.list_all_keyboards() if keyboard not in selected_locale_keymaps]
    all_keymaps = sorted(langtable.list_all_keyboards())

    selected_locale_timezones = langtable.list_timezones(languageId=GV.KICKSTART.locale)
    #all_timezones = selected_locale_timezones + [zone for zone in sorted(langtable.list_all_timezones()) if zone not in selected_locale_timezones]
    all_timezones = sorted(langtable.list_all_timezones())


    temp_frame = ttk.Frame(page_frame)
    temp_frame.pack(expand=1, fill='both')
    temp_frame.grid_rowconfigure(0, weight=1)
    temp_frame.columnconfigure(0, weight=1)
    temp_frame.columnconfigure(1, weight=1)
    keyboard_list_frame = ttk.Frame(temp_frame)
    keyboard_list_frame.grid(row=0, column=0, ipady=5, padx=5, sticky='news')
    timezone_list_frame = ttk.Frame(temp_frame)
    timezone_list_frame.grid(row=0, column=1, ipady=5, padx=5, sticky='news')

    keyboard_list = ttk.Treeview(keyboard_list_frame, columns='keyboard', show='headings', height=8)
    keyboard_list.heading('keyboard', text=LN.list_keymaps)
    keyboard_list.pack(side='left', fill='both', expand=1)
    keyboard_list_scrollbar = ttk.Scrollbar(keyboard_list_frame, orient="vertical", command=keyboard_list.yview)
    keyboard_list_scrollbar.pack(side='right', fill='y')
    keyboard_list.configure(yscrollcommand=keyboard_list_scrollbar.set)


    timezone_list = ttk.Treeview(timezone_list_frame, columns='timezone', show='headings', height=8)
    timezone_list.heading('timezone', text=LN.list_timezones)
    timezone_list.pack(side='left', fill='both', expand=1)
    timezone_list_scrollbar = ttk.Scrollbar(timezone_list_frame, orient="vertical", command=timezone_list.yview)
    timezone_list_scrollbar.pack(side='right', fill='y')
    timezone_list.configure(yscrollcommand=timezone_list_scrollbar.set)


    for keymap in all_keymaps:
        keyboard_list.insert(parent='', index='end', iid=keymap, values=(autoinst.get_keymap_description(keymap),))

    for timezone in all_timezones:
        #continent, city = timezone.split('/')
        #if continent not in timezone_list.get_children():
        #    timezone_list.insert(parent='', index='end', iid=continent, values=(continent,))
        #if city not in timezone_list.get_children(continent):
        #    timezone_list.insert(parent=continent, index='end', iid=timezone, values=(city,))
        timezone_list.insert(parent='', index='end', iid=timezone, values=(timezone,))

    
    if not (GV.KICKSTART.timezone and GV.KICKSTART.keymap):
        GV.KICKSTART.timezone = selected_locale_timezones[0]
        GV.KICKSTART.keymap = selected_locale_keymaps[0]
    #app.update()
    keyboard_list.focus(GV.KICKSTART.keymap)
    keyboard_list.selection_set(GV.KICKSTART.keymap)
    keyboard_list.yview_scroll(keyboard_list.index(keyboard_list.selection())-1, "units")

    timezone_list.focus(GV.KICKSTART.timezone)
    timezone_list.selection_set(GV.KICKSTART.timezone)
    timezone_list.yview_scroll(timezone_list.index(timezone_list.selection())-1, "units")

    def next_btn_action(*args):
        if timezone_list.focus() not in all_timezones or keyboard_list.focus() not in all_keymaps:
            return
        GV.KICKSTART.timezone = timezone_list.focus()
        GV.KICKSTART.keymap = keyboard_list.focus()
        GV.KICKSTART.keymap_type = 'xlayout'
        return page_autoinst_addition_3.run(app)

