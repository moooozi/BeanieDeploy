"""
Partition management operations.
Handles complex partitioning procedures and disk operations.
"""
from dataclasses import dataclass
from typing import Optional

from .disk import (
    PartitionInfo, get_efi_partition_info, get_windows_partition_info,
    resize_partition, new_partition, mount_volume_to_path
)
import os
import subprocess


@dataclass
class TemporaryPartition:
    """Temporary partition information."""
    mount_path: str
    partition_info: PartitionInfo
    

@dataclass
class PartitionGuids:
    """GUIDs of created partitions."""
    root_guid: Optional[str] = None
    boot_guid: Optional[str] = None
    

@dataclass
class PartitioningResult:
    """Result of partitioning procedure."""
    tmp_part: TemporaryPartition
    windows_partition: PartitionInfo
    efi_partition: PartitionInfo
    shrink_space: int
    sys_drive_original_size: int
    partition_guids: PartitionGuids


def partition_procedure(
    tmp_part_size: int,
    temp_part_label: str,
    shrink_space: int = 0,
    boot_part_size: int = 0,
    make_root_partition: bool = False,
) -> PartitioningResult:
    """
    Execute the complete partitioning procedure.
    
    Args:
        tmp_part_size: Size of temporary partition in bytes
        temp_part_label: Label for temporary partition
        shrink_space: Amount of space to shrink from system drive
        boot_part_size: Size of boot partition in bytes
        make_root_partition: Whether to create a root partition
        
    Returns:
        PartitioningResult with partition information
    """

    
    # Store original system drive size for potential rollback
    windows_partition = get_windows_partition_info()
    efi_partition = get_efi_partition_info()
    sys_drive_original_size = windows_partition.size
    if windows_partition.drive_letter is None:
        raise RuntimeError("System drive letter could not be determined.")
    # Calculate shrink space if not provided
    if not (shrink_space and make_root_partition):
        shrink_space = tmp_part_size + boot_part_size
    
    # Resize system drive
    sys_drive_new_size = sys_drive_original_size - (shrink_space + 1100000)  # Extra safety margin
    resize_partition(windows_partition.partition_guid, sys_drive_new_size)
    
    # Create partitions as needed
    partition_guids = _create_partitions(
        windows_partition.disk_number, shrink_space, tmp_part_size, 
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
    tmp_part_metadata = new_partition(windows_partition.disk_number, tmp_part_size, "FAT32", temp_part_label)
    
    # Get the volume GUID and mount it to the path
    volume_unique_id = tmp_part_metadata.volume_unique_id
    if volume_unique_id is None:
        raise RuntimeError("Temporary partition volume unique ID could not be determined.")
    mount_volume_to_path(volume_unique_id, tmp_mount_path)
    
    tmp_part = TemporaryPartition(
        mount_path=tmp_mount_path,
        partition_info = tmp_part_metadata,
    )
    return PartitioningResult(
        tmp_part=tmp_part,
        windows_partition = windows_partition,
        efi_partition = efi_partition,
        sys_drive_original_size=sys_drive_original_size,
        shrink_space=shrink_space,
        partition_guids=partition_guids,
    )


def _create_partitions(
    sys_disk_number: int,
    shrink_space: int,
    tmp_part_size: int,
    boot_part_size: int,
    make_root_partition: bool
) -> PartitionGuids:
    """Create the required partitions based on configuration.
    
    Returns:
        PartitionGuids with GUIDs for created partitions
    """
    partition_guids = PartitionGuids()
    
    if make_root_partition:
        root_space = shrink_space - (tmp_part_size + boot_part_size + 1100000)
        metadata = new_partition(sys_disk_number, root_space)
        partition_guids.root_guid = metadata.partition_guid
    
    if boot_part_size:
        metadata = new_partition(sys_disk_number, boot_part_size)
        partition_guids.boot_guid = metadata.partition_guid
    
    return partition_guids
