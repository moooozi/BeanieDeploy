import tkinter.ttk as ttk
import autoinst
import page_autoinst_addition_2
import tkinter_templates as tkt
import globals as GV
import translations.en as LN
import page_autoinst2
import global_tk_vars as tk_var


def run(app):
    """the autoinstall page on which you choose your language and locale"""
    tkt.init_frame(app)
    # *************************************************************************************************************
    page_frame = tkt.generic_page_layout(app, LN.title_autoinst2,
                                         LN.btn_next, lambda: next_btn_action(),
                                         LN.btn_back, lambda: page_autoinst2.run(app))
    if GV.IP_LOCALE:
        langs_and_locales = autoinst.get_locales_and_langs_sorted_with_names(territory=GV.IP_LOCALE['country_code'])
    else:
        langs_and_locales = autoinst.get_locales_and_langs_sorted_with_names()

    temp_frame = ttk.Frame(page_frame)
    temp_frame.pack()
    lang_list_fedora = ttk.Treeview(temp_frame, columns='lang', show='headings', height=8)
    lang_list_fedora.heading('lang', text=LN.lang)
    lang_list_fedora.pack(side=GV.UI.DI_VAR['l'], ipady=5, padx=5)
    locale_list_fedora = ttk.Treeview(temp_frame, columns='locale', show='headings', height=8)
    locale_list_fedora.heading('locale', text=LN.locale)
    locale_list_fedora.pack(side=GV.UI.DI_VAR['l'], ipady=5, padx=5)

    for i in range(len(langs_and_locales)):
        lang_list_fedora.insert(parent='', index='end', iid=str(i), values=('%s (%s)' % langs_and_locales[i][0][:2],))

    def on_lang_click(*args):
        for item in locale_list_fedora.get_children():
            locale_list_fedora.delete(item)
        for locale in langs_and_locales[int(lang_list_fedora.focus())][1]:
            locale_list_fedora.insert(parent='', index='end', iid=locale[2], values=locale[1:2])

    lang_list_fedora.bind('<<TreeviewSelect>>', on_lang_click)

    def next_btn_action(*args):
        locale = locale_list_fedora.focus()
        if autoinst.langtable.parse_locale(locale).language:
            # tk_var.selected_locale.set(spin)
            GV.KICKSTART.locale = locale
            return page_autoinst_addition_2.run(app)