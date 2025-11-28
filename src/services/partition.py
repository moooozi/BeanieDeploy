"""
Partition management operations.
Handles complex partitioning procedures and disk operations.
"""
from dataclasses import dataclass

from services.disk import (
    get_sys_drive_letter, get_disk_number, get_drive_size, new_volume_with_metadata,
    resize_partition, new_volume, get_system_efi_drive_uuid,
    mount_volume_to_path
)
import os
import subprocess
import win32com.client


def get_volume_uuid(drive_letter: str) -> str:
    """Get the UUID of a volume using WMI."""
    wmi = win32com.client.GetObject("winmgmts:")
    volumes = wmi.InstancesOf("Win32_Volume")
    for volume in volumes:
        if str(volume.DriveLetter).rstrip(':').upper() == drive_letter.upper():
            device_id = str(volume.DeviceID).strip()
            # DeviceID is like \\?\Volume{uuid}\
            start = device_id.find("{")
            end = device_id.find("}")
            return "{" + device_id[start+1:end] + "}"
    raise ValueError(f"Volume not found for drive {drive_letter}")

@dataclass
class TemporaryPartition:
    """Temporary partition information."""
    mount_path: str
    partition_guid: str
    partition_number: int
    offset: int
    size: int
    logical_sector_size: int
    start_lba: int
    size_lba: int
    

@dataclass
class PartitioningResult:
    """Result of partitioning procedure."""
    tmp_part: TemporaryPartition
    sys_drive_uuid: str
    sys_drive_win_uuid: str
    sys_efi_uuid: str
    shrink_space: int
    sys_drive_letter: str
    sys_disk_number: int
    sys_drive_original_size: int


def partition_procedure(
    tmp_part_size: int,
    temp_part_label: str,
    shrink_space: int = 0,
    boot_part_size: int = 0,
    efi_part_size: int = 0,
    make_root_partition: bool = False,
) -> PartitioningResult:
    """
    Execute the complete partitioning procedure.
    
    Args:
        tmp_part_size: Size of temporary partition in bytes
        temp_part_label: Label for temporary partition
        shrink_space: Amount of space to shrink from system drive
        boot_part_size: Size of boot partition in bytes
        efi_part_size: Size of EFI partition in bytes
        make_root_partition: Whether to create a root partition
        
    Returns:
        PartitioningResult with partition information
    """

    # Get system drive information
    sys_drive_letter = get_sys_drive_letter()
    sys_drive_win_uuid = get_volume_uuid(sys_drive_letter)
    sys_drive_uuid = _extract_uuid_from_string(sys_drive_win_uuid)
    
    # Store original system drive size for potential rollback
    sys_drive_original_size = get_drive_size(sys_drive_letter)
    
    # Get EFI and disk information
    sys_efi_uuid = get_system_efi_drive_uuid()
    sys_disk_number = get_disk_number(sys_drive_letter)
    
    # Calculate shrink space if not provided
    if not (shrink_space and make_root_partition):
        shrink_space = tmp_part_size + efi_part_size + boot_part_size
    
    # Resize system drive
    sys_drive_new_size = sys_drive_original_size - (shrink_space + 1100000)  # Extra safety margin
    resize_partition(sys_drive_letter, sys_drive_new_size)
    
    # Create partitions as needed
    _create_partitions(
        sys_disk_number, shrink_space, tmp_part_size, efi_part_size, 
        boot_part_size, make_root_partition
    )
    
    # Create temporary partition
    from pathlib import Path
    import tempfile
    
    # Create a temporary directory for mounting
    temp_base = Path(tempfile.gettempdir()) / "BeanieDeploy_TempMount"
    temp_base.mkdir(exist_ok=True)
    tmp_mount_path = str(temp_base / f"temp_part_{temp_part_label}")
    
    # Ensure the mount path is clean
    if os.path.exists(tmp_mount_path):
        subprocess.run(["rmdir", "/s", "/q", tmp_mount_path], 
                      check=True, capture_output=True, shell=True)
    
    # Create the volume without assigning a drive letter initially
    tmp_part_metadata = new_volume_with_metadata(sys_disk_number, tmp_part_size, "FAT32", temp_part_label)
    
    # Get the volume GUID and mount it to the path
    volume_guid = tmp_part_metadata["volume_guid"]
    mount_volume_to_path(volume_guid, tmp_mount_path)
    
    tmp_part = TemporaryPartition(
        mount_path=tmp_mount_path,
        partition_guid=tmp_part_metadata["partition_guid"],
        partition_number=tmp_part_metadata["partition_number"],
        offset=tmp_part_metadata["offset"],
        size=tmp_part_metadata["size"],
        logical_sector_size=tmp_part_metadata["logical_sector_size"],
        start_lba=tmp_part_metadata["start_lba"],
        size_lba=tmp_part_metadata["size_lba"],
    )
    return PartitioningResult(
        tmp_part=tmp_part,
        sys_drive_uuid=sys_drive_uuid,
        sys_drive_win_uuid=sys_drive_win_uuid,
        sys_efi_uuid=sys_efi_uuid,
        shrink_space=shrink_space,
        sys_drive_letter=sys_drive_letter,
        sys_disk_number=sys_disk_number,
        sys_drive_original_size=sys_drive_original_size,
    )


def _extract_uuid_from_string(uuid_string: str) -> str:
    """Extract UUID from a string containing braces."""
    start_idx = uuid_string.index("{") + 1
    end_idx = uuid_string.index("}")
    return uuid_string[start_idx:end_idx]


def _create_partitions(
    sys_disk_number: int,
    shrink_space: int,
    tmp_part_size: int,
    efi_part_size: int,
    boot_part_size: int,
    make_root_partition: bool
) -> None:
    """Create the required partitions based on configuration."""
    if make_root_partition:
        root_space = shrink_space - (tmp_part_size + efi_part_size + boot_part_size + 1100000)
        new_volume(sys_disk_number, root_space, "EXFAT", "ALLOC-ROOT")
    
    if boot_part_size:
        new_volume(sys_disk_number, boot_part_size, "EXFAT", "ALLOC-BOOT")
    
    if efi_part_size:
        new_volume(sys_disk_number, efi_part_size, "EXFAT", "ALLOC-EFI")
