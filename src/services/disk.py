"""
Disk and partition management services.
Handles ISO mounting, partition operations, drive management, etc.
"""
import subprocess
from typing import Optional

CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW

def get_sys_drive_letter() -> str:
    """Get the system drive letter (usually C)."""
    result = subprocess.run(
        [r"powershell.exe", r"$env:SystemDrive.Substring(0, 1)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        check=True,
        creationflags=CREATE_NO_WINDOW,
    )
    return result.stdout.strip()


def get_disk_number(drive_letter: str) -> int:
    """
    Get the disk number for a given drive letter.
    
    Args:
        drive_letter: Drive letter (e.g., 'C')
        
    Returns:
        Disk number as integer
    """
    script = (
        r"(Get-Partition | Where DriveLetter -eq "
        + drive_letter
        + r" | Get-Disk).Number"
    )
    result = subprocess.run(
        [r"powershell.exe", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        check=True,
        creationflags=CREATE_NO_WINDOW,
    )
    return int(result.stdout.strip())


def get_drive_size_after_resize(drive_letter: str, minus_space: int) -> int:
    """
    Calculate the new drive size after shrinking by specified amount.
    
    Args:
        drive_letter: Drive letter to check
        minus_space: Amount of space to subtract in bytes
        
    Returns:
        New size in bytes
    """
    script = (
        r"(Get-Volume | Where DriveLetter -eq "
        + drive_letter
        + ").Size -"
        + str(minus_space)
    )
    result = subprocess.run(
        [r"powershell.exe", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        check=True,
        creationflags=CREATE_NO_WINDOW,
    )
    return int(float(result.stdout.strip().replace(",", ".")))


def resize_partition(drive_letter: str, new_size: int) -> subprocess.CompletedProcess:
    """
    Resize a partition to a new size.
    
    Args:
        drive_letter: Drive letter to resize
        new_size: New size in bytes
        
    Returns:
        CompletedProcess result
    """
    script = r"Resize-Partition -DriveLetter " + drive_letter + r" -Size " + str(new_size)
    return subprocess.run(
        [r"powershell.exe", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        check=True,
        creationflags=CREATE_NO_WINDOW,
    )


def get_unused_drive_letter() -> Optional[str]:
    """
    Find an unused drive letter starting from G.
    
    Returns:
        Available drive letter or None if none available
    """
    drive_letters = [
        "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", 
        "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"
    ]
    
    for letter in drive_letters:
        result = subprocess.run(
            [r"powershell.exe", r"Get-Volume | Where-Object DriveLetter -eq " + letter],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            creationflags=CREATE_NO_WINDOW,
        )
        if not result.stdout.strip():
            return letter
    return None

def new_volume(
    disk_number: int,
    size: int,
    filesystem: str,
    label: str,
    drive_letter: Optional[str] = None
) -> subprocess.CompletedProcess:
    """
    Create a new volume on the specified disk.
    
    Args:
        disk_number: Disk number to create volume on
        size: Size of the volume in bytes
        filesystem: Filesystem type (e.g., 'FAT32', 'NTFS', 'EXFAT')
        label: Volume label
        drive_letter: Optional drive letter assignment
        
    Returns:
        CompletedProcess result
    """
    script = f"$part = New-Partition -DiskNumber {disk_number} -Size {size}"
    
    if drive_letter is not None:
        script += f" -DriveLetter {drive_letter}"
    
    script += " | Get-Volume; "
    script += f'$part | Format-Volume -FileSystem {filesystem} -NewFileSystemLabel "{label}"; '
    script += "Disable-Bitlocker -MountPoint $part.Path"
    
    return subprocess.run(
        [r"powershell.exe", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        check=True,
        creationflags=CREATE_NO_WINDOW,
    )

def set_partition_as_efi(drive_letter: str) -> subprocess.CompletedProcess[str]:
    """
    Set a partition as EFI system partition.
    
    Args:
        drive_letter: Drive letter of partition to convert
        
    Returns:
        CompletedProcess result
    """
    script = (
        "Get-Partition -DriveLetter "
        + drive_letter
        + ' | Set-Partition -GptType "{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}"'
    )
    return subprocess.run(
        [r"powershell.exe", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        creationflags=CREATE_NO_WINDOW,
    )

def mount_iso(iso_path: str) -> str:
    """
    Mount an ISO file and return the drive letter.
    
    Args:
        iso_path: Path to ISO file
        
    Returns:
        Drive letter of mounted ISO
    """
    script = f'(Mount-DiskImage -ImagePath "{iso_path}" | Get-Volume).DriveLetter'
    result = subprocess.run(
        [r"powershell.exe", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        check=True,
        creationflags=CREATE_NO_WINDOW,
    )
    return result.stdout.strip()


def unmount_iso(iso_path: str) -> str:
    """
    Unmount an ISO file.
    
    Args:
        iso_path: Path to ISO file
        
    Returns:
        Command output
    """
    if not iso_path:
        return ""
    
    script = f'Dismount-DiskImage -ImagePath "{iso_path}"'
    result = subprocess.run(
        [r"powershell.exe", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        creationflags=CREATE_NO_WINDOW,
    )
    return result.stdout.strip()


def remove_drive_letter(drive_letter: str) -> subprocess.CompletedProcess:
    """
    Remove the drive letter assignment from a partition.
    
    Args:
        drive_letter: Drive letter to remove
        
    Returns:
        CompletedProcess result
    """
    script = (
        f"Get-Volume -Drive {drive_letter} | Get-Partition | "
        f"Remove-PartitionAccessPath -accesspath {drive_letter}:\\"
    )
    return subprocess.run(
        ["powershell.exe", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        creationflags=CREATE_NO_WINDOW,
    )


def get_system_efi_drive_uuid() -> str:
    """
    Get the UUID of the system EFI partition.
    
    Returns:
        EFI partition UUID
    """
    script = '(Get-Partition | Where-Object -Property "IsSystem" -EQ true).AccessPaths'
    result = subprocess.run(
        [r"powershell.exe", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        check=True,
        creationflags=CREATE_NO_WINDOW,
    )
    output = result.stdout
    start_idx = output.index("{") + 1
    end_idx = output.index("}")
    return output[start_idx:end_idx]
