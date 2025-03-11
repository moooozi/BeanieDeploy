# Functions that do multiple things or call multiple other functions are declared here

import os
import shutil
import subprocess
import types
import functions as fn
import globals as GV
import compatibility_checks
from models.spin import Spin


def partition_procedure(
    tmp_part_size: int,
    temp_part_label: str,
    queue=None,
    shrink_space: int = 0,
    boot_part_size: int = 0,
    efi_part_size: int = 0,
    make_root_partition: bool = False,
):
    ps_script = rf"{GV.PATH.SCRIPTS}\PartitionMappings.ps1"

    sys_drive_letter = fn.get_sys_drive_letter()
    sys_uuid_script = f"(({ps_script}) | Where-Object -Property DriveLetter -EQ {sys_drive_letter}).VolumeName"
    sys_drive_win_uuid = fn.run_powershell_script(sys_uuid_script)
    sys_drive_uuid = sys_drive_win_uuid[
        sys_drive_win_uuid.index("{") + 1 : sys_drive_win_uuid.index("}")
    ]
    sys_efi_uuid = fn.get_system_efi_drive_uuid()
    sys_disk_number = fn.get_disk_number(sys_drive_letter)
    if not (shrink_space and make_root_partition):
        shrink_space = tmp_part_size + efi_part_size + boot_part_size
    sys_drive_new_size = fn.get_drive_size_after_resize(
        sys_drive_letter, shrink_space + 1100000
    )
    fn.resize_partition(sys_drive_letter, sys_drive_new_size)
    if make_root_partition:
        root_space = shrink_space - (
            tmp_part_size + efi_part_size + boot_part_size + 1100000
        )
        fn.new_volume(sys_disk_number, root_space, "EXFAT", "ALLOC-ROOT")
    if boot_part_size:
        fn.new_volume(sys_disk_number, boot_part_size, "EXFAT", "ALLOC-BOOT")
    if efi_part_size:
        fn.new_volume(sys_disk_number, efi_part_size, "EXFAT", "ALLOC-EFI")
    tmp_part_letter = fn.get_unused_drive_letter()
    fn.new_volume(
        sys_disk_number, tmp_part_size, "FAT32", temp_part_label, tmp_part_letter
    )

    tmp_part_path_script = f'(({ps_script}) | Where-Object -Property DriveLetter -EQ "{tmp_part_letter}").DevicePath'
    tmp_part_device_path = fn.run_powershell_script(tmp_part_path_script)
    print("tmp_part_device_path: ", tmp_part_device_path)
    if queue:
        queue.put(tmp_part_letter)
    return {
        "tmp_part_letter": tmp_part_letter,
        "tmp_part_device_path": tmp_part_device_path,
        "sys_drive_uuid": sys_drive_uuid,
        "sys_drive_win_uuid": sys_drive_win_uuid,
        "sys_efi_uuid": sys_efi_uuid,
    }


def add_boot_entry(boot_efi_file_path, device_path, is_permanent: bool = False):
    bootguid = fn.create_new_wbm(boot_efi_file_path, device_path)
    fn.make_boot_entry_first(bootguid, is_permanent)


