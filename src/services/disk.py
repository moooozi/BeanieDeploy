"""
Disk and partition management services.
Handles ISO mounting, partition operations, drive management, etc.
"""
import os
import posixpath
import subprocess
from typing import Optional
from pycdlib import PyCdlib
import contextlib
import winreg
CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW


@contextlib.contextmanager
def prevent_bitlocker_auto_encrypt():
    """
    Context manager that prevents Windows from automatically encrypting new volumes.
    
    Sets PreventDeviceEncryption registry key to 1 and restores the original value afterwards.
    """
    key_path = r"SYSTEM\CurrentControlSet\Control\BitLocker"
    value_name = "PreventDeviceEncryption"
    
    # Get the original value
    original_value = None
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ) as key:
            original_value, _ = winreg.QueryValueEx(key, value_name)
    except FileNotFoundError:
        pass  # Key doesn't exist
    
    # Set PreventDeviceEncryption to 1
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, 1)
    
    try:
        yield
    finally:
        # Restore the original value
        if original_value is None:
            # Key didn't exist, delete it
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, value_name)
            except FileNotFoundError:
                pass  # Already gone
        else:
            # Key existed, restore original value
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, original_value)


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

def new_partition(
    disk_number: int,
    size: int,
    filesystem: Optional[str] = None,
    label: Optional[str] = None,
    drive_letter: Optional[str] = None,
    assign_drive_letter: bool = False
) -> dict:
    """
    Create a new partition on the specified disk, optionally formatting it as a volume.
    
    Args:
        disk_number: Disk number to create partition on
        size: Size of the partition in bytes
        filesystem: Optional filesystem type (e.g., 'FAT32', 'NTFS', 'EXFAT'). If provided, the partition will be formatted.
        label: Optional volume label (only used if filesystem is provided)
        drive_letter: Optional drive letter assignment
        assign_drive_letter: Whether to automatically assign a drive letter if none specified (default: False)
        
    Returns:
        Dictionary with partition metadata:
        - partition_guid: str (GUID without braces)
        - partition_number: int
        - offset: int (bytes)
        - size: int (bytes)
        - logical_sector_size: int (bytes)
        - start_lba: int
        - size_lba: int
        - vol_unique_id: str (only included if formatted, volume unique ID in WMI format, typically \\\\?\\Volume{PartitionGuid})
    """
    import win32com.client
    
    wmi = win32com.client.GetObject("winmgmts:root/Microsoft/Windows/Storage")
    
    # Find the target disk
    disks = wmi.InstancesOf("MSFT_Disk")
    target_disk = None
    for disk in disks:
        if int(disk.Number) == disk_number:
            target_disk = disk
            break
    if not target_disk:
        raise ValueError(f"Disk {disk_number} not found")
    
    with prevent_bitlocker_auto_encrypt():
        # Create partition
        in_params = target_disk.Methods_("CreatePartition").InParameters.SpawnInstance_()
        in_params.Size = size
        in_params.UseMaximumSize = False
        in_params.Alignment = 0
        in_params.IsHidden = False
        in_params.IsActive = False
        
        if target_disk.PartitionStyle == 1:  # MBR
            in_params.MbrType = 6  # Huge
            # GptType not set
        else:  # GPT
            in_params.GptType = "{ebd0a0a2-b9e5-4433-87c0-68b6b72699c7}"
            # MbrType not set for GPT
        
        if drive_letter:
            in_params.DriveLetter = drive_letter
            in_params.AssignDriveLetter = False
        elif assign_drive_letter:
            in_params.DriveLetter = None
            in_params.AssignDriveLetter = True
        else:
            in_params.DriveLetter = None
            in_params.AssignDriveLetter = False
        
        out_params = target_disk.ExecMethod_("CreatePartition", in_params)
        result = out_params.ReturnValue
        if result != 0:
            raise RuntimeError(f"CreatePartition failed with code {result}: {out_params.ExtendedStatus}")
        
        partition = out_params.CreatedPartition
        
        vol_unique_id = None
        if filesystem:
            # Find the associated volume using WMI association
            associated_volumes = partition.Associators_("MSFT_PartitionToVolume")
            if not associated_volumes:
                raise RuntimeError("No volume associated with the created partition")
            
            target_volume = associated_volumes[0]  # Should be exactly one volume per partition
            
            # Map filesystem
            fs_map = {
                'FAT32': 'FAT32',
                'NTFS': 'NTFS',
                'EXFAT': 'ExFAT'
            }
            wmi_fs = fs_map.get(filesystem.upper(), filesystem.upper())
        
            # Format the volume
            in_params_format = target_volume.Methods_("Format").InParameters.SpawnInstance_()
            in_params_format.FileSystem = wmi_fs
            in_params_format.FileSystemLabel = label or ""
            in_params_format.Full = False
            in_params_format.Force = True
            
            out_params_format = target_volume.ExecMethod_("Format", in_params_format)
            result = out_params_format.ReturnValue
            if result != 0:
                raise RuntimeError(f"Format failed with code {result}: {out_params_format.ExtendedStatus}")
            
            vol_unique_id = str(target_volume.UniqueId).strip()
    
    # Return partition metadata
    partition_guid = str(partition.Guid).strip('{}')
    
    offset = int(partition.Offset)
    part_size = int(partition.Size)
    sector = int(target_disk.LogicalSectorSize)
    if sector <= 0:
        raise RuntimeError(f"Invalid logical sector size: {sector}")
    
    start_lba = offset // sector
    size_lba = part_size // sector
    
    result = {
        "partition_guid": partition_guid,
        "partition_number": int(partition.PartitionNumber),
        "offset": offset,
        "size": part_size,
        "logical_sector_size": sector,
        "start_lba": int(start_lba),
        "size_lba": int(size_lba),
    }
    if vol_unique_id:
        result["vol_unique_id"] = vol_unique_id
    return result


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


def mount_volume_to_path(volume_unique_id: str, mount_path: str) -> None:
    """
    Mount a volume to a specified path instead of a drive letter.
    
    Args:
        volume_unique_id: Volume unique ID ( \\\\?\\Volume{...}\\)
        mount_path: Path to mount the volume to
    """
    # Ensure the mount path exists
    import os
    os.makedirs(mount_path, exist_ok=True)
        
    # Mount the volume to the path
    subprocess.run(
        ['mountvol', mount_path, volume_unique_id],
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
