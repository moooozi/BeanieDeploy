import tkinter as tk
import tkinter.ttk as ttk
import types
import autoinst
import page_autoinst_addition_2
import page_install_method
import page_installing
import tkinter_templates as tkt
import globals as GV
import translations.en as LN
import functions as fn
import procedure as prc
from init import MID_FRAME, app


def run():
    """the page on which you get to review your selection before starting to install"""
    tkt.clear_frame(MID_FRAME)
    # *************************************************************************************************************
    tkt.generic_page_layout(MID_FRAME, LN.verify_question,
                            LN.btn_install, lambda: next_btn_action(),
                            LN.btn_back, lambda: validate_back_page())

    auto_restart_toggle_var = tk.BooleanVar(app, GV.INSTALL_OPTIONS.auto_restart)
    torrent_toggle_var = tk.BooleanVar(app, GV.INSTALL_OPTIONS.torrent)

    # GETTING ARGUMENTS READY
    tmp_part_size: int = GV.SELECTED_SPIN.size + fn.gigabyte(GV.APP.temp_part_failsafe_space)
    if GV.SELECTED_SPIN.is_live_img:
        tmp_part_size += GV.LIVE_OS_INSTALLER_SPIN.size
    if GV.AUTOINST.export_wifi:
        wifi_profiles = prc.get_wifi_profiles(GV.PATH.WORK_DIR)
    else:
        wifi_profiles = None
    kickstart = types.SimpleNamespace()
    kickstart.live_img_url = GV.INSTALL_OPTIONS.live_img_url

    partition = types.SimpleNamespace()
    partition.tmp_part_size = tmp_part_size
    partition.temp_part_label = GV.TMP_PARTITION_LABEL

    if GV.INSTALL_OPTIONS.install_method != 'custom':
        if GV.AUTOINST.keymap_timezone_source == 'ip':
            GV.AUTOINST.keymap = autoinst.get_keymaps(territory=GV.IP_LOCALE['country_code'])[0]
            GV.AUTOINST.keymap_type = 'xlayout'
            GV.AUTOINST.timezone = autoinst.langtable.list_timezones(territoryId=GV.IP_LOCALE['country_code'])[0]
        elif GV.AUTOINST.keymap_timezone_source == 'select':
            GV.AUTOINST.keymap = autoinst.get_keymaps(lang=GV.AUTOINST.locale)[0]
            GV.AUTOINST.keymap_type = 'xlayout'
            GV.AUTOINST.timezone = autoinst.langtable.list_timezones(languageId=GV.AUTOINST.locale)[0]
        elif GV.AUTOINST.keymap_timezone_source == 'custom':
            pass
        kickstart.ostree_args = GV.SELECTED_SPIN.ostree_args
        kickstart.is_encrypted = GV.AUTOINST.enable_encryption
        kickstart.passphrase = GV.AUTOINST.encryption_pass
        kickstart.wifi_profiles = wifi_profiles
        kickstart.keymap = GV.AUTOINST.keymap
        kickstart.keymap_type = GV.AUTOINST.keymap_type
        kickstart.lang = GV.AUTOINST.locale
        kickstart.timezone = GV.AUTOINST.timezone
        kickstart.username = GV.AUTOINST.username
        kickstart.fullname = GV.AUTOINST.fullname
        kickstart.partition_method = GV.INSTALL_OPTIONS.install_method

        if GV.INSTALL_OPTIONS.install_method == 'dualboot':
            partition.shrink_space = fn.gigabyte(GV.AUTOINST.dualboot_size)
            partition.boot_part_size = fn.gigabyte(GV.APP.linux_boot_partition_size)
            partition.efi_part_size = fn.megabyte(GV.APP.linux_efi_partition_size)
        # LOG ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        fn.log('\nKickstart arguments (sensitive data sensored):')
        for key, value in vars(kickstart).items():
            if key in ('passphrase', 'fullname', 'username', 'wifi_profiles'):
                if not value:
                    continue
                fn.log('%s: (sensitive data)' % key)
            else:
                fn.log('%s: %s' % (key, value))
        fn.log('\nPartitioning details:')
        for key, value in vars(partition).items():
            if key == 'queue': continue
            fn.log('%s: %s' % (key, value))
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    else:
        kickstart = {}
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
    installing.ks_kwargs = vars(kickstart)
    installing.part_kwargs = vars(partition)
    installing.rpm_source_dir = GV.PATH.RPM_SOURCE_DIR
    installing.rpm_dest_dir_name = GV.PATH.RPM_DEST_DIR_NAME
    if GV.SELECTED_SPIN.is_live_img:
        installing.live_img_iso_name = GV.LIVE_ISO_NAME
        installing.live_img_iso_path = GV.PATH.LIVE_ISO
        installing.live_img_iso_url = live_img.dl_link
        installing.live_img_hash256 = live_img.hash256

    # Constructing user verification text based on user's selections  ++++++++++++++++++++++++++++++++++++++++++++++
    review_sel = []
    if GV.INSTALL_OPTIONS.install_method == 'custom':
        review_sel.append(LN.verify_text['no_autoinst'] % GV.SELECTED_SPIN.name)
    else:
        if GV.INSTALL_OPTIONS.install_method == 'dualboot':
            review_sel.append(LN.verify_text['autoinst_dualboot'] % GV.SELECTED_SPIN.name)
            review_sel.append(LN.verify_text['autoinst_keep_data'])
        elif GV.INSTALL_OPTIONS.install_method == 'clean':
            review_sel.append(LN.verify_text['autoinst_clean'] % GV.SELECTED_SPIN.name)
            review_sel.append(LN.verify_text['autoinst_rm_all'])
        if GV.AUTOINST.export_wifi:
            review_sel.append(LN.verify_text['autoinst_wifi'] % GV.SELECTED_SPIN.name)
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    review_tree = ttk.Treeview(MID_FRAME, columns='error', show='', height=3)
    review_tree.pack(anchor=GV.UI.DI_VAR['w'], ipady=5, pady=10, padx=(0, 5), fill='x')
    review_tree.configure(selectmode='none')

    for i in range(len(review_sel)):
        review_tree.insert('', index='end', iid=str(i), values=(review_sel[i],))
    # additions options (checkboxes)
    c2_add = ttk.Checkbutton(MID_FRAME, text=LN.add_auto_restart, variable=auto_restart_toggle_var, onvalue=1,
                             offvalue=0)
    c2_add.pack(anchor=GV.UI.DI_VAR['w'])
    '''
    c3_add = ttk.Checkbutton(MID_FRAME, text=LN.add_torrent, variable=torrent_toggle_var, onvalue=1, offvalue=0)
    more_options_btn = ttk.Label(MID_FRAME, justify="center", text=LN.more_options, font=tkt.FONTS.tiny,
                                 foreground='#3aa9ff')
    more_options_btn.pack(pady=10, padx=10, anchor=GV.UI.DI_VAR['w'])
    more_options_btn.bind("<Button-1>",
                          lambda x: (more_options_btn.destroy(), c3_add.pack(anchor=GV.UI.DI_VAR['w'])))
    '''

    def validate_back_page(*args):
        if GV.INSTALL_OPTIONS.install_method == 'custom':
            page_install_method.run()
        else:
            page_autoinst_addition_2.run()

    def next_btn_action(*args):
        GV.INSTALL_OPTIONS.auto_restart = auto_restart_toggle_var.get()
        GV.INSTALL_OPTIONS.torrent = torrent_toggle_var.get()
        return page_installing.run(installer_kwargs=installing,
                                   installer_img_dl_percent_factor=installer_dl_percent_factor,
                                   live_img_dl_factor=live_img_dl_factor,)