def build_autoinstall_ks_file(
    keymap=None,
    keymap_type="vc",
    locale=None,
    timezone=None,
    ostree_args=None,
    username="",
    fullname="",
    wifi_profiles_dir_name=None,
    is_encrypted: bool = False,
    passphrase: str = None,
    tpm_auto_unlock: bool = True,
    live_img_url="",
    additional_repos=True,
    sys_drive_uuid=None,
    sys_efi_uuid=None,
    partition_method=None,
    additional_rpm_dir=None,
):
    kickstart_lines = []
    kickstart_lines.append("# Kickstart file created by Lnixify.")
    kickstart_lines.append("graphical")
    kickstart_lines.append("# removing kickstart files containing sensitive data and")
    kickstart_lines.append("# reverting install media boot options")
    kickstart_lines.append("%post --nochroot --logfile=/mnt/sysimage/root/ks-post.log")
    kickstart_lines.append("rm /run/install/repo/ks.cfg")
    kickstart_lines.append(
        "cp /run/install/repo/EFI/BOOT/BOOT.cfg /run/install/repo/EFI/BOOT/grub.cfg"
    )
    kickstart_lines.append("%end")

    # Importing Wi-Fi profiles
    if wifi_profiles_dir_name:
        kickstart_lines.append("# Importing Wi-Fi profiles")
        kickstart_lines.append(
            "%post --nochroot --logfile=/mnt/sysimage/root/ks-post_wifi.log"
        )
        kickstart_lines.append(
            "mkdir -p /mnt/sysimage/etc/NetworkManager/system-connections"
        )
        kickstart_lines.append(
            f"cp /run/install/repo/{wifi_profiles_dir_name}/*.* /mnt/sysimage/etc/NetworkManager/system-connections"
        )
        kickstart_lines.append("%end")
    # Installing additional packages
    if additional_rpm_dir:
        install_command = "rpm-ostree install" if ostree_args else "dnf install"
        kickstart_lines.append("# Installing additional packages")
        kickstart_lines.append(
            "%post --nochroot --logfile=/mnt/sysimage/root/ks-post_additional_rpm1.log"
        )
        kickstart_lines.append("mkdir -p /mnt/sysimage/root/tmp_rpm")
        kickstart_lines.append(
            f"cp /run/install/repo/{additional_rpm_dir}/*.rpm /mnt/sysimage/root/tmp_rpm"
        )
        kickstart_lines.append("%end")
        kickstart_lines.append("%post --logfile=/root/ks-post_additional_rpm2.log")
        kickstart_lines.append(f"{install_command} /root/tmp_rpm/*.rpm -y")
        kickstart_lines.append("rm -rf /root/tmp_rpm")
        kickstart_lines.append("%end")
    # Activating encryption auto-unlock using TPM2 chip
    if is_encrypted and passphrase and tpm_auto_unlock:
        kickstart_lines.append("# Activating encryption auto-unlock using TPM2 chip")
        kickstart_lines.append("%post  --logfile=/root/ks-post_tpm2_unlock.log")
        kickstart_lines.append(
            f"PASSWORD={passphrase} systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7+8 $device"
        )
        kickstart_lines.append("sed -ie '/^luks-/s/$/,tpm2-device=auto/' /etc/crypttab")
        kickstart_lines.append("dracut -f")
        kickstart_lines.append("%end")

    if additional_repos:
        pass

    if keymap and locale and timezone:
        firstboot_line = "firstboot --enable"
        # if each of keymap, locale, timezone & username is provided, firstboot is no longer needed
        if username:
            firstboot_line = "firstboot --disable"
    else:
        firstboot_line = "firstboot --reconfig"
        if not keymap:
            keymap = "us"
        if not locale:
            locale = "en_US.UTF-8"
        if not timezone:
            timezone = "America/New_York"

    kickstart_lines.append(firstboot_line)

    if keymap_type == "vc":
        kickstart_lines.append(f"keyboard --vckeymap={keymap}")
    else:
        kickstart_lines.append(f"keyboard --xlayouts='{keymap}'")
    kickstart_lines.append(f"lang {locale}")
    kickstart_lines.append("firewall --use-system-defaults")
    if ostree_args:
        kickstart_lines.append(f"ostreesetup {ostree_args}")
    if live_img_url:
        kickstart_lines.append(f"liveimg --url='{live_img_url}' --noverifyssl")

    kickstart_lines.append(f"timezone {timezone} --utc")

    root_partition = "part btrfs.01"
    efi_partition = ""
    if partition_method == "dualboot":
        efi_partition = f"mount /dev/disk/by-partuuid/{sys_efi_uuid} /boot/efi "
        root_partition += " --onpart=/dev/disk/by-label/ALLOC-ROOT"
    elif partition_method == "replace_win":
        efi_partition = f"part /boot/efi --fstype=efi --label=efi --onpart=/dev/disk/by-partuuid/{sys_efi_uuid}"
        root_partition += f" --onpart=/dev/disk/by-partuuid/{sys_drive_uuid}"

    if is_encrypted:
        # separate boot partition if encryption is enabled
        boot_partition = "part /boot --fstype=ext4 --label=fedora_boot --onpart=/dev/disk/by-label/ALLOC-BOOT"
        root_partition += " --encrypted"
        if passphrase:
            root_partition += f" --passphrase={passphrase}"
    else:
        # create /boot subvolume inside root if encryption is disable
        boot_partition = "btrfs /boot --subvol --name=boot fedora"

    kickstart_lines.append(efi_partition)
    kickstart_lines.append(root_partition)
    kickstart_lines.append("btrfs none --label=fedora btrfs.01")
    kickstart_lines.append("btrfs / --subvol --name=root fedora")
    kickstart_lines.append("btrfs /home --subvol --name=home fedora")
    kickstart_lines.append("btrfs /var --subvol --name=var fedora")
    kickstart_lines.append(boot_partition)

    if username:
        kickstart_lines.append(
            f"user --name={username} --gecos='{fullname}' --groups=wheel"
        )
    kickstart_lines.append("rootpw --lock")
    kickstart_lines.append("reboot")

    kickstart_txt = ""
    for line in kickstart_lines:
        kickstart_txt += line + "\n"

    return kickstart_txt


