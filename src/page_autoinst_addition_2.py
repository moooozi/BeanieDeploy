from page_manager import Page
import page_autoinst_addition_3
import tkinter.ttk as ttk
import autoinst
import libs.langtable as langtable
import page_autoinst_addition_1
import tkinter_templates as tkt
import globals as GV
import multilingual


class PageAutoinstAddition2(Page):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

    def init_page(self):

        page_frame = tkt.generic_page_layout(
            self,
            self.LN.title_autoinst3,
            self.LN.btn_next,
            lambda: self.next_btn_action(),
            self.LN.btn_back,
            lambda: self.switch_page("PageAutoinstAddition1"),
        )

        selected_locale_keymaps = langtable.list_keyboards(
            languageId=GV.KICKSTART.locale
        )
        all_keymaps = sorted(langtable.list_all_keyboards())

        selected_locale_timezones = langtable.list_timezones(
            languageId=GV.KICKSTART.locale
        )
        all_timezones = sorted(langtable.list_all_timezones())

        temp_frame = ttk.Frame(page_frame)
        temp_frame.pack(expand=1, fill="both")
        temp_frame.grid_rowconfigure(0, weight=1)
        temp_frame.columnconfigure(0, weight=1)
        temp_frame.columnconfigure(1, weight=1)
        keyboard_list_frame = ttk.Frame(temp_frame)
        keyboard_list_frame.grid(row=0, column=0, ipady=5, padx=5, sticky="news")
        timezone_list_frame = ttk.Frame(temp_frame)
        timezone_list_frame.grid(row=0, column=1, ipady=5, padx=5, sticky="news")

        keyboard_list = ttk.Treeview(
            keyboard_list_frame, columns="keyboard", show="headings", height=8
        )
        keyboard_list.heading("keyboard", text=self.LN.list_keymaps)
        keyboard_list.pack(side="left", fill="both", expand=1)
        keyboard_list_scrollbar = ttk.Scrollbar(
            keyboard_list_frame, orient="vertical", command=keyboard_list.yview
        )
        keyboard_list_scrollbar.pack(side="right", fill="y")
        keyboard_list.configure(yscrollcommand=keyboard_list_scrollbar.set)

        timezone_list = ttk.Treeview(
            timezone_list_frame, columns="timezone", show="headings", height=8
        )
        timezone_list.heading("timezone", text=self.LN.list_timezones)
        timezone_list.pack(side="left", fill="both", expand=1)
        timezone_list_scrollbar = ttk.Scrollbar(
            timezone_list_frame, orient="vertical", command=timezone_list.yview
        )
        timezone_list_scrollbar.pack(side="right", fill="y")
        timezone_list.configure(yscrollcommand=timezone_list_scrollbar.set)

        for keymap in all_keymaps:
            keyboard_list.insert(
                parent="",
                index="end",
                iid=keymap,
                values=(autoinst.get_keymap_description(keymap),),
            )

        for timezone in all_timezones:
            timezone_list.insert(
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

        keyboard_list.focus(default_keymap)
        keyboard_list.selection_set(default_keymap)
        keyboard_list.yview_scroll(
            keyboard_list.index(keyboard_list.selection()) - 1, "units"
        )

        timezone_list.focus(default_timezone)
        timezone_list.selection_set(default_timezone)
        timezone_list.yview_scroll(
            timezone_list.index(timezone_list.selection()) - 1, "units"
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
