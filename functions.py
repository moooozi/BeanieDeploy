import subprocess
import time
import webbrowser


def open_url(url):
    webbrowser.open_new_tab(url)


def compatibility_test(required_space_min, required_ram, queue):

    required_space_dualboot = required_space_min + 20 * 1024 * 1024 * 1024

    def check_uefi():
        return subprocess.run([r'powershell.exe', r'$env:firmware_type'], stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, shell=True)

    def check_totalram():
        return subprocess.run([r'powershell.exe',
                               r'(Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property capacity -Sum).sum /1gb'],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

    def check_space():
        return subprocess.run([r'powershell.exe',
                               r'(Get-Volume | Where DriveLetter -eq $env:SystemDrive.Substring(0, 1)).SizeRemaining'],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

    def check_resizable():
        return subprocess.run([r'powershell.exe',
                               r'((Get-Volume | Where DriveLetter -eq $env:SystemDrive.Substring(0, 1)).Size - (Get-PartitionSupportedSize -DriveLetter $env:SystemDrive.Substring(0, 1)).SizeMin)'],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

    def check_bitlocker_status():
        return subprocess.run(
            [r'powershell.exe', r'(Get-BitLockerVolume -MountPoint $env:SystemDrive).EncryptionPercentage'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, shell=True)

    totalram = int(str(check_totalram().stdout)[2:-5])
    if check_totalram().returncode != 0:
        result_totalram_check = 9
    elif totalram >= required_ram:
        result_totalram_check = 1
    else:
        result_totalram_check = 0
    if check_uefi().returncode != 0:
        result_uefi_check = 9
    elif b'uefi' in check_uefi().stdout.lower():
        result_uefi_check = 1
    else:
        result_uefi_check = 0

    if check_space().returncode != 0:
        result_space_check = 9

    space_available = int(str(check_space().stdout)[2:-5])

    if space_available > required_space_dualboot:
        result_space_check = 2
    elif space_available > required_space_min:
        result_space_check = 1
    else:
        result_space_check = 0

    if result_space_check in (1, 2):
        print(check_resizable())
        if check_resizable().returncode != 0:
            result_resizable_check = 9
        elif int(str(check_resizable().stdout)[2:-5]) > required_space_min:
            result_resizable_check = 1
        else:
            result_resizable_check = 0
    else:
        result_resizable_check = 8

    if check_bitlocker_status().returncode != 0:
        result_bitlocker_check = 9
    elif str(check_bitlocker_status().stdout)[2:-5] == '0':
        result_bitlocker_check = 1
    else:
        result_bitlocker_check = 0

    check_results = {'uefi': result_uefi_check,
                     'totalram': result_totalram_check,
                     'space': result_space_check,
                     'resizable': result_resizable_check,
                     'bitlocker': result_bitlocker_check}
    queue.put(check_results)


"""
def download_file_legacy():  # DEPRECATE METHOD, REPLACED WITH aria2 ***********************************************

    def download_file(url, destination, queue):
        arg = '(Start-BitsTransfer -Source "' + url + '" -Destination "' + destination + '" -Priority normal -Asynchronous).JobId'
        job_id = str(subprocess.run(
            [r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[86:122]
        queue.put(job_id)
    
    
    def get_download_size(job_id):
        arg = '(Get-BitsTransfer | ? { $_.JobId -eq "' + job_id + '" }).bytestotal'
        return str(subprocess.run(
            [r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[2:-5]
    
    
    def get_downloaded_size(job_id):
        arg = '(Get-BitsTransfer | ? { $_.JobId -eq "' + job_id + '" }).bytestransferred'
        return str(subprocess.run(
            [r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[2:-5]
    
    
    def track_download(job_id):
        dl_size = get_download_size(job_id)
        already_downloaded = get_downloaded_size(job_id)
        return [dl_size, already_downloaded]
    
    
    def finish_download(job_id):
        arg = '(Get-BitsTransfer | ? { $_.JobId -eq "' + job_id + '" }) | Complete-BitsTransfer'
        return subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
"""


def get_user_home_dir():
    return str(subprocess.run(
        [r'powershell.exe', r'$home'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[2:-5].replace(r'\\', '\\')


def create_dir(path):
    arg = "New-Item -Path '" + path + "' -ItemType Directory"
    str(subprocess.run(
        [r'powershell.exe', arg],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[2:-5].replace(r'\\', '\\')


def download_with_aria2(app_path, url, destination, istorrent, queue):
    arg = r' --dir="' + destination + '" ' + url
    if istorrent:
        arg = arg + '--seed-time=0'
    p = subprocess.Popen(app_path + arg, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True,
                         universal_newlines=True)
    tracker = {}
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
                            tracker['%'] = txt[index2 + 1:index1]
                        queue.put(tracker)
                    except (ValueError, IndexError): pass


def rename_file(dir_path, file_name, new_name):
    arg = 'Get-ChildItem -Path "' + dir_path + '" -Name -include "' + file_name + '" | Rename-item -Newname "' + new_name + '"'
    return subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


def move_files_to_dir(source, destination):
    arg = 'Get-ChildItem -Path ' + source + ' -Recurse -File | Move-Item -Destination ' + destination
    subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    arg = 'Get-ChildItem -Path ' + source + ' -Recurse -Directory | Remove-Item'
    subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


def get_sys_drive_letter():
    return subprocess.run([r'powershell.exe', r'$env:SystemDrive.Substring(0, 1)'], stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, shell=True)


def get_disk_number(drive_letter):
    arg = r'(Get-Partition | Where DriveLetter -eq ' + drive_letter + r' | Get-Disk).Number'
    return subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


def get_drive_size_after_resize(drive_letter, required_space):
    arg = r'(Get-Volume | Where DriveLetter -eq ' + drive_letter + ').Size -' + str(required_space)
    return subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


def resize_partition(drive_letter, new_size):
    arg = r'Resize-Partition -DriveLetter ' + drive_letter + r' -Size ' + new_size
    return subprocess.run(
        [r'powershell.exe', arg],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, shell=True)


def get_unused_drive_letter():
    drive_letters = [
        'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

    def test(test_letter):
        return str(subprocess.run([r'powershell.exe', r'Get-Volume | Where-Object DriveLetter -eq ' + test_letter],
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[2:-5]

    for letter in drive_letters:
        if not test(letter):
            return letter


def new_partition(disk_number, size, drive_letter):
    arg = r'New-Partition -DiskNumber ' + str(disk_number) + r' -Size ' + str(size) + r' -DriveLetter ' + drive_letter
    return subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


def format_volume(drive_letter, filesystem):
    arg = r'Format-Volume -DriveLetter ' + drive_letter + ' -FileSystem ' + filesystem
    return subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


def create_temp_boot_partition(tmp_part_size, queue):
    print('create_temp_boot_partition')
    sys_drive_letter = str(get_sys_drive_letter().stdout)[2:-5]
    sys_disk_number = str(get_disk_number(sys_drive_letter).stdout)[2:-5]
    sys_drive_new_size = str(get_drive_size_after_resize(sys_drive_letter, tmp_part_size + 1100000).stdout)[2:-5]
    resize_partition(sys_drive_letter, sys_drive_new_size)

    tmp_part_letter = get_unused_drive_letter()
    new_partition(sys_disk_number, tmp_part_size, tmp_part_letter)
    format_volume(tmp_part_letter, 'FAT32')
    queue.put([1, tmp_part_letter])


def mount_iso(iso_path):
    arg = '(Mount-DiskImage -ImagePath "' + iso_path + '" | Get-Volume).DriveLetter'
    return str(subprocess.run(
        [r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[2:-5]


def copy_files(source, destination, queue):
    arg = r'robocopy "' + source + '" "' + destination + '" /e /mt'
    subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    if True:
        queue.put(1)


def cleanup_after_install(location):
    arg = r'Remove-Item "' + location + '" -Recurse'
    subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


def restart_windows():
    subprocess.run([r'powershell.exe', r'Restart-Computer'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    print('restarting')


def add_boot_entry(boot_efi_file_path, boot_drive_letter, queue):
    arg1 = r'(bcdedit /copy {bootmgr} /d "TmpInstallMedia")'
    bootguid = str(subprocess.run([r'powershell.exe', arg1], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[2:-5]

    arg2 = """'{' + (""" + bootguid + """-split '[{}]')[1] + '}'"""
    bootguid = str(subprocess.run([r'powershell.exe', arg2], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[2:-5]

    arg3 = r'bcdedit /set ' + bootguid + ' path ' + boot_efi_file_path + ''
    subprocess.run([r'powershell.exe', arg3], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    arg4 = r'bcdedit /set ' + bootguid + ' device partition=' + boot_drive_letter + ':'
    subprocess.run([r'powershell.exe', arg4], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    arg5 = r'bcdedit /set {fwbootmgr} displayorder ' + bootguid + ' /addfirst'
    subprocess.run([r'powershell.exe', arg5], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    if True:
        queue.put(1)


def get_wifi_profiles():
    out = str(subprocess.run(
        [r'powershell.exe',
         r'(netsh wlan show profiles) | Select-String “\:(.+)$” | %{$name=$_.Matches.Groups[1].Value.Trim(); $_} | %{'
         r'(netsh wlan show profile name=”$name” key=clear)} | Select-String “Key Content\W+\:(.+)$” | %{'
         r'$pass=$_.Matches.Groups[1].Value.Trim(); $_} | %{[PSCustomObject]@{ PROFILE_NAME=$name;PASSWORD=$pass }} | '
         r'Format-Table -AutoSize'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[56:-13]
    out = out.split("\\r\\n")
    newout = []
    for i in out:
        i = i.split()
        newout.append(i)
    return newout


def build_autoinstall_ks_file(keymap, xlayouts, syslang, timezone, de_option, usrfullname, username, password):
    if de_option == 1:
        packages = "@^workstation-product-environment"
    textpart1 = "graphical\nkeyboard --vckeymap='" + keymap + "' --xlayouts='%s'\n" % xlayouts
    textpart2 = "lang " + syslang + ".UTF-8\n%packages\n" + packages + "\n%end\nfirstboot --enable\n"
    textpart3 = "autopart\nclearpart --none --initlabel\ntimezone %s --utc\nrootpw --lock\n" % timezone
    text = textpart1 + textpart2 + textpart3
    ks_file = open('anaconda-ks.cfg', 'w')
    ks_file.write(text)
    print(text)


