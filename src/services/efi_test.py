from ctypes import WinError
from math import e, radians
import os
import sys
import uuid
import firmware_variables as fwvars
import time
import subprocess
import json


def _setup_sys_path():
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))


def set_stuff():
    print("Create a new entry")
    new_entry = fwvars.get_parsed_boot_entry(8)
    new_entry.description = "Fedora Installer"
    for path in new_entry.file_path_list.paths:
        if path.is_hard_drive():
            hd_node = path.get_hard_drive_node()
            if not hd_node: continue
            """
            hd_node.partition_guid = "AC27B345-EC75-4731-A73C-97EDAE7CB6DE".lower()
            hd_node.partition_number = 4
            hd_node.partition_start_lba = 200478720
            hd_node.partition_size_lba = 7643136
            hd_node.partition_signature = uuid.UUID(hd_node.partition_guid).bytes_le
            path.set_hard_drive_node(hd_node)
            """
        elif path.is_file_path():
            path.set_file_path("\\EFI\\FedoraRecovery\\BOOTX64.EFI")
        else: continue
    # Delete the optional data bytes from the entry
    #new_entry.optional_data = b''
    # Find an unused entry_id for the new entry
    new_entry_id = None
    for i in range(50):
        try:
            fwvars.get_boot_entry(i)
        except OSError:
            new_entry_id = i
            break
    new_entry_id = 16
    fwvars.set_parsed_boot_entry(new_entry_id, new_entry)
    print(f"New entry created with ID {new_entry_id}")
    print(fwvars.get_parsed_boot_entry(new_entry_id).description)
    print("Set as BootNext")
    fwvars.set_boot_next(new_entry_id)
    print("Add to the boot order as second option")
    boot_order = [8]
    boot_order.insert(1, new_entry_id)
    fwvars.set_boot_order(boot_order)
    print(f"BootOrder updated: {fwvars.get_boot_order()}")

    

if __name__ == "__main__":
    _setup_sys_path()
    from services.system import get_admin
    get_admin()
    with fwvars.adjust_privileges():
        set_stuff()
        windows_entry = None
        #fwvars.set_boot_order([8])
        print("Current Boot Order:", fwvars.get_boot_order())
        entries = {i: fwvars.get_parsed_boot_entry(i).description for i in fwvars.get_boot_order()}
        for index, entry_desc in entries.items():
            if "fedora" in entry_desc.lower() and index != 14:
                pass
                #fwvars.set_boot_entry(index, b'')
        entries = fwvars.get_boot_order()
        bootnext = fwvars.get_boot_next()
        #fwvars.set_boot_next(8)
        print("BootNext:", bootnext)
        for entry in entries:
            print(f"Boot Entry ID: {entry}")
            if not fwvars.get_parsed_boot_entry(entry).file_path_list.get_hard_drive_node():
                pass
            entry = fwvars.get_parsed_boot_entry(entry)
            print(f"Entry Description: {entry.description}")
            print(f"Boot Entry: {entry}")
            print("  File Path List:")
            for path in entry.file_path_list.paths:
                print("    -", path)
            print("    - File Path:", entry.file_path_list.get_file_path())
            hard_drive_node = entry.file_path_list.get_hard_drive_node()
            if hard_drive_node is not None:
                print("  Hard Drive Node:")
                print("    - Partition Number:", hard_drive_node.partition_number)
                print("    - Partition Start:", hard_drive_node.partition_start_lba)
                print("    - Partition Size:", hard_drive_node.partition_size_lba)
                print("    - Partition Signature:", hard_drive_node.partition_signature.hex())
                print("    - Partition GUID:", hard_drive_node.partition_guid)
                print("    - Partition Format:", hard_drive_node.partition_format)
                print("    - Signature Type:", hard_drive_node.signature_type)
            print("  Attributes:", entry.attributes)
            print("  Optional Data:", entry.optional_data)
        print("Setting a boot entry from Windows' entry")
        # Create dict of entry_id -> description
        entries = {i: fwvars.get_parsed_boot_entry(i).description for i in fwvars.get_boot_order()}
        for index, entry_desc in entries.items():
            if "windows boot manager" in entry_desc.lower():
                print(f"Found Windows Boot Manager at index {index}")
                windows_entry = index
                break
        raise SystemExit


def get_partition_guids():
    cmd = [
        "powershell",
        "-Command",
        """
        Get-Partition | ForEach-Object {
            $part = $_
            $vol = Get-Volume -Partition $part -ErrorAction SilentlyContinue
            [PSCustomObject]@{
                DiskNumber = $part.DiskNumber
                PartitionNumber = $part.PartitionNumber
                GptType = $part.GptType
                Guid = $part.Guid
                Label = if ($vol) { $vol.FileSystemLabel } else { $null }
            }
        } | ConvertTo-Json
        """
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    partitions = json.loads(result.stdout)
    for part in partitions:
        print(f"Disk: {part['DiskNumber']}, Label: {part['Label']}, Partition: {part['PartitionNumber']}, GUID: {part.get('Guid', 'N/A')}, GPT Type: {part.get('GptType', 'N/A')}")

#get_partition_guids()

# Get the lba of GUID AC27B345-EC75-4731-A73C-97EDAE7CB6DE


hex_bytes = bytes.fromhex("90a42b9d95684b46bed4ea9244a676af")
guid = uuid.UUID(bytes_le=hex_bytes)
print(str(guid))  # Output: 9d2ba490-6895-464b-bed4-ea9244a676af
# input("Press Enter to exit...")

def get_partition_lba_by_guid(target_guid):
    # First, get partition info including disk number, offset, and size
    cmd = [
        "powershell",
        "-Command",
        f"""
        $part = Get-Partition | Where-Object {{$_.Guid -eq '{target_guid}'}}
        if ($part) {{
            $disk = Get-Disk -Number $part.DiskNumber
            [PSCustomObject]@{{
                DiskNumber = $part.DiskNumber
                PartitionNumber = $part.PartitionNumber
                Guid = $part.Guid
                Offset = $part.Offset
                Size = $part.Size
                LogicalSectorSize = $disk.LogicalSectorSize
            }} | ConvertTo-Json
        }}
        """
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if not result.stdout.strip():
        print(f"No partition found with GUID {target_guid}")
        return
    part = json.loads(result.stdout)
    sector_size = part.get("LogicalSectorSize", 512)  # Fallback to 512 if not found
    offset = part["Offset"]
    size = part["Size"]
    start_lba = offset // sector_size
    size_lba = size // sector_size
    print(f"Partition GUID: {part['Guid']}, Disk: {part['DiskNumber']}, Partition: {part['PartitionNumber']}, Start LBA: {start_lba}, Size (LBA): {size_lba}, Sector Size: {sector_size}")

get_partition_lba_by_guid("{AC27B345-EC75-4731-A73C-97EDAE7CB6DE}")