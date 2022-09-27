import tkinter as tk
import tkinter.ttk as ttk
import tkinter_templates as tkt
import globals as GV
import translations.en as LN
import functions as fn
import page_install_method
from init import app as tkinter, MID_FRAME as parent


def run():
    """the page on which you choose which distro/flaver and whether Autoinstall should be on or off"""
    tkt.clear_frame(parent)
    # *************************************************************************************************************
    page_frame = tkt.generic_page_layout(parent, LN.desktop_question, LN.btn_next, lambda: next_btn_action())
    desktop_var = tk.StringVar(tkinter, GV.UI.desktop)
    immutable_toggle_var = tk.BooleanVar(tkinter, False)
    available_desktop = []
    dict_spins_with_fullname_keys = []
    for dist in GV.ACCEPTED_SPINS:
        spin_fullname = dist.name + ' ' + dist.version
        dict_spins_with_fullname_keys.append(spin_fullname)
        if dist.desktop and dist.desktop not in available_desktop:
            available_desktop.append(dist.desktop)
    frame_desktop = tkt.add_frame_container(page_frame, 0, 0)
    for index, desktop in enumerate(available_desktop):
        tkt.add_radio_btn(frame_desktop, desktop, desktop_var, desktop, command=lambda: validate_input(),
                          pack=False).grid(ipady=5, row=index, column=0, sticky=GV.UI.DI_VAR['w'])
        if desktop in LN.desktop_hints.keys():
            ttk.Label(frame_desktop, wraplength=540, justify="center", text=LN.desktop_hints[desktop],
                      font=tkt.FONTS_smaller, foreground=tkt.light_blue).grid(ipadx=5, row=index, column=1,
                                                                      sticky=GV.UI.DI_VAR['w'])
    tkt.add_radio_btn(frame_desktop, LN.choose_spin_instead, desktop_var, 'else', command=lambda: validate_input(),
                      pack=False).grid(ipady=5, row=len(available_desktop), column=0, sticky=GV.UI.DI_VAR['w'])

    combo_list_spin = ttk.Combobox(page_frame, values=dict_spins_with_fullname_keys, state='readonly')
    combo_list_spin.bind("<<ComboboxSelected>>", lambda *args: validate_input())
    if not GV.UI.combo_list_spin:
        combo_list_spin.set(LN.choose_fedora_spin)
    else:
        combo_list_spin.set(GV.UI.combo_list_spin)
    frame_spin_info = tk.Frame(page_frame)
    frame_spin_info.pack(side=GV.UI.DI_VAR['r'], fill="x", pady=5)
    selected_spin_info_tree = ttk.Treeview(frame_spin_info, columns='info', show='', height=2)
    selected_spin_info_tree.configure(selectmode='none')

    def validate_input(*args):
        if desktop_var.get() == 'else':
            combo_list_spin.pack(padx=40, pady=5, anchor=GV.UI.DI_VAR['w'])
            if combo_list_spin.get() in dict_spins_with_fullname_keys:
                spin_index = dict_spins_with_fullname_keys.index(combo_list_spin.get())
            else:
                spin_index = None
        else:
            combo_list_spin.pack_forget()
            spin_index = None
            for index, dist in enumerate(GV.ACCEPTED_SPINS):
                if dist.desktop == desktop_var.get():
                    if bool(immutable_toggle_var.get()) == bool(dist.ostree_args):
                        spin_index = index
        if spin_index is not None:
            GV.SELECTED_SPIN = GV.ACCEPTED_SPINS[spin_index]
            if GV.SELECTED_SPIN.is_live_img:
                GV.KICKSTART.live_img_url = GV.APP.live_img_url

            if GV.SELECTED_SPIN.is_live_img:
                total_size = GV.LIVE_OS_INSTALLER_SPIN.size + GV.SELECTED_SPIN.size
            else:
                total_size = GV.SELECTED_SPIN.size
            if GV.SELECTED_SPIN.is_base_netinstall:
                dl_size_txt = LN.init_download % fn.byte_to_gb(total_size)
            else:
                dl_size_txt = LN.total_download % fn.byte_to_gb(total_size)
            dl_spin_name_text = '%s: %s %s' % (LN.selected_spin, GV.SELECTED_SPIN.name, GV.SELECTED_SPIN.version)
            selected_spin_info_tree.pack(anchor=GV.UI.DI_VAR['w'], ipady=5, padx=(0, 0), fill='x')
            selected_spin_info_tree.delete(*selected_spin_info_tree.get_children())
            selected_spin_info_tree.insert('', index='end', iid='name', values=(dl_spin_name_text,))
            selected_spin_info_tree.insert('', index='end', iid='size', values=(dl_size_txt,))
        return spin_index

    validate_input()

    def next_btn_action(*args):
        if validate_input() is None:
            return -1
        GV.UI.combo_list_spin = combo_list_spin.get()
        GV.UI.desktop = desktop_var.get()  # Saving UI settings
        # LOG #############################################
        fn.log('\nFedora Spin has been selected, spin details:')

        for key, value in vars(GV.SELECTED_SPIN).items():
            fn.log('  -> %s: %s' % (str(key), str(value)))
        # #################################################
        return page_install_method.run()
