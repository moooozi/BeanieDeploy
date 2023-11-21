import tkinter.ttk as ttk

import page_autoinst_addition_1
import tkinter_templates as tkt
import globals as GV
import multilingual
import page_install_method
import global_tk_vars as tk_var


def run(app):
    """the autoinstall page on which you choose whether to install alongside windows or start clean install"""
    tkt.init_frame(app)
    global LN, DI_VAR
    LN = multilingual.get_lang()
    DI_VAR = multilingual.get_di_var()
    # *************************************************************************************************************
    page_frame = tkt.generic_page_layout(app, LN.windows_question % GV.SELECTED_SPIN.name,
                                         LN.btn_next, lambda: next_btn_action(),
                                         LN.btn_back, lambda: page_install_method.run(app))

    frame_checkboxes = tkt.add_frame_container(page_frame)
    # tkt.add_check_btn(page_frame, LN.additional_setup_now, vAutoinst_additional_setup_t)

    check_wifi = tkt.add_check_btn(frame_checkboxes, LN.add_import_wifi % GV.SELECTED_SPIN.name,
                                   tk_var.export_wifi_toggle_var, pady=(5, 0),pack=False)
    check_wifi.grid(ipady=5, row=0, column=0, sticky=DI_VAR['nw'])

    check_rpm_fusion = tkt.add_check_btn(frame_checkboxes, LN.enable_rpm_fusion, tk_var.rpm_fusion_toggle_var,
                                         pady=(5, 0), pack=False)
    check_rpm_fusion.grid(ipady=5, row=1, column=0, sticky=DI_VAR['nw'])

    check_encrypt = tkt.add_check_btn(frame_checkboxes, LN.encrypted_root, tk_var.enable_encryption_toggle_var,
                      lambda: show_encrypt_options(tk_var.enable_encryption_toggle_var), pack=False)
    check_encrypt.grid(ipady=5, row=2, column=0, sticky=DI_VAR['nw'])

    frame_encryption_options = ttk.Frame(frame_checkboxes)

    encrypt_pass_note = ttk.Label(frame_encryption_options, wraplength=GV.UI.width, justify=DI_VAR['l'], text=LN.encrypt_reminder_txt, font=tkt.FONTS_smaller, foreground=tkt.color_blue)
    encrypt_pass_note.grid(pady=5, padx=(0, 0), column=0, columnspan=5, row=1, sticky=DI_VAR['nw'])

    # LOGIC
    def show_encrypt_options(var):
        if var.get():
            frame_encryption_options.grid(ipady=5,padx=(30, 0), row=3, column=0, sticky=DI_VAR['nw'])
        else:
            frame_encryption_options.grid_forget()

    show_encrypt_options(tk_var.enable_encryption_toggle_var)

    def next_btn_action(*args):
        page_autoinst_addition_1.run(app)
