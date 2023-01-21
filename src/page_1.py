import tkinter as tk
import tkinter.ttk as ttk
import tkinter_templates as tkt
import globals as GV
import translations.en as LN
import functions as fn
import page_install_method
import logging
import global_tk_vars as tk_var

def run(app):
    """the page on which you choose which distro/flaver and whether Autoinstall should be on or off"""
    tkt.init_frame(app)
    # *************************************************************************************************************
    page_frame = tkt.generic_page_layout(app, LN.startup_sentence + LN.desktop_question, LN.btn_next, lambda: next_btn_action())
    available_desktop = []
    dict_spins_with_fullname_keys = []
    for dist in GV.ACCEPTED_SPINS:
        spin_fullname = dist.name + ' ' + dist.version
        dict_spins_with_fullname_keys.append(spin_fullname)
        if dist.desktop and dist.desktop not in available_desktop:
            available_desktop.append(dist.desktop)
    desktops_description_dict = {}
    for desktop in available_desktop:
        # empty description if no description exists
        description = LN.desktop_hints[desktop] if desktop in LN.desktop_hints.keys() else ""
        desktops_description_dict[desktop] = {"name": desktop, "description": description}
    desktops_description_dict["else"] = {"name": LN.choose_spin_instead}
    frame_desktop = tkt.add_multi_radio_buttons(page_frame, desktops_description_dict, tk_var.desktop_var,
                                                lambda: validate_input())
    distro_description = ttk.Combobox(frame_desktop, values=dict_spins_with_fullname_keys, state='readonly')
    distro_description.bind("<<ComboboxSelected>>", lambda *args: validate_input())
    if not GV.UI.combo_list_spin:
        distro_description.set(LN.choose_fedora_spin)
    else:
        distro_description.set(GV.UI.combo_list_spin)
    frame_desktop.grid_rowconfigure(len(available_desktop)+1, weight=1)  # GUI bugfix for distro_description
    selected_spin_info_tree = ttk.Treeview(frame_desktop, columns='info', show='', height=2,)
    selected_spin_info_tree.configure(selectmode='none')

    def validate_input(*args):
        if tk_var.desktop_var.get() == 'else':
            distro_description.grid(ipady=5,padx=(30, 0), row=len(available_desktop)+1, column=0, columnspan=2,
                                 sticky=GV.UI.DI_VAR['nw'])
            if distro_description.get() in dict_spins_with_fullname_keys:
                spin_index = dict_spins_with_fullname_keys.index(distro_description.get())
            else:
                spin_index = None
        else:
            distro_description.grid_forget()
            spin_index = None
            for index, dist in enumerate(GV.ACCEPTED_SPINS):
                if dist.desktop == tk_var.desktop_var.get():
                    if not bool(dist.ostree_args):
                        spin_index = index
        if spin_index is not None:
            GV.SELECTED_SPIN = GV.ACCEPTED_SPINS[spin_index]
            if GV.SELECTED_SPIN.is_live_img:
                GV.KICKSTART.live_img_url = GV.APP_live_img_url

            if GV.SELECTED_SPIN.is_live_img:
                total_size = GV.LIVE_OS_INSTALLER_SPIN.size + GV.SELECTED_SPIN.size
            else:
                total_size = GV.SELECTED_SPIN.size
            if GV.SELECTED_SPIN.is_base_netinstall:
                dl_size_txt = LN.init_download % fn.byte_to_gb(total_size)
            else:
                dl_size_txt = LN.total_download % fn.byte_to_gb(total_size)
            dl_spin_name_text = '%s: %s %s' % (LN.selected_spin, GV.SELECTED_SPIN.name, GV.SELECTED_SPIN.version)
            selected_spin_info_tree.grid(ipady=5, row=len(available_desktop), rowspan=5, column=1, columnspan=2, sticky=GV.UI.DI_VAR['se'])
            selected_spin_info_tree.delete(*selected_spin_info_tree.get_children())
            selected_spin_info_tree.insert('', index='end', iid='name', values=(dl_spin_name_text,))
            selected_spin_info_tree.insert('', index='end', iid='size', values=(dl_size_txt,))
        return spin_index

    validate_input()

    def next_btn_action(*args):
        if validate_input() is None:
            return -1
        GV.UI.combo_list_spin = distro_description.get()
        GV.UI.desktop = tk_var.desktop_var.get()  # Saving UI settings
        # LOG #############################################
        log = '\nFedora Spin has been selected, spin details:'
        for key, value in vars(GV.SELECTED_SPIN).items():
            log += '\n --> %s: %s' % (str(key), str(value))
        logging.info(log)
        # #################################################
        return page_install_method.run(app)
