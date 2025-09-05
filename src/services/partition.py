"""
Partition management operations.
Handles complex partitioning procedures and disk operations.
"""
from dataclasses import dataclass

from services.disk import (
    get_sys_drive_letter, get_disk_number, get_drive_size_after_resize, new_volume_with_metadata,
    resize_partition, new_volume, get_unused_drive_letter, get_system_efi_drive_uuid
)
from services.system import run_powershell_script


@dataclass
class TemporaryPartition:
    """Temporary partition information."""
    letter: str
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
    sys_uuid_script = f"(Get-Volume -DriveLetter {sys_drive_letter}).UniqueId"
    sys_drive_win_uuid = run_powershell_script(sys_uuid_script)
    sys_drive_uuid = _extract_uuid_from_string(sys_drive_win_uuid)
    
    # Get EFI and disk information
    sys_efi_uuid = get_system_efi_drive_uuid()
    sys_disk_number = get_disk_number(sys_drive_letter)
    
    # Calculate shrink space if not provided
    if not (shrink_space and make_root_partition):
        shrink_space = tmp_part_size + efi_part_size + boot_part_size
    
    # Resize system drive
    sys_drive_new_size = get_drive_size_after_resize(
        sys_drive_letter, shrink_space + 1100000  # Extra safety margin
    )
    resize_partition(sys_drive_letter, sys_drive_new_size)
    
    # Create partitions as needed
    _create_partitions(
        sys_disk_number, shrink_space, tmp_part_size, efi_part_size, 
        boot_part_size, make_root_partition
    )
    
    # Create temporary partition
    tmp_part_letter = get_unused_drive_letter()
    if tmp_part_letter is None:
        raise RuntimeError("No available drive letters for temporary partition")
    
    tmp_part = new_volume_with_metadata(sys_disk_number, tmp_part_size, "FAT32", temp_part_label, tmp_part_letter)
        
    tmp_part = TemporaryPartition(
            letter=tmp_part_letter,
            partition_guid=tmp_part["partition_guid"],
            partition_number=tmp_part["partition_number"],
            offset=tmp_part["offset"],
            size=tmp_part["size"],
            logical_sector_size=tmp_part["logical_sector_size"],
            start_lba=tmp_part["start_lba"],
            size_lba=tmp_part["size_lba"],
        )
    return PartitioningResult(
        tmp_part=tmp_part,
        sys_drive_uuid=sys_drive_uuid,
        sys_drive_win_uuid=sys_drive_win_uuid,
        sys_efi_uuid=sys_efi_uuid,
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
