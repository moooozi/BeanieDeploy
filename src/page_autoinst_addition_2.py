from page_manager import Page
import tkinter.ttk as ttk
import autoinst
import libs.langtable as langtable
from templates.generic_page_layout import GenericPageLayout
import globals as GV
import math


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

        self.keyboard_list = ttk.Treeview(
            keyboard_list_frame, columns="keyboard", show="headings", height=8
        )
        self.keyboard_list.heading("keyboard", text=self.LN.list_keymaps)
        self.keyboard_list.pack(side="left", fill="both", expand=1)
        keyboard_list_scrollbar = ttk.Scrollbar(
            keyboard_list_frame, orient="vertical", command=self.keyboard_list.yview
        )
        keyboard_list_scrollbar.pack(side="right", fill="y")
        self.keyboard_list.configure(yscrollcommand=keyboard_list_scrollbar.set)

        self.timezone_list = ttk.Treeview(
            timezone_list_frame, columns="timezone", show="headings", height=8
        )
        self.timezone_list.heading("timezone", text=self.LN.list_timezones)
        self.timezone_list.pack(side="left", fill="both", expand=1)
        timezone_list_scrollbar = ttk.Scrollbar(
            timezone_list_frame, orient="vertical", command=self.timezone_list.yview
        )
        timezone_list_scrollbar.pack(side="right", fill="y")
        self.timezone_list.configure(yscrollcommand=timezone_list_scrollbar.set)

        for keymap in self.all_keymaps:
            self.keyboard_list.insert(
                parent="",
                index="end",
                iid=keymap,
                values=(autoinst.get_keymap_description(keymap),),
            )

        for timezone in self.all_timezones:
            self.timezone_list.insert(
                parent="",
                index="end",
                iid=timezone,
                values=(
                    langtable.timezone_name(
                        timezone, languageIdQuery=GV.KICKSTART.locale
                    ),
                ),
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

        self.keyboard_list.focus(default_keymap)
        self.keyboard_list.selection_set(default_keymap)
        self.keyboard_list.yview_scroll(
            self.keyboard_list.index(self.keyboard_list.selection()) - 1, "units"
        )

        self.timezone_list.focus(default_timezone)
        self.timezone_list.selection_set(default_timezone)
        self.timezone_list.yview_scroll(
            self.timezone_list.index(self.timezone_list.selection()) - 1, "units"
        )

    def next_btn_action(self, *args):
        if (
            self.timezone_list.focus() not in self.all_timezones
            or self.keyboard_list.focus() not in self.all_keymaps
        ):
            return
        GV.KICKSTART.timezone = self.timezone_list.focus()
        GV.KICKSTART.keymap = self.keyboard_list.focus()
        GV.KICKSTART.keymap_type = "xlayout"
        return self.switch_page("PageAutoinstAddition3")
