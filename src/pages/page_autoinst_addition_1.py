from models.page import Page, PageValidationResult
import tkinter.ttk as ttk
import autoinst
from templates.generic_page_layout import GenericPageLayout
from templates.list_view import ListView
import langtable


class PageAutoinstAddition1(Page):
    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)

    def init_page(self):
        page_layout = GenericPageLayout(
            self,
            self.LN.title_autoinst2,
            self.LN.btn_next,
            lambda: self.navigate_next(),
            self.LN.btn_back,
            lambda: self.navigate_previous(),
        )
        page_frame = page_layout.content_frame

        # Get IP locale from state instead of globals
        ip_locale = self.state.compatibility.ip_locale
        if ip_locale:
            langs_and_locales = autoinst.get_locales_and_langs_sorted_with_names(
                territory=ip_locale["country_code"]
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

        # Initialize kickstart if it doesn't exist
        if not self.state.installation.kickstart:
            from models.kickstart import Kickstart
            self.state.installation.kickstart = Kickstart()
        
        kickstart = self.state.installation.kickstart
        
        if not kickstart.locale:
            if ip_locale:
                kickstart.locale = langtable.list_locales(
                    territoryId=ip_locale["country_code"]
                )[0]
            else:
                kickstart.locale = "en_GB.UTF-8"

        language = autoinst.langtable.parse_locale(kickstart.locale).language
        lang_list.on_click(language)
        self.update()
        on_lang_click()
        self.locale_list.on_click(kickstart.locale)

    def validate_input(self) -> PageValidationResult:
        """Validate that a locale has been selected."""
        if not hasattr(self, 'locale_list'):
            return PageValidationResult(False, "Page not properly initialized")
            
        selected_locale = self.locale_list.get_selected()
        if not selected_locale:
            return PageValidationResult(False, "Please select a locale")
            
        # Validate that the selected locale is parseable
        try:
            parsed = autoinst.langtable.parse_locale(selected_locale)
            if not parsed.language:
                return PageValidationResult(False, "Selected locale is invalid")
        except Exception as e:
            return PageValidationResult(False, f"Invalid locale format: {str(e)}")
            
        return PageValidationResult(True)

    def on_next(self):
        """Save the selected locale to state."""
        selected_locale = self.locale_list.get_selected()
        kickstart = self.state.installation.kickstart
        if kickstart and selected_locale:
            kickstart.locale = selected_locale
            self.logger.info(f"Selected locale: {selected_locale}")
