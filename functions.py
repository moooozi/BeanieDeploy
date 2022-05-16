import re
import subprocess


def open_url(url):
    import webbrowser
    webbrowser.open_new_tab(url)


def compatibility_test(required_space_min, queue):

    def check_arch():
        return subprocess.run([r'powershell.exe', r'$env:PROCESSOR_ARCHITECTURE'], stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, shell=True, universal_newlines=True)

    def check_uefi():
        return subprocess.run([r'powershell.exe', r'$env:firmware_type'], stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, shell=True, universal_newlines=True)

    def check_totalram():
        return subprocess.run([r'powershell.exe',
                               r'(Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property capacity -Sum).sum'],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)

    def check_space():
        return subprocess.run([r'powershell.exe',
                               r'(Get-Volume | Where DriveLetter -eq $env:SystemDrive.Substring(0, 1)).SizeRemaining'],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)

    def check_resizable():
        return subprocess.run([r'powershell.exe',
                               r'((Get-Volume | Where DriveLetter -eq $env:SystemDrive.Substring(0, 1)).Size - (Get-PartitionSupportedSize -DriveLetter $env:SystemDrive.Substring(0, 1)).SizeMin)'],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)

    # check starting...
    queue.put('arch')
    check = check_arch()
    if check.returncode != 0:
        result_arch_check = -1
    else:
        result_arch_check = check.stdout.strip().lower()
    queue.put('uefi')
    check = check_uefi()
    if check.returncode != 0:
        result_uefi_check = -1
    elif 'uefi' in check.stdout.lower():
        result_uefi_check = 1
    else:
        result_uefi_check = 0
    queue.put('ram')
    check = check_totalram()
    if check.returncode != 0:
        result_totalram_check = -1
    else:
        result_totalram_check = int(check.stdout.strip())
    queue.put('space')
    check = check_space()
    if check.returncode != 0:
        result_space_check = -1
    else:
        result_space_check = int(check.stdout.strip())

    if result_space_check > required_space_min:
        queue.put('resizable')
        check = check_resizable()
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


