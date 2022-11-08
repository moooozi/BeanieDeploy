import tkinter.ttk as ttk

import page_autoinst_addition_1
import tkinter_templates as tkt
import globals as GV
import translations.en as LN
from init import MID_FRAME
import page_install_method
import global_tk_vars as tk_var


def run():
    """the autoinstall page on which you choose whether to install alongside windows or start clean install"""
    tkt.init_frame(MID_FRAME)
    # *************************************************************************************************************
    page_frame = tkt.generic_page_layout(MID_FRAME, LN.windows_question % GV.SELECTED_SPIN.name,
                                         LN.btn_next, lambda: next_btn_action(),
                                         LN.btn_back, lambda: page_install_method.run())

    # tkt.add_check_btn(page_frame, LN.additional_setup_now, vAutoinst_additional_setup_t)

    tkt.add_check_btn(page_frame, LN.add_import_wifi, tk_var.export_wifi_toggle_var, pady=(5, 0))
    tkt.add_check_btn(page_frame, LN.encrypted_root, tk_var.enable_encryption_toggle_var,
                      lambda: show_encrypt_options(tk_var.enable_encryption_toggle_var))

    frame_encryption_options = ttk.Frame(page_frame)

    encrypt_pass_note = ttk.Label(frame_encryption_options, wraplength=GV.UI.width, justify=GV.UI.DI_VAR['l'], text=LN.encrypt_reminder_txt, font=tkt.FONTS_smaller, foreground=tkt.color_blue)
    encrypt_pass_note.grid(pady=5, padx=(0, 0), column=0, columnspan=5, row=1, sticky=GV.UI.DI_VAR['w'])

    # LOGIC
    def show_encrypt_options(var):
        if var.get():
            frame_encryption_options.pack(fill='x', padx=(40, 0))
        else:
            frame_encryption_options.pack_forget()

    show_encrypt_options(tk_var.enable_encryption_toggle_var)

    def next_btn_action(*args):
        page_autoinst_addition_1.run()
