import os
from multiprocessing import Process

import functions as fn
# Functions that do multiple things or call multiple other functions are declared here


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
    queue.put(check_results)


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
                              wifi_profiles=None, is_encrypted: bool = False, passphrase: str = None, live_img_url='',
                              nvidia_drivers=True):

    kickstart_txt = "# Kickstart file created by Lnixify."
    kickstart_txt += "\ngraphical"
    kickstart_txt += "\n%post --nochroot --logfile=/mnt/sysimage/root/ks-post.log"
    kickstart_txt += '\nrm /run/install/repo/ks.cfg'
    kickstart_txt += '\ncp /run/install/repo/EFI/BOOT/BOOT.cfg /run/install/repo/EFI/BOOT/grub.cfg'
    if wifi_profiles and isinstance(wifi_profiles, list):
        kickstart_txt += "\nmkdir -p /mnt/sysimage/etc/NetworkManager/system-connections"
        template = r"""[connection]\nid=%name%\ntype=wifi\n\n[wifi]\nhidden=%hidden%\nssid=%ssid%\n\n[wifi-security]\nkey-mgmt=wpa-psk\npsk=%password%\n\n[ipv4]\nmethod=auto\n\n[ipv6]\naddr-gen-mode=stable-privacy\nmethod=auto\n\n[proxy]\n"""
        for profile in wifi_profiles:
            network_file = template.replace('%name%', profile['name']).replace('%ssid%', profile['ssid']).replace('%hidden%', profile['hidden']).replace('%password%', profile['password'])
            kickstart_txt += "\necho $'" + network_file + \
                             "' > " + "/mnt/sysimage/etc/NetworkManager/system-connections/'%s.nmconnection'" % profile['name']
    if nvidia_drivers:
        kickstart_txt += "\nmkdir -p /mnt/sysimage/etc/profile.d/"
        kickstart_txt += '\ncp /run/install/repo/lnixify/nvidia_inst /mnt/sysimage/etc/profile.d/nvidia_inst.sh'
    kickstart_txt += '\n%end'


    # if not (keymap and lang and timezone):
    #     if not keymap: keymap = 'us'
    #     if not lang: lang = 'en_US.UTF-8'
    #     if not timezone: timezone = 'America/New_York'
    #     kickstart_txt += "\nfirstboot --reconfig"
    # else:
    kickstart_txt += "\nfirstboot --enable"
    if keymap_type == 'vc':
        kickstart_txt += "\nkeyboard --vckeymap=%s" % keymap
    else:
        kickstart_txt += "\nkeyboard --xlayouts='%s'" % keymap
    kickstart_txt += "\nlang " + lang
    kickstart_txt += "\nfirewall --use-system-defaults"
    if ostree_args:
        kickstart_txt += "\nostreesetup " + ostree_args
    if live_img_url:
        kickstart_txt += "\nliveimg --url='%s' --noverifyssl" % live_img_url

    kickstart_txt += "\ntimezone " + timezone + " --utc"
    # kickstart_txt += "\nignoredisk --drives="
    kickstart_txt += "\npart btrfs.01 --onpart=/dev/disk/by-label/ALLOC-ROOT"
    if is_encrypted:
        kickstart_txt += ' --encrypted'
        if passphrase:
            kickstart_txt += ' --passphrase=' + passphrase
    kickstart_txt += "\nbtrfs none --label=fedora btrfs.01" \
                     "\nbtrfs / --subvol --name=root fedora" \
                     "\nbtrfs /home --subvol --name=home fedora" \
                     "\nbtrfs /var --subvol --name=var fedora" \
                     "\npart /boot --fstype=ext4 --label=fedora_boot --onpart=/dev/disk/by-label/ALLOC-BOOT " \
                     "\npart /boot/efi --fstype=efi --label=fedora_efi --onpart=/dev/disk/by-label/ALLOC-EFI"

    if username:
        kickstart_txt += "\nuser --name=" + username + " --gecos='" + fullname + "' --groups=wheel"
    kickstart_txt += "\nrootpw --lock"
    kickstart_txt += "\nreboot"

    return kickstart_txt


