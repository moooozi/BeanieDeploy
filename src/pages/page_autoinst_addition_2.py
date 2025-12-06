import logging
import math

import customtkinter as ctk

from models.page import Page, PageValidationResult
from multilingual import _
from services.patched_langtable import keyboards_db, langtable
from services.system import (
    get_current_windows_timezone,
    get_current_windows_timezone_iana,
    get_windows_timezone_from_iana,
)
from templates.ctk_treeview import CTkTreeView


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
        self.page_manager.set_title(_("title.autoinst3"))

        page_frame = self

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

        self.all_timezones = sorted(langtable.list_all_timezones())

        temp_frame = ctk.CTkContainer(page_frame)
        temp_frame.pack(expand=1, fill="both")
        temp_frame.grid_rowconfigure(0, weight=1)
        temp_frame.columnconfigure(0, weight=1, uniform="cols")
        temp_frame.columnconfigure(1, weight=1, uniform="cols")

        self.keyboard_list = CTkTreeView(
            temp_frame, title=_("list.keymaps"), multi_select=True
        )

        self.timezone_list = CTkTreeView(temp_frame, title=_("list.timezones"))

        self.keyboard_list.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.timezone_list.grid(row=0, column=1, sticky="nsew")
        # Sort keymaps by description alphabetically
        keymaps_sorted = sorted(
            self.all_keymaps, key=lambda k: keyboards_db[k].description.lower()
        )

        for keymap in keymaps_sorted:
            self.keyboard_list.insert(
                "", "end", iid=keymap, text=keyboards_db[keymap].description
            )

        for timezone in self.all_timezones:
            timezone_name = langtable.timezone_name(
                timezone, languageIdQuery=kickstart.locale_settings.locale or "en"
            )
            self.timezone_list.insert(
                "", "end", iid=timezone, text=timezone_name or timezone
            )

        # IP timezone in IANA format
        ip_timezone = (
            self.state.compatibility.ip_locale.time_zone
            if self.state.compatibility.ip_locale is not None
            and hasattr(self.state.compatibility.ip_locale, "time_zone")
            else None
        )

        # Determine default timezone
        if ip_timezone:
            ip_windows_tz = get_windows_timezone_from_iana(ip_timezone)
            current_windows_tz = get_current_windows_timezone()
            if (
                ip_windows_tz
                and current_windows_tz
                and ip_windows_tz == current_windows_tz
            ):
                default_timezone = ip_timezone
            else:
                default_timezone = get_current_windows_timezone_iana()
        else:
            default_timezone = get_current_windows_timezone_iana()

        default_keymap = (
            selected_locale_keymaps[0]
            if not kickstart.locale_settings.keymaps
            else kickstart.locale_settings.keymaps[0]
        )

        # Preselect default values
        if kickstart.locale_settings.keymaps:
            self.keyboard_list.selection_set(kickstart.locale_settings.keymaps)
        else:
            self.keyboard_list.preselect(default_keymap)
        self.timezone_list.preselect(default_timezone)

    def validate_input(self) -> PageValidationResult:
        """Validate that both timezone and keymap are selected."""
        if not hasattr(self, "timezone_list") or not hasattr(self, "keyboard_list"):
            return PageValidationResult(False, "Page not properly initialized")

        selected_timezone = self.timezone_list.selection()[0]
        selected_keymaps = self.keyboard_list.selection()

        if selected_timezone not in self.all_timezones:
            return PageValidationResult(False, "Please select a valid timezone")

        if any(keymap not in self.all_keymaps for keymap in selected_keymaps):
            return PageValidationResult(False, "Please select a valid keyboard layout")

        return PageValidationResult(True)

    def on_next(self):
        """Save the selected timezone and keymap to state."""
        kickstart = self.state.installation.kickstart
        if kickstart:
            selected_timezone = self.timezone_list.selection()[0]
            selected_keymaps = list(self.keyboard_list.selection())

            if selected_timezone:
                kickstart.locale_settings.timezone = selected_timezone
            if selected_keymaps:
                kickstart.locale_settings.keymaps = selected_keymaps
                kickstart.locale_settings.keymap_type = "xlayout"

            logging.info(
                f"Selected timezone: {kickstart.locale_settings.timezone}, keymaps: {kickstart.locale_settings.keymaps}"
            )

    def on_show(self):
        """Called when page is shown - reinitialize if locale changed."""
        if hasattr(self, "selected_locale"):
            kickstart = self.state.installation.kickstart
            if kickstart and self.selected_locale != kickstart.locale_settings.locale:
                logging.info("Locale changed, reinitializing page")
                for widget in self.winfo_children():
                    widget.destroy()
                self._initiated = False
                self.init_page()
                self._initiated = True
        # If items are seleceted in the treeview, make them visible by updating scrollbar
        if hasattr(self, "keyboard_list"):
            self.after(1, lambda: self.keyboard_list.see())
        if hasattr(self, "timezone_list"):
            self.after(1, lambda: self.timezone_list.see())
