import page_autoinst_addition_3
import tkinter.ttk as ttk
import autoinst
import page_autoinst_addition_1
import tkinter_templates as tkt
import globals as GV
import translations.en as LN
import global_tk_vars as tk_var


def run(app):
    """the autoinstall page on which you choose your timezone and keyboard layout"""
    tkt.init_frame(app)
    # *************************************************************************************************************
    page_frame = tkt.generic_page_layout(app, LN.title_autoinst3,
                                         LN.btn_next, lambda: next_btn_action(),
                                         LN.btn_back, lambda: page_autoinst_addition_1.run(app))

    if GV.KICKSTART.keymap_type == 'vc':
        tk_var.custom_keymap_var.set(GV.KICKSTART.keymap)

    chosen_locale_name = autoinst.langtable.language_name(languageId=GV.KICKSTART.locale)

    options_dict = {}
    if GV.IP_LOCALE:
        locale_from_ip = autoinst.langtable.list_locales(territoryId=GV.IP_LOCALE['country_code'])[0]
        locale_from_ip_name = autoinst.langtable.language_name(languageId=locale_from_ip)
        if locale_from_ip != GV.KICKSTART.locale:
            options_dict['ip'] = {'name': LN.keymap_tz_option % locale_from_ip_name, 'description': LN.keymap_tz_ip_description}
    options_dict['select'] = {'name': LN.keymap_tz_option % chosen_locale_name, 'description': LN.keymap_tz_selected_description}
    options_dict['custom'] = {'name': LN.keymap_tz_custom}

    frame_radios = tkt.add_multi_radio_buttons(page_frame, options_dict, tk_var.keymap_timezone_source_var,
                                               lambda: spawn_more_widgets())
    timezone_all = sorted(autoinst.all_timezones())
    lists_frame = ttk.Frame(frame_radios)
    timezone_txt = ttk.Label(lists_frame, wraplength=GV.UI.width, justify=GV.UI.DI_VAR['l'], text=LN.list_timezones,
                             font=tkt.FONTS_tiny)
    timezone_list = ttk.Combobox(lists_frame, name="timezone", textvariable=tk_var.custom_timezone_var)
    timezone_list['values'] = tuple(timezone_all)
    timezone_list['state'] = 'readonly'

    all_keymaps = autoinst.get_available_keymaps()

    keyboards_txt = ttk.Label(lists_frame, wraplength=GV.UI.width, justify=GV.UI.DI_VAR['l'], text=LN.list_keymaps,
                              font=tkt.FONTS_tiny)
    keyboard_list = ttk.Combobox(lists_frame, name="keyboard", textvariable=tk_var.custom_keymap_var)
    keyboard_list['values'] = tuple(all_keymaps)
    keyboard_list['state'] = 'readonly'

    if GV.IP_LOCALE:
        timezone_list.set(GV.IP_LOCALE['time_zone'])

    def spawn_more_widgets(*args):
        if tk_var.keymap_timezone_source_var.get() == 'custom':
            lists_frame.grid(ipady=5, padx=30, row=3, column=0, sticky=GV.UI.DI_VAR['w'])
            keyboards_txt.grid(pady=5, padx=5, column=0, row=1, sticky=GV.UI.DI_VAR['w'])
            keyboard_list.grid(pady=5, padx=5, column=1, row=1)
            timezone_txt.grid(pady=5, padx=5, column=0, row=0, sticky=GV.UI.DI_VAR['w'])
            timezone_list.grid(pady=5, padx=5, column=1, row=0)
        else:
            lists_frame.grid_forget()

    def next_btn_action(*args):
        page_autoinst_addition_3.run(app)
