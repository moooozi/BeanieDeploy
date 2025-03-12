import os
from pathlib import Path
import shutil
import subprocess
import time
import functions as fn
import procedure as prc
import globals as GV


def download_hash_handler(file_hash, expected_hash, work_dir, queue=None):
    file_hash = file_hash.strip().lower()
    expected_hash = expected_hash.strip().lower()
    if not expected_hash:
        return True
    if file_hash == expected_hash:
        return True
    error = "failed" if not file_hash else "mismatch"
    response = {"go_next": False, "cleanup": False, "app_quit": False}
    if queue:  # for GUI mode
        response_dict = {
            "error": error,
            "file_hash": file_hash,
            "expected_hash": expected_hash,
        }
        queue.put(("ERR: checksum", response_dict))
        # Wait to make sure the front end receives ur Queue and not u receive your own.
        time.sleep(2)
        while True:
            while queue.qsize() == 0:
                pass
            _response = queue.get()
            if isinstance(_response, dict) and "go_next" in _response.keys():
                response = _response
                print(response)
                break
    else:  # for CLI mode
        yes_responses = ("y", "yes")
        if file_hash == "":
            question = input("checksum verification failed, continue anyways? y/n  ")
            if question.lower() in yes_responses:
                response["go_next"] = True
            else:
                question = input("cleanup? y/n  ")
                if question.lower() in yes_responses:
                    response["cleanup"] = True
                response["app_quit"] = True
        else:
            question = input("checksum mismatch, retry? y/n  ")
            if question.lower() not in yes_responses:
                question = input("cleanup? y/n  ")
                if question.lower() in yes_responses:
                    response["cleanup"] = True
                response["app_quit"] = True

    if response["go_next"]:
        return True
    if response["cleanup"]:
        fn.rmdir(work_dir)
    if response["app_quit"]:
        fn.app_quit()  # This will only exit the backend process


def queue_safe_put(queue, data):
    if queue:
        queue.put(data)


