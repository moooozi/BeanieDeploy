"""
Disk and partition management services.
Handles ISO mounting, partition operations, drive management, etc.
"""

import contextlib
import logging
import os
import posixpath
import subprocess
import winreg
from dataclasses import dataclass
from pathlib import Path

from utils import PartitionUuid, com_context

CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW


@dataclass
class PartitionInfo:
    """Structured partition information."""

    partition_guid: str
    partition_number: int
    disk_number: int
    disk_guid: str
    offset: int
    size: int
    logical_sector_size: int
    start_lba: int
    size_lba: int
    disk_partition_style: int
    drive_letter: str | None = None
    free_space: int | None = None
    volume_unique_id: str | None = None


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
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ
        ) as key:
            original_value, _ = winreg.QueryValueEx(key, value_name)
    except FileNotFoundError:
        pass  # Key doesn't exist

    # Set PreventDeviceEncryption to 1
    with winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE
    ) as key:
        winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, 1)

    try:
        yield
    finally:
        # Restore the original value
        if original_value is None:
            # Key didn't exist, delete it
            try:
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE
                ) as key:
                    winreg.DeleteValue(key, value_name)
            except FileNotFoundError:
                pass  # Already gone
        else:
            # Key existed, restore original value
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, original_value)


def resize_partition(guid: str, new_size: int) -> None:
    """
    Resize a partition to a new size using MSFT_Partition.Resize method.

    Args:
        guid: Partition GUID (with or without braces)
        new_size: New size in bytes

    Raises:
        RuntimeError: If resize operation fails or partition not found
    """
    with com_context():
        import win32com.client

        guid = PartitionUuid.to_raw(guid)

        wmi = win32com.client.GetObject("winmgmts:root/Microsoft/Windows/Storage")
        partitions = wmi.InstancesOf("MSFT_Partition")

        for partition in partitions:
            part_guid = PartitionUuid.to_raw(str(partition.Guid))
            if part_guid.lower() == guid.lower():
                # Prepare resize parameters
                in_params = partition.Methods_("Resize").InParameters.SpawnInstance_()
                in_params.Size = new_size

                result = partition.ExecMethod_("Resize", in_params)
                if result.ReturnValue != 0:
                    msg = f"Resize failed with code {result.ReturnValue}: {result.ExtendedStatus}"
                    raise RuntimeError(msg)
                return

        msg = f"No partition found with GUID {guid}"
        raise RuntimeError(msg)


