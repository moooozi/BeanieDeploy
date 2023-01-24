import globals as GV
import global_tk_vars as tk_var
import page_installing
import procedure as prc
import logging
import types
import autoinst
import functions as fn


def run(app):
    # GETTING ARGUMENTS READY
    GV.INSTALL_OPTIONS.export_wifi = tk_var.export_wifi_toggle_var.get()
    GV.KICKSTART.is_encrypted = tk_var.enable_encryption_toggle_var.get()
    GV.KICKSTART.passphrase = tk_var.encrypt_passphrase_var.get()
    GV.KICKSTART.tpm_auto_unlock = tk_var.encryption_tpm_unlock_toggle_var.get()

    wifi_profiles = prc.get_wifi_profiles(GV.PATH.WORK_DIR) if GV.INSTALL_OPTIONS.export_wifi else None

    install_method = GV.KICKSTART.partition_method
    # creating new partition for root is only needed when installing alongside Windows
    GV.PARTITION.make_root_partition = True if install_method == 'dualboot' else False
    # Only create separate boot partition if encryption is enabled
    GV.PARTITION.boot_part_size = 0
    # Do not create additional efi partition
    GV.PARTITION.efi_part_size = 0

    if GV.KICKSTART.partition_method != 'custom':
        if GV.KICKSTART.is_encrypted:  # create separate boot partition
            GV.PARTITION.boot_part_size = GV.APP_linux_boot_partition_size
        GV.KICKSTART.ostree_args = GV.SELECTED_SPIN.ostree_args
        GV.KICKSTART.wifi_profiles = wifi_profiles
        GV.INSTALL_OPTIONS.keymap_timezone_source = tk_var.keymap_timezone_source_var.get()
        if GV.INSTALL_OPTIONS.keymap_timezone_source == 'ip':
            GV.KICKSTART.keymap = autoinst.get_keymaps(territory=GV.IP_LOCALE['country_code'])[0]
            GV.KICKSTART.keymap_type = 'xlayout'
            GV.KICKSTART.timezone = autoinst.langtable.list_timezones(territoryId=GV.IP_LOCALE['country_code'])[0]
        elif GV.INSTALL_OPTIONS.keymap_timezone_source == 'select':
            GV.KICKSTART.keymap = autoinst.get_keymaps(lang=GV.KICKSTART.locale)[0]
            GV.KICKSTART.keymap_type = 'xlayout'
            GV.KICKSTART.timezone = autoinst.langtable.list_timezones(languageId=GV.KICKSTART.locale)[0]
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

    installer_img.file_name = GV.INSTALL_ISO_NAME
    installer_img.file_hint = "installer_iso"
    installer_args.dl_files = [installer_img, ]

    if GV.SELECTED_SPIN.is_live_img:
        live_img.file_name = GV.LIVE_ISO_NAME
        live_img.file_hint = "live_img_iso"
        installer_args.dl_files.append(live_img)

    for file in installer_args.dl_files:
        if not hasattr(file, "file_name"):
            file.file_name = fn.get_file_name_from_url(file.dl_link)
        if not hasattr(file, "file_name"):
            file.file_name = fn.get_file_name_from_url(file.dl_link)
        if not hasattr(file, "hash256"):
            file.hash256 = ""
        else:  # for consistency
            file.hash256 = file.hash256.strip().lower()
        if not hasattr(file, "size"):
            file.size = 0

    installer_args.ks_kwargs = GV.KICKSTART
    installer_args.part_kwargs = GV.PARTITION
    installer_args.rpm_source_dir = GV.PATH.RPM_SOURCE_DIR
    installer_args.rpm_dest_dir_name = GV.PATH.RPM_DEST_DIR_NAME
    installer_args.grub_cfg_relative_path = GV.PATH.RELATIVE_GRUB_CFG
    installer_args.tmp_partition_label = GV.PARTITION.temp_part_label
    installer_args.kickstart_cfg_relative_path = GV.PATH.RELATIVE_KICKSTART
    installer_args.efi_file_relative_path = GV.APP_default_efi_file_path

    return page_installing.run(app, installer_args=installer_args)