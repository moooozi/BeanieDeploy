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
    tkt.clear_frame(MID_FRAME)
    # *************************************************************************************************************
    tkt.generic_page_layout(MID_FRAME, LN.windows_question % GV.SELECTED_SPIN.name,
                            LN.btn_next, lambda: next_btn_action(),
                            LN.btn_back, lambda: page_install_method.run())

    # tkt.add_check_btn(MID_FRAME, LN.additional_setup_now, vAutoinst_additional_setup_t)
    export_wifi_toggle_var = tk.BooleanVar(app, GV.INSTALL_OPTIONS.export_wifi)
    enable_encryption_toggle_var = tk.BooleanVar(app, GV.KICKSTART.is_encrypted)
    encrypt_passphrase_var = tk.StringVar(app, GV.KICKSTART.passphrase)
    encryption_tpm_unlock_toggle_var = tk.BooleanVar(app, GV.KICKSTART.tpm_auto_unlock)

    tkt.add_check_btn(MID_FRAME, LN.add_import_wifi, export_wifi_toggle_var, pady=(5, 0))
    tkt.add_check_btn(MID_FRAME, LN.encrypted_root, enable_encryption_toggle_var,
                      lambda: show_encrypt_options(enable_encryption_toggle_var))

    only_digit_regex = r'^[0-9]+$'  # digits
    entry2_frame = ttk.Frame(MID_FRAME)

    encrypt_pass_pre = ttk.Label(entry2_frame, wraplength=540, justify=GV.UI.DI_VAR['l'],
                                 text=LN.entry_encrypt_passphrase_pre, font=tkt.FONTS.tiny)
    encrypt_passphrase_entry = ttk.Entry(entry2_frame, show="\u2022", width=10, textvariable=encrypt_passphrase_var)
    tkt.var_tracer(encrypt_passphrase_var, "write",
                   lambda *args: fn.validate_with_regex(encrypt_passphrase_var,
                                                        regex=only_digit_regex, mode='fix'))
    pass_confirm_var = tk.StringVar()
    encrypt_pass_confirm_pre = ttk.Label(entry2_frame, wraplength=540, justify=GV.UI.DI_VAR['l'],
                                         text=LN.entry_encrypt_passphrase_confirm_pre, font=tkt.FONTS.tiny)
    encrypt_pass_confirm_entry = ttk.Entry(entry2_frame, show="\u2022", width=10, textvariable=pass_confirm_var)
    encrypt_pass_confirm_not_matched = ttk.Label(entry2_frame, wraplength=540, justify=GV.UI.DI_VAR['l'],
                                                 text=LN.not_matched, font=tkt.FONTS.tiny, foreground='#ff4a4a')
    tpm_unlock = tkt.add_check_btn(entry2_frame, LN.encryption_tpm_unlock, encryption_tpm_unlock_toggle_var, pack=False)

    tkt.var_tracer(pass_confirm_var, "write",
                   lambda *args:
                   show_not_matched_warning(pass_confirm_var.get() != encrypt_passphrase_var.get()))

    encrypt_pass_pre.grid(column=0, row=0, sticky=GV.UI.DI_VAR['w'])
    encrypt_passphrase_entry.grid(pady=2, padx=5, column=1, row=0)
    encrypt_pass_confirm_pre.grid(column=0, row=1, sticky=GV.UI.DI_VAR['w'])
    encrypt_pass_confirm_entry.grid(pady=2, padx=5, column=1, row=1)
    tpm_unlock.grid(column=0, row=2, sticky=GV.UI.DI_VAR['w'])

    # LOGIC
    def show_not_matched_warning(is_true: bool):
        if is_true:
            encrypt_pass_confirm_not_matched.grid(pady=5, padx=(0, 0), column=2, row=1, sticky=GV.UI.DI_VAR['w'])
        else:
            encrypt_pass_confirm_not_matched.grid_forget()

    def show_encrypt_options(var):
        if var.get():
            entry2_frame.pack(fill='x', padx=(40, 0))
        else:
            entry2_frame.pack_forget()

    show_encrypt_options(enable_encryption_toggle_var)

    def next_btn_action(*args):
        if enable_encryption_toggle_var.get() and not (encrypt_passphrase_var.get() == pass_confirm_var.get() != ''):
            return
        else:
            GV.INSTALL_OPTIONS.export_wifi = export_wifi_toggle_var.get()
            GV.KICKSTART.is_encrypted = enable_encryption_toggle_var.get()
            GV.KICKSTART.passphrase = encrypt_passphrase_var.get()
            GV.KICKSTART.tpm_auto_unlock = encryption_tpm_unlock_toggle_var.get()
            page_autoinst_addition_1.run()
