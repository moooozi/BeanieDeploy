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


def get_drive_size(drive_letter: str) -> int:
    """
    Get the current size of a drive.
    
    Args:
        drive_letter: Drive letter to check
        
    Returns:
        Current size in bytes
    """
    script = r"(Get-Volume | Where DriveLetter -eq " + drive_letter + ").Size"
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


def new_volume_with_metadata(
    disk_number: int,
    size: int,
    filesystem: str,
    label: str,
    drive_letter: Optional[str] = None,
) -> dict:
    """
    Create a new partition, format it and return reliable metadata about it.

    Returns a dict with keys:
      - partition_guid: str (GUID without braces)
      - partition_number: int
      - offset: int (bytes)
      - size: int (bytes)
      - logical_sector_size: int (bytes)
      - start_lba: int
      - size_lba: int

    This function will raise RuntimeError if any required field cannot be obtained.
    It does not use placeholder values.
    Requires administrative privileges.
    """
    import json

    drive_arg = f"-DriveLetter {drive_letter}" if drive_letter else ""
    ps = fr"""
    $p = New-Partition -DiskNumber {disk_number} -Size {size} -ErrorAction Stop {drive_arg}
    # Wait for partition to be ready
    $maxTries = 10
    $tries = 0
    while ($p -and $p.Guid -eq $null -and $tries -lt $maxTries) {{
        Start-Sleep -Seconds 1
        $p = Get-Partition -DiskNumber {disk_number} | Where-Object Size -EQ {size}
        $tries++
    }}
    if ($p -eq $null) {{ throw "Partition creation failed or not found after waiting." }}
    # Format the partition
    $formatResult = $p | Format-Volume -FileSystem {filesystem} -NewFileSystemLabel \"{label}\" -ErrorAction Stop
    # Wait for volume object to appear
    $vol = $null
    $tries = 0
    while ($vol -eq $null -and $tries -lt $maxTries) {{
        Start-Sleep -Seconds 1
        $vol = Get-Volume -Partition $p -ErrorAction SilentlyContinue
        $tries++
    }}
    if ($vol -eq $null) {{ throw "Volume object not found after formatting partition." }}
    # Disable BitLocker if present
    $bitlocker = Disable-BitLocker -MountPoint $vol.Path -ErrorAction SilentlyContinue
    
    $disk = Get-Disk -Number $p.DiskNumber -ErrorAction Stop
    $obj = [PSCustomObject]@{{
      PartitionGuid     = $p.Guid
      PartitionNumber   = $p.PartitionNumber
      Offset            = $p.Offset
      Size              = $p.Size
      LogicalSectorSize = $disk.LogicalSectorSize
      VolumeGuid        = $vol.UniqueId
    }}
    $obj | ConvertTo-Json -Compress
    """

    result = subprocess.run(
        [r"powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        check=True,
        creationflags=CREATE_NO_WINDOW,
    )

    payload = result.stdout.strip()
    if not payload:
        raise RuntimeError("PowerShell returned no output when creating partition")

    try:
        data = json.loads(payload)
    except Exception as e:
        raise RuntimeError(f"Failed to parse PowerShell JSON output: {e}\nOutput: {payload}")

    # Validate required fields
    required_fields = ["PartitionGuid", "PartitionNumber", "Offset", "Size", "LogicalSectorSize", "VolumeGuid"]
    for f in required_fields:
        if f not in data or data[f] is None or str(data[f]).strip() == "":
            raise RuntimeError(f"Required field '{f}' missing from PowerShell output: {data}")

    # Normalize and compute LBAs
    part_guid = str(data["PartitionGuid"]).strip()
    if part_guid.startswith("{") and part_guid.endswith("}"):
        part_guid = part_guid[1:-1]

    volume_guid = str(data["VolumeGuid"]).strip()
    
    offset = int(data["Offset"])
    part_size = int(data["Size"])
    sector = int(data["LogicalSectorSize"])
    if sector <= 0:
        raise RuntimeError(f"Invalid logical sector size: {sector}")

    start_lba = offset // sector
    size_lba = part_size // sector

    return {
        "partition_guid": part_guid,
        "partition_number": int(data["PartitionNumber"]),
        "offset": offset,
        "size": part_size,
        "logical_sector_size": sector,
        "start_lba": int(start_lba),
        "size_lba": int(size_lba),
        "volume_guid": volume_guid,
    }


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


def mount_volume_to_path(volume_guid: str, mount_path: str) -> None:
    """
    Mount a volume to a specified path instead of a drive letter.
    
    Args:
        volume_guid: Volume GUID (with or without braces)
        mount_path: Path to mount the volume to
    """
    # Ensure the mount path exists
    import os
    os.makedirs(mount_path, exist_ok=True)
    
    # Normalize GUID format
    if not volume_guid.startswith("\\\\?\\Volume{"):
        if volume_guid.startswith("{") and volume_guid.endswith("}"):
            volume_guid = f"\\\\?\\Volume{volume_guid}"
        else:
            volume_guid = f"\\\\?\\Volume{{{volume_guid}}}"
    
    # Mount the volume to the path
    subprocess.run(
        ['mountvol', mount_path, volume_guid],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        shell=True,
        check=True,
        creationflags=CREATE_NO_WINDOW,
    )


def unmount_volume_from_path(mount_path: str) -> None:
    """
    Unmount a volume from a specified path.
    
    Args:
        mount_path: Path where the volume is mounted
    """
    subprocess.run(
        [r"mountvol", mount_path, "/d"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
        shell=True,
        creationflags=CREATE_NO_WINDOW,
    )


def get_partition_info_by_guid(guid: str) -> dict:
    """
    Get partition information by GUID (partition GUID or volume GUID).
    
    Args:
        guid: Partition GUID or Volume GUID (with or without braces)
        
    Returns:
        Dictionary with partition information including PartitionNumber, StartLBA, SizeLBA, etc.
    """
    import json
    
    # Normalize GUID format - remove braces if present
    guid = guid.strip('{}')
    
    ps = f"""
    $ErrorActionPreference = "Stop"
    
    # Find partition by GUID
    $p = Get-Partition | Where-Object {{ $_.Guid -eq "{{{guid}}}" }} | Select-Object -First 1
    if (-not $p) {{
        throw "Could not find partition with GUID {guid}"
    }}
    
    $disk = Get-Disk -Number $p.DiskNumber -ErrorAction Stop
    
    $obj = [PSCustomObject]@{{
      PartitionGuid     = $p.Guid
      PartitionNumber   = $p.PartitionNumber
      Offset            = $p.Offset
      Size              = $p.Size
      LogicalSectorSize = $disk.LogicalSectorSize
    }}
    $obj | ConvertTo-Json -Compress
    """

    result = subprocess.run(
        [r"powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        check=True,
        creationflags=CREATE_NO_WINDOW,
    )

    payload = result.stdout.strip()
    if not payload:
        raise RuntimeError(f"No partition found with GUID {guid}")

    try:
        data = json.loads(payload)
    except Exception as e:
        raise RuntimeError(f"Failed to parse PowerShell JSON output: {e}\nOutput: {payload}")

    # Normalize and compute LBAs
    part_guid = str(data["PartitionGuid"]).strip()
    if part_guid.startswith("{") and part_guid.endswith("}"):
        part_guid = part_guid[1:-1]

    offset = int(data["Offset"])
    part_size = int(data["Size"])
    sector = int(data["LogicalSectorSize"])
    if sector <= 0:
        raise RuntimeError(f"Invalid logical sector size: {sector}")

    start_lba = offset // sector
    size_lba = part_size // sector

    return {
        "partition_guid": part_guid,
        "partition_number": int(data["PartitionNumber"]),
        "offset": offset,
        "size": part_size,
        "logical_sector_size": sector,
        "start_lba": int(start_lba),
        "size_lba": int(size_lba),
    }