def build_grub_cfg_file(root_partition_label, is_autoinst=False):
    grub_lines = [
        "### Grub configuration generated by Lnixify ###",
        'set default="0"',
        """function load_video {
            insmod efi_gop
            insmod efi_uga
            insmod video_bochs
            insmod video_cirrus
            insmod all_video
        }""",
        "load_video",
        "set gfxpayload=keep",
        "insmod gzio",
        "insmod part_gpt",
        "insmod ext2",
        "set timeout=5",
        f"search --no-floppy --set=root -l '{root_partition_label}'",
    ]

    menu_entries = [
        (
            "Install Fedora",
            "linuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% rd.live.check quiet",
            "initrdefi /images/pxeboot/initrd.img",
        ),
        (
            "Install Fedora (RAM-Boot)",
            "linuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% rd.live.check rd.live.ram quiet",
            "initrdefi /images/pxeboot/initrd.img",
        ),
        (
            "Install Fedora 36 in basic graphics mode",
            "linuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% nomodeset quiet",
            "initrdefi /images/pxeboot/initrd.img",
        ),
        (
            "Rescue a Fedora system",
            "linuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% inst.rescue quiet",
            "initrdefi /images/pxeboot/initrd.img",
        ),
    ]

    if is_autoinst:
        grub_lines.append(
            """menuentry 'Auto Install Fedora' --class fedora --class gnu-linux --class gnu --class os {
                linuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% rd.live.check inst.ks=hd:LABEL=%root_label% quiet
                initrdefi /images/pxeboot/initrd.img
            }"""
        )

    for title, linux_cmd, initrd_cmd in menu_entries[:2]:
        grub_lines.append(
            f"""menuentry '{title}' --class fedora --class gnu-linux --class gnu --class os {{
                {linux_cmd}
                {initrd_cmd}
            }}"""
        )

    grub_lines.append("submenu 'Troubleshooting -->' {")
    for title, linux_cmd, initrd_cmd in menu_entries[2:]:
        grub_lines.append(
            f"""    menuentry '{title}' --class fedora --class gnu-linux --class gnu --class os {{
                {linux_cmd}
                {initrd_cmd}
            }}"""
        )
    grub_lines.append("}")

    grub_file_text = "\n".join(grub_lines).replace("%root_label%", root_partition_label)
    return grub_file_text


def parse_spins(spins_list):
    accepted_spins_list = []
    live_os_base_index = None
    for index, current_spin in enumerate(spins_list):
        spin_keys = list(current_spin.keys())
        if not all(i in spin_keys for i in ("name", "size", "hash256", "dl_link")):
            continue
        current_spin["dl_link"] = GV.FEDORA_BASE_DOWNLOAD_URL + current_spin["dl_link"]
        if "torrent_link" in spin_keys:
            current_spin["torrent_link"] = (
                GV.FEDORA_TORRENT_DOWNLOAD_URL + current_spin["torrent_link"]
            )
        spin = Spin(
            name=current_spin.get("name"),
            size=current_spin.get("size"),
            hash256=current_spin.get("hash256"),
            dl_link=current_spin.get("dl_link"),
            is_live_img=current_spin.get("is_live_img", False),
            version=current_spin.get("version", ""),
            desktop=current_spin.get("desktop", ""),
            is_auto_installable=current_spin.get("is_auto_installable", False),
            is_advanced=current_spin.get("is_advanced", False),
            torrent_link=current_spin.get("torrent_link", ""),
            ostree_args=current_spin.get("ostree_args", ""),
            is_base_netinstall=current_spin.get("is_base_netinstall", False),
            is_default=current_spin.get("is_default", False),
            is_featured=current_spin.get("is_featured", False),
        )
        accepted_spins_list.append(spin)
    for index, spin in enumerate(accepted_spins_list):
        if spin.is_base_netinstall:
            live_os_base_index = index
            break
    if live_os_base_index is None:
        final_spin_list = []
        for index, spin in enumerate(accepted_spins_list):
            if spin.is_live_img:
                continue
            else:
                final_spin_list.append(spin)
    else:
        final_spin_list = accepted_spins_list
    return live_os_base_index, final_spin_list


def get_wifi_profiles(wifi_profile_dir):

    fn.rmdir(wifi_profile_dir)
    fn.mkdir(wifi_profile_dir)

    fn.extract_wifi_profiles(wifi_profile_dir)
    wifi_profiles = []
    for filename in os.listdir(wifi_profile_dir):
        try:
            with open(
                os.path.join(wifi_profile_dir, filename), "r"
            ) as f:  # open in readonly mode
                xml_file = f.read()
                wifi_profile: dict = fn.parse_xml(xml_file)
                name = wifi_profile["WLANProfile"]["name"]
                ssid = wifi_profile["WLANProfile"]["SSIDConfig"]["SSID"]["name"]
                if (key := "nonBroadcast") in (
                    attr := wifi_profile["WLANProfile"]["SSIDConfig"]
                ) and attr[key] == "true":
                    hidden = "true"
                else:
                    hidden = "false"
                password_type = wifi_profile["WLANProfile"]["MSM"]["security"][
                    "sharedKey"
                ]["keyType"]
                password = wifi_profile["WLANProfile"]["MSM"]["security"]["sharedKey"][
                    "keyMaterial"
                ]
                profile = {
                    "name": name,
                    "ssid": ssid,
                    "hidden": hidden,
                    "password": password,
                }
                wifi_profiles.append(profile)
        except KeyError:
            print("Note: a wifi profile could not be exported, so it will be skipped")
            continue
    fn.rmdir(wifi_profile_dir)
    fn.mkdir(wifi_profile_dir)
    return wifi_profiles


def check_valid_existing_file(file_path, file_hash):
    if not os.path.isfile(file_path):
        return False
    if fn.get_sha256_hash(file_path).lower() == file_hash.lower():
        return True
    else:
        os.remove(file_path)
        return None


def initiate_kickstart_arguments_from_user_input(
    autoinstall: dict, install_options: dict
):
    pass
