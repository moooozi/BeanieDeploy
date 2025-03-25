from models.page_manager import Page
import autoinst
import libs.langtable as langtable
from templates.generic_page_layout import GenericPageLayout
from templates.list_view import ListView
import globals as GV
import math
import tkinter_templates as tkt
import tkinter.ttk as ttk


class PageAutoinstAddition2(Page):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.set_scaling()  # Set scaling during initialization

    def set_scaling(self):
        scaling_factor = self._get_widget_scaling()
        if scaling_factor > 1:
            scaling_factor = math.ceil(scaling_factor)
        self.tk.call("tk", "scaling", scaling_factor)

    def init_page(self):
        page_layout = GenericPageLayout(
            self,
            self.LN.title_autoinst3,
            self.LN.btn_next,
            lambda: self.next_btn_action(),
            self.LN.btn_back,
            lambda: self.switch_page("PageAutoinstAddition1"),
        )
        page_frame = page_layout.content_frame

        self.selected_locale = GV.KICKSTART.locale

        selected_locale_keymaps = langtable.list_keyboards(
            languageId=GV.KICKSTART.locale
        )
        self.all_keymaps = sorted(langtable.list_all_keyboards())

        selected_locale_timezones = langtable.list_timezones(
            languageId=GV.KICKSTART.locale
        )
        self.all_timezones = sorted(langtable.list_all_timezones())

        temp_frame = ttk.Frame(page_frame)
        temp_frame.pack(expand=1, fill="both")
        temp_frame.grid_rowconfigure(0, weight=1)
        temp_frame.columnconfigure(0, weight=1)
        temp_frame.columnconfigure(1, weight=1)
        keyboard_list_frame = ttk.Frame(temp_frame)
        keyboard_list_frame.grid(row=0, column=0, ipady=5, padx=5, sticky="news")
        timezone_list_frame = ttk.Frame(temp_frame)
        timezone_list_frame.grid(row=0, column=1, ipady=5, padx=5, sticky="news")

        self.keyboard_list = ListView(keyboard_list_frame, title=self.LN.list_keymaps)
        self.keyboard_list.pack(side="left", fill="both", expand=1)

        self.timezone_list = ListView(timezone_list_frame, title=self.LN.list_timezones)
        self.timezone_list.pack(side="left", fill="both", expand=1)

        for keymap in self.all_keymaps:
            self.keyboard_list.add_item(keymap, autoinst.get_keymap_description(keymap))

        for timezone in self.all_timezones:
            self.timezone_list.add_item(
                timezone,
                langtable.timezone_name(timezone, languageIdQuery=GV.KICKSTART.locale),
            )

        default_timezone = (
            selected_locale_timezones[0]
            if not GV.KICKSTART.timezone
            else GV.KICKSTART.timezone
        )
        default_keymap = (
            selected_locale_keymaps[0]
            if not GV.KICKSTART.keymap
            else GV.KICKSTART.keymap
        )

        self.keyboard_list.on_click(default_keymap)
        self.timezone_list.on_click(default_timezone)

    def next_btn_action(self, *args):
        if (
            self.timezone_list.get_selected() not in self.all_timezones
            or self.keyboard_list.get_selected() not in self.all_keymaps
        ):
            return
        GV.KICKSTART.timezone = self.timezone_list.get_selected()
        GV.KICKSTART.keymap = self.keyboard_list.get_selected()
        GV.KICKSTART.keymap_type = "xlayout"
        return self.switch_page("PageAutoinstAddition3")

    def on_show(self):
        if self.selected_locale != GV.KICKSTART.locale:
            tkt.flush_frame(self)
            self.init_page()
