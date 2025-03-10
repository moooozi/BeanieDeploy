import tkinter.ttk as ttk
import tkinter_templates as tkt
import globals as GV
import multilingual
import functions as fn
from page_manager import Page
import tkinter as tk


class PageAutoinstAddition3(Page):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.fullname = tk.StringVar(parent, GV.KICKSTART.fullname)
        self.username = tk.StringVar(parent, GV.KICKSTART.username)

    def init_page(self):
        # GNOME allows User account creation during initial start tour, so we use that and skip creating a user
        if GV.SELECTED_SPIN.desktop == "GNOME":
            GV.KICKSTART.username = ""
            self.switch_page("PageVerify")
            return

        page_frame = tkt.generic_page_layout(
            self,
            self.LN.title_autoinst4,
            self.LN.btn_next,
            lambda: self.next_btn_action(),
            self.LN.btn_back,
            lambda: self.switch_page("PageAutoinstAddition2"),
        )

        userinfo_frame = tkt.add_frame_container(page_frame)
        fullname_pre = tkt.add_text_label(
            userinfo_frame,
            text=self.LN.entry_fullname,
            font=tkt.FONTS_smaller,
            pack=False,
        )
        self.fullname_entry = ttk.Entry(
            userinfo_frame, width=10, textvariable=self.fullname
        )
        username_pre = tkt.add_text_label(
            userinfo_frame,
            text=self.LN.entry_username,
            font=tkt.FONTS_smaller,
            pack=False,
        )
        self.username_entry = ttk.Entry(
            userinfo_frame, width=10, textvariable=self.username
        )

        fullname_pre.grid(pady=5, padx=(10, 0), column=0, row=0, sticky=self.DI_VAR.w)
        self.fullname_entry.grid(pady=5, padx=5, column=1, row=0)
        username_pre.grid(pady=5, padx=(10, 0), column=0, row=1, sticky=self.DI_VAR.w)
        self.username_entry.grid(pady=5, padx=5, column=1, row=1)
        encrypt_pass_note = tkt.add_text_label(
            userinfo_frame,
            text=self.LN.password_reminder_txt,
            font=tkt.FONTS_smaller,
            foreground=tkt.color_blue,
            pack=False,
        )
        encrypt_pass_note.grid(
            pady=5, padx=(10, 0), column=0, columnspan=5, row=2, sticky=self.DI_VAR.nw
        )

        validation_func = self.register(
            lambda var: fn.validate_with_regex(var, valid_username_regex) is True
        )
        self.username_entry.config(
            validate="none", validatecommand=(validation_func, "%P")
        )
        # Regex
        portable_fs_chars = r"a-zA-Z0-9._-"
        _name_base = (
            r"[a-zA-Z0-9._]["
            + portable_fs_chars
            + r"]{0,30}(["
            + portable_fs_chars
            + r"]|\$)?"
        )
        valid_username_regex = (
            r"^" + _name_base + "$"
        )  # A regex for user and group names.

        tkt.var_tracer(
            self.username, "write", lambda *args: self.username_entry.validate()
        )

    def next_btn_action(self, *args):
        self.username_entry.validate()
        syntax_invalid = "invalid" in self.username_entry.state()
        if syntax_invalid:
            return -1
        GV.KICKSTART.username = self.username_entry.get()
        GV.KICKSTART.fullname = self.fullname_entry.get()

        self.switch_page("PageVerify")
