import tkinter.ttk as ttk
import page_autoinst2
import page_verify
import tkinter_templates as tkt
import globals as GV
import multilingual
import functions as fn
import page_1
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
                                         LN.btn_back, lambda: page_1.run(app))

    space_dualboot = GV.APP_dualboot_required_space + GV.APP_linux_boot_partition_size + \
                     GV.APP_additional_failsafe_space + GV.PARTITION.tmp_part_size * 2
    space_clean = GV.APP_linux_boot_partition_size + GV.APP_additional_failsafe_space + GV.PARTITION.tmp_part_size * 2
    
    from sys import argv
    if '--skip_check' not in argv:
        dualboot_space_available = GV.COMPATIBILITY_RESULTS.resizable > space_dualboot
        replace_win_space_available = GV.COMPATIBILITY_RESULTS.resizable > space_clean
        max_size = fn.byte_to_gb(
        GV.COMPATIBILITY_RESULTS.resizable - GV.SELECTED_SPIN.size - GV.APP_additional_failsafe_space)
        max_size = round(max_size, 2)
    else:
        dualboot_space_available = True
        replace_win_space_available = True
        max_size = 9999
    
    is_auto_installable = GV.SELECTED_SPIN.is_auto_installable

    dualboot_error_msg = ""
    replace_win_error_msg = ""
    if not is_auto_installable:
        dualboot_error_msg = LN.warn_not_available
        replace_win_error_msg = LN.warn_not_available
    else:
        if not dualboot_space_available:
            dualboot_error_msg = LN.warn_space
        if not replace_win_space_available:
            replace_win_error_msg = LN.warn_space

    install_methods_dict = {
        'dualboot': {"name": LN.windows_options['dualboot'], "error": dualboot_error_msg},
        'replace_win': {"name": LN.windows_options['replace_win'], "error": replace_win_error_msg},
        'custom': {"name": LN.windows_options['custom']}}

    radio_buttons = tkt.add_multi_radio_buttons(page_frame, install_methods_dict, tk_var.install_method_var,
                                                lambda: show_more_options_if_needed())

    # GUI
    if not tk_var.install_method_var.get():
        default = 'custom' if not is_auto_installable else 'dualboot' if dualboot_space_available else 'replace_win'
        tk_var.install_method_var.set(default)

    min_size = fn.byte_to_gb(GV.APP_dualboot_required_space)
    entry1_frame = ttk.Frame(radio_buttons)
    radio_buttons.rowconfigure(5, weight=1)
    entry1_frame.grid(row=5, column=0, columnspan=2, padx=0, sticky=DI_VAR['w'])

    warn_backup_sys_drive_files = tkt.add_text_label(entry1_frame,
                                                     text=LN.warn_backup_files_txt % f"{fn.get_sys_drive_letter()}:\\",
                                                     font=tkt.FONTS_smaller, foreground=tkt.color_red, pack=False)
    size_dualboot_txt_pre = tkt.add_text_label(entry1_frame, text=LN.dualboot_size_txt % GV.SELECTED_SPIN.name,
                                               font=tkt.FONTS_smaller, pack=False)
    size_dualboot_entry = ttk.Entry(entry1_frame, width=10, textvariable=tk_var.dualboot_size_var,)
    validation_func = app.register(lambda x: x.replace('.', '', 1).isdigit() and min_size <= float(x) <= max_size)
    size_dualboot_entry.config(validate='none', validatecommand=(validation_func, '%P'))
    size_dualboot_txt_post = tkt.add_text_label(entry1_frame, text='(%sGB - %sGB)' % (min_size, max_size),
                                                font=tkt.FONTS_smaller, foreground=tkt.color_blue, pack=False)
    tkt.var_tracer(tk_var.dualboot_size_var, "write", lambda *args: size_dualboot_entry.validate())

    app.update_idletasks()

    def show_more_options_if_needed():

        warn_backup_sys_drive_files.grid_forget()
        size_dualboot_txt_pre.grid_forget()
        size_dualboot_entry.grid_forget()
        size_dualboot_txt_post.grid_forget()
        if tk_var.install_method_var.get() == 'dualboot':
            size_dualboot_txt_pre.grid(pady=5, padx=(10, 0), column=0, row=0, sticky=DI_VAR['w'])
            size_dualboot_entry.grid(pady=5, padx=5, column=1, row=0)
            size_dualboot_txt_post.grid(pady=5, padx=(0, 0), column=2, row=0, sticky=DI_VAR['w'])
        elif tk_var.install_method_var.get() == 'replace_win':
            warn_backup_sys_drive_files.grid(pady=5, padx=(10, 0), column=0, row=0, sticky=DI_VAR['w'])

    show_more_options_if_needed()  # GUI bugfix

    def next_btn_action(*args):
        if tk_var.install_method_var.get() not in GV.AVAILABLE_INSTALL_METHODS:
            return -1
        GV.KICKSTART.partition_method = tk_var.install_method_var.get()
        if GV.KICKSTART.partition_method == 'dualboot':
            size_dualboot_entry.validate()
            syntax_invalid = 'invalid' in size_dualboot_entry.state()
            if syntax_invalid:
                return -1
            GV.PARTITION.shrink_space = fn.gigabyte(tk_var.dualboot_size_var.get())
        elif GV.KICKSTART.partition_method == 'custom':
            GV.PARTITION.shrink_space = 0
            GV.PARTITION.boot_part_size = 0
            GV.PARTITION.efi_part_size = 0
            return page_verify.run(app)
        return page_autoinst2.run(app)
