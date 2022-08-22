import tkinter as tk
import tkinter.ttk as ttk
import autoinst
import page_autoinst_addition_1
import page_verify
import tkinter_templates as tkt
import globals as GV
import translations.en as LN
from init import MID_FRAME, app


def run():
    """the autoinstall page on which you choose your timezone and keyboard layout"""
    tkt.clear_frame(MID_FRAME)
    # *************************************************************************************************************
    tkt.generic_page_layout(MID_FRAME, LN.title_autoinst3,
                            LN.btn_next, lambda: next_btn_action(),
                            LN.btn_back, lambda: page_autoinst_addition_1.run())

    custom_timezone_var = tk.StringVar(app, GV.AUTOINST.timezone)
    custom_keymap_var = tk.StringVar(app)
    if GV.AUTOINST.keymap_type == 'vc':
        custom_keymap_var.set(GV.AUTOINST.keymap)

    keymap_timezone_source_var = tk.StringVar(app, GV.AUTOINST.keymap_timezone_source)

    chosen_locale_name = autoinst.langtable.language_name(languageId=GV.AUTOINST.locale)
    if GV.IP_LOCALE:
        locale_from_ip = autoinst.langtable.list_locales(territoryId=GV.IP_LOCALE['country_code'])[0]
        locale_from_ip_name = autoinst.langtable.language_name(languageId=locale_from_ip)
        if locale_from_ip != GV.AUTOINST.locale:
            tkt.add_radio_btn(MID_FRAME, LN.keymap_tz_option % locale_from_ip_name, keymap_timezone_source_var,
                              'ip', command=lambda: spawn_more_widgets())

    tkt.add_radio_btn(MID_FRAME, LN.keymap_tz_option % chosen_locale_name, keymap_timezone_source_var, 'select',
                      lambda: spawn_more_widgets())
    tkt.add_radio_btn(MID_FRAME, LN.keymap_tz_custom, keymap_timezone_source_var, 'custom',
                      lambda: spawn_more_widgets())

    timezone_all = sorted(autoinst.all_timezones())
    lists_frame = ttk.Frame(MID_FRAME)
    timezone_txt = ttk.Label(lists_frame, wraplength=540, justify=GV.UI.DI_VAR['l'], text=LN.list_timezones,
                             font=tkt.FONTS.tiny)
    timezone_list = ttk.Combobox(lists_frame, name="timezone", textvariable=custom_timezone_var)
    timezone_list['values'] = tuple(timezone_all)
    timezone_list['state'] = 'readonly'

    all_keymaps = autoinst.get_available_keymaps()

    keyboards_txt = ttk.Label(lists_frame, wraplength=540, justify=GV.UI.DI_VAR['l'], text=LN.list_keymaps,
                              font=tkt.FONTS.tiny)
    keyboard_list = ttk.Combobox(lists_frame, name="keyboard", textvariable=custom_keymap_var)
    keyboard_list['values'] = tuple(all_keymaps)
    keyboard_list['state'] = 'readonly'

    if GV.IP_LOCALE:
        timezone_list.set(GV.IP_LOCALE['time_zone'])

    def spawn_more_widgets(*args):
        if keymap_timezone_source_var.get() == 'custom':
            lists_frame.pack(fill='x', padx=20)
            keyboards_txt.grid(pady=5, padx=5, column=0, row=1, sticky=GV.UI.DI_VAR['w'])
            keyboard_list.grid(pady=5, padx=5, column=1, row=1)
            timezone_txt.grid(pady=5, padx=5, column=0, row=0, sticky=GV.UI.DI_VAR['w'])
            timezone_list.grid(pady=5, padx=5, column=1, row=0)
        else:
            lists_frame.pack_forget()

    def next_btn_action(*args):
        if keymap_timezone_source_var.get() == 'custom':
            GV.AUTOINST.keymap = custom_keymap_var.get()
            GV.AUTOINST.keymap_type = 'vc'
            GV.AUTOINST.timezone = custom_timezone_var.get()
        GV.AUTOINST.keymap_timezone_source = keymap_timezone_source_var.get()
        page_verify.run()