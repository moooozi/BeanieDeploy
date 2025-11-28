from models.page import Page, PageValidationResult
from templates.generic_page_layout import GenericPageLayout
from templates.list_view import ListView
import tkinter_templates 
from multilingual import _

class PageAutoinstAddition1(Page):
    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)

    def init_page(self):
        page_layout = GenericPageLayout(
            self,
            _("title.autoinst2"),
            _("btn.next"),
            lambda: self.navigate_next(),
            _("btn.back"),
            lambda: self.navigate_previous(),
        )
        page_frame = page_layout.content_frame

        # Get IP locale from state instead of globals
        from core.autoinst_addition1_logic import get_langs_and_locales, get_fallback_langs_and_locales
        ip_locale = self.state.compatibility.ip_locale
        langs_and_locales = get_langs_and_locales(ip_locale)

        # Debug logging for PyInstaller bundle issues
        self.logger.debug(f"Available languages: {list(langs_and_locales.keys())}")
        if not langs_and_locales:
            self.logger.error("No languages/locales loaded - this may be a PyInstaller bundling issue")
            langs_and_locales = get_fallback_langs_and_locales()

        temp_frame = tkinter_templates.FrameContainer(page_frame)
        temp_frame.pack(expand=1, fill="both")
        temp_frame.grid_rowconfigure(0, weight=1)
        temp_frame.columnconfigure(0, weight=1)
        temp_frame.columnconfigure(1, weight=1)
        lang_list_frame = tkinter_templates.FrameContainer(temp_frame)
        lang_list_frame.grid(row=0, column=0, ipady=5, padx=5, sticky="news")
        locale_list_frame = tkinter_templates.FrameContainer(temp_frame)
        locale_list_frame.grid(row=0, column=1, ipady=5, padx=5, sticky="news")

        lang_list = ListView(
            lang_list_frame,
            title=_("lang"),
        )
        lang_list.selection_callback = lambda *arg: on_lang_click()
        lang_list.pack(side="left", fill="both", expand=1)

        self.locale_list = ListView(locale_list_frame, title=_("locale"))
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
            from models.kickstart import KickstartConfig
            self.state.installation.kickstart = KickstartConfig()
        
        kickstart = self.state.installation.kickstart
        
        from core.autoinst_addition1_logic import get_available_locales
        if not kickstart.locale.locale:
            available_locales = get_available_locales(ip_locale)
            if available_locales:
                kickstart.locale.locale = available_locales[0]
            else:
                kickstart.locale.locale = "en_GB.UTF-8"

        from core.autoinst_addition1_logic import get_language_from_locale
        language = get_language_from_locale(kickstart.locale.locale)
        
        # Ensure the language exists in langs_and_locales before clicking
        from core.autoinst_addition1_logic import get_fallback_language, get_first_locale_for_language
        if language in langs_and_locales:
            lang_list.on_click(language)
            self.update()
            on_lang_click()
            self.locale_list.on_click(kickstart.locale.locale)
        else:
            self.logger.warning(f"Language '{language}' not found in available languages")
            fallback_lang = get_fallback_language(language, langs_and_locales)
            if fallback_lang:
                self.logger.info(f"Using fallback language: {fallback_lang}")
                lang_list.on_click(fallback_lang)
                self.update()
                on_lang_click()
                first_locale = get_first_locale_for_language(langs_and_locales, fallback_lang)
                if first_locale:
                    kickstart.locale.locale = first_locale
                    self.locale_list.on_click(first_locale)
                else:
                    kickstart.locale.locale = "en_US.UTF-8"
            else:
                self.logger.error("No languages available at all")

    def validate_input(self) -> PageValidationResult:
        """Validate that a locale has been selected."""
        if not hasattr(self, 'locale_list'):
            return PageValidationResult(False, "Page not properly initialized")
            
        selected_locale = self.locale_list.get_selected()
        if not selected_locale:
            return PageValidationResult(False, "Please select a locale")
            
        # Validate that the selected locale is parseable
        from core.autoinst_addition1_logic import validate_locale
        valid, error = validate_locale(selected_locale)
        if not valid:
            return PageValidationResult(False, error)
        return PageValidationResult(True)

    def on_next(self):
        """Save the selected locale to state."""
        selected_locale = self.locale_list.get_selected()
        kickstart = self.state.installation.kickstart
        if kickstart and selected_locale:
            kickstart.locale.locale = selected_locale
            self.logger.info(f"Selected locale: {selected_locale}")
