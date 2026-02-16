"""
Partition management operations.
Handles complex partitioning procedures and disk operations.
"""

import subprocess
from dataclasses import dataclass

from models.partition import Partition

from .disk import (
    PartitionInfo,
    get_efi_partition_info,
    get_windows_partition_info,
    mount_volume_to_path,
    new_partition,
    resize_partition,
)


@dataclass
class TemporaryPartition:
    """Temporary partition information."""

    mount_path: str
    partition_info: PartitionInfo


@dataclass
class PartitionGuids:
    """GUIDs of created partitions."""

    root_guid: str | None = None
    boot_guid: str | None = None


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
    partition: Partition,
) -> PartitioningResult:
    """
    Execute the complete partitioning procedure.

    Args:
        partition: Partition configuration object
    Returns:
        PartitioningResult with partition information
    """

    # Store original system drive size for potential rollback
    windows_partition = get_windows_partition_info()
    efi_partition = get_efi_partition_info()
    sys_drive_original_size = windows_partition.size
    if windows_partition.drive_letter is None:
        msg = "System drive letter could not be determined."
        raise RuntimeError(msg)
    # Calculate shrink space if not provided
    if not (partition.shrink_space and partition.make_root_partition):
        partition.shrink_space = partition.tmp_part_size + partition.boot_part_size

    # Resize system drive
    sys_drive_new_size = sys_drive_original_size - (
        partition.shrink_space + 1100000
    )  # Extra safety margin
    resize_partition(windows_partition.partition_guid, sys_drive_new_size)

    # Create partitions as needed
    partition_guids = _create_partitions(
        windows_partition.disk_number,
        partition.shrink_space,
        partition.tmp_part_size,
        partition.boot_part_size,
        partition.make_root_partition,
    )

    # Create temporary partition
    import tempfile
    from pathlib import Path

    # Create a temporary directory for mounting
    temp_base = Path(tempfile.gettempdir()) / "BeanieDeploy_TempMount"
    temp_base.mkdir(exist_ok=True)
    tmp_mount_path = str(temp_base / f"temp_part_{partition.temp_part_label}")

    # Ensure the mount path is clean
    if Path(tmp_mount_path).exists():
        subprocess.run(
            ["rmdir", "/s", "/q", tmp_mount_path],
            capture_output=True,
            shell=True,
        )

    # Create the volume without assigning a drive letter initially
    tmp_part_metadata = new_partition(
        windows_partition.disk_number,
        partition.tmp_part_size,
        "FAT32",
        partition.temp_part_label,
    )

    # Get the volume GUID and mount it to the path
    volume_unique_id = tmp_part_metadata.volume_unique_id
    if volume_unique_id is None:
        msg = "Temporary partition volume unique ID could not be determined."
        raise RuntimeError(msg)
    mount_volume_to_path(volume_unique_id, tmp_mount_path)

    tmp_part = TemporaryPartition(
        mount_path=tmp_mount_path,
        partition_info=tmp_part_metadata,
    )
    return PartitioningResult(
        tmp_part=tmp_part,
        windows_partition=windows_partition,
        efi_partition=efi_partition,
        sys_drive_original_size=sys_drive_original_size,
        shrink_space=partition.shrink_space,
        partition_guids=partition_guids,
    )


def _create_partitions(
    sys_disk_number: int,
    shrink_space: int,
    tmp_part_size: int,
    boot_part_size: int,
    make_root_partition: bool,
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
