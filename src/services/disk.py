"""
Disk and partition management services.
Handles ISO mounting, partition operations, drive management, etc.
"""
import os
import posixpath
import subprocess
from typing import Optional
from pycdlib import PyCdlib
CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW

def get_sys_drive_letter() -> str:
    """Get the system drive letter (usually C)."""
    return os.environ.get('SystemDrive', 'C')[0]


def get_disk_number(drive_letter: str) -> int:
    """
    Get the disk number for a given drive letter.
    
    Args:
        drive_letter: Drive letter (e.g., 'C')
        
    Returns:
        Disk number as integer
    """
    import win32com.client
    wmi = win32com.client.GetObject("winmgmts:")
    partitions = wmi.InstancesOf("Win32_DiskPartition")
    for partition in partitions:
        # Check if this partition has the drive letter
        for assoc in partition.Associators_("Win32_LogicalDiskToPartition"):
            if assoc.DeviceID.upper() == drive_letter.upper() + ":":
                return partition.DiskIndex
    raise ValueError(f"No disk found for drive letter {drive_letter}")


def get_drive_size(drive_letter: str) -> int:
    """
    Get the current size of a drive.
    
    Args:
        drive_letter: Drive letter to check
        
    Returns:
        Current size in bytes
    """
    import win32com.client
    wmi = win32com.client.GetObject("winmgmts:")
    volumes = wmi.InstancesOf("Win32_Volume")
    for volume in volumes:
        if str(volume.DriveLetter).rstrip(':').upper() == drive_letter.upper():
            return int(volume.Capacity)
    raise ValueError(f"No volume found for drive letter {drive_letter}")


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
    import win32com.client
    wmi = win32com.client.GetObject("winmgmts:")
    volumes = wmi.InstancesOf("Win32_Volume")
    used_letters = set()
    for volume in volumes:
        letter = str(volume.DriveLetter).strip()
        if letter:
            used_letters.add(letter.rstrip(':').upper())
    
    drive_letters = [
        "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", 
        "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"
    ]
    
    for letter in drive_letters:
        if letter not in used_letters:
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

def extract_iso_to_dir(iso_path: str, target_dir: str, filter_func=None) -> str:
    iso = PyCdlib()
    iso.open(iso_path)
    os.makedirs(target_dir, exist_ok=True)

    try:
        for parent, dirs, files in iso.walk(joliet_path='/'):
            rel_path = parent.lstrip('/')
            local_dir = os.path.join(target_dir, rel_path)

            wrote_any_file = False
            for f in files:
                iso_file_path = posixpath.join(parent, f)
                local_file_path = os.path.join(local_dir, f)

                if filter_func and not filter_func(iso_file_path):
                    continue

                # Create the directory only when we actually need to write a file
                if not wrote_any_file:
                    os.makedirs(local_dir, exist_ok=True)
                    wrote_any_file = True

                iso.get_file_from_iso(local_path=local_file_path, joliet_path=iso_file_path)
    finally:
        iso.close()

    return target_dir



def get_system_efi_drive_uuid() -> str:
    """
    Get the UUID of the system EFI partition.
    
    Returns:
        EFI partition UUID
    """
    import win32com.client
    wmi = win32com.client.GetObject("winmgmts:")
    volumes = wmi.InstancesOf("Win32_Volume")
    for volume in volumes:
        if volume.SystemVolume:
            device_id = str(volume.DeviceID)
            # DeviceID is like \\?\Volume{uuid}\
            start = device_id.find("{") + 1
            end = device_id.find("}")
            return device_id[start:end]
    raise ValueError("EFI partition not found")


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
    Get partition information by GUID (partition GUID) using pure WMI.
    
    Uses MSFT_Partition.Guid to find the partition by its unique GUID.
    
    Args:
        guid: Partition GUID (with or without braces)
        
    Returns:
        Dictionary with partition information
    """
    import win32com.client
    
    # Normalize GUID format - remove braces if present
    guid = guid.strip('{}')
    
    # Connect to Storage namespace
    wmi = win32com.client.GetObject("winmgmts:root/Microsoft/Windows/Storage")
    
    # Find partition by unique GUID
    partitions = wmi.InstancesOf("MSFT_Partition")
    target_partition = None
    for partition in partitions:
        part_guid = str(partition.Guid).strip('{}')
        if part_guid.lower() == guid.lower():
            target_partition = partition
            break
    
    if not target_partition:
        raise RuntimeError(f"No partition found with GUID {guid}")
    
    # Get disk info
    disks = wmi.InstancesOf("MSFT_Disk")
    disk = None
    for d in disks:
        if str(d.Path) == str(target_partition.DiskId):
            disk = d
            break
    
    if not disk:
        raise RuntimeError("Could not find disk for partition")
    
    # Compute LBAs
    offset = int(target_partition.Offset)
    part_size = int(target_partition.Size)
    sector = int(disk.LogicalSectorSize)
    if sector <= 0:
        raise RuntimeError(f"Invalid logical sector size: {sector}")
    
    start_lba = offset // sector
    size_lba = part_size // sector
    
    return {
        "partition_guid": guid,
        "partition_number": int(target_partition.PartitionNumber),
        "offset": offset,
        "size": part_size,
        "logical_sector_size": sector,
        "start_lba": int(start_lba),
        "size_lba": int(size_lba),
    }
