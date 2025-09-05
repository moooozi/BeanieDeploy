import firmware_variables as fwvars

def find_free_entry_ids(start=0, end=25):
    free_ids = []
    unknown_ids = []
    for i in range(start, end + 1):
        try:
            fwvars.get_boot_entry(i)
            description = fwvars.get_parsed_boot_entry(i).description
            print(f"Entry ID {i} is occupied: {description}")
        except OSError as e:
            if hasattr(e, 'winerror') and e.winerror == 203:
                print(f"Entry ID {i} is free (WinError 203)")
                free_ids.append(i)
            else:
                print(f"Entry ID {i} is unknown (error {getattr(e, 'winerror', None)}): {e}")
                unknown_ids.append(i)
    print(f"Free entry IDs in range {start}-{end}: {free_ids}")
    if unknown_ids:
        print(f"Unknown entry IDs in range {start}-{end}: {unknown_ids}")

if __name__ == "__main__":
    with fwvars.adjust_privileges():
        find_free_entry_ids()
