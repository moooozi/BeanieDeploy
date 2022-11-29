import popup_advanced_options
import tkinter.ttk as ttk
import tkinter_templates as tkt
import types
import autoinst
import page_autoinst_addition_2
import page_install_method
import page_installing
import globals as GV
import translations.en as LN
import procedure as prc
import logging
import global_tk_vars as tk_var
from gui_functions import get_first_tk_parent
def run(app):
    """the page on which you get to review your selection before starting to install"""
    tkt.init_frame(app)
    # *************************************************************************************************************
    page_frame = tkt.generic_page_layout(app, LN.verify_question,
                                         LN.btn_install, lambda: next_btn_action(),
                                         LN.btn_back, lambda: validate_back_page())

    # GETTING ARGUMENTS READY
    tmp_part_size: int = GV.SELECTED_SPIN.size + GV.APP_temp_part_failsafe_space
    if GV.SELECTED_SPIN.is_live_img:
        tmp_part_size += GV.LIVE_OS_INSTALLER_SPIN.size
    if GV.INSTALL_OPTIONS.export_wifi:
        wifi_profiles = prc.get_wifi_profiles(GV.PATH.WORK_DIR)
    else:
        wifi_profiles = None

    GV.INSTALL_OPTIONS.export_wifi = tk_var.export_wifi_toggle_var.get()
    GV.KICKSTART.is_encrypted = tk_var.enable_encryption_toggle_var.get()
    GV.KICKSTART.passphrase = tk_var.encrypt_passphrase_var.get()
    GV.KICKSTART.tpm_auto_unlock = tk_var.encryption_tpm_unlock_toggle_var.get()
    if tk_var.keymap_timezone_source_var.get() == 'custom':
        GV.KICKSTART.keymap = tk_var.custom_keymap_var.get()
        GV.KICKSTART.keymap_type = 'vc'
        GV.KICKSTART.timezone = tk_var.custom_timezone_var.get()
    GV.INSTALL_OPTIONS.keymap_timezone_source = tk_var.keymap_timezone_source_var.get()
    GV.KICKSTART.lang = tk_var.selected_locale.get()

    GV.PARTITION.tmp_part_size = tmp_part_size
    GV.PARTITION.temp_part_label = GV.TMP_PARTITION_LABEL

    if GV.KICKSTART.partition_method != 'custom':
        if GV.INSTALL_OPTIONS.keymap_timezone_source == 'ip':
            GV.KICKSTART.keymap = autoinst.get_keymaps(territory=GV.IP_LOCALE['country_code'])[0]
            GV.KICKSTART.keymap_type = 'xlayout'
            GV.KICKSTART.timezone = autoinst.langtable.list_timezones(territoryId=GV.IP_LOCALE['country_code'])[0]
        elif GV.INSTALL_OPTIONS.keymap_timezone_source == 'select':
            GV.KICKSTART.keymap = autoinst.get_keymaps(lang=GV.KICKSTART.lang)[0]
            GV.KICKSTART.keymap_type = 'xlayout'
            GV.KICKSTART.timezone = autoinst.langtable.list_timezones(languageId=GV.KICKSTART.lang)[0]
        elif GV.INSTALL_OPTIONS.keymap_timezone_source == 'custom':
            pass
        GV.KICKSTART.ostree_args = GV.SELECTED_SPIN.ostree_args
        GV.KICKSTART.wifi_profiles = wifi_profiles

        if GV.KICKSTART.partition_method == 'dualboot':
            GV.PARTITION.boot_part_size = GV.APP_linux_boot_partition_size
            GV.PARTITION.efi_part_size = GV.APP_linux_efi_partition_size
        # LOG ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        log_kickstart = '\nKickstart arguments (sensitive data sensored):'
        for key, value in vars(GV.KICKSTART).items():
            if key in ('passphrase', 'fullname', 'username', 'wifi_profiles'):
                if not value:
                    continue
                log_kickstart += '\n --> %s: (sensitive data)' % key
            else:
                log_kickstart += '\n --> %s: %s' % (key, value)
        logging.info(log_kickstart)
        log_partition = '\nPartitioning details:'
        for key, value in vars(GV.PARTITION).items():
            log_partition += '\n --> %s: %s' % (key, value)
        logging.info(log_partition)
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    if GV.SELECTED_SPIN.is_live_img:
        installer_img = GV.LIVE_OS_INSTALLER_SPIN
        live_img = GV.SELECTED_SPIN
        live_img_size = live_img.size
        total_download_size = live_img.size + installer_img.size
    else:
        installer_img = GV.SELECTED_SPIN
        live_img = None
        live_img_size = 0
        total_download_size = installer_img.size
    installer_dl_percent_factor = installer_img.size / total_download_size * 0.90
    live_img_dl_factor = live_img_size / total_download_size * 0.90

    installing = types.SimpleNamespace()
    installing.work_dir = GV.PATH.WORK_DIR
    installing.aria2_path = GV.PATH.ARIA2C
    installing.installer_iso_name = GV.INSTALL_ISO_NAME
    installing.installer_iso_path = GV.PATH.INSTALL_ISO
    installing.installer_iso_url = installer_img.dl_link
    installing.installer_img_hash256 = installer_img.hash256
    installing.ks_kwargs = GV.KICKSTART
    installing.part_kwargs = GV.PARTITION
    installing.rpm_source_dir = GV.PATH.RPM_SOURCE_DIR
    installing.rpm_dest_dir_name = GV.PATH.RPM_DEST_DIR_NAME
    installing.grub_cfg_relative_path = GV.PATH.RELATIVE_GRUB_CFG
    installing.tmp_partition_label = GV.TMP_PARTITION_LABEL
    installing.kickstart_cfg_relative_path = GV.PATH.RELATIVE_KICKSTART
    installing.efi_file_relative_path = GV.APP_default_efi_file_path
    if GV.SELECTED_SPIN.is_live_img:
        installing.live_img_iso_name = GV.LIVE_ISO_NAME
        installing.live_img_iso_path = GV.PATH.LIVE_ISO
        installing.live_img_iso_url = live_img.dl_link
        installing.live_img_hash256 = live_img.hash256

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
        return page_installing.run(app,
                                   installer_kwargs=installing,
                                   installer_img_dl_percent_factor=installer_dl_percent_factor,
                                   live_img_dl_factor=live_img_dl_factor, )