def build_grub_cfg_file(root_partition_label, is_autoinst=False):
    part_pre = """### Grub configuration generated by Lnixify ###"""
    part_const1 = """\nset default="0"\nfunction load_video {\n  insmod efi_gop\n  insmod efi_uga\n  insmod video_bochs\n  insmod video_cirrus\n  insmod all_video\n}\nload_video\nset gfxpayload=keep\ninsmod gzio\ninsmod part_gpt\ninsmod ext2\nset timeout=5"""
    part_scan = """\nsearch --no-floppy --set=root -l '%root_label%'\n"""
    if is_autoinst:
        entry1 = """\nmenuentry 'Auto Install Fedora 36' --class fedora --class gnu-linux --class gnu --class os {\n\tlinuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% rd.live.check inst.ks=hd:LABEL=%root_label% quiet\n\tinitrdefi /images/pxeboot/initrd.img \n}"""
    else:
        entry1 = ''
    entry2 = """\nmenuentry 'Install Fedora 36' --class fedora --class gnu-linux --class gnu --class os {\n\tlinuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% rd.live.check quiet\n\tinitrdefi /images/pxeboot/initrd.img\n}"""
    entry3 = """\nmenuentry 'Install Fedora 36 with RAM-Boot' --class fedora --class gnu-linux --class gnu --class os {\n\tlinuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% rd.live.check rd.live.ram=1 quiet\n\tinitrdefi /images/pxeboot/initrd.img\n}"""
    entry4 = """\nmenuentry 'Install Fedora 36 without testing the media' --class fedora --class gnu-linux --class gnu --class os {\n\tlinuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% quiet\n\tinitrdefi /images/pxeboot/initrd.img\n}"""
    submenu = """\nsubmenu 'Troubleshooting -->' {\n
                \tmenuentry 'Install Fedora 36 in basic graphics mode' --class fedora --class gnu-linux --class gnu --class os {\n\t\tlinuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% nomodeset quiet\n\t\tinitrdefi /images/pxeboot/initrd.img\n\t}
                \tmenuentry 'Rescue a Fedora system' --class fedora --class gnu-linux --class gnu --class os {\n\t\tlinuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% inst.rescue quiet\n\t\tinitrdefi /images/pxeboot/initrd.img\n\t}\n}
                """

    grub_file_text = part_pre + part_const1 + part_scan + entry1 + entry2 + entry3 + entry4 + submenu
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
        accepted_spins_list.append(current_spin)
    for index, spin in enumerate(accepted_spins_list):
        if spin["is_base_netinstall"]:
            live_os_base_index = index
            break
    if live_os_base_index is None:
        final_spin_list = []
        for index, spin in enumerate(accepted_spins_list):
            if spin["is_live_img"]:
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
            print('a wifi profile could not be exported, so it will be skipped')
            continue
    fn.rmdir(work_directory)
    return wifi_profiles


def start_download(main_gui, status_shared_var, aria2location, dl_path, spin: dict,
                   queue, iso_file_new_name: str,
                   progress_bar=None, progress_factor=1, check_existing_file_hash_only=False,
                   do_torrent_dl: bool = False, ln_job='', ln_speed='', ln_dl_timeleft=''):
    file_path = dl_path + '\\' + iso_file_new_name
    if not check_existing_file_hash_only:
        filename = fn.get_file_name_from_url(spin['dl_link'])
        if do_torrent_dl and spin['torrent_link']:
            # if torrent is selected and a torrent link is available
            args = (aria2location, spin['torrent_link'], dl_path, 1, queue)
        else:
            # if torrent is not selected or not available (direct download)
            args = (aria2location, spin['dl_link'], dl_path, 0, queue)
        Process(target=fn.download_with_aria2, args=args).start()
        while True:
            while not queue.qsize(): main_gui.after(500, main_gui.update())
            while queue.qsize() != 1: queue.get()
            dl_status = queue.get()
            if dl_status == 'OK':
                break
            if progress_bar:
                progress_bar['value'] = dl_status['%'] * progress_factor
            status_shared_var.set(ln_job + '\n%s\n%s: %s/s, %s: %s' % (dl_status['size'], ln_speed,
                                                                       dl_status['speed'], ln_dl_timeleft,
                                                                       dl_status['eta']))

        location = fn.find_file_by_name(filename, dl_path)
        if iso_file_new_name:
            new_file_path = dl_path + '\\' + iso_file_new_name
            fn.move_and_replace(location, new_file_path)
    if spin['hash256']:
        while queue.qsize(): queue.get()  # to empty the queue
        Process(target=fn.check_hash, args=(file_path, spin['hash256'], queue,)).start()
        while not queue.qsize(): main_gui.after(100, main_gui.update())
        return queue.get()
    else:
        return 1


def check_valid_existing_file(path, file_hash):
    if fn.check_if_exists(path):
        if fn.check_hash(path, file_hash) == 1:
            return True
        else:
            fn.rm(path)
    return False


def initiate_kickstart_arguments_from_user_input(autoinstall: dict, install_options: dict):
    pass

