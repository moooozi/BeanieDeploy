# Functions that do multiple things or call multiple other functions are declared here

import os
import types
import multiprocessing

import functions as fn


def compatibility_test(required_space_min, queue):
    # check starting...
    queue.put('arch')
    check = fn.check_arch()
    if check.returncode != 0:
        result_arch_check = -1
    else:
        result_arch_check = check.stdout.strip().lower()
    queue.put('uefi')
    check = fn.check_uefi()
    if check.returncode != 0:
        result_uefi_check = -1
    elif 'uefi' in check.stdout.lower():
        result_uefi_check = 1
    else:
        result_uefi_check = 0
    queue.put('ram')
    check = fn.check_totalram()
    if check.returncode != 0:
        result_totalram_check = -1
    else:
        result_totalram_check = int(check.stdout.strip())
    queue.put('space')
    check = fn.check_space()
    if check.returncode != 0:
        result_space_check = -1
    else:
        result_space_check = int(check.stdout.strip())

    if result_space_check > required_space_min:
        queue.put('resizable')
        check = fn.check_resizable()
        if check.returncode != 0:
            result_resizable_check = -1
        else:
            result_resizable_check = int(check.stdout.strip())
    else:
        result_resizable_check = -2

    check_results = {'uefi': result_uefi_check,
                     'ram': result_totalram_check,
                     'space': result_space_check,
                     'resizable': result_resizable_check,
                     'arch': result_arch_check}
    if queue: queue.put(check_results)
    else: return check_results


def partition_procedure(tmp_part_size: int, temp_part_label: str, queue, shrink_space: int = None,
                        boot_part_size: int = None, efi_part_size: int = None):
    sys_drive_letter = fn.get_sys_drive_letter()
    print(fn.relabel_volume(sys_drive_letter, 'WindowsOS'))
    sys_disk_number = fn.get_disk_number(sys_drive_letter)
    if shrink_space is None:
        shrink_space = tmp_part_size
    sys_drive_new_size = fn.get_drive_size_after_resize(sys_drive_letter, shrink_space + 1100000)
    fn.resize_partition(sys_drive_letter, sys_drive_new_size)
    if efi_part_size and boot_part_size and shrink_space:
        root_space = shrink_space - (tmp_part_size + efi_part_size + boot_part_size + 1100000)
        fn.new_volume(sys_disk_number, root_space, 'EXFAT', 'ALLOC-ROOT')
        fn.new_volume(sys_disk_number, boot_part_size, 'EXFAT', 'ALLOC-BOOT')
        fn.new_volume(sys_disk_number, efi_part_size, 'EXFAT', 'ALLOC-EFI')
    tmp_part_letter = fn.get_unused_drive_letter()
    fn.new_volume(sys_disk_number, tmp_part_size, 'FAT32', temp_part_label, tmp_part_letter)
    queue.put((1, tmp_part_letter))


def add_boot_entry(boot_efi_file_path, boot_drive_letter, is_permanent: bool = False, queue=None):

    bootguid = fn.create_new_wbm(boot_efi_file_path, boot_drive_letter)
    fn.make_boot_entry_first(bootguid, is_permanent)
    if queue: queue.put(1)
    else:
        return 1


