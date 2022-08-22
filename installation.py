import functions as fn
import procedure as prc
import globals as GV


def download_hash_handler(dl_hash, work_dir):
    go_next = False
    yes_responses = ('y', 'yes')
    if dl_hash == 1:
        go_next = True
    elif dl_hash == -1:
        question = input('checksum verification failed, continue anyways? y/n')
        if question.lower() in yes_responses:
            go_next = True
        else:
            question = input('cleanup? y/n')
            if question.lower() in yes_responses:
                fn.rmdir(work_dir)
            fn.app_quit()
    else:
        question = input('checksum mismatch, retry? y/n')
        if question != 'y':
            question = input('cleanup? y/n')
            if question.lower() in yes_responses:
                fn.rmdir(work_dir)
            fn.app_quit()
    return go_next


def queue_safe_put(queue, data):
    if queue:
        queue.put(data)


def download_and_track_spin(aria2_path, url, destination, expected_sha256_hash=None,
                            new_file_name=None, queue=None):
    fn.download_with_aria2(aria2_path, url=url, destination=destination, output_name=new_file_name, queue=queue)
    if new_file_name:
        file_path = destination + '\\' + new_file_name
    else:
        file_path = destination + '\\' + fn.get_file_name_from_url(url)
    if expected_sha256_hash:
        queue_safe_put(queue, 'STAGE: verifying_checksum')
        hash_result = fn.check_hash(file_path=file_path, sha256_hash=expected_sha256_hash)
    else:
        hash_result = 1

    return file_path, hash_result


def install(work_dir, aria2_path, ks_kwargs: dict, part_kwargs: dict,
            installer_iso_name, installer_iso_path, installer_iso_url, installer_img_hash256=None,
            live_img_iso_name=None, live_img_iso_path=None, live_img_iso_url=None, live_img_hash256=None,
            rpm_source_dir=None, rpm_dest_dir_name=None,
            queue=None):
    # INSTALL STARTING
    fn.mkdir(work_dir)
    live_img_required = bool(live_img_iso_url)
    installer_exist = prc.check_valid_existing_file(installer_iso_path, installer_img_hash256)
    live_img_exist = live_img_required and prc.check_valid_existing_file(live_img_iso_path, live_img_hash256)
    if not installer_exist:
        while True:
            queue_safe_put(queue, 'STAGE: downloading')
            file_path, checksum = download_and_track_spin(aria2_path, url=installer_iso_url, destination=work_dir,
                                                          new_file_name=installer_iso_name,
                                                          expected_sha256_hash=installer_img_hash256,
                                                          queue=queue)
            if download_hash_handler(checksum, work_dir):
                break  # re-download if file checksum didn't match expected, continue otherwise
    if live_img_required and not live_img_exist:
        while True:
            queue_safe_put(queue, 'STAGE: downloading')
            file_path, checksum = download_and_track_spin(aria2_path, url=live_img_iso_url, destination=work_dir,
                                                          new_file_name=live_img_iso_name,
                                                          expected_sha256_hash=live_img_hash256,
                                                          queue=queue)
            if download_hash_handler(checksum, work_dir):
                break  # re-download if file checksum didn't match expected, continue otherwise

    queue_safe_put(queue, 'APP: critical_process_running')
    queue_safe_put(queue, 'STAGE: creating_tmp_part')

    tmp_part_letter = prc.partition_procedure(**part_kwargs)

    queue_safe_put(queue, 'APP: critical_process_done')
    queue_safe_put(queue, 'STAGE: copying_to_tmp_part')

    installer_mount_letter = fn.mount_iso(installer_iso_path)
    source_files = installer_mount_letter + ':\\'
    destination = tmp_part_letter + ':\\'
    fn.copy_files(source=source_files, destination=destination)
    if live_img_iso_url:
        live_img_mount_letter = fn.mount_iso(live_img_iso_path)
        source_files = live_img_mount_letter + ':\\LiveOS\\'
        destination = tmp_part_letter + ':\\LiveOS\\'
        fn.copy_files(source=source_files, destination=destination)

    if rpm_source_dir and rpm_dest_dir_name:
        rpm_dest_path = '%s:\\%s\\' % (tmp_part_letter, rpm_dest_dir_name)
        fn.copy_files(source=rpm_source_dir, destination=rpm_dest_path)

    queue_safe_put(queue, 'STAGE: adding_tmp_boot_entry')

    if GV.KICKSTART.partition_method != 'custom':
        grub_cfg_file = GV.PATH.GRUB_CONFIG_AUTOINST
    else:
        grub_cfg_file = GV.PATH.GRUB_CONFIG_DEFUALT
    grub_cfg_dest_path = tmp_part_letter + ':\\' + GV.PATH.RELATIVE_GRUB_CFG
    fn.set_file_readonly(grub_cfg_dest_path, False)
    fn.copy_and_rename_file(grub_cfg_file, grub_cfg_dest_path)
    grub_cfg_txt = prc.build_grub_cfg_file(GV.TMP_PARTITION_LABEL,
                                           GV.KICKSTART.partition_method != 'custom')
    fn.set_file_readonly(grub_cfg_dest_path, False)
    grub_cfg = open(grub_cfg_dest_path, 'w')
    grub_cfg.write(grub_cfg_txt)
    grub_cfg.close()
    fn.set_file_readonly(grub_cfg_dest_path, True)
    nvidia_script_dest_path = tmp_part_letter + ':\\%s' % GV.PATH.RELATIVE_NVIDIA_SCRIPT
    fn.copy_and_rename_file(GV.PATH.NVIDIA_SCRIPT, nvidia_script_dest_path)

    if GV.KICKSTART.partition_method != 'custom':
        kickstart_txt = prc.build_autoinstall_ks_file(**ks_kwargs)
        if kickstart_txt:
            kickstart = open(tmp_part_letter + ':\\%s' % GV.PATH.RELATIVE_KICKSTART, 'w')
            kickstart.write(kickstart_txt)
            kickstart.close()

    queue_safe_put(queue, 'APP: critical_process_running')  # prevent closing the app

    if GV.KICKSTART.partition_method == 'clean':
        is_new_boot_order_permanent = True
    else:
        is_new_boot_order_permanent = False
    boot_kwargs = {'boot_efi_file_path': GV.APP.default_efi_file_path,
                   'boot_drive_letter': tmp_part_letter,
                   'is_permanent': is_new_boot_order_permanent}
    prc.add_boot_entry(**boot_kwargs)
    # step 5: clean up iso and other downloaded files since install is complete
    fn.unmount_iso(installer_iso_path)
    fn.unmount_iso(live_img_iso_path)
    fn.remove_drive_letter(tmp_part_letter)
    # fn.rmdir(DOWNLOAD_PATH)
    fn.set_windows_time_to_utc()

    queue_safe_put(queue, 'APP: critical_process_done')  # re-enable closing the app
    queue_safe_put(queue, 'STAGE: install_done')
    return True
