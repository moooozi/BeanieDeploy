import logging

import customtkinter as ctk

from autoinst import SUPPORTED_LANGS, get_locales_and_langs_sorted_with_names
from core.autoinst_addition1_logic import get_language_from_locale
from models.page import Page, PageValidationResult
from multilingual import _
from services.patched_langtable import langtable
from services.system import get_windows_ui_locale
from templates.ctk_treeview import CTkTreeView


class PageAutoinstAddition1(Page):
    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)

    def init_page(self):
        self.page_manager.set_title(_("title.autoinst2"))

        # Get IP locale from state instead of globals

        ip_locale = self.state.compatibility.ip_locale

        # List of (locale, weight) tuples to help determine best locales
        combined_locale_list = []

        windows_locale = get_windows_ui_locale()
        windows_locale_list = langtable.list_locales(
            concise=True, languageId=windows_locale, show_weights=True
        )

        if ip_locale and ip_locale.country_code:
            ip_locale_list = langtable.list_locales(
                concise=True, territoryId=ip_locale.country_code, show_weights=True
            )
            combined_locale_list = self._combine_locale_lists(
                windows_locale_list, ip_locale_list
            )
        else:
            combined_locale_list = windows_locale_list

        combined_locale_list = self._filter_locale_list_weights(
            combined_locale_list, 100
        )
        combined_locale_list = self._filter_supported_locales(combined_locale_list)
        default_locale = (
            combined_locale_list[0][0] if combined_locale_list else "en_GB.UTF-8"
        )

        langs_and_locales = get_locales_and_langs_sorted_with_names(
            combined_locale_list
        )

        temp_frame = ctk.CTkContainer(self)
        temp_frame.pack(expand=1, fill="both")
        temp_frame.grid_rowconfigure(0, weight=1)
        temp_frame.columnconfigure(0, weight=1, uniform="cols")
        temp_frame.columnconfigure(1, weight=1, uniform="cols")

        self.lang_list = CTkTreeView(
            temp_frame,
            title=_("lang"),
        )

        self.locale_list = CTkTreeView(temp_frame, title=_("locale"))

        self.lang_list.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.locale_list.grid(row=0, column=1, sticky="nsew")

        for lang, lang_details in langs_and_locales.items():
            self.lang_list.insert(
                "",
                "end",
                iid=lang,
                text=f"{lang_details['names']['english']} ({lang_details['names']['native']})",
            )

        def on_lang_click(*_args):
            for item in self.locale_list.get_children():
                self.locale_list.delete(item)
            selected = self.lang_list.selection()
            selected_lang = selected[0] if selected else None
            if selected_lang:
                for locale, locale_details in langs_and_locales[selected_lang][
                    "locales"
                ].items():
                    self.locale_list.insert(
                        "", "end", iid=locale, text=locale_details["names"]["native"]
                    )

            self.locale_list.update_scrollbar_visibility()

        self.lang_list.bind_selection(on_lang_click)
        self.lang_list.bind("<<TreeviewSelect>>", on_lang_click)

        # Initialize kickstart if it doesn't exist
        if not self.state.installation.kickstart:
            from models.kickstart import KickstartConfig

            self.state.installation.kickstart = KickstartConfig()

        kickstart = self.state.installation.kickstart

        if not kickstart.locale_settings.locale:
            kickstart.locale_settings.locale = default_locale

        # Preselect default locale and language
        default_language = get_language_from_locale(default_locale)
        self.lang_list.preselect(default_language)
        self.update()
        on_lang_click()
        self.locale_list.preselect(default_locale)
        self.lang_list.update_scrollbar_visibility()

    def validate_input(self) -> PageValidationResult:
        """Validate that a locale has been selected."""
        if not hasattr(self, "locale_list"):
            return PageValidationResult(False, "Page not properly initialized")

        selected_locale = self.locale_list.selection()[0]
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
        selected_locale = self.locale_list.selection()[0]
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

    def _combine_locale_lists(self, list1: list, list2: list) -> list:
        """Combine two locale lists."""
        # For duplicate keys, combine their weights by summing them
        combined: dict[str, int] = {}
        for locale, weight in list1:
            combined[locale] = combined.get(locale, 0) + weight
        for locale, weight in list2:
            combined[locale] = combined.get(locale, 0) + weight
        # Return sorted by weight descending
        return sorted(combined.items(), key=lambda x: x[1], reverse=True)

    def _filter_locale_list_weights(self, locale_list: list, threshold: int) -> list:
        """Filter locale list by weight threshold."""
        return [
            (locale, weight) for locale, weight in locale_list if weight >= threshold
        ]

    def _filter_supported_locales(self, locale_list: list) -> list:
        """Filter locale list to only include supported locales."""
        return [
            (locale, weight)
            for locale, weight in locale_list
            if get_language_from_locale(locale) in SUPPORTED_LANGS
        ]
