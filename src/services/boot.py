"""
Boot management services.
Handles EFI boot entries, boot order management, etc.
"""
import re
import subprocess
from typing import List, Dict
from config.settings import get_config


class BootManagerError(Exception):
    """Exception raised for boot manager operation errors."""
    pass


def create_boot_entry(name: str, path: str, duplicate_of: str) -> str:
    """
    Create a boot entry by duplicating an existing one.

    Args:
        name: The name of the boot entry
        path: The path to the boot entry
        duplicate_of: The identifier of an existing boot entry to duplicate

    Returns:
        The new boot entry identifier

    Raises:
        ValueError: If arguments are invalid
        RuntimeError: If boot entry creation fails
    """
    if not all([name, path, duplicate_of]):
        raise ValueError("One or more arguments are missing")
    
    # Validate duplicate_of format (4 hexadecimal digits)
    if not re.match(r"^[0-9A-Fa-f]{4}$", duplicate_of):
        raise ValueError("Invalid duplicate_of argument")

    bootmgr_helper = str(get_config().paths.bootmgr_helper_relative)
    result = subprocess.run(
        [bootmgr_helper, "-c", f"Boot{duplicate_of}", name, path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    
    print(result.stdout)
    
    # Extract new boot entry ID from output
    match = re.search(
        r"Successfully duplicated Boot[0-9A-Fa-f]{4} to Boot([0-9A-Fa-f]{4}) with",
        result.stdout,
    )

    if match:
        return match.group(1)
    else:
        raise RuntimeError("Failed to extract new boot entry identifier from output")


def set_bootnext(entry_id: str) -> None:
    """
    Set the next boot entry.

    Args:
        entry_id: The identifier of the boot entry to set as next boot

    Raises:
        ValueError: If entry_id format is invalid
        RuntimeError: If setting bootnext fails
    """
    # Validate entry_id format (4 hexadecimal digits)
    if not re.match(r"^[0-9A-Fa-f]{4}$", entry_id):
        raise ValueError("Invalid entry_id argument")

    bootmgr_helper = str(get_config().paths.bootmgr_helper_relative)
    result = subprocess.run(
        [bootmgr_helper, "-N", f"{entry_id}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )

    # Check if command was successful
    if f": set to {entry_id.lower()}" not in result.stdout.lower():
        raise RuntimeError("Failed to set bootnext value")


def get_boot_current() -> str:
    """
    Get the current boot entry identifier.

    Returns:
        The identifier of the current boot entry

    Raises:
        RuntimeError: If current boot entry cannot be determined
    """
    bootmgr_helper = str(get_config().paths.bootmgr_helper_relative)
    result = subprocess.run(
        [bootmgr_helper, "-c"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    
    # Parse output to extract boot current ID
    match = re.search(r"BootCurrent\s+:\s+([0-9A-Fa-f]{4})\s+\(hex\)", result.stdout)

    if match:
        return match.group(1)
    else:
        raise RuntimeError("Failed to extract current boot entry identifier from output")


def get_boot_entries() -> List[Dict[str, str]]:
    """
    Get the list of all boot entries.

    Returns:
        List of dictionaries containing boot entry information

    Raises:
        RuntimeError: If boot entries cannot be retrieved
    """
    bootmgr_helper = str(get_config().paths.bootmgr_helper_relative)
    result = subprocess.run(
        [bootmgr_helper, "-B"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )

    boot_entries = []
    entry_pattern = re.compile(r"^(Boot[0-9A-Fa-f]{4})\[\*\]\s+:\s+(.+)$", re.MULTILINE)
    matches = entry_pattern.findall(result.stdout)

    if not matches:
        raise RuntimeError(f"Error retrieving boot entries: {result.stdout}")

    for match in matches:
        entry_id, description = match
        boot_entries.append({"entry_id": entry_id, "description": description})

    return boot_entries


# TODO: These functions are referenced but not implemented yet
# They seem to be related to Windows Boot Manager operations
def create_new_wbm(boot_efi_file_path: str, device_path: str) -> str:
    """
    Create a new Windows Boot Manager entry.
    
    Args:
        boot_efi_file_path: Path to the EFI boot file
        device_path: Device path for the entry
        
    Returns:
        Boot GUID of the created entry
        
    Note:
        This function needs to be implemented based on the specific 
        Windows Boot Manager operations required.
    """
    # This is a placeholder - needs actual implementation
    raise NotImplementedError("create_new_wbm function needs to be implemented")


def make_boot_entry_first(boot_guid: str, is_permanent: bool = False) -> None:
    """
    Make a boot entry the first in the boot order.
    
    Args:
        boot_guid: GUID of the boot entry
        is_permanent: Whether to make the change permanent
        
    Note:
        This function needs to be implemented based on the specific
        Windows Boot Manager operations required.
    """
    # This is a placeholder - needs actual implementation
    raise NotImplementedError("make_boot_entry_first function needs to be implemented")


def add_boot_entry(boot_efi_file_path: str, device_path: str, is_permanent: bool = False) -> None:
    """
    Add a new boot entry to the Windows Boot Manager.
    
    Args:
        boot_efi_file_path: Path to the EFI boot file
        device_path: Device path for the boot entry
        is_permanent: Whether to make the boot entry permanent
        
    Raises:
        BootManagerError: If boot entry creation fails
    """
    try:
        bootguid = create_new_wbm(boot_efi_file_path, device_path)
        make_boot_entry_first(bootguid, is_permanent)
        
    except Exception as e:
        raise BootManagerError(f"Failed to add boot entry: {e}") from e
