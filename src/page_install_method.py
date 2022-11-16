import tkinter.ttk as ttk
import page_autoinst2
import page_verify
import tkinter_templates as tkt
import globals as GV
import translations.en as LN
import functions as fn
import page_1
from init import app as tkinter, MID_FRAME
import global_tk_vars as tk_var


def run():
    """the autoinstall page on which you choose whether to install alongside windows or start clean install"""
    tkt.init_frame(MID_FRAME)
    # *************************************************************************************************************
    page_frame = tkt.generic_page_layout(MID_FRAME, LN.windows_question % GV.SELECTED_SPIN.name,
                                         LN.btn_next, lambda: next_btn_action(),
                                         LN.btn_back, lambda: page_1.run())

    radio_buttons = tkt.add_frame_container(page_frame)
    r1_autoinst_dualboot = tkt.add_radio_btn(radio_buttons, LN.windows_options['dualboot'],
                                             tk_var.install_method_var, 'dualboot', lambda: show_dualboot_options(True),
                                             pack=False)
    r1_autoinst_dualboot.grid(ipady=5, column=0, row=0, sticky=GV.UI.DI_VAR['w'])
    r1_warning = ttk.Label(radio_buttons, wraplength=GV.UI.width, justify="center", text='', font=tkt.FONTS_smaller,
                           foreground=tkt.color_red)
    r1_warning.grid(padx=20, column=1, row=0, sticky=GV.UI.DI_VAR['w'])
    r2_autoinst_clean = tkt.add_radio_btn(radio_buttons, LN.windows_options['clean'], tk_var.install_method_var, 'clean',
                                          lambda: show_dualboot_options(False), pack=False)
    r2_autoinst_clean.grid(ipady=5, column=0, row=2, sticky=GV.UI.DI_VAR['w'])
    r2_warning = ttk.Label(radio_buttons, wraplength=GV.UI.width, justify="center", text='', font=tkt.FONTS_smaller,
                           foreground=tkt.color_red)
    r2_warning.grid(padx=20, column=1, row=2, sticky=GV.UI.DI_VAR['w'])
    r3_custom = tkt.add_radio_btn(radio_buttons, LN.windows_options['custom'], tk_var.install_method_var, 'custom',
                                  lambda: show_dualboot_options(False), pack=False)
    r3_custom.grid(ipady=5, column=0, row=3, sticky=GV.UI.DI_VAR['w'])

    min_size = fn.byte_to_gb(GV.APP_dualboot_required_space)
    max_size = fn.byte_to_gb(
        GV.COMPATIBILITY_RESULTS.resizable - GV.SELECTED_SPIN.size - GV.APP_additional_failsafe_space)
    max_size = round(max_size, 2)
    float_regex = r'^[0-9]*\.?[0-9]{0,3}$'  # max 3 decimal digits
    entry1_frame = ttk.Frame(radio_buttons)
    entry1_frame.grid(row=1, column=0, columnspan=4, padx=10)
    size_dualboot_txt_pre = ttk.Label(entry1_frame, wraplength=GV.UI.width, justify=GV.UI.DI_VAR['l'],
                                      text=LN.dualboot_size_txt, font=tkt.FONTS_smaller)
    size_dualboot_entry = ttk.Entry(entry1_frame, width=10, textvariable=tk_var.dualboot_size_var)
    size_dualboot_txt_post = ttk.Label(entry1_frame, wraplength=GV.UI.width, justify=GV.UI.DI_VAR['l'],
                                       text='(%sGB - %sGB)' % (min_size, max_size), font=tkt.FONTS_smaller)
    tkt.var_tracer(tk_var.dualboot_size_var, "write",
                   lambda *args: fn.validate_with_regex(tk_var.dualboot_size_var, regex=float_regex, mode='fix'))

    # LOGIC
    space_dualboot = GV.APP_dualboot_required_space + GV.APP_additional_failsafe_space + GV.SELECTED_SPIN.size
    if GV.COMPATIBILITY_RESULTS.resizable < space_dualboot:
        r1_warning.config(text=LN.warn_space)
        r1_autoinst_dualboot.configure(state='disabled')
    if not GV.SELECTED_SPIN.is_auto_installable:
        r1_warning.config(text=LN.warn_not_available)
        r2_warning.config(text=LN.warn_not_available)
        r1_autoinst_dualboot.configure(state='disabled')
        r2_autoinst_clean.configure(state='disabled')
        tk_var.install_method_var.set('custom')
    tkinter.update_idletasks()

    def show_dualboot_options(is_true: bool):
        if is_true:
            size_dualboot_txt_pre.grid(pady=5, padx=(10, 0), column=0, row=0, sticky=GV.UI.DI_VAR['w'])
            size_dualboot_entry.grid(pady=5, padx=5, column=1, row=0)
            size_dualboot_txt_post.grid(pady=5, padx=(0, 0), column=2, row=0, sticky=GV.UI.DI_VAR['w'])
        else:
            size_dualboot_txt_pre.grid_forget()
            size_dualboot_entry.grid_forget()
            size_dualboot_txt_post.grid_forget()

    if tk_var.install_method_var.get() == 'dualboot': show_dualboot_options(True)  # GUI bugfix

    def next_btn_action(*args):
        if tk_var.install_method_var.get() not in GV.AVAILABLE_INSTALL_METHODS:
            return -1
        GV.KICKSTART.partition_method = tk_var.install_method_var.get()
        if GV.KICKSTART.partition_method == 'dualboot':
            syntax_valid = fn.validate_with_regex(tk_var.dualboot_size_var, regex=float_regex,
                                                  mode='read') not in (False, 'empty')
            if syntax_valid and min_size <= float(tk_var.dualboot_size_var.get()) <= max_size:
                GV.PARTITION.shrink_space = fn.gigabyte(tk_var.dualboot_size_var.get())
            else:
                return -1
        if GV.KICKSTART.partition_method == 'custom':
            return page_verify.run()
        return page_autoinst2.run()