def get_unused_drive_letter() -> str | None:
    """
    Find an unused drive letter starting from G.

    Returns:
        Available drive letter or None if none available
    """
    with com_context():
        import win32com.client

        wmi = win32com.client.GetObject("winmgmts:")
        volumes = wmi.InstancesOf("Win32_Volume")
        used_letters = set()
        for volume in volumes:
            letter = str(volume.DriveLetter).strip()
            if letter:
                used_letters.add(letter.rstrip(":").upper())

        # fmt: off
        drive_letters = ["G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
        # fmt: on

        for letter in drive_letters:
            if letter not in used_letters:
                return letter
        return None


def new_partition(
    disk_number: int,
    size: int,
    filesystem: str | None = None,
    label: str | None = None,
    drive_letter: str | None = None,
    assign_drive_letter: bool = False,
    force_decrypt: bool = True,
) -> PartitionInfo:
    """
    Create a new partition on the specified disk, optionally formatting it as a volume.

    Args:
        disk_number: Disk number to create partition on
        size: Size of the partition in bytes
        filesystem: Optional filesystem type (e.g., 'FAT32', 'NTFS', 'EXFAT'). If provided, the partition will be formatted.
        label: Optional volume label (only used if filesystem is provided)
        drive_letter: Optional drive letter assignment
        assign_drive_letter: Whether to automatically assign a drive letter if none specified (default: False)
        force_decrypt: Whether to attempt decryption on the formatted volume (default: True)

    Returns:
        PartitionInfo object with partition information
    """
    with com_context():
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
            msg = f"Disk {disk_number} not found"
            raise ValueError(msg)

        with prevent_bitlocker_auto_encrypt():
            # Create partition
            in_params = target_disk.Methods_(
                "CreatePartition"
            ).InParameters.SpawnInstance_()
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
                msg = f"CreatePartition failed with code {result}: {out_params.ExtendedStatus}"
                raise RuntimeError(msg)

            partition = out_params.CreatedPartition

            vol_unique_id = None
            if filesystem:
                # Find the associated volume using WMI association
                associated_volumes = partition.Associators_("MSFT_PartitionToVolume")
                if not associated_volumes:
                    msg = "No volume associated with the created partition"
                    raise RuntimeError(msg)

                target_volume = associated_volumes[
                    0
                ]  # Should be exactly one volume per partition

                # Map filesystem
                fs_map = {"FAT32": "FAT32", "NTFS": "NTFS", "EXFAT": "ExFAT"}
                wmi_fs = fs_map.get(filesystem.upper(), filesystem.upper())

                # Format the volume
                in_params_format = target_volume.Methods_(
                    "Format"
                ).InParameters.SpawnInstance_()
                in_params_format.FileSystem = wmi_fs
                in_params_format.FileSystemLabel = label or ""
                in_params_format.Full = False
                in_params_format.Force = True

                out_params_format = target_volume.ExecMethod_(
                    "Format", in_params_format
                )
                result = out_params_format.ReturnValue
                if result != 0:
                    msg = f"Format failed with code {result}: {out_params_format.ExtendedStatus}"
                    raise RuntimeError(msg)

                vol_unique_id = str(target_volume.UniqueId).strip()

        # Attempt to decrypt the volume if requested
        if force_decrypt and vol_unique_id:
            decrypt_partition(vol_unique_id)

        # Return partition metadata as PartitionInfo
        partition_guid = PartitionUuid.to_raw(str(partition.Guid))

        offset = int(partition.Offset)
        part_size = int(partition.Size)
        sector = int(target_disk.LogicalSectorSize)
        if sector <= 0:
            msg = f"Invalid logical sector size: {sector}"
            raise RuntimeError(msg)

        start_lba = offset // sector
        size_lba = part_size // sector

        # For newly created partitions, free_space is initially the full size
        free_space = part_size if filesystem else None

        return PartitionInfo(
            partition_guid=partition_guid,
            partition_number=int(partition.PartitionNumber),
            disk_number=int(target_disk.Number),
            disk_guid=PartitionUuid.to_raw(str(target_disk.Guid)),
            offset=offset,
            size=part_size,
            logical_sector_size=sector,
            start_lba=int(start_lba),
            size_lba=int(size_lba),
            disk_partition_style=int(target_disk.PartitionStyle),
            drive_letter=drive_letter,
            free_space=free_space,
            volume_unique_id=vol_unique_id,
        )


def extract_iso_to_dir(iso_path: str, target_dir: str, filter_func=None) -> str:
    from pycdlib.pycdlib import PyCdlib

    iso = PyCdlib()
    iso.open(iso_path)
    Path(target_dir).mkdir(parents=True, exist_ok=True)

    try:
        for parent, _, files in iso.walk(joliet_path="/"):
            rel_path = parent.lstrip("/")
            local_dir = Path(target_dir) / rel_path

            wrote_any_file = False
            for f in files:
                iso_file_path = posixpath.join(parent, f)
                local_file_path = local_dir / f

                if filter_func and not filter_func(iso_file_path):
                    continue

                # Create the directory only when we actually need to write a file
                if not wrote_any_file:
                    local_dir.mkdir(parents=True, exist_ok=True)
                    wrote_any_file = True

                iso.get_file_from_iso(
                    local_path=str(local_file_path), joliet_path=iso_file_path
                )
    finally:
        iso.close()

    return target_dir


def get_iso_contents_size(iso_path: str, filter_func=None) -> int:
    """
    Get the total size of all files in an ISO image.

    Args:
        iso_path: Path to the ISO file
        filter_func: Optional function to filter which files to include

    Returns:
        Total size in bytes
    """
    from pycdlib.pycdlib import PyCdlib

    iso = PyCdlib()
    iso.open(iso_path)

    total_size = 0
    try:
        for parent, _, files in iso.walk(joliet_path="/"):
            for f in files:
                iso_file_path = posixpath.join(parent, f)

                if filter_func and not filter_func(iso_file_path):
                    continue

                # Get file size from ISO
                file_entry = iso.get_record(joliet_path=iso_file_path)
                total_size += file_entry.get_data_length()
    finally:
        iso.close()

    return total_size


def get_file_size_in_iso(iso_path: str, file_path: str) -> int:
    """
    Get the size of a specific file in an ISO image.

    Args:
        iso_path: Path to the ISO file
        file_path: Path to the file within the ISO (starting with /)

    Returns:
        File size in bytes, or 0 if file not found
    """
    from pycdlib.pycdlib import PyCdlib

    iso = PyCdlib()
    iso.open(iso_path)

    try:
        file_entry = iso.get_record(joliet_path=file_path)
        return file_entry.get_data_length()
    except Exception:
        return 0
    finally:
        iso.close()


def get_efi_drive_uuid() -> str:
    """
    Get the UUID of the system EFI partition.

    First tries to get it from the BootCurrent UEFI boot entry.
    Falls back to finding the first EFI system partition using WMI.

    Returns:
        EFI partition UUID
    """
    # Try firmware_variables approach first
    try:
        from firmware_variables import (
            adjust_privileges,
            get_parsed_boot_entry,
            get_variable,
        )

        with adjust_privileges():
            # Get BootCurrent
            boot_current_data, _ = get_variable("BootCurrent")
            boot_current = int.from_bytes(boot_current_data, byteorder="little")

            # Get the boot entry
            load_option = get_parsed_boot_entry(boot_current)

            # Get hard drive node from device path
            if load_option.file_path_list:
                hard_drive_node = load_option.file_path_list.get_hard_drive_node()
                if hard_drive_node and hard_drive_node.partition_guid:
                    return hard_drive_node.partition_guid

    except Exception:
        # Fall back to WMI approach if firmware_variables fails
        pass

    # Fallback: Find EFI partition using WMI
    with com_context():
        import win32com.client

        # Connect to Storage namespace
        wmi = win32com.client.GetObject("winmgmts:root/Microsoft/Windows/Storage")

        # EFI System Partition GUID
        efi_guid = "{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}"

        # Find partitions with EFI GPT type
        partitions = wmi.InstancesOf("MSFT_Partition")
        for partition in partitions:
            if str(partition.GptType).lower() == efi_guid.lower():
                # Return the partition GUID
                return PartitionUuid.to_raw(str(partition.Guid))

        msg = "EFI partition not found"
        raise ValueError(msg)


def mount_volume_to_path(volume_unique_id: str, mount_path: str) -> None:
    """
    Mount a volume to a specified path instead of a drive letter.

    Args:
        volume_unique_id: Volume unique ID ( \\\\?\\Volume{...}\\)
        mount_path: Path to mount the volume to
    """
    # Unmount if already mounted to avoid conflicts
    with contextlib.suppress(subprocess.CalledProcessError):
        unmount_volume_from_path(mount_path)

    # Ensure the mount path exists
    Path(mount_path).mkdir(parents=True, exist_ok=True)

    # Mount the volume to the path
    subprocess.run(
        ["mountvol", mount_path, volume_unique_id],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
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


def _get_partition_info(partition, wmi) -> PartitionInfo:
    """
    Internal helper to extract partition information from a partition object.

    Args:
        partition: MSFT_Partition object
        wmi: WMI connection object

    Returns:
        PartitionInfo object with partition information
    """
    # Get disk info
    disks = wmi.InstancesOf("MSFT_Disk")
    disk = None
    for d in disks:
        if str(d.Path) == str(partition.DiskId):
            disk = d
            break

    if not disk:
        msg = "Could not find disk for partition"
        raise RuntimeError(msg)

    # Extract drive letter from AccessPaths
    drive_letter = None
    if partition.AccessPaths:
        for path in partition.AccessPaths:
            path_str = str(path)
            # Look for drive letter pattern (e.g., "C:\")
            if len(path_str) >= 3 and path_str[1:3] == ":\\" and path_str[0].isalpha():
                drive_letter = path_str[0].upper()
                break  # Use the first drive letter found

    # Get free space from associated volume
    free_space = None
    volume_unique_id = None
    try:
        # Use MSFT_PartitionToVolume association to get the volume
        associated_volumes = partition.Associators_("MSFT_PartitionToVolume")
        if associated_volumes:
            # Should be exactly one volume per partition
            volume = associated_volumes[0]
            free_space = int(volume.SizeRemaining)
            volume_unique_id = str(volume.UniqueId).strip()
    except Exception:
        # If free space query fails, leave it as None
        msg = f"MSFT_PartitionToVolume association failed for {partition.Guid}"
        logging.warning(msg)

    # Compute LBAs
    offset = int(partition.Offset)
    part_size = int(partition.Size)
    sector = int(disk.LogicalSectorSize)
    start_lba = offset // sector
    size_lba = part_size // sector

    return PartitionInfo(
        partition_guid=PartitionUuid.to_raw(str(partition.Guid)),
        partition_number=int(partition.PartitionNumber),
        disk_number=int(disk.Number),
        disk_guid=PartitionUuid.to_raw(str(disk.Guid)),
        offset=offset,
        size=part_size,
        logical_sector_size=sector,
        start_lba=int(start_lba),
        size_lba=int(size_lba),
        disk_partition_style=int(disk.PartitionStyle),
        drive_letter=drive_letter,
        free_space=free_space,
        volume_unique_id=volume_unique_id,
    )


def get_windows_partition_info() -> PartitionInfo:
    """Get cached Windows system partition info.

    Returns:
        PartitionInfo object for the Windows system partition
    """
    system_drive = os.environ.get("SYSTEMDRIVE", "C:")[0]
    return get_partition_info_by_drive_letter(system_drive)


def get_efi_partition_info() -> PartitionInfo:
    """Get cached EFI system partition info.

    Returns:
        PartitionInfo object for the EFI system partition
    """
    efi_guid = get_efi_drive_uuid()
    return get_partition_info_by_guid(efi_guid)


def get_partition_info_by_guid(guid: str) -> PartitionInfo:
    """
    Get partition information by GUID (partition GUID) using pure WMI.

    Uses MSFT_Partition.Guid to find the partition by its unique GUID.

    Args:
        guid: Partition GUID (with or without braces)

    Returns:
        PartitionInfo object with partition information
    """
    with com_context():
        import win32com.client

        # Normalize GUID format - remove braces if present
        guid = PartitionUuid.to_raw(guid)

        # Connect to Storage namespace
        wmi = win32com.client.GetObject("winmgmts:root/Microsoft/Windows/Storage")

        # Find partition by unique GUID
        partitions = wmi.InstancesOf("MSFT_Partition")
        target_partition = None
        for partition in partitions:
            part_guid = PartitionUuid.to_raw(str(partition.Guid))
            if part_guid.lower() == guid.lower():
                target_partition = partition
                break

        if not target_partition:
            msg = f"No partition found with GUID {guid}"
            raise RuntimeError(msg)

        return _get_partition_info(target_partition, wmi)


def get_partition_info_by_drive_letter(drive_letter: str) -> PartitionInfo:
    """
    Get partition information by drive letter using pure WMI.

    Args:
        drive_letter: Drive letter (e.g., 'C')

    Returns:
        PartitionInfo object with partition information
    """
    with com_context():
        import win32com.client

        # Connect to Storage namespace
        wmi = win32com.client.GetObject("winmgmts:root/Microsoft/Windows/Storage")

        # Find partition by drive letter
        partitions = wmi.InstancesOf("MSFT_Partition")
        target_partition = None
        drive_path = drive_letter.upper() + ":\\"
        for partition in partitions:
            if partition.AccessPaths and drive_path in partition.AccessPaths:
                target_partition = partition
                break

        if not target_partition:
            msg = f"No partition found for drive letter {drive_letter}"
            raise RuntimeError(msg)

        return _get_partition_info(target_partition, wmi)


def get_partition_supported_size(guid: str) -> int:
    """
    Get the supported resizable size for a partition by GUID.

    Args:
        guid: Partition GUID (with or without braces)

    Returns:
        Resizable size in bytes (current size - minimum supported size)
    """
    with com_context():
        import win32com.client

        wmi = win32com.client.GetObject(r"winmgmts:root\Microsoft\Windows\Storage")
        partitions = wmi.InstancesOf("MSFT_Partition")

        for partition in partitions:
            part_guid = PartitionUuid.to_raw(str(partition.Guid))
            if part_guid.lower() == guid.lower():
                method_result = wmi.ExecMethod(partition.Path_.Path, "GetSupportedSize")
                if method_result.ReturnValue == 0:
                    size_min = int(method_result.SizeMin)
                    current_size = int(partition.Size)
                    return current_size - size_min
                msg = f"GetSupportedSize failed with code {method_result.ReturnValue}"
                raise RuntimeError(msg)

        msg = f"Partition with GUID {guid} not found"
        raise ValueError(msg)


def delete_partition(guid: str) -> None:
    """
    Delete a partition by its GUID.

    Args:
        guid: Partition GUID (with or without braces)

    Raises:
        RuntimeError: If no partition is found with the given GUID
    """
    with com_context():
        import win32com.client

        guid = PartitionUuid.to_raw(guid)

        wmi = win32com.client.GetObject("winmgmts:root/Microsoft/Windows/Storage")
        partitions = wmi.InstancesOf("MSFT_Partition")
        found = False
        for partition in partitions:
            part_guid = PartitionUuid.to_raw(str(partition.Guid))
            if part_guid.lower() == guid.lower():
                result = partition.ExecMethod_("DeleteObject")
                if result.ReturnValue != 0:
                    msg = f"DeleteObject failed with code {result.ReturnValue}"
                    raise RuntimeError(msg)
                found = True
                break

        if not found:
            msg = f"No partition found with GUID {guid}"
            raise RuntimeError(msg)


def _decrypt_partition(volume_unique_id: str) -> None:
    r"""
    Begin decryption of a fully encrypted volume or resume decryption of a partially encrypted volume.

    Args:
        volume_unique_id: Volume unique ID (e.g., \\?\Volume{guid}\)

    Raises:
        ValueError: If encryptable volume not found
        RuntimeError: If the Decrypt operation fails
    """
    volume_id = volume_unique_id

    with com_context():
        import win32com.client

        wmi = win32com.client.GetObject(
            "winmgmts:root/cimv2/Security/MicrosoftVolumeEncryption"
        )
        volumes = wmi.InstancesOf("Win32_EncryptableVolume")

        for vol in volumes:
            if vol.DeviceID == volume_id:
                # Clear auto-unlock keys if present
                clear_result = vol.ExecMethod_("ClearAllAutoUnlockKeys")
                if clear_result.ReturnValue != 0:
                    msg = f"ClearAllAutoUnlockKeys failed with code {clear_result.ReturnValue}"
                    logging.warning(msg)

                # Disable key protectors
                disable_result = vol.ExecMethod_("DisableKeyProtectors")
                if disable_result.ReturnValue != 0:
                    msg = f"DisableKeyProtectors failed with code {disable_result.ReturnValue}"
                    logging.warning(msg)

                # Then, initiate decryption
                result = vol.ExecMethod_("Decrypt")
                if result.ReturnValue != 0:
                    msg = f"Decrypt failed with code {result.ReturnValue}"
                    logging.error(msg)
                    raise RuntimeError(msg)
                return

        msg = "Encryptable volume not found"
        logging.error(msg)
        raise ValueError(msg)


def decrypt_partition(volume_unique_id: str) -> bool:
    r"""
    Attempt to decrypt a BitLocker volume, suppressing errors.

    Args:
        volume_unique_id: Volume unique ID (e.g., \\?\Volume{guid}\)

    Returns:
        True if decryption was initiated successfully, False otherwise.
    """
    try:
        _decrypt_partition(volume_unique_id)
        return True
    except Exception:
        return False
