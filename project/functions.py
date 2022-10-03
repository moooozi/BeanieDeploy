import json
import re
import shutil
import subprocess
import winreg
from urllib.request import urlopen
import libs.xmltodict as xmltodict
import os
import pathlib


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


def get_windows_username():
    return str(subprocess.run(
        [r'powershell.exe', r'$env:UserName'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, universal_newlines=True).stdout).replace(r'\\', '\\')


def set_file_readonly(filepath, is_true: bool):
    if is_true: value = '$true'
    else: value = '$false'
    return subprocess.run([r'powershell.exe',
                           r'Set-ItemProperty ' + filepath + ' -name IsReadOnly -value ' + value],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)


def download_with_aria2(aria2_path, url, destination, output_name=None,  is_torrent=False, queue=None):
    arg = r' --dir="%s" ' % destination
    if output_name and not is_torrent:
        arg += r'--out=%s ' % output_name
    if is_torrent:
        arg += ' --seed-time=0 '
    arg += url

    p = subprocess.Popen(aria2_path + arg, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True,
                         universal_newlines=True)
    tracker = {
        'speed': '0',
        'eta': 'N/A',
        'size': '',
        '%': '0'
    }
    # Parsing output
    while True:
        output = p.stdout.readline()
        if output == '' and p.poll() is not None:
            return 0
        if output:
            if '(OK):download completed' in output:
                if queue: queue.put('ARIA2C: Done')
                return 1
            elif queue:
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
                        queue.put(('ARIA2C: Tracking %s' % output_name, tracker))
                    except (ValueError, IndexError): pass


def get_sha256_hash(file_path):
    arg = r'(Get-FileHash "' + file_path + '" -Algorithm SHA256).Hash'
    out = subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         shell=True, universal_newlines=True)
    if out.returncode != 0 or len(out.stdout.strip()) != 64:
        return ''
    return out.stdout.strip().lower()


def get_sys_drive_letter():
    return subprocess.run([r'powershell.exe', r'$env:SystemDrive.Substring(0, 1)'], stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, shell=True, universal_newlines=True).stdout.strip()


def get_disk_number(drive_letter: str):
    arg = r'(Get-Partition | Where DriveLetter -eq ' + drive_letter + r' | Get-Disk).Number'
    return int(subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True,
                              universal_newlines=True).stdout.strip())


def get_drive_size_after_resize(drive_letter: str, minus_space: int):
    arg = r'(Get-Volume | Where DriveLetter -eq ' + drive_letter + ').Size -' + str(minus_space)
    return int(float(subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    shell=True, universal_newlines=True).stdout.strip()))


def resize_partition(drive_letter: str, new_size: int):
    arg = r'Resize-Partition -DriveLetter ' + drive_letter + r' -Size ' + str(new_size)
    return subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          shell=True, universal_newlines=True)


def get_unused_drive_letter():
    drive_letters = ['G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    for letter in drive_letters:
        test = subprocess.run([r'powershell.exe', r'Get-Volume | Where-Object DriveLetter -eq ' + letter], stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, shell=True, universal_newlines=True).stdout.strip()
        if not test: return letter


def relabel_volume(drive_letter: str, new_label: str):
    arg = r'Set-Volume -DriveLetter "' + drive_letter + '" -NewFileSystemLabel "' + new_label + '"'
    return subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).returncode


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
    if not iso_path:
        return False
    arg = 'Dismount-DiskImage -ImagePath "' + iso_path + '"'
    return str(subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              shell=True, universal_newlines=True).stdout.strip())


def remove_drive_letter(drive_letter):
    arg = 'Get-Volume -Drive %s | Get-Partition | Remove-PartitionAccessPath -accesspath %s:\\' % (drive_letter, drive_letter)
    return subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          shell=True, universal_newlines=True)


def copy_files(source, destination):
    arg = r'robocopy "' + source + '" "' + destination + '" /e /mt'
    subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


def copy_and_rename_file(source, destination, queue=None):
    mkdir(pathlib.Path(destination).parent.absolute())
    shutil.copyfile(src=source, dst=destination)
    if queue:
        queue.put(1)


def rmdir(location):
    if os.path.isdir(location):
        return shutil.rmtree(location)


def mkdir(location):
    if not os.path.isdir(location):
        return os.makedirs(location)


def app_quit():
    raise SystemExit


def quit_and_restart_windows():
    subprocess.run([r'powershell.exe', r'Restart-Computer'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    app_quit()


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
    #log(out.stdout)


def create_new_wbm(boot_efi_file_path, boot_drive_letter):
    arg = r'bcdedit /copy "{bootmgr}" /d "Linux Install Media"'
    bootguid = subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, shell=True, universal_newlines=True).stdout.strip()
    #log(bootguid)
    bootguid = bootguid[bootguid.index('{'):bootguid.index('}') + 1]
    arg = r'bcdedit /set  "' + bootguid + '" path ' + boot_efi_file_path + ''
    subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    arg = r'bcdedit /set "' + bootguid + '" device partition=' + boot_drive_letter + ':'
    subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    return bootguid


def extract_wifi_profiles(folder_path):
    args = 'netsh wlan export profile key=clear folder="%s"' % folder_path
    out = subprocess.run([r'powershell.exe', args],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    return out.returncode


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
    return str(pathlib.Path(__file__).parent.absolute())


def get_admin():
    from sys import executable, argv
    from ctypes import windll
    if not windll.shell32.IsUserAnAdmin():
        windll.shell32.ShellExecuteW(None, "runas", executable, " ".join(argv), None, 1)
        raise SystemExit


def get_json(url, queue=None, named: str = None):
    """

    :param url:
    :param queue:
    :param named:
    :return:
    """
    out = urlopen(url).read()
    data = json.loads(out)
    if named: return_var = (named, data)
    else: return_var = data
    if queue:
        queue.put(return_var)
    else:
        return return_var


def parse_xml(xml):
    return xmltodict.parse(xml)


def gigabyte(gb): return int(float(gb) * 1073741824)
def megabyte(mb): return int(float(mb) * 1048576)
def byte_to_gb(byte): return round(int(byte) / 1073741824, 2)


def detect_nvidia(queue=None):
    out = subprocess.run([r'powershell.exe', 'Get-WmiObject Win32_VideoController'], stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    is_found = 'NVIDIA' in out.stdout
    if queue: queue.put(is_found)
    else: return is_found


def get_file_name_from_url(url):
    from urllib.parse import urlparse
    a = urlparse(url)
    return os.path.basename(a.path)


def find_file_by_name(name, lookup_dir):
    for root, dirs, files in os.walk(lookup_dir):
            if name in files:
                return os.path.join(root, name)


def set_windows_time_to_utc():
    try:
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Control\TimeZoneInformation')
        winreg.SetValueEx(key, 'RealTimeIsUniversal', 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
        return True
    except:
        return False
        #log("Error: Couldn't change Windows Time settings to use UTC universal timing")


def get_user_downloads_folder():

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders') as key:
        downloads_dir = winreg.QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')[0]
    return downloads_dir

