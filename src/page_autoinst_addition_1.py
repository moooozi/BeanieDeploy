import tkinter.ttk as ttk
import autoinst
import page_autoinst_addition_2
import tkinter_templates as tkt
import globals as GV
import multilingual
import page_autoinst2
import global_tk_vars as tk_var


def run(app):
    """the autoinstall page on which you choose your language and locale"""
    tkt.init_frame(app)
    global LN, DI_VAR
    LN = multilingual.get_lang()
    DI_VAR = multilingual.get_di_var()
    # *************************************************************************************************************
    page_frame = tkt.generic_page_layout(app, LN.title_autoinst2,
                                         LN.btn_next, lambda: next_btn_action(),
                                         LN.btn_back, lambda: page_autoinst2.run(app))
    if GV.IP_LOCALE:
        langs_and_locales = autoinst.get_locales_and_langs_sorted_with_names(territory=GV.IP_LOCALE['country_code'])
    else:
        langs_and_locales = autoinst.get_locales_and_langs_sorted_with_names()


    temp_frame = ttk.Frame(page_frame)
    temp_frame.pack(expand=1, fill='both')
    temp_frame.grid_rowconfigure(0, weight=1)
    temp_frame.columnconfigure(0, weight=1)
    temp_frame.columnconfigure(1, weight=1)
    lang_list_frame = ttk.Frame(temp_frame)
    lang_list_frame.grid(row=0, column=0, ipady=5, padx=5, sticky='news')
    locale_list_frame = ttk.Frame(temp_frame)
    locale_list_frame.grid(row=0, column=1, ipady=5, padx=5, sticky='news')

    lang_list = ttk.Treeview(lang_list_frame, columns='lang', show='headings', height=8)
    lang_list.heading('lang', text=LN.lang)
    lang_list.pack(side='left', fill='both', expand=1)
    lang_list_scrollbar = ttk.Scrollbar(lang_list_frame, orient="vertical", command=lang_list.yview)
    lang_list_scrollbar.pack(side='right', fill='y')
    lang_list.configure(yscrollcommand=lang_list_scrollbar.set)

    locale_list = ttk.Treeview(locale_list_frame, columns='locale', show='headings', height=8)
    locale_list.heading('locale', text=LN.locale)
    locale_list.pack(side='left', fill='both', expand=1)
    locale_list_scrollbar = ttk.Scrollbar(locale_list_frame, orient="vertical", command=locale_list.yview)
    locale_list_scrollbar.pack(side='right', fill='y')
    locale_list.configure(yscrollcommand=locale_list_scrollbar.set)

    for lang, lang_details in langs_and_locales.items():
        lang_list.insert(parent='', index='end', iid=lang, values=(f'{lang_details['names']['english']} ({lang_details['names']['native']})',))

    #for i in range(len(langs_and_locales)):
    #    lang_list.insert(parent='', index='end', iid=langs_and_locales[i][0][2], values=('%s (%s)' % langs_and_locales[i][0][:2],))

    def on_lang_click(*args):
        for item in locale_list.get_children():
            locale_list.delete(item)
        for locale, locale_details in langs_and_locales[lang_list.focus()]['locales'].items():
            locale_list.insert(parent='', index='end', iid=locale, values=(locale_details['names']['native'],))

    lang_list.bind('<<TreeviewSelect>>', on_lang_click)


    if not GV.KICKSTART.locale:
        GV.KICKSTART.locale = 'en_GB.UTF-8'
    #app.update()
    language = autoinst.langtable.parse_locale(GV.KICKSTART.locale).language
    lang_list.focus(language)
    lang_list.selection_set(language)
    lang_list.yview_scroll(locale_list.index(locale_list.selection())-1, "units")
    app.update()
    on_lang_click()
    locale_list.focus(GV.KICKSTART.locale)
    locale_list.selection_set(GV.KICKSTART.locale)
    locale_list.yview_scroll(locale_list.index(locale_list.selection())-1, "units")

    def next_btn_action(*args):
        locale = locale_list.focus()
        if autoinst.langtable.parse_locale(locale).language:
            # tk_var.selected_locale.set(spin)
            GV.KICKSTART.locale = locale
            return page_autoinst_addition_2.run(app)