import globals as GV
import global_tk_vars as tk_var
import page_installing
import procedure as prc
import logging
import types
import autoinst


def run(app):
    # GETTING ARGUMENTS READY
    GV.INSTALL_OPTIONS.export_wifi = tk_var.export_wifi_toggle_var.get()
    GV.KICKSTART.is_encrypted = tk_var.enable_encryption_toggle_var.get()
    GV.KICKSTART.passphrase = tk_var.encrypt_passphrase_var.get()
    GV.KICKSTART.tpm_auto_unlock = tk_var.encryption_tpm_unlock_toggle_var.get()

    wifi_profiles = prc.get_wifi_profiles(GV.PATH.WORK_DIR) if GV.INSTALL_OPTIONS.export_wifi else None

    tmp_part_size: int = GV.SELECTED_SPIN.size + GV.APP_temp_part_failsafe_space
    if GV.SELECTED_SPIN.is_live_img:
        tmp_part_size += GV.LIVE_OS_INSTALLER_SPIN.size

    install_method = GV.KICKSTART.partition_method
    GV.PARTITION.tmp_part_size = tmp_part_size
    GV.PARTITION.temp_part_label = GV.TMP_PARTITION_LABEL
    GV.PARTITION.make_root_partition = True if install_method == 'dualboot' else False
    GV.PARTITION.boot_part_size = GV.APP_linux_boot_partition_size if install_method in ("dualboot", "clean") else 0
    GV.PARTITION.efi_part_size = GV.APP_linux_efi_partition_size if install_method == 'dualboot' else 0

    if GV.KICKSTART.partition_method != 'custom':
        GV.KICKSTART.ostree_args = GV.SELECTED_SPIN.ostree_args
        GV.KICKSTART.wifi_profiles = wifi_profiles
        GV.KICKSTART.lang = tk_var.selected_locale.get()
        GV.INSTALL_OPTIONS.keymap_timezone_source = tk_var.keymap_timezone_source_var.get()
        if GV.INSTALL_OPTIONS.keymap_timezone_source == 'ip':
            GV.KICKSTART.keymap = autoinst.get_keymaps(territory=GV.IP_LOCALE['country_code'])[0]
            GV.KICKSTART.keymap_type = 'xlayout'
            GV.KICKSTART.timezone = autoinst.langtable.list_timezones(territoryId=GV.IP_LOCALE['country_code'])[0]
        elif GV.INSTALL_OPTIONS.keymap_timezone_source == 'select':
            GV.KICKSTART.keymap = autoinst.get_keymaps(lang=GV.KICKSTART.lang)[0]
            GV.KICKSTART.keymap_type = 'xlayout'
            GV.KICKSTART.timezone = autoinst.langtable.list_timezones(languageId=GV.KICKSTART.lang)[0]
        elif GV.INSTALL_OPTIONS.keymap_timezone_source == 'custom':
            GV.KICKSTART.keymap = tk_var.custom_keymap_var.get()
            GV.KICKSTART.keymap_type = 'vc'
            GV.KICKSTART.timezone = tk_var.custom_timezone_var.get()

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
    else:
        installer_img = GV.SELECTED_SPIN
        live_img = None
        live_img_size = 0

    installer_args = types.SimpleNamespace()
    installer_args.work_dir = GV.PATH.WORK_DIR
    installer_args.aria2_path = GV.PATH.ARIA2C

    installer_args.installer_iso_name = GV.INSTALL_ISO_NAME
    installer_args.installer_iso_path = GV.PATH.INSTALL_ISO
    installer_args.installer_iso_url = installer_img.dl_link
    installer_args.installer_iso_size = installer_img.size
    installer_args.installer_img_hash256 = installer_img.hash256

    installer_img.file_name = GV.INSTALL_ISO_NAME
    installer_img.file_hint = "installer_iso"

    installer_args.dl_files = [installer_img, ]

    if GV.SELECTED_SPIN.is_live_img:
        live_img.file_name = GV.LIVE_ISO_NAME
        live_img.file_hint = "live_img_iso"
        installer_args.dl_files.append(live_img)

    installer_args.ks_kwargs = GV.KICKSTART
    installer_args.part_kwargs = GV.PARTITION
    installer_args.rpm_source_dir = GV.PATH.RPM_SOURCE_DIR
    installer_args.rpm_dest_dir_name = GV.PATH.RPM_DEST_DIR_NAME
    installer_args.grub_cfg_relative_path = GV.PATH.RELATIVE_GRUB_CFG
    installer_args.tmp_partition_label = GV.TMP_PARTITION_LABEL
    installer_args.kickstart_cfg_relative_path = GV.PATH.RELATIVE_KICKSTART
    installer_args.efi_file_relative_path = GV.APP_default_efi_file_path

    return page_installing.run(app, installer_args=installer_args)