import tkinter.ttk as ttk
import page_autoinst2
import page_verify
import tkinter_templates as tkt
import globals as GV
import translations.en as LN
import functions as fn
import page_1
import global_tk_vars as tk_var


def run(app):
    """the autoinstall page on which you choose whether to install alongside windows or start clean install"""
    tkt.init_frame(app)
    # *************************************************************************************************************
    page_frame = tkt.generic_page_layout(app, LN.windows_question % GV.SELECTED_SPIN.name,
                                         LN.btn_next, lambda: next_btn_action(),
                                         LN.btn_back, lambda: page_1.run(app))

    space_dualboot = GV.APP_dualboot_required_space + GV.APP_additional_failsafe_space + GV.SELECTED_SPIN.size
    dualboot_space_available = GV.COMPATIBILITY_RESULTS.resizable < space_dualboot
    is_auto_installable = GV.SELECTED_SPIN.is_auto_installable
    options_dict = {}
    options_dict['dualboot'] = {
        "name": LN.windows_options['dualboot'],
        "error": LN.warn_not_available if not is_auto_installable else LN.warn_space if dualboot_space_available else ""
    }
    options_dict['clean'] = {
        "name": LN.windows_options['clean'],
        "error": LN.warn_not_available if not is_auto_installable else ""}
    options_dict['custom'] = {"name": LN.windows_options['custom']}
    radio_buttons = tkt.add_multi_radio_buttons(page_frame, options_dict, tk_var.install_method_var,
                                                lambda: show_more_options_if_needed())
    # LOGIC
    if not GV.SELECTED_SPIN.is_auto_installable:
        tk_var.install_method_var.set('custom')

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

    app.update_idletasks()

    def show_more_options_if_needed():
        if tk_var.install_method_var.get() == 'dualboot':
            size_dualboot_txt_pre.grid(pady=5, padx=(10, 0), column=0, row=0, sticky=GV.UI.DI_VAR['nw'])
            size_dualboot_entry.grid(pady=5, padx=5, column=1, row=0)
            size_dualboot_txt_post.grid(pady=5, padx=(0, 0), column=2, row=0, sticky=GV.UI.DI_VAR['nw'])
        else:
            size_dualboot_txt_pre.grid_forget()
            size_dualboot_entry.grid_forget()
            size_dualboot_txt_post.grid_forget()

    show_more_options_if_needed()  # GUI bugfix

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
            return page_verify.run(app)
        return page_autoinst2.run(app)