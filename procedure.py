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
                              wifi_profiles=None, is_encrypted: bool = False, passphrase: str = None):

    kickstart_txt = "# Kickstart file created by Lnixify."
    kickstart_txt += "\ngraphical"
    if wifi_profiles and isinstance(wifi_profiles, list):
        kickstart_txt += "\n%post"
        kickstart_txt += "\nmkdir -p /mnt/sysimage/etc/NetworkManager/system-connections"
        template = r"""[connection]\nid=%ssid%\ntype=wifi\n\n[wifi]\nhidden=false\nssid=%ssid%\n\n[wifi-security]\nkey-mgmt=wpa-psk\npsk=%password%\n\n[ipv4]\nmethod=auto\n\n[ipv6]\naddr-gen-mode=stable-privacy\nmethod=auto\n\n[proxy]\n"""
        for profile in wifi_profiles:
            kickstart_txt += "\necho $'" + template.replace('%ssid%', profile[0]).replace('%password%', profile[1]) + \
                             "' > " + "/mnt/sysimage/etc/NetworkManager/system-connections/'%s.nmconnection'" % profile[0]
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