import tkinter.ttk as ttk
import tkinter_templates as tkt
import globals as GV
import multilingual
import page_1
import logging
import multilingual

def run(app):
    """the page on which you choose which distro/flaver and whether Autoinstall should be on or off"""
    tkt.init_frame(app)
    global LN, DI_VAR
    LN = multilingual.get_lang()
    DI_VAR = multilingual.get_di_var()
    # *************************************************************************************************************
    page_frame = tkt.generic_page_layout(app, LN.lang_question, LN.btn_next, lambda: next_btn_action())

    frame_lang = tkt.add_frame_container(page_frame, fill='both', expand=1)
    lang_list_pre = tkt.add_text_label(frame_lang, text=LN.lang + ': ',font=tkt.FONTS_smaller, pack=False)
    lang_list = ttk.Combobox(frame_lang, values=list(multilingual.available_languages.keys()), state='readonly')
    lang_list.bind("<<ComboboxSelected>>", lambda *args: set_lang())

    lang_list.set(multilingual.get_current_lang())

    lang_list_pre.grid(pady=5, padx=(10, 0), column=0, row=0, sticky=DI_VAR['w'])
    lang_list.grid(ipady=5, padx=(30, 0), row=0, column=1, columnspan=2,sticky=DI_VAR['nw'])
    
    def set_lang():
        DI_VAR, GV.language_file = multilingual.set_lang(lang_list.get())
        run(app)


    def next_btn_action(*args):
        return page_1.run(app)
