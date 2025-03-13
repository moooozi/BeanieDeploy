from templates.generic_page_layout import GenericPageLayout
import tkinter_templates as tkt
import globals as GV
from models.page_manager import Page
import tkinter as tk
import customtkinter as ctk


class PageAutoinst2(Page):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.enable_encryption_toggle_var = tk.BooleanVar(
            parent, GV.KICKSTART.is_encrypted
        )

        self.export_wifi_toggle_var = tk.BooleanVar(
            parent, GV.INSTALL_OPTIONS.export_wifi
        )

    def init_page(self):
        page_layout = GenericPageLayout(
            self,
            self.LN.windows_question % GV.SELECTED_SPIN.name,
            self.LN.btn_next,
            lambda: self.next_btn_action(),
            self.LN.btn_back,
            lambda: self.switch_page("PageInstallMethod"),
        )
        page_frame = page_layout.content_frame
        frame_checkboxes = ctk.CTkFrame(
            page_frame,
            bg_color="transparent",
            fg_color="transparent",
            corner_radius=0,
            border_width=0,
        )
        frame_checkboxes.grid(row=0, column=0, sticky="ew")
        page_frame.grid_columnconfigure(0, weight=1)
        page_frame.grid_rowconfigure(0, weight=1)

        check_wifi = tkt.add_check_btn(
            frame_checkboxes,
            self.LN.add_import_wifi % GV.SELECTED_SPIN.name,
            self.export_wifi_toggle_var,
            pady=(5, 0),
            pack=False,
        )
        check_wifi.grid(ipady=5, row=0, column=0, sticky=self.DI_VAR.w)

        check_encrypt = tkt.add_check_btn(
            frame_checkboxes,
            self.LN.encrypted_root,
            self.enable_encryption_toggle_var,
            lambda: self.show_encrypt_options(self.enable_encryption_toggle_var),
            pack=False,
        )
        check_encrypt.grid(ipady=5, row=2, column=0, sticky=self.DI_VAR.w)

        self.encrypt_pass_note = ctk.CTkLabel(
            frame_checkboxes,
            wraplength=GV.MAX_WIDTH,
            justify=self.DI_VAR.l,
            text=self.LN.encrypt_reminder_txt,
            font=tkt.FONTS_smaller,
            text_color=tkt.color_blue,
        )
        self.encrypt_pass_note.grid(
            pady=5, padx=(0, 0), row=2, column=1, sticky=self.DI_VAR.w
        )
        self.encrypt_pass_note.grid_remove()

        self.show_encrypt_options(self.enable_encryption_toggle_var)

    def show_encrypt_options(self, var):
        if var.get():
            self.encrypt_pass_note.grid()
        else:
            self.encrypt_pass_note.grid_remove()

    def next_btn_action(self, *args):
        GV.KICKSTART.is_encrypted = self.enable_encryption_toggle_var.get()
        GV.INSTALL_OPTIONS.export_wifi = self.export_wifi_toggle_var.get()
        self.switch_page("PageAutoinstAddition1")
