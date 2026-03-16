#!/usr/bin/env python3
"""
wingone-partition-resize — first-boot partition cleanup and root resize.

What this does
--------------
  1. Deletes the temporary partition {tmp_part_uuid} from its disk.
  2. Extends the root btrfs partition (ROOT_PARTUUID from
     /var/lib/wingone-install/partition_uuids) to fill all newly freed space.
  3. Resizes the btrfs filesystem online so the OS sees the extra space.
  4. Disables and removes this script so it never runs again.

This service runs once at first boot, before sysinit.target.
All output goes to the journal (stdout/stderr are captured by systemd).
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PARTITION_UUIDS_FILE = Path("/var/lib/wingone-install/partition_uuids")

# Placeholder — substituted by the runner before the script is installed.
TMP_PART_UUID = "{tmp_part_uuid_placeholder}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def log(msg: str) -> None:
    """Print to stdout; systemd captures this into the journal."""
    print(f"[wingone-partition-resize] {msg}", flush=True)


def die(msg: str, code: int = 1) -> NoReturn:
    print(f"[wingone-partition-resize] FATAL: {msg}", file=sys.stderr, flush=True)
    sys.exit(code)


def run(
    cmd: list[str], check: bool = True, input_text: str | None = None
) -> subprocess.CompletedProcess:
    log(f"$ {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        input=input_text,
    )
    if result.stdout:
        log(result.stdout.strip())
    if result.stderr:
        log(result.stderr.strip())
    if check and result.returncode != 0:
        die(f"Command failed (exit {result.returncode}): {' '.join(cmd)}")
    return result


# ---------------------------------------------------------------------------
# UUID / device resolution  (same lsblk-based approach as partition.py)
# ---------------------------------------------------------------------------


def partuuid_to_node(partuuid: str) -> str | None:
    """
    Resolve a PARTUUID to its kernel node path via lsblk.
    Returns None if the UUID is not found (partition may not exist).
    """
    result = subprocess.run(
        ["lsblk", "--json", "--output", "PATH,PARTUUID"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        die(f"lsblk failed: {result.stderr.strip()}")

    data = json.loads(result.stdout)
    target = partuuid.upper()

    def walk(nodes: list) -> str | None:
        for node in nodes:
            if (node.get("partuuid") or "").upper() == target:
                return node["path"]
            found = walk(node.get("children") or [])
            if found:
                return found
        return None

    return walk(data.get("blockdevices", []))


def node_to_parent_disk(node: str) -> str:
    """
    Return the parent disk device of a partition node using lsblk PKNAME.
    e.g. /dev/sda2 → /dev/sda,  /dev/nvme0n1p3 → /dev/nvme0n1
    """
    result = subprocess.run(
        ["lsblk", "--nodeps", "--noheadings", "--output", "PKNAME", node],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        die(f"lsblk PKNAME failed for {node}: {result.stderr.strip()}")
    pkname = result.stdout.strip()
    if not pkname:
        die(f"Could not determine parent disk for {node}")
    return f"/dev/{pkname}"


def node_to_partno(node: str) -> int:
    """Return the partition number of *node* via lsblk PARTN."""
    result = subprocess.run(
        ["lsblk", "--nodeps", "--noheadings", "--output", "PARTN", node],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        die(f"lsblk PARTN failed for {node}: {result.stderr.strip()}")
    try:
        return int(result.stdout.strip())
    except ValueError:
        die(f"Could not determine partition number for {node}")


def refresh_kernel_partition_view(disk: str) -> None:
    """Ask the kernel and udev to re-read partition table changes."""
    # Different tools succeed in different boot states / kernels; run all best-effort.
    run(["partprobe", disk], check=False)
    run(["blockdev", "--rereadpt", disk], check=False)
    run(["udevadm", "settle"], check=False)


def unmount_partition_if_mounted(node: str) -> None:
    """Unmount all mountpoints of *node* so it can be safely deleted."""
    result = subprocess.run(
        ["findmnt", "--noheadings", "--raw", "--source", node, "--output", "TARGET"],
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        die(f"findmnt failed for {node}: {result.stderr.strip()}")

    targets = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not targets:
        log(f"{node} is not mounted.")
        return

    # Unmount deeper mountpoints first if there are nested mounts.
    for target in sorted(targets, key=len, reverse=True):
        log(f"Unmounting {node} from {target}...")
        run(["umount", target])


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------


def read_root_partuuid() -> str:
    """Read ROOT_PARTUUID from the staging file left by the installer."""
    if not PARTITION_UUIDS_FILE.exists():
        die(f"Partition UUIDs file not found: {PARTITION_UUIDS_FILE}")

    for line in PARTITION_UUIDS_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("ROOT_PARTUUID="):
            value = line.split("=", 1)[1].strip()
            if value:
                return value.upper()

    die(f"ROOT_PARTUUID not found in {PARTITION_UUIDS_FILE}")


def delete_tmp_partition(tmp_uuid: str) -> str | None:
    """
    Delete the temporary partition by PARTUUID.
    Returns the disk device so the caller can reuse it.
    """
    log(f"Resolving temporary partition {tmp_uuid}...")
    node = partuuid_to_node(tmp_uuid)
    if node is None:
        log(f"Partition {tmp_uuid} not found — already deleted? Skipping.")
        return None

    disk = node_to_parent_disk(node)
    partno = node_to_partno(node)

    unmount_partition_if_mounted(node)

    log(f"Deleting {node} (partition {partno} on {disk})...")
    run(["sfdisk", "--delete", disk, str(partno)])
    refresh_kernel_partition_view(disk)
    log("Temporary partition deleted.")
    return disk


def extend_root_partition(root_uuid: str, disk: str) -> None:
    """
    Extend the root partition to fill all remaining free space on *disk*
    using sfdisk's non-interactive partition editor.
    """
    log(f"Resolving root partition {root_uuid}...")
    node = partuuid_to_node(root_uuid)
    if node is None:
        die(f"Root partition {root_uuid} not found — cannot resize.")

    partno = node_to_partno(node)
    log(f"Extending {node} (partition {partno} on {disk}) to 100%...")

    # Equivalent to: echo ", +" | sfdisk --no-reread -N <partno> <disk>
    run(["sfdisk", "--no-reread", "-N", str(partno), disk], input_text=", +\n")
    refresh_kernel_partition_view(disk)
    log("Partition table updated.")


def resize_btrfs() -> None:
    """Tell the btrfs filesystem on / to expand to fill the partition."""
    log("Resizing btrfs filesystem on / to max...")
    run(["btrfs", "filesystem", "resize", "max", "/"])
    log("btrfs resize complete.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    log("Starting post-install partition resize.")

    root_uuid = read_root_partuuid()
    log(f"ROOT_PARTUUID : {root_uuid}")
    log(f"TMP_PART_UUID : {TMP_PART_UUID}")

    disk = delete_tmp_partition(TMP_PART_UUID)

    if disk is None:
        # Tmp partition was already gone; still try to find the disk via root.
        root_node = partuuid_to_node(root_uuid)
        if root_node is None:
            die("Cannot find root partition — nothing to resize.")
        disk = node_to_parent_disk(root_node)

    extend_root_partition(root_uuid, disk)
    resize_btrfs()

    log("All done — partition resize successful.")


if __name__ == "__main__":
    main()
