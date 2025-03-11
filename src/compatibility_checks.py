from dataclasses import dataclass
from enum import Enum
import subprocess
from typing import Any, Dict
import functions as fn


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
    returncode: int
    process: subprocess.CompletedProcess


class DoneChecks:
    def __init__(self):
        self.checks: Dict[CheckType, Check] = {
            check_type: Check(
                name=check_type.value, result=None, returncode=None, process=None
            )
            for check_type in CheckType
        }


class Checks:
    def __init__(self):
        self.check_functions = {
            CheckType.ARCH: check_arch,
            CheckType.UEFI: check_uefi,
            CheckType.RAM: check_ram,
            CheckType.SPACE: check_space,
            CheckType.RESIZABLE: check_resizable,
        }


def check_arch():
    print("Checking architecture...")
    proc = subprocess.run(
        [r"powershell.exe", r"$env:PROCESSOR_ARCHITECTURE"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    return Check(
        CheckType.ARCH.value,
        proc.stdout.strip().lower(),
        proc.returncode,
        proc,
    )


def check_uefi():
    print("Checking firmware type...")
    proc = subprocess.run(
        [r"powershell.exe", r"$env:firmware_type"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    return Check(
        CheckType.UEFI.value,
        proc.stdout.strip().lower(),
        proc.returncode,
        proc,
    )


def check_ram():
    print("Checking RAM size...")
    proc = subprocess.run(
        [
            r"powershell.exe",
            r"(Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property capacity -Sum).sum",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    return Check(
        CheckType.RAM.value,
        int(proc.stdout.strip()),
        proc.returncode,
        proc,
    )


def check_space():
    print("Checking available space...")
    proc = subprocess.run(
        [
            r"powershell.exe",
            r"(Get-Volume | Where DriveLetter -eq $env:SystemDrive.Substring(0, 1)).SizeRemaining",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    return Check(
        CheckType.SPACE.value,
        int(proc.stdout.strip()),
        proc.returncode,
        proc,
    )


def check_resizable():
    if not fn.is_admin():
        return Check(CheckType.RESIZABLE.value, "Not an admin", -200, None)
    proc = subprocess.run(
        [
            r"powershell.exe",
            r"((Get-Volume | Where DriveLetter -eq $env:SystemDrive.Substring(0, 1)).Size - (Get-PartitionSupportedSize -DriveLetter $env:SystemDrive.Substring(0, 1)).SizeMin)",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    return Check(
        CheckType.RESIZABLE.value,
        int(proc.stdout.strip()),
        proc.returncode,
        proc,
    )
