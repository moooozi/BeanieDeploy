import time
import webbrowser
import subprocess
from multiprocessing import Queue



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

    #def check_resizable():
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

    #if result_space_check in (1, 2):
    #    print(check_resizable())
    #    if check_resizable().returncode != 0:
    #        result_resizable_check = 9
    #    elif int(str(check_resizable().stdout)[2:-5]) > required_space_min:
    #        result_resizable_check = 1
    #    else:
    #        result_resizable_check = 0
    #else:
    #    result_resizable_check = 8
    result_resizable_check = 8
    check_results = {'result_uefi_check': result_uefi_check,
                     'result_totalram_check': result_totalram_check,
                     'result_space_check': result_space_check,
                     'result_resizable_check': result_resizable_check}
    queue.put(check_results)

    #return check_results