def build_autoinstall_ks_file(keymap=None, keymap_type='vc', lang=None, timezone=None, ostree_args=None, username='', fullname='',
                              wifi_profiles=None, is_encrypted: bool = False, passphrase: str = None,
                              tpm_auto_unlock: bool = True, live_img_url='', nvidia_drivers=True, additional_repos=True,
                              partition_method=None, additional_rpm_dir=None):
    kickstart_lines = []
    kickstart_lines.append("# Kickstart file created by Lnixify.")
    kickstart_lines.append("graphical")
    kickstart_lines.append("# removing kickstart files containing sensitive data and")
    kickstart_lines.append("# reverting install media boot options")
    kickstart_lines.append("%post --nochroot --logfile=/mnt/sysimage/root/ks-post.log")
    kickstart_lines.append("rm /run/install/repo/ks.cfg")
    kickstart_lines.append("cp /run/install/repo/EFI/BOOT/BOOT.cfg /run/install/repo/EFI/BOOT/grub.cfg")
    kickstart_lines.append("%end")

    # Importing Wi-Fi profiles
    if wifi_profiles and isinstance(wifi_profiles, list):
        kickstart_lines.append("# Importing Wi-Fi profiles")
        kickstart_lines.append("%post --nochroot --logfile=/mnt/sysimage/root/ks-post_wifi.log")
        kickstart_lines.append("mkdir -p /mnt/sysimage/etc/NetworkManager/system-connections")
        template = r"""[connection]\nid=%name%\ntype=wifi\n\n[wifi]\nhidden=%hidden%\nssid=%ssid%\n\n[wifi-security]\nkey-mgmt=wpa-psk\npsk=%password%\n\n[ipv4]\nmethod=auto\n\n[ipv6]\naddr-gen-mode=stable-privacy\nmethod=auto\n\n[proxy]\n"""
        for index, profile in enumerate(wifi_profiles):
            network_file = template.replace('%name%', profile['name']).replace('%ssid%', profile['ssid']).replace('%hidden%', profile['hidden']).replace('%password%', profile['password'])
            kickstart_lines.append("echo $'" + network_file + \
                             "' > " + "/mnt/sysimage/etc/NetworkManager/system-connections/imported_wifi%s.nmconnection" % str(index))
        kickstart_lines.append("%end")
    # if nvidia_drivers:
    #    kickstart_lines.append("mkdir -p /mnt/sysimage/etc/profile.d/")
    #    kickstart_lines.append("cp /run/install/repo/lnixify/nvidia_inst /mnt/sysimage/etc/profile.d/nvidia_inst.sh")
    if additional_rpm_dir:
        kickstart_lines.append("# Installing additional packages")
        kickstart_lines.append("%post --nochroot --logfile=/mnt/sysimage/root/ks-post_additional_rpm.log")
        kickstart_lines.append("mkdir -p /mnt/sysimage/home/tmp_rpm")
        kickstart_lines.append("cp /run/install/repo/" + additional_rpm_dir + '/* /mnt/sysimage/home/tmp_rpm')
        kickstart_lines.append("chroot /mnt/sysimage/")
        kickstart_lines.append("dnf install /home/tmp_rpm/*.rpm -y")
        kickstart_lines.append("rm -rf /home/tmp_rpm")
        kickstart_lines.append("%end")
    if is_encrypted and passphrase and tpm_auto_unlock:
        kickstart_lines.append("# Activating encryption auto-unlock using TPM2 chip")
        kickstart_lines.append("%post --nochroot --logfile=/mnt/sysimage/root/ks-post_tpm2_unlock.log")
        kickstart_lines.append("chroot /mnt/sysimage/")
        kickstart_lines.append("PASSWORD=%s systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7+8 $device" % passphrase)
        kickstart_lines.append("sed -ie '/^luks-/s/$/,tpm2-device=auto/' /etc/crypttab")
        kickstart_lines.append("dracut -f")
        kickstart_lines.append("%end")
    '''
    if additional_repos:
        kickstart_lines.append("# Activating unrestricted Flatpak")
        kickstart_lines.append("%post --nochroot --logfile=/mnt/sysimage/root/ks-post_additional_repos.log")
        kickstart_lines.append("chroot /mnt/sysimage/")
        kickstart_lines.append("flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo")
        kickstart_lines.append("%end")
    '''

    if not (keymap and lang and timezone):
        if not keymap: keymap = 'us'
        if not lang: lang = 'en_US.UTF-8'
        if not timezone: timezone = 'America/New_York'
        kickstart_lines.append("firstboot --reconfig")
    else:
        kickstart_lines.append("firstboot --enable")

    if keymap_type == 'vc':
        kickstart_lines.append("keyboard --vckeymap=%s" % keymap)
    else:
        kickstart_lines.append("keyboard --xlayouts='%s'" % keymap)
    kickstart_lines.append("lang " + lang)
    kickstart_lines.append("firewall --use-system-defaults")
    if ostree_args:
        kickstart_lines.append("ostreesetup " + ostree_args)
    if live_img_url:
        kickstart_lines.append("liveimg --url='%s' --noverifyssl" % live_img_url)

    kickstart_lines.append("timezone " + timezone + " --utc")

    if partition_method == 'clean':
        kickstart_lines.append("clearpart --all")
    root_partition = "part btrfs.01 --onpart=/dev/disk/by-label/ALLOC-ROOT"
    if is_encrypted:
        root_partition += ' --encrypted'
        if passphrase:
            root_partition += ' --passphrase=' + passphrase

    kickstart_lines.append(root_partition)
    kickstart_lines.append("btrfs none --label=fedora btrfs.01")
    kickstart_lines.append("btrfs / --subvol --name=root fedora")
    kickstart_lines.append("btrfs /home --subvol --name=home fedora")
    kickstart_lines.append("btrfs /var --subvol --name=var fedora")
    kickstart_lines.append("part /boot --fstype=ext4 --label=fedora_boot --onpart=/dev/disk/by-label/ALLOC-BOOT ")
    kickstart_lines.append("part /boot/efi --fstype=efi --label=fedora_efi --onpart=/dev/disk/by-label/ALLOC-EFI")

    if username:
        kickstart_lines.append("user --name=" + username + " --gecos='" + fullname + "' --groups=wheel")
    kickstart_lines.append("rootpw --lock")
    kickstart_lines.append("reboot")

    kickstart_txt = ""
    for line in kickstart_lines:
        kickstart_txt += line + '\n'

    return kickstart_txt


