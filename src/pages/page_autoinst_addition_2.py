import logging
import math

import tkinter_templates
import tkinter_templates as tkt
from models.page import Page, PageValidationResult
from multilingual import _
from services.patched_langtable import langtable
from templates.generic_page_layout import GenericPageLayout
from templates.list_view import ListView


class PageAutoinstAddition2(Page):
    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)
        self.set_scaling()  # Set scaling during initialization

    def set_scaling(self):
        scaling_factor = self._get_widget_scaling()
        if scaling_factor > 1:
            scaling_factor = math.ceil(scaling_factor)
        self.tk.call("tk", "scaling", scaling_factor)

    def init_page(self):
        page_layout = GenericPageLayout(
            self,
            _("title.autoinst3"),
            _("btn.next"),
            lambda: self.navigate_next(),
            _("btn.back"),
            lambda: self.navigate_previous(),
        )
        page_frame = page_layout.content_frame

        # Get locale from state instead of globals
        kickstart = self.state.installation.kickstart
        if not kickstart:
            logging.error("No kickstart configuration found")
            return

        self.selected_locale = kickstart.locale_settings.locale

        selected_locale_keymaps = langtable.list_keyboards(
            languageId=kickstart.locale_settings.locale
        )
        self.all_keymaps = sorted(langtable.list_all_keyboards())

        selected_locale_timezones = langtable.list_timezones(
            languageId=kickstart.locale_settings.locale
        )
        self.all_timezones = sorted(langtable.list_all_timezones())

        temp_frame = tkinter_templates.FrameContainer(page_frame)
        temp_frame.pack(expand=1, fill="both")
        temp_frame.grid_rowconfigure(0, weight=1)
        temp_frame.columnconfigure(0, weight=1)
        temp_frame.columnconfigure(1, weight=1)
        keyboard_list_frame = tkinter_templates.FrameContainer(temp_frame)
        keyboard_list_frame.grid(row=0, column=0, ipady=5, padx=5, sticky="news")
        timezone_list_frame = tkinter_templates.FrameContainer(temp_frame)
        timezone_list_frame.grid(row=0, column=1, ipady=5, padx=5, sticky="news")

        self.keyboard_list = ListView(keyboard_list_frame, title=_("list.keymaps"))
        self.keyboard_list.pack(side="left", fill="both", expand=1)

        self.timezone_list = ListView(timezone_list_frame, title=_("list.timezones"))
        self.timezone_list.pack(side="left", fill="both", expand=1)

        for keymap in self.all_keymaps:
            self.keyboard_list.add_item(keymap, keymap)

        for timezone in self.all_timezones:
            timezone_name = langtable.timezone_name(
                timezone, languageIdQuery=kickstart.locale_settings.locale or "en"
            )
            self.timezone_list.add_item(timezone, timezone_name or timezone)

        default_timezone = (
            selected_locale_timezones[0]
            if not kickstart.locale_settings.timezone
            else kickstart.locale_settings.timezone
        )
        default_keymap = (
            selected_locale_keymaps[0]
            if not kickstart.locale_settings.keymap
            else kickstart.locale_settings.keymap
        )

        # Preselect default values
        self.keyboard_list.preselect(default_keymap)
        self.timezone_list.preselect(default_timezone)

    def validate_input(self) -> PageValidationResult:
        """Validate that both timezone and keymap are selected."""
        if not hasattr(self, "timezone_list") or not hasattr(self, "keyboard_list"):
            return PageValidationResult(False, "Page not properly initialized")

        selected_timezone = self.timezone_list.get_selected()
        selected_keymap = self.keyboard_list.get_selected()

        if selected_timezone not in self.all_timezones:
            return PageValidationResult(False, "Please select a valid timezone")

        if selected_keymap not in self.all_keymaps:
            return PageValidationResult(False, "Please select a valid keyboard layout")

        return PageValidationResult(True)

    def on_next(self):
        """Save the selected timezone and keymap to state."""
        kickstart = self.state.installation.kickstart
        if kickstart:
            selected_timezone = self.timezone_list.get_selected()
            selected_keymap = self.keyboard_list.get_selected()

            if selected_timezone:
                kickstart.locale_settings.timezone = selected_timezone
            if selected_keymap:
                kickstart.locale_settings.keymap = selected_keymap
                kickstart.locale_settings.keymap_type = "xlayout"

            logging.info(
                f"Selected timezone:S {kickstart.locale_settings.timezone}, keymap: {kickstart.locale_settings.keymap}"
            )

    def on_show(self):
        """Called when page is shown - reinitialize if locale changed."""
        if hasattr(self, "selected_locale"):
            kickstart = self.state.installation.kickstart
            if kickstart and self.selected_locale != kickstart.locale_settings.locale:
                logging.info("Locale changed, reinitializing page")
                tkt.flush_frame(self)
                self._initiated = False
                self.init_page()
                self._initiated = True
