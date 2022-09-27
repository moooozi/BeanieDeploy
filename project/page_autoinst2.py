import tkinter as tk
import tkinter.ttk as ttk

import page_autoinst_addition_1
import tkinter_templates as tkt
import globals as GV
import translations.en as LN
import functions as fn
from init import app, MID_FRAME
import page_install_method


def run():
    """the autoinstall page on which you choose whether to install alongside windows or start clean install"""
    tkt.init_frame(MID_FRAME)
    # *************************************************************************************************************
    page_frame = tkt.generic_page_layout(MID_FRAME, LN.windows_question % GV.SELECTED_SPIN.name,
                            LN.btn_next, lambda: next_btn_action(),
                            LN.btn_back, lambda: page_install_method.run())

    # tkt.add_check_btn(page_frame, LN.additional_setup_now, vAutoinst_additional_setup_t)
    export_wifi_toggle_var = tk.BooleanVar(app, GV.INSTALL_OPTIONS.export_wifi)
    enable_encryption_toggle_var = tk.BooleanVar(app, GV.KICKSTART.is_encrypted)
    encrypt_passphrase_var = tk.StringVar(app, GV.KICKSTART.passphrase)
    encryption_tpm_unlock_toggle_var = tk.BooleanVar(app, GV.KICKSTART.tpm_auto_unlock)

    tkt.add_check_btn(page_frame, LN.add_import_wifi, export_wifi_toggle_var, pady=(5, 0))
    tkt.add_check_btn(page_frame, LN.encrypted_root, enable_encryption_toggle_var,
                      lambda: show_encrypt_options(enable_encryption_toggle_var))

    frame_encryption_options = ttk.Frame(page_frame)

    encrypt_pass_pre = ttk.Label(frame_encryption_options, justify=GV.UI.DI_VAR['l'],
                                 text=LN.entry_encrypt_passphrase_pre, font=tkt.FONTS_smaller)
    encrypt_passphrase_entry = ttk.Entry(frame_encryption_options, show="\u2022", width=10, textvariable=encrypt_passphrase_var)
    pass_confirm_var = tk.StringVar()
    encrypt_pass_confirm_pre = ttk.Label(frame_encryption_options, justify=GV.UI.DI_VAR['l'],
                                         text=LN.entry_encrypt_passphrase_confirm_pre, font=tkt.FONTS_smaller)
    encrypt_pass_confirm_entry = ttk.Entry(frame_encryption_options, show="\u2022", width=10, textvariable=pass_confirm_var)
    encrypt_pass_confirm_not_matched = ttk.Label(frame_encryption_options, justify=GV.UI.DI_VAR['l'],
                                                 text=LN.not_matched, font=tkt.FONTS_smaller, foreground=tkt.light_red)
    encrypt_pass_note = ttk.Label(frame_encryption_options, wraplength=GV.UI.width, justify=GV.UI.DI_VAR['l'],
                                  text=LN.encrypt_reminder_txt, font=tkt.FONTS_smaller, foreground=tkt.light_blue)
    tpm_unlock = tkt.add_check_btn(frame_encryption_options, LN.encryption_tpm_unlock, encryption_tpm_unlock_toggle_var, pack=False)

    tkt.var_tracer(pass_confirm_var, "write",
                   lambda *args:
                   show_not_matched_warning(pass_confirm_var.get() != encrypt_passphrase_var.get()))

    encrypt_pass_pre.grid(column=0, row=0, sticky=GV.UI.DI_VAR['w'])
    encrypt_passphrase_entry.grid(pady=3, padx=5, column=1, row=0, sticky=GV.UI.DI_VAR['w'])
    encrypt_pass_confirm_pre.grid(column=2, row=0, sticky=GV.UI.DI_VAR['w'])
    encrypt_pass_confirm_entry.grid(pady=3, padx=5, column=3, row=0, sticky=GV.UI.DI_VAR['w'])
    encrypt_pass_note.grid(pady=5, padx=(0, 0), column=0, columnspan=5, row=1, sticky=GV.UI.DI_VAR['w'])
    # tpm_unlock.grid(pady=3, column=0, row=2, sticky=GV.UI.DI_VAR['w'])

    # LOGIC
    def show_not_matched_warning(is_true: bool):
        if is_true:
            encrypt_pass_confirm_not_matched.grid(pady=5, padx=(0, 0), column=4, columnspan=2, row=0, sticky=GV.UI.DI_VAR['w'])
        else:
            encrypt_pass_confirm_not_matched.grid_forget()

    def show_encrypt_options(var):
        if var.get():
            frame_encryption_options.pack(fill='x', padx=(40, 0))
        else:
            frame_encryption_options.pack_forget()

    show_encrypt_options(enable_encryption_toggle_var)

    def next_btn_action(*args):
        if enable_encryption_toggle_var.get() and not (encrypt_passphrase_var.get() == pass_confirm_var.get()):
            return
        else:
            GV.INSTALL_OPTIONS.export_wifi = export_wifi_toggle_var.get()
            GV.KICKSTART.is_encrypted = enable_encryption_toggle_var.get()
            GV.KICKSTART.passphrase = encrypt_passphrase_var.get()
            GV.KICKSTART.tpm_auto_unlock = encryption_tpm_unlock_toggle_var.get()
            page_autoinst_addition_1.run()
