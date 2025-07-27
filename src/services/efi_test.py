import os
import sys
import firmware_variables as fwvars

def _setup_sys_path():
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))


if __name__ == "__main__":
    _setup_sys_path()
    from services.system import get_admin
    get_admin()
    with fwvars.adjust_privileges():
        entries = fwvars.get_boot_order()
        for entry in entries:
            print(f"Boot Entry: {entry}")
            entry = fwvars.get_parsed_boot_entry(entry)
            print("  Description:", entry.description)
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

            print("    - Bytes:", "\n")
            print(entry.file_path_list.to_bytes())
            print("  Attributes:", entry.attributes)
            print("  Optional Data:", entry.optional_data)
    input("Press Enter to exit...")


    """
    \x04\x01*\x00\x01\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\xfb\x19}\x95\xf7\x9ahO\xb9\xb2\xef\x1cr\xc6"g\x02\x02\x04\x04F\x00\\x00E\x00F\x00I\x00\\x00M\x00i\x00c\x00r\x00o\x00s\x00o\x00f\x00t\x00\\x00B\x00o\x00o\x00t\x00\\x00b\x00o\x00o\x00t\x00m\x00g\x00f\x00w\x00.\x00e\x00f\x00i\x00\x00\x00\x7f\xff\x04\x00
    """


"""
Mnemonic	| Byte Offset | Byte Length
Type        | 0           | 1
Sub-Type    | 1           | 1
Length      | 2           | 2
Partition Number | 4           | 4
Partition Start | 8           | 8
Partition Size | 16          | 8
Partition Signature | 24      | 16
Partition Format | 40        | 1
Signature Type | 41        | 1
"""