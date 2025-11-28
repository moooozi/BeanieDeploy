from dataclasses import dataclass
from enum import Enum
import os
import platform
import shutil
import subprocess
from typing import Any, Dict, Optional
import win32com.client

from services.privilege_manager import elevated

# Required space for EFI files: measured 12.7MB for EFI directory + 5MB safety buffer
REQUIRED_EFI_SPACE_MB = 18


class CheckType(Enum):
    ARCH = "arch"
    UEFI = "uefi"
    RAM = "ram"
    SPACE = "space"
    RESIZABLE = "resizable"
    EFI_SPACE = "efi_space"


@dataclass
class Check:
    name: str
    result: Any
    returncode: Optional[int]
    process: Optional[subprocess.CompletedProcess[str]]


class DoneChecks:
    def __init__(self):
        self.checks: Dict[CheckType, Check] = {
            check_type: Check(
                name=check_type.value, result=None, returncode=None, process=None
            )
            for check_type in CheckType
        }


def check_arch():
    print("Checking architecture...")
    # Use Python's platform module instead of PowerShell
    result = platform.machine().lower()

    return Check(
        CheckType.ARCH.value,
        result,
        0,  # Success return code
        None,  # No subprocess used
    )


def check_uefi():
    print("Checking firmware type...")
    # Use PowerShell but with hidden window
    proc = os.environ.get('SystemDrive', 'C')[0]

    return Check(
        CheckType.UEFI.value,
        proc.lower(),
        0,  # Success return code
        None,  # No subprocess used
    )


def check_ram():
    print("Checking RAM size...")
    # Use WMI instead of PowerShell
    try:
        wmi = win32com.client.GetObject("winmgmts:")
        memories = wmi.InstancesOf("Win32_PhysicalMemory")
        total_capacity = 0
        for memory in memories:
            total_capacity += int(memory.Capacity)
        return Check(
            CheckType.RAM.value,
            total_capacity,
            0,  # Success
            None,
        )
    except Exception as e:
        return Check(
            CheckType.RAM.value,
            str(e),
            1,  # Error
            None,
        )


def check_space():
    print("Checking available space...")
    # Use shutil.disk_usage instead of PowerShell
    try:
        # Get the system drive (usually C:)
        system_drive = os.environ.get("SystemDrive", "C:")
        if not system_drive.endswith(":"):
            system_drive += ":"

        # Get disk usage
        _, _, free = shutil.disk_usage(system_drive + "\\")
        return Check(
            CheckType.SPACE.value,
            free,  # Available space in bytes
            0,  # Success return code
            None,  # No subprocess used
        )
    except Exception as e:
        # Fallback to WMI if shutil fails
        try:
            wmi = win32com.client.GetObject("winmgmts:")
            system_drive = os.environ.get("SystemDrive", "C:")[0]
            volumes = wmi.InstancesOf("Win32_Volume")
            for volume in volumes:
                if str(volume.DriveLetter).upper() == system_drive.upper():
                    return Check(
                        CheckType.SPACE.value,
                        int(volume.FreeSpace),
                        0,
                        None,
                    )
            # If not found, return error
            return Check(
                CheckType.SPACE.value,
                str(e),
                1,
                None,
            )
        except Exception as wmi_e:
            return Check(
                CheckType.SPACE.value,
                str(e) + " | WMI error: " + str(wmi_e),
                1,
                None,
            )


def check_resizable():
    """Check available resizable space on system drive (requires admin privileges)."""
    
    print("Checking resizable space...")
    # API is identical to subprocess.run()
    proc = elevated.run(
        [
            r"powershell.exe",
            "-Command",
            r"((Get-Volume | Where DriveLetter -eq $env:SystemDrive.Substring(0, 1)).Size - (Get-PartitionSupportedSize -DriveLetter $env:SystemDrive.Substring(0, 1)).SizeMin)",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    print(f"Resizable check output: {proc.stdout.strip()}")
    return Check(
        CheckType.RESIZABLE.value,
        int(proc.stdout.strip()) if proc.returncode == 0 else proc.stdout.strip(),
        proc.returncode,
        proc,
    )


def _get_efi_free_space() -> int:
    """Get free space on EFI partition using WMI."""
    import win32com.client
    wmi = win32com.client.GetObject("winmgmts:")
    volumes = wmi.InstancesOf("Win32_Volume")
    for volume in volumes:
        if volume.SystemVolume:
            return int(volume.FreeSpace)
    raise ValueError("EFI partition not found")


def check_efi_space():
    """Check available free space on the EFI partition."""
    print("Checking EFI partition space...")
    result_value = _get_efi_free_space()
    return Check(
        CheckType.EFI_SPACE.value,
        result_value,
        0,
        None,
    )


check_functions = {
    CheckType.ARCH: check_arch,
    CheckType.UEFI: check_uefi,
    CheckType.RAM: check_ram,
    CheckType.SPACE: check_space,
    CheckType.RESIZABLE: check_resizable,
    CheckType.EFI_SPACE: check_efi_space,
}
