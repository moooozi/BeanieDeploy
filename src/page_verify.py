import popup_advanced_options
import pre_install
import tkinter.ttk as ttk
import tkinter_templates as tkt
import page_autoinst_addition_2
import page_install_method
import globals as GV
import translations.en as LN
import global_tk_vars as tk_var
from gui_functions import get_first_tk_parent


def run(app):
    """the page on which you get to review your selection before starting to install"""
    tkt.init_frame(app)
    # *************************************************************************************************************
    page_frame = tkt.generic_page_layout(app, LN.verify_question,
                                         LN.btn_install, lambda: next_btn_action(),
                                         LN.btn_back, lambda: validate_back_page())

    # Constructing user verification text based on user's selections  ++++++++++++++++++++++++++++++++++++++++++++++
    review_sel = []
    if GV.KICKSTART.partition_method == 'custom':
        review_sel.append(LN.verify_text['no_autoinst'] % GV.SELECTED_SPIN.name)
    else:
        if GV.KICKSTART.partition_method == 'dualboot':
            review_sel.append(LN.verify_text['autoinst_dualboot'] % GV.SELECTED_SPIN.name)
            review_sel.append(LN.verify_text['autoinst_keep_data'])
        elif GV.KICKSTART.partition_method == 'clean':
            review_sel.append(LN.verify_text['autoinst_clean'] % GV.SELECTED_SPIN.name)
            review_sel.append(LN.verify_text['autoinst_rm_all'])
        if GV.INSTALL_OPTIONS.export_wifi:
            review_sel.append(LN.verify_text['autoinst_wifi'] % GV.SELECTED_SPIN.name)
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    review_tree = ttk.Treeview(page_frame, columns='error', show='', height=3)
    review_tree.configure(selectmode='none')

    for i in range(len(review_sel)):
        review_tree.insert('', index='end', iid=str(i), values=(review_sel[i],))
    review_tree.pack(ipady=5, pady=10, padx=(0, 5), fill='x', expand=1)

    # additions options (checkboxes)
    frame_options = tkt.add_frame_container(page_frame)

    check_restart = tkt.add_check_btn(frame_options, text=LN.add_auto_restart, var=tk_var.auto_restart_toggle_var, pack=False)
    check_restart.grid(ipady=5, row=0, column=0, sticky=GV.UI.DI_VAR['nw'])

    '''
    c3_add = ttk.Checkbutton(page_frame, text=LN.add_torrent, variable=torrent_toggle_var, onvalue=1, offvalue=0)
    '''
    more_options_btn = ttk.Label(frame_options, justify="center", text=LN.more_options, font=tkt.FONTS_smaller,
                                 foreground=tkt.color_blue)
    more_options_btn.grid(ipady=5, row=2, column=0, sticky=GV.UI.DI_VAR['nw'])
    more_options_btn.bind("<Button-1>",
                          lambda x: popup_advanced_options.run(master=get_first_tk_parent(app)))

    def validate_back_page(*args):
        if GV.KICKSTART.partition_method == 'custom':
            page_install_method.run(app)
        else:
            page_autoinst_addition_2.run(app)

    def next_btn_action(*args):
        GV.INSTALL_OPTIONS.auto_restart = tk_var.auto_restart_toggle_var.get()
        GV.INSTALL_OPTIONS.torrent = tk_var.torrent_toggle_var.get()
        return pre_install.run(app)
