from dataclasses import dataclass
from enum import Enum
import os
import platform
import shutil
import subprocess
from typing import Any, Dict, Optional


class CheckType(Enum):
    ARCH = "arch"
    UEFI = "uefi"
    RAM = "ram"
    SPACE = "space"
    RESIZABLE = "resizable"


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
    proc = subprocess.run(
        [r"powershell.exe", r"$env:firmware_type"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    return Check(
        CheckType.UEFI.value,
        proc.stdout.strip().lower(),
        proc.returncode,
        proc,
    )


def check_ram():
    print("Checking RAM size...")
    # Use PowerShell with hidden window for RAM check
    proc = subprocess.run(
        [
            r"powershell.exe",
            r"(Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property capacity -Sum).sum",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    return Check(
        CheckType.RAM.value,
        int(proc.stdout.strip()) if proc.returncode == 0 else proc.stdout.strip(),
        proc.returncode,
        proc,
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
        # Fallback to PowerShell if shutil fails
        proc = subprocess.run(
            [
                r"powershell.exe",
                r"(Get-Volume | Where DriveLetter -eq $env:SystemDrive.Substring(0, 1)).SizeRemaining",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return Check(
            CheckType.SPACE.value,
            int(proc.stdout.strip()) if proc.returncode == 0 else str(e),
            proc.returncode,
            proc,
        )


def check_resizable():
    """Check available resizable space on system drive (requires admin privileges)."""
    from services.privilege_manager import elevated
    
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


check_functions = {
    CheckType.ARCH: check_arch,
    CheckType.UEFI: check_uefi,
    CheckType.RAM: check_ram,
    CheckType.SPACE: check_space,
    CheckType.RESIZABLE: check_resizable,
}
