"""
Partition management operations.
Handles complex partitioning procedures and disk operations.
"""

import logging
from dataclasses import dataclass

from models.partition import PartitioningOptions

from .disk import (
    Partition,
    delete_partition,
    get_efi_partition,
    get_windows_partition,
    new_partition,
    resize_partition,
)


@dataclass
class PartitionGuids:
    """GUIDs of created partitions."""

    root_guid: str | None = None
    boot_guid: str | None = None


@dataclass
class PartitioningResult:
    """Result of partitioning procedure."""

    tmp_part: Partition
    windows_partition: Partition
    efi_partition: Partition
    shrink_space: int
    sys_drive_original_size: int
    partition_guids: PartitionGuids


def partition_procedure(
    options: PartitioningOptions,
) -> PartitioningResult:
    """
    Execute the complete partitioning procedure.

    Creates all required partitions (root, boot, temp) after shrinking the
    system drive.  If any step after the initial resize fails, all
    already-created partitions are deleted and the system drive is restored
    to its original size before the error is re-raised.

    Args:
        options: Partitioning options

    Returns:
        PartitioningResult with partition information

    Raises:
        RuntimeError: If any partitioning step fails (after rollback).
    """

    # --- gather baseline info ---
    windows_partition = get_windows_partition()
    efi_partition = get_efi_partition()
    sys_drive_original_size = windows_partition.size

    if windows_partition.drive_letter is None:
        msg = "System drive letter could not be determined."
        raise RuntimeError(msg)

    # Calculate shrink space if not provided
    if not (options.shrink_space and options.make_root_partition):
        options.shrink_space = options.tmp_part_size + options.boot_part_size

    # --- resize system drive ---
    sys_drive_new_size = sys_drive_original_size - (
        options.shrink_space + 1100000
    )  # Extra safety margin
    resize_partition(windows_partition.partition_guid, sys_drive_new_size)

    # --- create partitions with rollback on failure ---
    created_guids: list[str] = []
    try:
        partition_guids = _create_partitions(
            windows_partition.disk_number,
            options.shrink_space,
            options.tmp_part_size,
            options.boot_part_size,
            options.make_root_partition,
            created_guids,
        )

        # Create the temporary partition (no mounting - caller is responsible)
        tmp_part = new_partition(
            windows_partition.disk_number,
            options.tmp_part_size,
            "FAT32",
            options.temp_part_label,
        )
        created_guids.append(tmp_part.partition_guid)

        if tmp_part.volume_unique_id is None:
            msg = "Temporary partition volume unique ID could not be determined."
            raise RuntimeError(msg)

    except Exception as exc:
        try:
            _rollback_partitions(
                created_guids,
                windows_partition.partition_guid,
                sys_drive_original_size,
            )
        except RuntimeError as rollback_exc:
            raise rollback_exc from exc
        raise

    return PartitioningResult(
        tmp_part=tmp_part,
        windows_partition=windows_partition,
        efi_partition=efi_partition,
        sys_drive_original_size=sys_drive_original_size,
        shrink_space=options.shrink_space,
        partition_guids=partition_guids,
    )


def _rollback_partitions(
    created_guids: list[str],
    sys_partition_guid: str,
    original_size: int,
) -> None:
    """Delete all created partitions and restore the system drive size.

    Best-effort: individual failures are logged and collected.  If any
    rollback step fails, a RuntimeError summarising all failures is raised
    *after* every step has been attempted, so the caller can surface the
    information alongside the original error.
    """
    failures: list[str] = []

    for guid in reversed(created_guids):
        try:
            delete_partition(guid)
        except Exception:
            msg = f"failed to delete partition {guid}"
            logging.warning("Rollback: %s", msg)
            failures.append(msg)

    try:
        resize_partition(sys_partition_guid, original_size)
    except Exception:
        msg = f"failed to restore system partition to {original_size} bytes"
        logging.error("Rollback: %s", msg)
        failures.append(msg)

    if failures:
        detail = "; ".join(failures)
        msg = f"Rollback completed with errors: {detail}"
        raise RuntimeError(msg)


def _create_partitions(
    sys_disk_number: int,
    shrink_space: int,
    tmp_part_size: int,
    boot_part_size: int,
    make_root_partition: bool,
    created_guids: list[str],
) -> PartitionGuids:
    """Create the required partitions based on configuration.

    Each successfully created partition's GUID is appended to *created_guids*
    so the caller can roll them back on failure.

    Returns:
        PartitionGuids with GUIDs for created partitions
    """
    partition_guids = PartitionGuids()

    if make_root_partition:
        root_space = shrink_space - (tmp_part_size + boot_part_size + 1100000)
        metadata = new_partition(sys_disk_number, root_space)
        partition_guids.root_guid = metadata.partition_guid
        created_guids.append(metadata.partition_guid)

    if boot_part_size:
        metadata = new_partition(sys_disk_number, boot_part_size)
        partition_guids.boot_guid = metadata.partition_guid
        created_guids.append(metadata.partition_guid)

    return partition_guids
