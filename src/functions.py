import hashlib
import json
import re
import shutil
import subprocess
import time
import winreg
import ctypes
from urllib.request import urlopen

import urllib
import libs.xmltodict as xmltodict
import os
import pathlib
from dataclasses import dataclass
from typing import Any


def open_url(url):
    import webbrowser

    webbrowser.open_new_tab(url)


def get_windows_username():
    return os.getlogin()


def set_file_readonly(filepath, is_true: bool):
    if is_true:
        os.chmod(filepath, 0o444)  # Read-only
    else:
        os.chmod(filepath, 0o666)  # Read-write


def format_speed(speed):
    speed_bits = speed * 8  # Convert bytes to bits
    if speed_bits < 1024:
        return f"{speed_bits:.2f} bit/s"
    elif speed_bits < 1024 * 1024:
        return f"{speed_bits / 1024:.2f} Kbit/s"
    else:
        return f"{speed_bits / (1024 * 1024):.2f} Mbit/s"


def format_size(size):
    if size < 1024:
        return f"{size:.2f} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"


def format_speed(speed):
    speed_bits = speed * 8  # Convert bytes to bits
    if speed_bits < 1024:
        return f"{speed_bits:.2f} bit/s"
    elif speed_bits < 1024 * 1024:
        return f"{speed_bits / 1024:.2f} Kbit/s"
    else:
        return f"{speed_bits / (1024 * 1024):.2f} Mbit/s"


def format_eta(eta):
    if eta < 60:
        return f"{eta:.2f} s"
    elif eta < 3600:
        return f"{eta / 60:.2f} min"
    else:
        return f"{eta / 3600:.2f} h"


def download_with_standard_lib(url, destination, output_name=None, queue=None):
    local_filename = output_name if output_name else url.split("/")[-1]
    local_filepath = os.path.join(destination, local_filename)

    tracker = {
        "type": "dl_tracker",
        "file_name": local_filename,
        "status": "downloading",
        "speed": "0",
        "eta": "N/A",
        "size": "",
        "%": "0",
    }

    with urllib.request.urlopen(url) as response:
        total_size = int(response.getheader("Content-Length").strip())
        tracker["size"] = total_size
        downloaded_size = 0
        start_time = time.time()

        with open(local_filepath, "wb") as f:
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                f.write(chunk)
                downloaded_size += len(chunk)
                elapsed_time = time.time() - start_time
                if elapsed_time > 0:
                    speed = downloaded_size / elapsed_time
                    eta = (total_size - downloaded_size) / speed if speed > 0 else "N/A"
                else:
                    speed = 0
                    eta = "N/A"
                tracker["speed"] = f"{speed:.2f}"
                tracker["eta"] = f"{eta:.2f}" if eta != "N/A" else "N/A"
                tracker["%"] = int((downloaded_size / total_size) * 100)
                if queue:
                    queue.put(tracker)

    tracker["status"] = "complete"
    if queue:
        queue.put(tracker)
    return 1