def build_grub_cfg_file(root_partition_label, is_autoinst=False):
    grub_lines = []
    grub_lines.append("""### Grub configuration generated by Lnixify ###""")
    grub_lines.append("""set default="0")""")
    grub_lines.append("""function load_video {
                            \n  insmod efi_gop
                            \n  insmod efi_uga
                            \n  insmod video_bochs
                            \n  insmod video_cirrus
                            \n  insmod all_video\n}""")
    grub_lines.append("""load_video""")
    grub_lines.append("""set gfxpayload=keep""")
    grub_lines.append("""insmod gzio""")
    grub_lines.append("""insmod part_gpt""")
    grub_lines.append("""insmod ext2""")
    grub_lines.append("""set timeout=5""")
    grub_lines.append("""search --no-floppy --set=root -l '%root_label%'\n""")
    if is_autoinst:
        grub_lines.append("""menuentry 'Auto Install Fedora 36' --class fedora --class gnu-linux --class gnu --class os {
                            \n\tlinuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% rd.live.check inst.ks=hd:LABEL=%root_label% quiet
                            \n\tinitrdefi /images/pxeboot/initrd.img \n}""")

    grub_lines.append("""menuentry 'Install Fedora 36' --class fedora --class gnu-linux --class gnu --class os {
                            \n\tlinuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% rd.live.check quiet
                            \n\tinitrdefi /images/pxeboot/initrd.img\n}""")

    grub_lines.append("""menuentry 'Install Fedora 36 with RAM-Boot' --class fedora --class gnu-linux --class gnu --class os {
                            \n\tlinuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% rd.live.check rd.live.ram=1 quiet
                            \n\tinitrdefi /images/pxeboot/initrd.img\n}""")

    grub_lines.append("""menuentry 'Install Fedora 36 without testing the media' --class fedora --class gnu-linux --class gnu --class os {
                            \n\tlinuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% quiet
                            \n\tinitrdefi /images/pxeboot/initrd.img\n}""")
    grub_lines.append("""submenu 'Troubleshooting -->' {\n
                    \tmenuentry 'Install Fedora 36 in basic graphics mode' --class fedora --class gnu-linux --class gnu --class os {
                            \n\t\tlinuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% nomodeset quiet
                            \n\t\tinitrdefi /images/pxeboot/initrd.img\n\t}
                    \tmenuentry 'Rescue a Fedora system' --class fedora --class gnu-linux --class gnu --class os {
                            \n\t\tlinuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% inst.rescue quiet
                            \n\t\tinitrdefi /images/pxeboot/initrd.img\n\t}\n}""")

    grub_file_text = ""
    for line in grub_lines:
        grub_file_text += line + '\n'
    grub_file_text = grub_file_text.replace('%root_label%', root_partition_label)
    return grub_file_text


