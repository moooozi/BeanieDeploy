import json
import re
import shutil
import subprocess
import requests
import xmltodict
import os
from pathlib import Path


def open_url(url):
    import webbrowser
    webbrowser.open_new_tab(url)


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


def get_user_home_dir():
    return str(subprocess.run(
        [r'powershell.exe', r'$home'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[2:-5].replace(r'\\', '\\')


def get_windows_username():
    return str(subprocess.run(
        [r'powershell.exe', r'$env:UserName'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[2:-5].replace(r'\\', '\\')


def set_file_readonly(filepath, is_true: bool):
    if is_true: value = '$true'
    else: value = '$false'
    return subprocess.run([r'powershell.exe',
                           r'Set-ItemProperty ' + filepath + ' -name IsReadOnly -value ' + value],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)


def download_with_aria2(app_path, url, destination, is_torrent, queue):
    arg = r' --dir="' + destination + '" ' + url
    if is_torrent:
        arg += ' --seed-time=0'

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

'''
def move_files_to_dir(source, destination):
    arg = 'Get-ChildItem -Path ' + source + ' -Recurse -File | Move-Item -Destination ' + destination
    subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    arg = 'Get-ChildItem -Path ' + source + ' -Recurse -Directory | Remove-Item'
    subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
'''


def check_hash(file_path, sha256_hash, queue=None):
    arg = r'(Get-FileHash "' + file_path + '" -Algorithm SHA256).Hash'
    out = subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         shell=True, universal_newlines=True)
    if out.returncode != 0:
        result = -1
    elif out.stdout.strip().upper() == sha256_hash.upper():
        result = 1
    else:
        result = (out.stdout.strip().upper(), sha256_hash.upper())
    if queue:
        queue.put(result)
    else:
        return result


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
    arg = '$part = New-Partition -DiskNumber ' + str(disk_number) + r' -Size ' + str(size)
    if drive_letter is not None:
        arg += ' -DriveLetter ' + drive_letter
    arg += ' | Get-Volume; '
    arg += '$part | Format-Volume' + ' -FileSystem ' + filesystem + ' -NewFileSystemLabel "' + label + '"; '
    arg += 'Disable-Bitlocker -MountPoint $part.Path'
    return subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


def mount_iso(iso_path):
    arg = '(Mount-DiskImage -ImagePath "' + iso_path + '" | Get-Volume).DriveLetter'
    return str(subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              shell=True, universal_newlines=True).stdout.strip())


def unmount_iso(iso_path):
    arg = 'Dismount-DiskImage -ImagePath "' + iso_path + '"'
    return str(subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              shell=True, universal_newlines=True).stdout.strip())


def remove_drive_letter(drive_letter):
    arg = 'Get-Volume -Drive %s | Get-Partition | Remove-PartitionAccessPath -accesspath %s:\\' % (drive_letter, drive_letter)
    return subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          shell=True, universal_newlines=True)


def copy_files(source, destination, queue=None):
    arg = r'robocopy "' + source + '" "' + destination + '" /e /mt'
    subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    if queue:
        queue.put(1)


def copy_and_rename_file(source, destination, queue=None):
    mkdir(Path(destination).parent.absolute())
    shutil.copyfile(src=source, dst=destination)
    if queue:
        queue.put(1)


def rm(location):
    if os.path.isfile(location):
        return os.remove(location)


def rmdir(location):
    if os.path.isdir(location):
        return shutil.rmtree(location)


def mkdir(location):
    if not os.path.isdir(location):
        return os.makedirs(location)


def move_and_replace(path, dest):
    os.replace(path, dest)


def restart_windows():
    subprocess.run([r'powershell.exe', r'Restart-Computer'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


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
    bootguid = bootguid[bootguid.index('{'):bootguid.index('}') + 1]
    arg = r'bcdedit /set  "' + bootguid + '" path ' + boot_efi_file_path + ''
    subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    arg = r'bcdedit /set "' + bootguid + '" device partition=' + boot_drive_letter + ':'
    subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    return bootguid


'''
def get_wifi_profiles():
    args = """$WirelessSSIDs = (netsh wlan show profiles | Select-String ': ' ) -replace ".*:\s+" ; $WifiInfo = foreach($SSID in $WirelessSSIDs) {$Password = (netsh wlan show profiles name=$SSID key=clear | Select-String 'Key Content') -replace ".*:\s+" ; New-Object -TypeName psobject -Property @{"SSID"=$SSID;"Password"=$Password}} ; $WifiInfo | ConvertTo-Json"""
    out = str(subprocess.run([r'powershell.exe', args],
              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, universal_newlines=True).stdout)
    profiles = json.loads(out)
    list_of_profiles = []
    for profile in profiles:
        try:
            ssid: str = profile['SSID']
            password: str = profile['Password']
            if not password or not ssid:
                continue
            profile_list = (ssid, password)
            list_of_profiles.append(profile_list)
        except (KeyError, ValueError, IndexError, NameError):
            pass
    return list_of_profiles
'''


def extract_wifi_profiles(folder_path):
    args = 'netsh wlan export profile key=clear folder="%s"' % folder_path
    out = subprocess.run([r'powershell.exe', args],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    return out.returncode


def check_if_exists(path, check_if_is_dir=False):
    if check_if_is_dir:
        return os.path.isdir(path)
    return os.path.isfile(path)


def validate_with_regex(var, regex, mode='read'):
    regex_compiled = re.compile(regex)
    while var.get() != '':
        if re.match(regex_compiled, var.get()):
            print('Note: input has been accepted')
            return True
        elif mode == 'read':
            return False
        elif mode == 'fix':
            var.set(var.get()[:-1])
            print('Note: input has been modified, reason: forbidden character')
    # indicate the string is empty now
    return 'empty'


def get_current_dir_path():
    return str(Path(__file__).parent.absolute())


def get_admin():
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


def get_json(url, queue=None):
    out = requests.get(url).text
    data = json.loads(out)
    if queue:
        queue.put(data)
    else:
        return data


def parse_xml(xml):
    return xmltodict.parse(xml)


def gigabyte(gb): return int(gb * 1073741824)
def megabyte(mb): return int(mb * 1048576)
def byte_to_gb(byte): return round(byte / 1073741824, 2)


def detect_nvidia(queue=None):
    out = subprocess.run([r'powershell.exe', 'Get-WmiObject Win32_VideoController'], stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    is_found = 'NVIDIA' in out.stdout
    if queue: queue.put(is_found)
    else: return is_found


def log(text, mode='a'):
    with open('generated_log.txt', mode) as file:
        file.write(text + '\n')
    print(text)


def get_file_name_from_url(url):
    from urllib.parse import urlparse
    a = urlparse(url)
    return os.path.basename(a.path)


def find_file_by_name(name, lookup_dir):
    for root, dirs, files in os.walk(lookup_dir):
            if name in files:
                return os.path.join(root, name)


def set_windows_time_to_utc():
    args = r'reg add "HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\TimeZoneInformation" /v RealTimeIsUniversal /d 1 /t REG_DWORD /f'
    return subprocess.run([r'powershell.exe', args], stdout=subprocess.PIPE,
                   stderr=subprocess.STDOUT, shell=True, universal_newlines=True)