def get_user_home_dir():
    return str(subprocess.run(
        [r'powershell.exe', r'$home'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[2:-5].replace(r'\\', '\\')


def get_windows_username():
    return str(subprocess.run(
        [r'powershell.exe', r'$env:UserName'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[2:-5].replace(r'\\', '\\')


def create_dir(path):
    arg = "New-Item -Path '" + path + "' -ItemType Directory"
    subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


def set_file_readonly(filepath, is_true: bool):
    if is_true: value = '$true'
    else: value = '$false'
    return subprocess.run([r'powershell.exe',
                           r'Set-ItemProperty ' + filepath + ' -name IsReadOnly -value ' + value],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)


def download_with_aria2(app_path, url, destination, is_torrent, queue):
    arg = r' --dir="' + destination + '" ' + url
    if is_torrent:
        arg = arg + ' --seed-time=0'
    p = subprocess.Popen(app_path + arg, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True,
                         universal_newlines=True)
    # Parsing output
    tracker = {
        'speed': '0',
        'eta': 'N/A',
        'size': '',
        '%': '0'
    }
    while True:
        output = p.stdout.readline()
        if output == '' and p.poll() is not None:
            return 0
        if output:
            if '(OK):download completed' in output:
                queue.put('OK')
            else:
                if (txt := output.strip())[0:2] == '[#':
                    txt = txt[1:-1]
                    try:
                        txt = txt.replace('iB', 'B')
                        if (eta_key := 'ETA:') in txt:
                            index = txt.index(eta_key)
                            tracker['eta'] = txt[index + len(eta_key):].split(' ', 1)[0]
                        if (speed_key := 'DL:') in txt:
                            index = txt.index(speed_key)
                            tracker['speed'] = txt[index + len(speed_key):].split(' ', 1)[0]
                        if '%)' and 'B/' in txt:
                            index1 = txt.index('%)')
                            index2 = txt.index('(')
                            tracker['size'] = txt.split()[1]
                            tracker['%'] = int(txt[index2 + 1:index1])
                        queue.put(tracker)
                    except (ValueError, IndexError): pass


def rename_file(dir_path, file_name, new_name):
    arg = 'Get-ChildItem -Path "' + dir_path + '" -Name -include "' + file_name + '"'
    out = str(subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             shell=True).stdout)[2:-5]
    out = out.split('\\r\\n')[0]
    arg = 'Rename-item -Path "' + dir_path + '\\' + out + '" -Newname "' + new_name + '"'
    return subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


def move_files_to_dir(source, destination):
    arg = 'Get-ChildItem -Path ' + source + ' -Recurse -File | Move-Item -Destination ' + destination
    subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    arg = 'Get-ChildItem -Path ' + source + ' -Recurse -Directory | Remove-Item'
    subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


def check_hash(file_path, sha256_hash, queue):
    arg = r'(Get-FileHash "' + file_path + '" -Algorithm SHA256).Hash'
    out = subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         shell=True, universal_newlines=True)
    if out.returncode != 0: queue.put(-1)
    print('filehash: %s ' % out.stdout.strip().upper(), 'expected: %s' % sha256_hash.upper())
    if out.stdout.strip().upper() == sha256_hash.upper(): queue.put(1)
    else: queue.put((out.stdout.strip().upper(), sha256_hash.upper()))


def get_sys_drive_letter():
    return subprocess.run([r'powershell.exe', r'$env:SystemDrive.Substring(0, 1)'], stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, shell=True, universal_newlines=True).stdout.strip()


def get_disk_number(drive_letter: str):
    arg = r'(Get-Partition | Where DriveLetter -eq ' + drive_letter + r' | Get-Disk).Number'
    return int(subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True,
                              universal_newlines=True).stdout.strip())


def get_drive_size_after_resize(drive_letter: str, minus_space: int):
    arg = r'(Get-Volume | Where DriveLetter -eq ' + drive_letter + ').Size -' + str(minus_space)
    return int(subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              shell=True, universal_newlines=True).stdout.strip())


def resize_partition(drive_letter: str, new_size: int):
    arg = r'Resize-Partition -DriveLetter ' + drive_letter + r' -Size ' + str(new_size)
    return subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


def get_unused_drive_letter():
    drive_letters = ['G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

    def test(test_letter):
        return str(subprocess.run([r'powershell.exe', r'Get-Volume | Where-Object DriveLetter -eq ' + test_letter],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, shell=True, universal_newlines=True).stdout.strip())

    for letter in drive_letters:
        if not test(letter):
            return letter


def relabel_volume(drive_letter: str, new_label: str):
    arg = r'Set-Volume -DriveLetter "' + drive_letter + '" -NewFileSystemLabel "' + new_label + '"'
    return subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


def new_volume(disk_number: int, size: int, filesystem: str, label: str, drive_letter: str = None):
    arg = 'New-Partition -DiskNumber ' + str(disk_number) + r' -Size ' + str(size)
    if drive_letter is not None:
        arg += ' -DriveLetter ' + drive_letter
    arg += ' | Format-Volume' + ' -FileSystem ' + filesystem + ' -NewFileSystemLabel "' + label + '"'
    return subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


def partition_procedure(tmp_part_size: int, temp_part_label: str, queue, shrink_space: int = None,
                        boot_part_size: int = None, efi_part_size: int = None,):
    sys_drive_letter = get_sys_drive_letter()
    print(relabel_volume(sys_drive_letter, 'WindowsOS'))
    sys_disk_number = get_disk_number(sys_drive_letter)
    if shrink_space is None:
        shrink_space = tmp_part_size
    sys_drive_new_size = get_drive_size_after_resize(sys_drive_letter, shrink_space + 1100000)
    resize_partition(sys_drive_letter, sys_drive_new_size)
    if efi_part_size and boot_part_size and shrink_space:
        root_space = shrink_space - (tmp_part_size + efi_part_size + boot_part_size + 1100000)
        new_volume(sys_disk_number, root_space, 'EXFAT', 'ALLOC-ROOT')
        new_volume(sys_disk_number, boot_part_size, 'EXFAT', 'ALLOC-BOOT')
        new_volume(sys_disk_number, efi_part_size, 'EXFAT', 'ALLOC-EFI')

    tmp_part_letter = get_unused_drive_letter()
    new_volume(sys_disk_number, tmp_part_size, 'FAT32', temp_part_label, tmp_part_letter)
    queue.put((1, tmp_part_letter))


def mount_iso(iso_path):
    arg = '(Mount-DiskImage -ImagePath "' + iso_path + '" | Get-Volume).DriveLetter'
    return str(subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              shell=True, universal_newlines=True).stdout.strip())


def unmount_iso(iso_path):
    arg = 'Dismount-DiskImage -ImagePath "' + iso_path + '"'
    return str(subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              shell=True, universal_newlines=True).stdout.strip())


def copy_files(source, destination, queue):
    arg = r'robocopy "' + source + '" "' + destination + '" /e /mt'
    subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    if True:
        queue.put(1)


def copy_one_file(source, destination):
    arg = r'Copy-Item "' + source + '" -Destination "' + destination + '"'
    subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


def remove_folder(location):
    arg = r'Remove-Item "' + location + '" -Recurse'
    subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


def restart_windows():
    subprocess.run([r'powershell.exe', r'Restart-Computer'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


def add_boot_entry(boot_efi_file_path, boot_drive_letter, is_permanent: bool = False, queue=None):

    def make_boot_entry_first(bootguid, is_permanent: bool = False):
        """

        :param bootguid:
        :param is_permanent:
        """
        if is_permanent:
            arg = r'bcdedit /set "{fwbootmgr}" displayorder "' + bootguid + '" /addfirst'
        else:
            arg = r'bcdedit /set "{fwbootmgr}" bootsequence "' + bootguid + '" /addfirst'

        out = subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        print(out)

    def create_new_wbm(boot_efi_file_path, boot_drive_letter):
        arg = r'bcdedit /copy "{bootmgr}" /d "Linux Install Media"'
        bootguid = subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, shell=True, universal_newlines=True).stdout.strip()
        print(bootguid)
        bootguid = bootguid[bootguid.index('{'):bootguid.index('}') + 1]
        print(bootguid)
        arg = r'bcdedit /set  "' + bootguid + '" path ' + boot_efi_file_path + ''
        out = subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        print(out)
        arg = r'bcdedit /set "' + bootguid + '" device partition=' + boot_drive_letter + ':'
        out = subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        print(out)
        return bootguid

    bootguid = create_new_wbm(boot_efi_file_path, boot_drive_letter)
    make_boot_entry_first(bootguid)
    if queue: queue.put(1)
    else: return 1


def get_wifi_profiles():
    out = str(subprocess.run(
        [r'powershell.exe',
         r'(netsh wlan show profiles) | Select-String “\:(.+)$” | %{$name=$_.Matches.Groups[1].Value.Trim(); $_} | %{'
         r'(netsh wlan show profile name=”$name” key=clear)} | Select-String “Key Content\W+\:(.+)$” | %{'
         r'$pass=$_.Matches.Groups[1].Value.Trim(); $_} | %{[PSCustomObject]@{ PROFILE_NAME="$name)name";'
         r'PASSWORD="passwd($pass" }} | Format-Table -AutoSize'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, universal_newlines=True).stdout)
    print(out)
    out = out.split("\n")
    newout = []
    for i in out:
        i = ' '.join(i.split())
        if ')name passwd(' in i:
            i = i.split(')name passwd(')
            newout.append(i)
    return newout


def check_file_if_exists(path):
    arg = 'Test-Path -Path "' + path + '" -PathType Leaf'
    return str(subprocess.run(
        [r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[2:-5]


def build_autoinstall_ks_file(keymap, lang, timezone, ostree_args=None, username='', fullname='', wifi_profiles=None,
                              encrypted: bool = False, passphrase: str = None):
    kickstart_txt = "# Kickstart file created by Lnixify."
    kickstart_txt += "\ngraphical"
    if wifi_profiles:
        kickstart_txt += "\n%post"
        template = r"""[connection]\nid=%ssid%\ntype=wifi\n\n[wifi]\nhidden=false\nssid=%ssid%\n\n[wifi-security]\nkey-mgmt=wpa-psk\npsk=%password%\n\n[ipv4]\nmethod=auto\n\n[ipv6]\naddr-gen-mode=stable-privacy\nmethod=auto\n\n[proxy]\n"""
        for profile in wifi_profiles:
            kickstart_txt += "\necho $'" + template.replace('%ssid%', profile[0]).replace('%password%', profile[1]) + \
                             "' > " + "'/mnt/sysimage/etc/NetworkManager/system-connections/%s.nmconnection'" % profile[0]
    kickstart_txt += "\nkeyboard --vckeymap=" + keymap
    kickstart_txt += "\nlang " + lang
    kickstart_txt += "\nfirewall --use-system-defaults"
    if ostree_args:
        kickstart_txt += "\nostreesetup " + ostree_args
    kickstart_txt += "\nfirstboot --enable"
    kickstart_txt += "\ntimezone " + timezone + " --utc"
    kickstart_txt += "\nignoredisk --drives=" \
                     "\npart btrfs.01 --onpart=/dev/disk/by-label/ALLOC-ROOT"
    if encrypted:
        kickstart_txt += ' --encrypted'
        if passphrase:
            kickstart_txt += ' --passphrase=' + passphrase
        kickstart_txt += "\nbtrfs none --label=fedora btrfs.01" \
                         "\nbtrfs / --subvol --name=root fedora" \
                         "\nbtrfs /home --subvol --name=home fedora" \
                         "\nbtrfs /var --subvol --name=var fedora" \
                         "\npart /boot --fstype=ext4 --label=fedora_boot --onpart=/dev/disk/by-label/ALLOC-BOOT " \
                         "\npart /boot/efi --fstype=efi --label=fedora_efi --onpart=/dev/disk/by-label/ALLOC-EFI" \
                         "\nbootloader --location=none"

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


def validate_with_regex(var, regex, mode='read'):
    regex_compiled = re.compile(regex)
    while var.get() != '':
        if re.match(regex_compiled, var.get()):
            print('variable has been accepted')
            return True
        elif mode == 'read':
            return False
        elif mode == 'fix':
            var.set(var.get()[:-1])
            print('variable has been modified')
    # indicate the string is empty now
    return 'empty'


def get_current_dir_path():
    from pathlib import Path
    return str(Path(__file__).parent.absolute())


def get_admin(app):
    from sys import executable, argv
    from ctypes import windll
    if not windll.shell32.IsUserAnAdmin():
        windll.shell32.ShellExecuteW(None, "runas", executable, " ".join(argv), None, 1)
        raise SystemExit


'''def logger():
    with open(DOWNLOAD_PATH + '\\last_run.txt', 'x') as run_log:
        file = '\nvDist.get() = %s' % vDist.get() + \
               '\nvAutorestart_t.get() = %s' % vAutorestart_t.get() + \
               '\nvAutoinst_t.get() = %s' % vAutoinst_t.get() + \
               '\nvAutoinst_option.get() = %s' % vAutoinst_option.get() + \
               '\nSELECTED_LOCALE = %s' % Autoinst_SELECTED_LOCALE + \
               '\nvAutoinst_Username.get() = %s' % vAutoinst_Username.get() + \
               '\nvAutoinst_Fullname.get() = %s' % vAutoinst_Fullname.get() + \
               '\nvAutoinst_Timezone.get() = %s' % vAutoinst_Timezone.get() + \
               '\nvAutoinst_Keyboard.get() = %s' % vAutoinst_Keyboard.get()
        run_log.write(file)'''


def gigabyte(gb): return int(gb * 1073741824)
def megabyte(mb): return int(mb * 1048576)
def byte_to_gb(byte): return round(byte / 1073741824, 2)

