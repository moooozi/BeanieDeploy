import time
import APP_INFO
import webbrowser
import subprocess
from multiprocessing import Queue

import app


def open_url(url):
    webbrowser.open_new_tab(url)


def compatibility_test(queue):
    print('hey')
    required_space_min = 900 * 1024 * 1024
    required_space_dualboot = required_space_min + 70 * 1024 * 1024 * 1024
    required_ram = 4

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

    # def check_resizable():
    #    return subprocess.run([r'powershell.exe',
    #                           r'((Get-Volume | Where DriveLetter -eq $env:SystemDrive.Substring(0, 1)).Size - (Get-PartitionSupportedSize -DriveLetter $env:SystemDrive.Substring(0, 1)).SizeMin)'],
    #                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

    totalram = int(check_totalram().stdout)
    result_resizable_check = 0
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

    # if result_space_check in (1, 2):
    #    print(check_resizable())
    #    if check_resizable().returncode != 0:
    #        result_resizable_check = 9
    #    elif int(str(check_resizable().stdout)[2:-5]) > required_space_min:
    #        result_resizable_check = 1
    #    else:
    #        result_resizable_check = 0
    # else:
    #    result_resizable_check = 8
    result_resizable_check = 8
    check_results = {'result_uefi_check': result_uefi_check,
                     'result_totalram_check': result_totalram_check,
                     'result_space_check': result_space_check,
                     'result_resizable_check': result_resizable_check}
    queue.put(check_results)

    # return check_results


def create_temp_boot_partition():
    print('create_temp_boot_partition')

    def get_sys_drive_letter():
        return subprocess.run([r'powershell.exe', r'$env:SystemDrive.Substring(0, 1)'], stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, shell=True)

    def get_disk_number(drive_letter):
        return subprocess.run(
            [r'powershell.exe', r'(Get-Partition | Where DriveLetter -eq ' + drive_letter + ' | Get-Disk).Number'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, shell=True)

    def get_drive_size_after_resize(drive_letter):
        return subprocess.run(
            [r'powershell.exe',
             r'(Get-Volume | Where DriveLetter -eq ' + drive_letter + ').Size -' + APP_INFO.required_shrink_space],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, shell=True)

    def resize_partition(drive_letter, new_size):
        return subprocess.run(
            [r'powershell.exe',
             r'Resize-Partition -DriveLetter ' + drive_letter + ' -Size ' + new_size],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, shell=True)

    def new_partition(disk_number, size, drive_letter):
        return subprocess.run(
            [r'powershell.exe',
             r'New-Partition -DiskNumber ' + disk_number + ' -Size ' + size + ' -DriveLetter ' + drive_letter],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, shell=True)

    def format_volume(drive_letter, filesystem):
        return subprocess.run(
            [r'powershell.exe',
             r'Format-Volume -DriveLetter ' + drive_letter + ' -FileSystem ' + filesystem],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, shell=True)

    sys_drive_letter = str(get_sys_drive_letter().stdout)[2:-5]
    sys_disk_number = str(get_disk_number(sys_drive_letter).stdout)[2:-5]
    sys_drive_new_size = str(get_drive_size_after_resize(sys_drive_letter).stdout)[2:-5]
    resize_partition(sys_drive_letter, sys_drive_new_size)

    tmp_part_size = APP_INFO.required_shrink_space - 1000000
    tmp_part_letter = 'T'
    new_partition(sys_disk_number, tmp_part_size, tmp_part_letter)
    format_volume(tmp_part_letter, 'FAT32')


def get_user_home():
    return str(subprocess.run(
        [r'powershell.exe', r'$home'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[2:-5]


def download_file(url, destination, queue2):
    job_id = str(subprocess.run(
        [r'powershell.exe',
         r'(Start-BitsTransfer -Source ' + url + ' -Destination ' + destination + ' -Priority normal -Asynchronous).JobId'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, shell=True).stdout)[2:-5]
    queue2.put(job_id)


def get_download_size(job_id):
    return int(str(subprocess.run(
        [r'powershell.exe', r'(Get-BitsTransfer | ? { $_.JobId -eq "' + job_id + '" }).bytestotal'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[2:-5])


def track(job_id):
    return int(str(subprocess.run(
        [r'powershell.exe', r'(Get-BitsTransfer | ? { $_.JobId -eq "' + job_id + '" }).bytestransferred'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[2:-5])


def join_downloaded_file(job_id):
    return int(str(subprocess.run(
        [r'powershell.exe', r'(Get-BitsTransfer | ? { $_.JobId -eq "' + job_id + '" }).bytestransferred'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[2:-5])