def install(
    work_dir,
    ks_kwargs: GV.Kickstart,
    part_kwargs,
    dl_files,
    rpm_source_dir=None,
    rpm_dst_dir_name=None,
    grub_cfg_relative_path=None,
    tmp_partition_label=None,
    kickstart_cfg_relative_path=None,
    efi_file_relative_path=None,
    wifi_profiles_src_dir=None,
    wifi_profiles_dst_dir_name=None,
    queue=None,
):
    # INSTALL STARTING
    fn.mkdir(work_dir)
    installer_iso_path = ""
    live_image_required = False
    live_img_iso_path = ""
    for file in dl_files:
        fn.mkdir(file.dst_dir)
        file_path = rf"{file.dst_dir}\{file.file_name}"
        # Logic for special files with a hint
        if hasattr(file, "file_hint") and (hint := file.file_hint):
            if hint == "installer_iso":
                installer_iso_path = file_path
            elif hint == "live_img_iso":
                live_img_iso_path = file_path
                live_image_required = True

        file_already_exists = False
        if os.path.isfile(file_path):
            if file.hash256 == fn.get_sha256_hash(file_path):
                file_already_exists = True
            else:
                os.remove(file_path)
        if file_already_exists is True:
            queue.put(
                {
                    "type": "dl_tracker",
                    "file_name": file.file_name,
                    "status": "complete",
                }
            )
            continue
        while True:
            queue_safe_put(queue, "STAGE: downloading")
            fn.download_with_standard_lib(
                url=file.dl_link,
                destination=file.dst_dir,
                output_name=file.file_name,
                queue=queue,
            )
            queue_safe_put(queue, "STAGE: verifying_checksum")
            actual_file_hash = fn.get_sha256_hash(file_path)
            if not file.hash256 or download_hash_handler(
                actual_file_hash, file.hash256, work_dir, queue
            ):
                break  # exit the loop if the file matches the criteria
            # remove the file and re-download otherwise
            os.remove(file_path)

    queue_safe_put(queue, "APP: critical_process_running")
    queue_safe_put(queue, "STAGE: creating_tmp_part")

    partitioning_results = prc.partition_procedure(**vars(part_kwargs))
    tmp_part_letter = partitioning_results["tmp_part_letter"]
    tmp_part_device_path = partitioning_results["tmp_part_device_path"]
    sys_drive_uuid = partitioning_results["sys_drive_uuid"]
    sys_efi_uuid = partitioning_results["sys_efi_uuid"]

    queue_safe_put(queue, "APP: critical_process_done")
    queue_safe_put(queue, "STAGE: copying_to_tmp_part")

    installer_mount_letter = fn.mount_iso(installer_iso_path)
    source_files = installer_mount_letter + ":\\"
    destination = tmp_part_letter + ":\\"

    # Copy the boot loader to the EFI partition
    bootloader_src_path = Path(source_files) / "EFI" / "BOOT"
    efi_partition = fn.get_system_efi_drive_uuid()
    efi_mount_letter = fn.get_unused_drive_letter()
    bootloader_dst_path = Path(f"{efi_mount_letter}:\\EFI\\{GV.APP_SW_NAME}")

    command = ["mountvol", f"{efi_mount_letter}:", rf"\\?\Volume{{{efi_partition}}}"]
    # Mount the EFI partition
    out = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    # Check if the mount was successful
    if out.returncode != 0:
        raise RuntimeError(f"Failed to mount EFI partition: {out.stderr}")

    # Create the destination directory if it doesn't exist
    print(f"Creating destination directory: {bootloader_dst_path}")
    try:
        if bootloader_dst_path.exists():
            shutil.rmtree(bootloader_dst_path)
        bootloader_dst_path.mkdir(parents=True, exist_ok=True)

        # Copy the contents of the bootloader directory
        for item in bootloader_src_path.iterdir():
            dest = bootloader_dst_path / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

        # Unmount the EFI partition
        subprocess.run(["mountvol", f"{efi_mount_letter}:", "/D"], check=True)

        shutil.copytree(source_files, destination, dirs_exist_ok=True)

        if live_image_required:
            live_img_mount_letter = fn.mount_iso(live_img_iso_path)
            source_files = live_img_mount_letter + ":\\LiveOS\\"
            destination = tmp_part_letter + ":\\LiveOS\\"
            shutil.copytree(source_files, destination, dirs_exist_ok=True)

        if rpm_source_dir and rpm_dst_dir_name:
            rpm_dst_path = f"{tmp_part_letter}:\\{rpm_dst_dir_name}\\"
            fn.mkdir(rpm_dst_path)
            fn.copy_files(source=rpm_source_dir, destination=rpm_dst_path)

        if wifi_profiles_src_dir and wifi_profiles_dst_dir_name:
            wifi_profiles_dst_path = (
                f"{tmp_part_letter}:\\{wifi_profiles_dst_dir_name}\\"
            )
            fn.copy_files(
                source=wifi_profiles_src_dir, destination=wifi_profiles_dst_path
            )
        queue_safe_put(queue, "STAGE: adding_tmp_boot_entry")

        grub_cfg_dest_path = bootloader_dst_path / "grub.cfg"
        fn.set_file_readonly(grub_cfg_dest_path, False)
        grub_cfg_txt = prc.build_grub_cfg_file(
            tmp_partition_label, ks_kwargs.partition_method != "custom"
        )
        with open(grub_cfg_dest_path, "w") as grub_cfg:
            grub_cfg.write(grub_cfg_txt)
        fn.set_file_readonly(grub_cfg_dest_path, True)
        if not ks_kwargs.partition_method == "custom":
            kickstart_txt = prc.build_autoinstall_ks_file(**vars(ks_kwargs))
            with open(
                tmp_part_letter + ":\\%s" % kickstart_cfg_relative_path, "w"
            ) as kickstart:
                kickstart.write(kickstart_txt)

        queue_safe_put(
            queue, "APP: critical_process_running"
        )  # prevent closing the app

        # Drive Letter no longer needed, so we remove it
        fn.remove_drive_letter(tmp_part_letter)

        is_new_boot_order_permanent = (
            True if ks_kwargs.partition_method == "replace_win" else False
        )

        boot_kwargs = {
            "boot_efi_file_path": efi_file_relative_path,
            "device_path": tmp_part_device_path,
            "is_permanent": is_new_boot_order_permanent,
        }

        boot_current = fn.get_boot_current()
        list_boot_entries = fn.get_boot_entries()
        reference_entry = None
        # if the boot entry exists in the list of boot entries with the description "Windows Boot Manager"
        # then we can use this as a reference
        # Otherwise, look for the boot entry with name "Windows Boot Manager" and use that as a reference
        for entry in list_boot_entries:
            if entry["description"] == "Windows Boot Manager":
                reference_entry = entry["entry_id"][4:]  # remove the "Boot" prefix
                if entry["entry_id"] == f"Boot{boot_current}":
                    break
        if reference_entry is None:
            raise RuntimeError("Windows Boot Manager entry not found")

        new_boot_entry = fn.create_boot_entry(
            "Fedora Recovery",
            efi_file_relative_path,
            reference_entry,
        )
        fn.set_bootnext(new_boot_entry)
        # unmount and clean up iso and other downloaded files since installation is now complete
        fn.unmount_iso(installer_iso_path)
        fn.unmount_iso(live_img_iso_path)

        # fn.rmdir(DOWNLOAD_PATH)
        # fn.set_windows_time_to_utc()

        queue_safe_put(queue, "APP: critical_process_done")  # re-enable closing the app
        queue_safe_put(queue, "STAGE: install_done")
    except Exception as e:

        # unmount and throw the error back
        fn.unmount_iso(installer_iso_path)
        fn.unmount_iso(live_img_iso_path)
        command = ["mountvol", f"{efi_mount_letter}:", "/D"]
        # Unmount the EFI partition
        out = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
        raise
    return True