def get_sha256_hash(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_sys_drive_letter():
    return subprocess.run(
        [r"powershell.exe", r"$env:SystemDrive.Substring(0, 1)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    ).stdout.strip()


def get_disk_number(drive_letter: str):
    arg = (
        r"(Get-Partition | Where DriveLetter -eq "
        + drive_letter
        + r" | Get-Disk).Number"
    )
    return int(
        subprocess.run(
            [r"powershell.exe", arg],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        ).stdout.strip()
    )


def get_drive_size_after_resize(drive_letter: str, minus_space: int):
    arg = (
        r"(Get-Volume | Where DriveLetter -eq "
        + drive_letter
        + ").Size -"
        + str(minus_space)
    )
    return int(
        float(
            subprocess.run(
                [r"powershell.exe", arg],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
            .stdout.strip()
            .replace(",", ".")
        )
    )


def resize_partition(drive_letter: str, new_size: int):
    arg = r"Resize-Partition -DriveLetter " + drive_letter + r" -Size " + str(new_size)
    return subprocess.run(
        [r"powershell.exe", arg],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )


def get_unused_drive_letter():
    drive_letters = [
        "G",
        "H",
        "I",
        "J",
        "K",
        "L",
        "M",
        "N",
        "O",
        "P",
        "Q",
        "R",
        "S",
        "T",
        "U",
        "V",
        "W",
        "X",
        "Y",
        "Z",
    ]
    for letter in drive_letters:
        test = subprocess.run(
            [r"powershell.exe", r"Get-Volume | Where-Object DriveLetter -eq " + letter],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        ).stdout.strip()
        if not test:
            return letter


def relabel_volume(drive_letter: str, new_label: str):
    arg = (
        r'Set-Volume -DriveLetter "'
        + drive_letter
        + '" -NewFileSystemLabel "'
        + new_label
        + '"'
    )
    return subprocess.run(
        [r"powershell.exe", arg],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    ).returncode


def new_volume(
    disk_number: int, size: int, filesystem: str, label: str, drive_letter: str = None
):
    arg = (
        "$part = New-Partition -DiskNumber " + str(disk_number) + r" -Size " + str(size)
    )
    if drive_letter is not None:
        arg += " -DriveLetter " + drive_letter
    arg += " | Get-Volume; "
    arg += (
        "$part | Format-Volume"
        + " -FileSystem "
        + filesystem
        + ' -NewFileSystemLabel "'
        + label
        + '"; '
    )
    arg += "Disable-Bitlocker -MountPoint $part.Path"
    return subprocess.run(
        [r"powershell.exe", arg],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def set_partition_as_efi(drive_letter: str):
    arg = (
        "Get-Partition -DriveLetter "
        + drive_letter
        + ' | Set-Partition -GptType "{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}"'
    )

    return subprocess.run(
        [r"powershell.exe", arg],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def mount_iso(iso_path):
    arg = '(Mount-DiskImage -ImagePath "' + iso_path + '" | Get-Volume).DriveLetter'
    return str(
        subprocess.run(
            [r"powershell.exe", arg],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        ).stdout.strip()
    )


def unmount_iso(iso_path):
    if not iso_path:
        return False
    arg = 'Dismount-DiskImage -ImagePath "' + iso_path + '"'
    return str(
        subprocess.run(
            [r"powershell.exe", arg],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        ).stdout.strip()
    )


def remove_drive_letter(drive_letter):
    arg = (
        "Get-Volume -Drive %s | Get-Partition | Remove-PartitionAccessPath -accesspath %s:\\"
        % (drive_letter, drive_letter)
    )
    return subprocess.run(
        ["powershell.exe", arg],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )


def copy_files(source, destination):
    shutil.copytree(source, destination, dirs_exist_ok=True)


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
    # Initiate system shutdown
    ctypes.windll.advapi32.InitiateSystemShutdownW(None, "Restarting...", 0, True, True)
    app_quit()


def run_powershell_script(script):
    out = subprocess.run(
        [r"powershell.exe", "-ExecutionPolicy", "Unrestricted", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    return out.stdout


def make_boot_entry_first(bootguid, is_permanent: bool = False):
    """

    :param bootguid:
    :param is_permanent:
    """
    if is_permanent:
        arg = r'bcdedit /set "{fwbootmgr}" displayorder "' + bootguid + '" /addfirst'
    else:
        arg = r'bcdedit /set "{fwbootmgr}" bootsequence "' + bootguid + '" /addfirst'

    out = subprocess.run(
        [r"powershell.exe", arg],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    # log(out.stdout)


def create_new_wbm(boot_efi_file_path, device_path):
    arg = r'bcdedit /copy "{bootmgr}" /d "Linux Recovery"'
    bootguid = subprocess.run(
        [r"powershell.exe", arg],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    ).stdout.strip()
    # log(bootguid)
    bootguid = bootguid[bootguid.index("{") : bootguid.index("}") + 1]
    arg = rf'bcdedit /set "{bootguid}" path {boot_efi_file_path}'
    subprocess.run(
        [r"powershell.exe", arg],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    arg = rf'bcdedit /set "{bootguid}" device partition={device_path}'
    subprocess.run(
        [r"powershell.exe", arg],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return bootguid


def get_system_efi_drive_uuid():
    args = """(Get-Partition | Where-Object -Property "IsSystem" -EQ true).AccessPaths 
    | Where-Object { $_ -like '\\?\volume*' }"""
    out = subprocess.run(
        [r"powershell.exe", args],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    ).stdout
    trimmed_uuid = out[out.index("{") + 1 : out.index("}")]
    return trimmed_uuid


def extract_wifi_profiles(folder_path):
    args = 'netsh wlan export profile key=clear folder="%s"' % folder_path
    out = subprocess.run(
        [r"powershell.exe", args],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    return out.returncode


def validate_with_regex(var, regex, mode="read"):
    regex_compiled = re.compile(regex)
    while var != "":
        if re.match(regex_compiled, var):
            return True
        elif mode == "read":
            return False
        elif mode == "fix":
            var = var[:-1]
    # indicate the string is empty now
    return None


def is_admin():
    return ctypes.windll.shell32.IsUserAnAdmin()


def get_admin(args):
    from sys import executable, argv

    args = " ".join(argv) + " " + args
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, args, None, 1)
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
    if named:
        return_var = (named, data)
    else:
        return_var = data
    if queue:
        queue.put(return_var)
    else:
        return return_var


def parse_xml(xml):
    return xmltodict.parse(xml)


def gigabyte(gb):
    return int(float(gb) * 1073741824)


def megabyte(mb):
    return int(float(mb) * 1048576)


def byte_to_gb(byte):
    return round(int(byte) / 1073741824, 2)


def detect_nvidia(queue=None):
    out = subprocess.run(
        [r"powershell.exe", "Get-WmiObject Win32_VideoController"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    is_found = "NVIDIA" in out.stdout
    if queue:
        queue.put(is_found)
    else:
        return is_found


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
        key = winreg.CreateKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\TimeZoneInformation",
        )
        winreg.SetValueEx(key, "RealTimeIsUniversal", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
        return True
    except:
        return False
        # log("Error: Couldn't change Windows Time settings to use UTC universal timing")


def get_user_downloads_folder():
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
    ) as key:
        downloads_dir = winreg.QueryValueEx(
            key, "{374DE290-123F-4565-9164-39C4925E467B}"
        )[0]
    return downloads_dir


def enqueue_output(out, queue):
    for line in iter(out.readline, b""):
        try:
            parsed_line = json.loads(line)
        except json.decoder.JSONDecodeError:
            parsed_line = line
        queue.put(parsed_line)
    out.close()


def windows_language_code():
    import locale

    lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
    lang_code = locale.windows_locale[lang_id]
    return lang_code.split("_")[0]


def cleanup_on_reboot(dir_to_delete):
    dir_to_delete = dir_to_delete.replace("/", "\\")
    cmd = f'CMD /C rmdir /s /q "{dir_to_delete}"'

    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
        0,
        winreg.KEY_SET_VALUE,
    ) as key:
        winreg.SetValueEx(key, "MyAppCleanup", 0, winreg.REG_SZ, cmd)
