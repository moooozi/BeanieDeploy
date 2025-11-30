import ctypes
import logging
import platform

import win32com.client

from core.state import get_state
from models.check import Check, CheckType
from services.disk import get_partition_supported_size
from services.privilege_manager import elevated
from utils import com_context


def check_arch():
    result = platform.machine().lower()

    return Check(
        CheckType.ARCH.value,
        result,
        0,  # Success return code
        None,  # No subprocess used
    )


def check_uefi():
    try:
        # Load kernel32.dll
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        get_fw_type = kernel32.GetFirmwareType
        get_fw_type.argtypes = [ctypes.POINTER(ctypes.c_uint)]
        get_fw_type.restype = ctypes.c_bool

        fw_type = ctypes.c_uint()
        success = get_fw_type(ctypes.byref(fw_type))

        if not success:
            raise ctypes.WinError(ctypes.get_last_error())

        if fw_type.value == 2:  # UEFI
            proc = True
        elif fw_type.value == 1:  # BIOS
            proc = False
        else:
            proc = None

    except Exception as e:
        msg = "Error determining firmware type: " + str(e)
        logging.exception(msg)
        proc = None

    return Check(
        CheckType.UEFI.value,
        proc,
        0 if proc is not None else 1,  # Success or error return code
        None,  # No subprocess used
    )


def check_ram():
    # Use WMI instead of PowerShell
    try:
        with com_context():
            wmi = win32com.client.GetObject("winmgmts:")
            memories = wmi.InstancesOf("Win32_PhysicalMemory")
            total_capacity = 0
            for memory in memories:
                total_capacity += int(memory.Capacity)
            logging.info(f"RAM capacity: {total_capacity} bytes")
            return Check(
                CheckType.RAM.value,
                total_capacity,
                0,  # Success
                None,
            )
    except Exception as e:
        logging.exception("Error checking RAM: " + str(e))
        return Check(
            CheckType.RAM.value,
            str(e),
            1,  # Error
            None,
        )


def check_space():
    # Use shutil.disk_usage instead of PowerShell
    try:
        # Get the system drive info
        partition_info = get_state().installation.windows_partition_info
        if partition_info.free_space is not None:
            return Check(
                CheckType.SPACE.value,
                partition_info.free_space,
                0,
                None,
            )
        # If free_space is not available, return error
        return Check(
            CheckType.SPACE.value,
            "Free space information not available",
            1,
            None,
        )
    except Exception as e:
        return Check(
            CheckType.SPACE.value,
            str(e) + " | Fallback error: " + str(e),
            1,
            None,
        )


def check_resizable():
    """Check available resizable space on system drive."""
    try:
        partition_info = get_state().installation.windows_partition_info

        # Extract GUID
        partition_guid = partition_info.partition_guid

        # Get supported resizable size
        resizable_size = elevated.call(
            get_partition_supported_size, args=(partition_guid,)
        )

        return Check(
            CheckType.RESIZABLE.value,
            resizable_size,
            0,
            None,
        )
    except Exception as e:
        return Check(
            CheckType.RESIZABLE.value,
            str(e),
            1,
            None,
        )


def _get_efi_free_space() -> int:
    """Get free space on EFI partition."""
    efi_partition_info = get_state().installation.efi_partition_info
    if efi_partition_info.free_space is None:
        msg = "EFI partition free space information not available"
        raise ValueError(msg)
    return efi_partition_info.free_space


def check_efi_space():
    """Check available free space on the EFI partition."""
    result_value = _get_efi_free_space()
    return Check(
        CheckType.EFI_SPACE.value,
        result_value,
        0,
        None,
    )


check_functions = {
    CheckType.ARCH: check_arch,
    CheckType.UEFI: check_uefi,
    CheckType.RAM: check_ram,
    CheckType.SPACE: check_space,
    CheckType.RESIZABLE: check_resizable,
    CheckType.EFI_SPACE: check_efi_space,
}
