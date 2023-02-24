import tkinter
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
    page_frame = tkt.generic_page_layout(app, LN.desktop_question, LN.btn_next, lambda: next_btn_action())
    list_spins_with_fullname = []
    listed_distro_dict = {}
    for dist in GV.ACCEPTED_SPINS:
        spin_fullname = f"{dist.name} {dist.version}"
        list_spins_with_fullname.append(spin_fullname)
        if dist.is_default:
            # tk_var.distro_var.set(spin_fullname) if tk_var.distro_var.get() == '' else ''
            listed_distro_dict[spin_fullname] = {
                "name": spin_fullname,
                "description": LN.distro_hint[dist.name] if dist.name in LN.distro_hint else ""
            }

    listed_distro_dict["else"] = {"name": LN.something_else}
    frame_distro = tkt.add_multi_radio_buttons(page_frame, listed_distro_dict, tk_var.distro_var,
                                               lambda: validate_input())
    distro_combolist = ttk.Combobox(frame_distro, values=list_spins_with_fullname, state='readonly')
    distro_combolist.bind("<<ComboboxSelected>>", lambda *args: validate_input())

    # GUI Bugfix
    if not GV.UI.combo_list_spin:
        distro_combolist.set(LN.choose_distro)
    else:
        distro_combolist.set(GV.UI.combo_list_spin)

    info_frame = tkinter.Frame(page_frame)
    tkt.add_text_label(info_frame, LN.info_about_selection, anchor=GV.UI.DI_VAR['w'], pady=5, padx=4,
                       foreground=tkt.color_green, font=tkt.FONTS_smaller)
    frame_distro.grid_rowconfigure(len(listed_distro_dict)+1, weight=1)  # GUI bugfix for distro_description
    selected_spin_info_tree = ttk.Treeview(info_frame, columns='info', show='', height=4,)
    selected_spin_info_tree.configure(selectmode='none')
    selected_spin_info_tree.column('info', width=250)
    selected_spin_info_tree.pack(ipady=5, fill='x', )

    def validate_input(*args):
        spin_index = None
        if (distro := tk_var.distro_var.get()) in list_spins_with_fullname:
            spin_index = list_spins_with_fullname.index(distro)
            distro_combolist.grid_forget()

        elif tk_var.distro_var.get() == 'else':
            distro_combolist.grid(ipady=5, padx=(30, 0), row=len(listed_distro_dict)+1, column=0, columnspan=2,
                                  sticky=GV.UI.DI_VAR['nw'])
            if distro_combolist.get() in list_spins_with_fullname:
                spin_index = list_spins_with_fullname.index(distro_combolist.get())

        if spin_index is not None:
            GV.SELECTED_SPIN = GV.ACCEPTED_SPINS[spin_index]
            total_size = GV.SELECTED_SPIN.size
            total_size += GV.LIVE_OS_INSTALLER_SPIN.size if GV.SELECTED_SPIN.is_live_img else 0
            GV.PARTITION.tmp_part_size = total_size + GV.APP_temp_part_failsafe_space
            if GV.SELECTED_SPIN.is_base_netinstall:
                dl_size_txt = LN.init_download % fn.byte_to_gb(total_size)
            else:
                dl_size_txt = LN.total_download % fn.byte_to_gb(total_size)
            dl_spin_name_text = f'{LN.selected_dist}: {GV.SELECTED_SPIN.name} {GV.SELECTED_SPIN.version}'
            dl_spin_desktop = f'{LN.desktop_environment}: {GV.SELECTED_SPIN.desktop}'

            if GV.SELECTED_SPIN.desktop in LN.desktop_hints.keys():
                dl_spin_desktop_desc = LN.desktop_hints[GV.SELECTED_SPIN.desktop]
            else:
                dl_spin_desktop_desc = ""
            info_frame.pack(side="bottom", fill='x')
            selected_spin_info_tree.delete(*selected_spin_info_tree.get_children())
            selected_spin_info_tree.insert('', index='end', iid='name', values=(dl_spin_name_text,))
            selected_spin_info_tree.insert('', index='end', iid='size', values=(dl_size_txt,))
            selected_spin_info_tree.insert('', index='end', iid='desktop', values=(dl_spin_desktop,))
            selected_spin_info_tree.insert('', index='end', iid='desktop_desc', values=(dl_spin_desktop_desc,))
        return spin_index

    validate_input()

    def next_btn_action(*args):
        if validate_input() is None:
            return -1
        # Saving UI state
        GV.UI.combo_list_spin = distro_combolist.get()
        #GV.UI.desktop = tk_var.desktop_var.get()
        # LOG #############################################
        log = '\nFedora Spin has been selected, spin details:'
        for key, value in vars(GV.SELECTED_SPIN).items():
            log += '\n --> %s: %s' % (str(key), str(value))
        logging.info(log)
        # #################################################
        return page_install_method.run(app)
