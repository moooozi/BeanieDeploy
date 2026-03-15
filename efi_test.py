#!/usr/bin/env python3
"""Script to create and delete files/directories in the EFI partition."""

import os
import shutil
import stat
import sys
from pathlib import Path


def handle_remove_readonly(func, path, exc):
    """Helper function to handle removal of read-only files."""
    if not os.access(path, os.W_OK):
        Path(path).chmod(stat.S_IWRITE)
        func(path)
    else:
        raise


def main():
    efi_path = Path("D:\\EFI\\beanie")
    example_efi = efi_path / "example.efi"
    example_cfg = efi_path / "example.cfg"

    try:
        # Create the beanie directory
        print(f"Creating directory: {efi_path}")
        efi_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Directory created: {efi_path}")

        # Create example.efi
        print(f"\nCreating file: {example_efi}")
        example_efi.touch()
        print(f"✓ File created: {example_efi}")

        # Create example.cfg
        print(f"\nCreating file: {example_cfg}")
        example_cfg.touch()
        print(f"✓ File created: {example_cfg}")

        # Make example.cfg read-only
        print(f"\nSetting {example_cfg} to read-only")
        os.chmod(example_cfg, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        print("✓ File is now read-only")

        # List directory contents
        print(f"\nDirectory contents of {efi_path}:")
        for item in efi_path.iterdir():
            print(f"  - {item.name}")

        # Attempt to delete the entire beanie directory
        print(f"\nAttempting to force delete directory: {efi_path}")
        shutil.rmtree(efi_path, onerror=handle_remove_readonly)
        print(
            "✓ Directory and all contents deleted successfully (read-only flags ignored)"
        )

        # Verify deletion
        if not efi_path.exists():
            print(f"\n✓ Verification: {efi_path} no longer exists")
        else:
            print(f"\n✗ Verification failed: {efi_path} still exists")

    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
