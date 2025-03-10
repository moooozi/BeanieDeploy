from dataclasses import dataclass
import subprocess
from typing import Any
import functions as fn


@dataclass
class Check:
    name: str
    result: Any
    returncode: int
    process: subprocess.CompletedProcess


def check_arch():
    proc = subprocess.run(
        [r"powershell.exe", r"$env:PROCESSOR_ARCHITECTURE"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    return Check(
        "arch",
        proc.stdout.strip().lower(),
        proc.returncode,
        proc,
    )


def check_uefi():
    proc = subprocess.run(
        [r"powershell.exe", r"$env:firmware_type"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    return Check(
        "uefi",
        proc.stdout.strip().lower(),
        proc.returncode,
        proc,
    )


def check_ram():
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
        "ram",
        int(proc.stdout.strip()),
        proc.returncode,
        proc,
    )


def check_space():
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
        "space",
        int(proc.stdout.strip()),
        proc.returncode,
        proc,
    )


def check_resizable():
    if not fn.is_admin():
        return Check("resizable", "Not an admin", -200, None)
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
        "resizable",
        int(proc.stdout.strip()),
        proc.returncode,
        proc,
    )
