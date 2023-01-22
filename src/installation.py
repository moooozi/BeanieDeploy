import multiprocessing
import functions as fn
import procedure as prc
#import globals as GV


def download_hash_handler(file_hash, expected_hash, work_dir, queue=None):
    file_hash = file_hash.strip().lower()
    expected_hash = expected_hash.strip().lower()
    if not expected_hash:
        return True
    if file_hash == expected_hash:
        return True
    error = 'mismatch'
    if not file_hash:
        error = 'failed'
    response = {'go_next': False, 'cleanup': False, 'app_quit': False}
    if queue:  # for GUI mode
        response_queue = multiprocessing.Queue()
        response_dict = {'error': error, 'file_hash': file_hash, 'expected_hash': expected_hash}
        queue.put(('ERR: checksum', response_dict, response_queue))
        while response_queue.qsize() == 0: pass
        response = response_queue.get()
    else:  # for CLI mode
        yes_responses = ('y', 'yes')
        if file_hash == '':
            question = input('checksum verification failed, continue anyways? y/n  ')
            if question.lower() in yes_responses:
                response['go_next'] = True
            else:
                question = input('cleanup? y/n  ')
                if question.lower() in yes_responses:
                    response['cleanup'] = True
                response['app_quit'] = True
        else:
            question = input('checksum mismatch, retry? y/n  ')
            if question.lower() not in yes_responses:
                question = input('cleanup? y/n  ')
                if question.lower() in yes_responses:
                    response['cleanup'] = True
                response['app_quit'] = True

    if response['go_next']: return True
    if response['cleanup']: fn.rmdir(work_dir)
    if response['app_quit']: fn.app_quit()


def queue_safe_put(queue, data):
    if queue: queue.put(data)


def download_spin_and_get_checksum(aria2_path, url, destination, new_file_name=None, queue=None):
    queue_safe_put(queue, 'STAGE: downloading')
    fn.download_with_aria2(aria2_path, url=url, destination=destination, output_name=new_file_name, queue=queue)
    if new_file_name:
        file_path = destination + '\\' + new_file_name
    else:
        file_path = destination + '\\' + fn.get_file_name_from_url(url)

    queue_safe_put(queue, 'STAGE: verifying_checksum')
    return fn.get_sha256_hash(file_path=file_path)


def install(work_dir, aria2_path, ks_kwargs, part_kwargs,
            dl_files, rpm_source_dir=None, rpm_dest_dir_name=None,
            queue=None, grub_cfg_relative_path=None,
            tmp_partition_label=None, kickstart_cfg_relative_path=None, efi_file_relative_path=None):
    # INSTALL STARTING
    fn.mkdir(work_dir)
    installer_iso_path = ""
    live_image_required = False
    live_img_iso_path = ""
    for file in dl_files:
        if not hasattr(file, "file_name"):
            file.file_name = fn.get_file_name_from_url(file.dl_link)
        if not hasattr(file, "file_name"):
            file.file_name = fn.get_file_name_from_url(file.dl_link)
        if not hasattr(file, "hash256"):
            file.hash256 = ""
        file_path = fr"{file.dl_path}\{file.file_name}"
        # Logic for special files with a hint
        if hasattr(file, "file_hint") and (hint := file.file_hint):
            if hint == "installer_iso":
                installer_iso_path = file_path
            elif hint == "live_img_iso":
                live_img_iso_path = file_path
                live_image_required = True

        file_exists = prc.check_valid_existing_file(file_path, file.hash256)
        if file_exists: continue
        while True:
            file_hash = download_spin_and_get_checksum(aria2_path, file.dl_link, work_dir,
                                                       file.file_name, queue)
            if not file.hash256 or download_hash_handler(file_hash, file.hash256, work_dir, queue):
                break  # this will re-download if file checksum didn't match expected, and continue otherwise

    queue_safe_put(queue, 'APP: critical_process_running')
    queue_safe_put(queue, 'STAGE: creating_tmp_part')

    partitioning_results = prc.partition_procedure(**vars(part_kwargs))
    tmp_part_letter = partitioning_results['tmp_part_letter']
    tmp_part_device_path = partitioning_results['tmp_part_device_path']
    sys_drive_uuid = partitioning_results['sys_drive_uuid']
    sys_drive_win_uuid = partitioning_results['sys_drive_win_uuid']

    ks_kwargs.sys_drive_uuid = partitioning_results['sys_drive_uuid']
    ks_kwargs.sys_efi_uuid = partitioning_results['sys_efi_uuid']

    queue_safe_put(queue, 'APP: critical_process_done')
    queue_safe_put(queue, 'STAGE: copying_to_tmp_part')

    installer_mount_letter = fn.mount_iso(installer_iso_path)
    source_files = installer_mount_letter + ':\\'
    destination = tmp_part_letter + ':\\'
    fn.copy_files(source=source_files, destination=destination)
    if live_image_required:
        live_img_mount_letter = fn.mount_iso(live_img_iso_path)
        source_files = live_img_mount_letter + ':\\LiveOS\\'
        destination = tmp_part_letter + ':\\LiveOS\\'
        fn.copy_files(source=source_files, destination=destination)

    if rpm_source_dir and rpm_dest_dir_name:
        rpm_dest_path = '%s:\\%s\\' % (tmp_part_letter, rpm_dest_dir_name)
        fn.copy_files(source=rpm_source_dir, destination=rpm_dest_path)

    queue_safe_put(queue, 'STAGE: adding_tmp_boot_entry')

    grub_cfg_dest_path = tmp_part_letter + ':\\' + grub_cfg_relative_path
    fn.set_file_readonly(grub_cfg_dest_path, False)
    grub_cfg_txt = prc.build_grub_cfg_file(tmp_partition_label,
                                           ks_kwargs.partition_method != 'custom')
    fn.set_file_readonly(grub_cfg_dest_path, False)
    with open(grub_cfg_dest_path, 'w') as grub_cfg:
        grub_cfg.write(grub_cfg_txt)
    fn.set_file_readonly(grub_cfg_dest_path, True)
    if not ks_kwargs.partition_method == 'custom':
        kickstart_txt = prc.build_autoinstall_ks_file(**vars(ks_kwargs))
        with open(tmp_part_letter + ':\\%s' % kickstart_cfg_relative_path, 'w') as kickstart:
            kickstart.write(kickstart_txt)

    queue_safe_put(queue, 'APP: critical_process_running')  # prevent closing the app


    # Getting temporary partition's DevicePath, like e.g. "\Device\HarddiskVolume5"

    # Drive Letter no longer needed, so we remove it
    fn.remove_drive_letter(tmp_part_letter)

    is_new_boot_order_permanent = True if ks_kwargs.partition_method == 'clean' else False

    boot_kwargs = {'boot_efi_file_path': efi_file_relative_path,
                   'device_path': tmp_part_device_path,
                   'is_permanent': is_new_boot_order_permanent}
    prc.add_boot_entry(**boot_kwargs)
    # unmount and clean up iso and other downloaded files since installation is now complete
    fn.unmount_iso(installer_iso_path)
    fn.unmount_iso(live_img_iso_path)

    # fn.rmdir(DOWNLOAD_PATH)
    fn.set_windows_time_to_utc()

    queue_safe_put(queue, 'APP: critical_process_done')  # re-enable closing the app
    queue_safe_put(queue, 'STAGE: install_done')
    return True
