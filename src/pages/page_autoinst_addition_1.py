import logging

import tkinter_templates
from models.page import Page, PageValidationResult
from multilingual import _
from templates.generic_page_layout import GenericPageLayout
from templates.list_view import ListView


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
        from core.autoinst_addition1_logic import (
            get_fallback_langs_and_locales,
            get_langs_and_locales,
        )

        ip_locale = self.state.compatibility.ip_locale
        langs_and_locales = get_langs_and_locales(ip_locale)

        if not langs_and_locales:
            logging.error(
                "No languages/locales loaded - this may be a PyInstaller bundling issue"
            )
            langs_and_locales = get_fallback_langs_and_locales()

        temp_frame = tkinter_templates.FrameContainer(page_frame)
        temp_frame.pack(expand=1, fill="both")
        temp_frame.grid_rowconfigure(0, weight=1)
        temp_frame.columnconfigure(0, weight=1, uniform="cols")
        temp_frame.columnconfigure(1, weight=1, uniform="cols")

        self.lang_list = ListView(
            temp_frame,
            title=_("lang"),
        )

        self.locale_list = ListView(temp_frame, title=_("locale"))

        self.lang_list.grid(
            row=0, column=0, sticky="nsew", padx=5, pady=5, ipady=5, ipadx=5
        )

        self.locale_list.grid(
            row=0, column=1, sticky="nsew", padx=5, pady=5, ipady=5, ipadx=5
        )

        for lang, lang_details in langs_and_locales.items():
            self.lang_list.add_item(
                lang,
                f"{lang_details['names']['english']} ({lang_details['names']['native']})",
            )

        def on_lang_click(*_args):
            self.locale_list.clear()
            selected_lang = self.lang_list.get_selected()
            if selected_lang:
                for locale, locale_details in langs_and_locales[selected_lang][
                    "locales"
                ].items():
                    self.locale_list.add_item(locale, locale_details["names"]["native"])

            self.locale_list.update_scrollbar_visibility()

        self.lang_list.selection_callback = on_lang_click
        self.lang_list.bind("<<ListboxSelect>>", on_lang_click)

        # Initialize kickstart if it doesn't exist
        if not self.state.installation.kickstart:
            from models.kickstart import KickstartConfig

            self.state.installation.kickstart = KickstartConfig()

        kickstart = self.state.installation.kickstart

        from core.autoinst_addition1_logic import get_available_locales

        if not kickstart.locale_settings.locale:
            available_locales = get_available_locales(ip_locale)
            if available_locales:
                kickstart.locale_settings.locale = available_locales[0]
            else:
                kickstart.locale_settings.locale = "en_GB.UTF-8"

        from core.autoinst_addition1_logic import get_language_from_locale

        language = get_language_from_locale(kickstart.locale_settings.locale)

        # Ensure the language exists in langs_and_locales before clicking
        from core.autoinst_addition1_logic import (
            get_fallback_language,
            get_first_locale_for_language,
        )

        if language in langs_and_locales:
            self.lang_list.preselect(language)
            self.update()
            on_lang_click()
            self.locale_list.preselect(kickstart.locale_settings.locale)
            self.lang_list.update_scrollbar_visibility()
        else:
            logging.warning(f"Language '{language}' not found in available languages")
            fallback_lang = get_fallback_language(language, langs_and_locales)
            if fallback_lang:
                logging.info(f"Using fallback language: {fallback_lang}")
                self.lang_list.preselect(fallback_lang)
                self.update()
                on_lang_click()
                first_locale = get_first_locale_for_language(
                    langs_and_locales, fallback_lang
                )
                if first_locale:
                    kickstart.locale_settings.locale = first_locale
                    self.locale_list.preselect(first_locale)
                else:
                    kickstart.locale_settings.locale = "en_US.UTF-8"
                self.lang_list.update_scrollbar_visibility()
            else:
                logging.error("No languages available at all")

    def validate_input(self) -> PageValidationResult:
        """Validate that a locale has been selected."""
        if not hasattr(self, "locale_list"):
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
            kickstart.locale_settings.locale = selected_locale
            logging.info(f"Selected locale: {selected_locale}")

    def on_show(self):
        # If items are seleceted in the treeview, make them visible by updating scrollbar
        if hasattr(self, "locale_list"):
            self.after(1, lambda: self.locale_list.see())
        if hasattr(self, "lang_list"):
            self.after(1, lambda: self.lang_list.see())