def parse_spins(spins_list):
    accepted_spins_list = []
    live_os_base_index = None
    for index, current_spin in enumerate(spins_list):
        spin_keys = list(current_spin.keys())
        if not all(i in spin_keys for i in ("name", "size", "hash256", "dl_link")):
            continue
        if (attr := "dl_link") not in spin_keys:
            current_spin[attr] = ''
        if (attr := "is_live_img") not in spin_keys:
            current_spin[attr] = False
        if (attr := "version") not in spin_keys:
            current_spin[attr] = ''
        if (attr := "desktop") not in spin_keys:
            current_spin[attr] = ''
        if (attr := "is_auto_installable") not in spin_keys:
            current_spin[attr] = False
        if (attr := "is_recommended") not in spin_keys:
            current_spin[attr] = False
        if (attr := "is_advanced") not in spin_keys:
            current_spin[attr] = False
        if (attr := "torrent_link") not in spin_keys:
            current_spin[attr] = ''
        if (attr := "ostree_args") not in spin_keys:
            current_spin[attr] = ''
        if (attr := "is_base_netinstall") not in spin_keys:
            current_spin[attr] = False
        spin_ns = types.SimpleNamespace(**current_spin)
        accepted_spins_list.append(spin_ns)
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


def get_wifi_profiles(work_directory):

    work_directory += r'\wifi_profiles'
    fn.rmdir(work_directory)
    fn.mkdir(work_directory)

    fn.extract_wifi_profiles(work_directory)
    wifi_profiles = []
    for filename in os.listdir(work_directory):
        try:
            with open(os.path.join(work_directory, filename), 'r') as f:  # open in readonly mode
                xml_file = f.read()
                wifi_profile: dict = fn.parse_xml(xml_file)
                name = wifi_profile['WLANProfile']['name']
                ssid = wifi_profile['WLANProfile']['SSIDConfig']['SSID']['name']
                if (key := 'nonBroadcast') in (attr := wifi_profile['WLANProfile']['SSIDConfig']) and attr[key] == 'true':
                    hidden = 'true'
                else:
                    hidden = 'false'
                password_type = wifi_profile['WLANProfile']['MSM']['security']['sharedKey']['keyType']
                password = wifi_profile['WLANProfile']['MSM']['security']['sharedKey']['keyMaterial']
                profile = {'name': name, 'ssid': ssid, 'hidden': hidden, 'password': password}
                wifi_profiles.append(profile)
        except KeyError:
            print('Note: a wifi profile could not be exported, so it will be skipped')
            continue
    fn.rmdir(work_directory)
    return wifi_profiles


def start_async_download(app_path, url, destination, is_torrent=False, queue=None):
    args = (app_path, url, destination, is_torrent, queue)
    multiprocessing.Process(target=fn.download_with_aria2, args=args).start()


def decide_torrent_or_direct_download(torrent_preferred, direct_link, torrent_link):
    torrent_exist = bool(torrent_link)
    if torrent_exist and torrent_preferred:
        is_torrent = True
        link = torrent_link
    else:
        is_torrent = False
        link = direct_link
    return link, is_torrent


def check_valid_existing_file(path, file_hash):
    if fn.check_if_exists(path):
        if fn.check_hash(path, file_hash) == 1:
            return True
        else:
            fn.rm(path)
    return False


def initiate_kickstart_arguments_from_user_input(autoinstall: dict, install_options: dict):
    pass


def init_paths(paths_namespace):
    current_dir = fn.get_current_dir_path()
    downloads_dir = fn.get_user_downloads_folder()
    for key, value in (path_dict := vars(paths_namespace)).items():
        path_dict[key] = value.replace('%CURRENT_DIR%', current_dir).replace('%DOWNLOADS_DIR%', downloads_dir)
    return types.SimpleNamespace(**path_dict)

