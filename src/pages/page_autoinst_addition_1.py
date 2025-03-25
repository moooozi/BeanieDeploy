from models.page_manager import Page
import tkinter.ttk as ttk
import autoinst
from templates.generic_page_layout import GenericPageLayout
from templates.list_view import ListView
import tkinter_templates as tkt
import globals as GV
import libs.langtable as langtable


class PageAutoinstAddition1(Page):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

    def init_page(self):
        page_layout = GenericPageLayout(
            self,
            self.LN.title_autoinst2,
            self.LN.btn_next,
            lambda: self.next_btn_action(),
            self.LN.btn_back,
            lambda: self.switch_page("PageAutoinst2"),
        )
        page_frame = page_layout.content_frame

        if GV.IP_LOCALE:
            langs_and_locales = autoinst.get_locales_and_langs_sorted_with_names(
                territory=GV.IP_LOCALE["country_code"]
            )
        else:
            langs_and_locales = autoinst.get_locales_and_langs_sorted_with_names()

        temp_frame = ttk.Frame(page_frame)
        temp_frame.pack(expand=1, fill="both")
        temp_frame.grid_rowconfigure(0, weight=1)
        temp_frame.columnconfigure(0, weight=1)
        temp_frame.columnconfigure(1, weight=1)
        lang_list_frame = ttk.Frame(temp_frame)
        lang_list_frame.grid(row=0, column=0, ipady=5, padx=5, sticky="news")
        locale_list_frame = ttk.Frame(temp_frame)
        locale_list_frame.grid(row=0, column=1, ipady=5, padx=5, sticky="news")

        lang_list = ListView(
            lang_list_frame,
            title=self.LN.lang,
        )
        lang_list.selection_callback = lambda *arg: on_lang_click()
        lang_list.pack(side="left", fill="both", expand=1)

        self.locale_list = ListView(locale_list_frame, title=self.LN.locale)
        self.locale_list.pack(side="left", fill="both", expand=1)

        for lang, lang_details in langs_and_locales.items():
            lang_list.add_item(
                lang,
                f"{lang_details['names']['english']} ({lang_details['names']['native']})",
            )

        def on_lang_click(*args):
            self.locale_list.clear()
            selected_lang = lang_list.get_selected()
            if selected_lang:
                for locale, locale_details in langs_and_locales[selected_lang][
                    "locales"
                ].items():
                    self.locale_list.add_item(locale, locale_details["names"]["native"])

        lang_list.bind("<<ListboxSelect>>", on_lang_click)

        if not GV.KICKSTART.locale:
            if GV.IP_LOCALE:
                GV.KICKSTART.locale = langtable.list_locales(
                    territoryId=GV.IP_LOCALE["country_code"]
                )[0]
            else:
                GV.KICKSTART.locale = "en_GB.UTF-8"

        language = autoinst.langtable.parse_locale(GV.KICKSTART.locale).language
        lang_list.on_click(language)
        self.update()
        on_lang_click()
        self.locale_list.on_click(GV.KICKSTART.locale)

    def next_btn_action(self, *args):
        locale = self.locale_list.get_selected()
        if autoinst.langtable.parse_locale(locale).language:
            GV.KICKSTART.locale = locale
            self.switch_page("PageAutoinstAddition2")
