#!/usr/bin/env python3
"""
Append an EFI / boot / root partition trio to a GPT disk.

Layout appended
---------------
  +1  1 GiB   EFI System Partition   (type: ESP)
  +2  1 GiB   Linux boot partition   (type: Linux filesystem)
  +3  <rest>  Linux root partition   (type: Linux filesystem)

No partition is formatted — the script only writes partition table entries.
Any partition selected for deletion is unmounted first.

Configuration (see CONFIGURATION block below)
---------------------------------------------
  DISK
      Target block device — a path (/dev/sda, /dev/disk/by-id/…) or a
      bare GPT disk GUID.  Symlinks are resolved automatically.

  DELETE_ALL
      If True, all existing partitions are removed before appending.
      When ALL_EXCEPT is also set, those partitions are spared.

  ALL_EXCEPT
      Only consulted when DELETE_ALL is True. Comma-separated list of
      partition specs to keep. Each spec may be a device node, a
      by-partuuid symlink, or a bare PARTUUID. Non-matching specs are
      silently ignored. Leave empty to delete every existing partition.

Assumptions deliberately avoided
---------------------------------
  • Sector size is NOT assumed — queried from the kernel via blockdev --getss.
  • Partition node names are NOT guessed — resolved via lsblk by PARTUUID.

Output
------
  Progress / diagnostics → stderr.
  On success, one JSON object → stdout:

    {
      "device": "/dev/sda",
      "disk_guid": "...",
      "sector_size": 512,
      "partitions": {
        "efi":  { "node": "/dev/sda3", "partuuid": "..." },
        "boot": { "node": "/dev/sda4", "partuuid": "..." },
        "root": { "node": "/dev/sda5", "partuuid": "..." }
      }
    }
"""


# =============================================================================
# CONFIGURATION — placeholders in {} are replaced by the runner at launch time.
#
#   DISK        Device path or GPT disk GUID.
#               e.g.  /dev/sda   or   12345678-ABCD-EF01-2345-6789ABCDEF01
#
#   DELETE_ALL  "true"  → delete existing partitions before appending.
#               "false" → append only; ALL_EXCEPT is ignored entirely.
#
#   ALL_EXCEPT  Only consulted when DELETE_ALL is true.
#               Comma-separated partition specs to keep (and not delete).
#               Each spec may be a device node (/dev/sda1), a by-partuuid
#               symlink, or a bare PARTUUID.  Non-matching specs are ignored.
#               Leave empty to delete every existing partition.
# =============================================================================

DISK = "{disk_path_or_uuid}"
DELETE_ALL = "{should_delete_all}"
ALL_EXCEPT = "{delete_all_except}"  # comma-separated specs to keep; only used when DELETE_ALL is true

# =============================================================================

import json
import os
import subprocess
import sys
import time
import uuid

# ---------------------------------------------------------------------------
# GPT partition type GUIDs
# ---------------------------------------------------------------------------
TYPE_EFI = "C12A7328-F81F-11D2-BA4B-00A0C93EC93B"  # EFI System Partition
TYPE_LINUX = "0FC63DAF-8483-4772-8E79-3D69D8477DE4"  # Linux filesystem

ONE_GIB = 1 << 30  # bytes


def die(message: str, code: int = 1) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(code)


def make_uuid() -> str:
    """Return a new random UUID in upper-case (GPT convention)."""
    return str(uuid.uuid4()).upper()


# ---------------------------------------------------------------------------
# Hardware queries
# ---------------------------------------------------------------------------


def query_sector_size(device: str) -> int:
    """
    Ask the kernel for the logical sector size of *device* via blockdev --getss.
    Typically 512, but 4096 on 4Kn NVMe drives.
    """
    result = subprocess.run(
        ["blockdev", "--getss", device],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        die(f"blockdev --getss {device} failed:\n{result.stderr.strip()}")
    try:
        size = int(result.stdout.strip())
    except ValueError:
        die(f"unexpected output from blockdev --getss: {result.stdout!r}")
    if size <= 0 or (size & (size - 1)) != 0:
        die(f"blockdev returned a non-power-of-two sector size: {size}")
    return size


def query_disk_guid(device: str) -> str:
    """
    Return the GPT disk GUID (PTUUID) in upper-case.

    This is the OS-agnostic identifier stored in the GPT header itself —
    distinct from partition PARTUUIDs and from filesystem UUIDs
    (the latter are filesystem-level and Linux/udev-specific).

    Queried via ``lsblk --nodeps`` so we only inspect the disk, not its
    partitions.
    """
    result = subprocess.run(
        ["lsblk", "--nodeps", "--noheadings", "--output", "PTUUID", device],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        die(f"lsblk (PTUUID) failed:\n{result.stderr.strip()}")
    guid = result.stdout.strip().upper()
    if not guid:
        die(f"Could not read disk GUID from {device} — is it a GPT disk?")
    return guid


def resolve_device(argument: str) -> str:
    """
    Resolve the user-supplied *argument* to an absolute block device path.

    Two forms are accepted:

    • A device path  — anything that starts with '/' (e.g. /dev/sda,
      /dev/disk/by-id/…).  Symlinks are resolved with os.path.realpath so
      the rest of the script always works with the canonical node.

    • A GPT disk GUID / PTUUID  — a bare UUID string (no leading '/').
      All block devices visible to lsblk are scanned; the one whose PTUUID
      matches (case-insensitive) is returned.  Exits with an error if zero
      or more than one match is found.
    """
    if argument.startswith("/"):
        real = os.path.realpath(argument)
        if not os.path.exists(real):
            die(f"Device path does not exist: {argument}")
        return real

    # Treat as a disk GUID — scan every top-level block device.
    target_guid = argument.upper()

    result = subprocess.run(
        ["lsblk", "--json", "--nodeps", "--output", "PATH,PTUUID"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        die(f"lsblk failed while scanning for disk GUID:\n{result.stderr.strip()}")

    data = json.loads(result.stdout)
    matches = [
        dev["path"]
        for dev in data.get("blockdevices", [])
        if (dev.get("ptuuid") or "").upper() == target_guid
    ]

    if not matches:
        die(f"No block device found with disk GUID {argument}")
    if len(matches) > 1:
        die(
            f"Ambiguous disk GUID {argument} matched multiple devices: "
            + ", ".join(matches)
        )

    return matches[0]


def get_device_partitions(device: str) -> list[dict]:
    """
    Return all current partitions of *device* as a list of dicts:
      [{"node": "/dev/sda1", "partuuid": "UPPER-UUID", "partno": 1}, ...]

    Uses lsblk --output PATH,PARTUUID,PARTN so we never guess node names
    or partition numbers from string patterns.
    """
    result = subprocess.run(
        ["lsblk", "--json", "--output", "PATH,PARTUUID,PARTN", "--path", device],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        die(f"lsblk failed:\n{result.stderr.strip()}")

    data = json.loads(result.stdout)
    partitions = []

    def walk(nodes: list) -> None:
        for node in nodes:
            # lsblk only sets 'partn' on actual partition entries
            if node.get("partn") is not None:
                partitions.append(
                    {
                        "node": node["path"],
                        "partuuid": (node.get("partuuid") or "").upper(),
                        "partno": int(node["partn"]),
                    }
                )
            walk(node.get("children") or [])

    walk(data.get("blockdevices", []))
    return partitions


def refresh_kernel_partition_table(device: str) -> None:
    """
    Ask the kernel to re-read partition table changes and wait for udev.

    We try partprobe first, then fall back to blockdev --rereadpt.
    """
    partprobe = subprocess.run(
        ["partprobe", device],
        capture_output=True,
        text=True,
    )
    if partprobe.returncode != 0:
        print(
            f"partprobe failed for {device}, trying blockdev --rereadpt...",
            file=sys.stderr,
        )
        reread = subprocess.run(
            ["blockdev", "--rereadpt", device],
            capture_output=True,
            text=True,
        )
        if reread.returncode != 0:
            die(
                "Failed to refresh kernel partition table via partprobe and "
                f"blockdev --rereadpt:\n{partprobe.stderr.strip()}\n{reread.stderr.strip()}"
            )

    # Let udev process device-node changes before we continue.
    settle = subprocess.run(["udevadm", "settle"], capture_output=True, text=True)
    if settle.returncode != 0:
        print(
            f"warning: udevadm settle returned {settle.returncode}: "
            f"{settle.stderr.strip()}",
            file=sys.stderr,
        )


def get_partition_mountpoints(device: str) -> dict[str, list[str]]:
    """
    Return mounted target paths for each partition node on *device*.

    Output shape: {"/dev/sda1": ["/boot/efi"], ...}
    """
    result = subprocess.run(
        ["lsblk", "--json", "--output", "PATH,PARTN,MOUNTPOINTS", "--path", device],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        die(f"lsblk failed while querying mount points:\n{result.stderr.strip()}")

    data = json.loads(result.stdout)
    mount_map: dict[str, list[str]] = {}

    def walk(nodes: list) -> None:
        for node in nodes:
            if node.get("partn") is not None:
                mounts = [
                    m
                    for m in (node.get("mountpoints") or [])
                    if isinstance(m, str) and m.strip()
                ]
                if mounts:
                    mount_map[node["path"]] = mounts
            walk(node.get("children") or [])

    walk(data.get("blockdevices", []))
    return mount_map


def unmount_partitions(partitions: list[dict], mount_map: dict[str, list[str]]) -> None:
    """Unmount every mount point that belongs to the provided partitions."""
    for part in partitions:
        node = part["node"]
        mounts = mount_map.get(node, [])
        if not mounts:
            continue

        # Unmount deeper paths first if nested mount points exist.
        for mount in sorted(set(mounts), key=len, reverse=True):
            print(f"Unmounting {node} from {mount}", file=sys.stderr)
            result = subprocess.run(
                ["umount", mount],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                die(f"Failed to unmount {mount} ({node}):\n{result.stderr.strip()}")


# ---------------------------------------------------------------------------
# Partition spec resolution
# ---------------------------------------------------------------------------


def resolve_spec_to_partuuid(
    spec: str, existing: list[dict], disk_guid: str
) -> str | None:
    """
    Resolve a user-supplied partition spec to a PARTUUID present in *existing*,
    or return None if the spec cannot be matched (treat as non-existent).

    Accepted spec forms
    -------------------
    • /dev/disk/by-partuuid/<uuid>  — symlink; resolve with os.path.realpath,
                                      then match the resulting node
    • /dev/sdaN / /dev/nvme0n1pN    — direct node; match by node path
    • <partition-partuuid>          — match directly against partuuid field
    • <disk-guid / ptuuid>          — the GPT disk GUID; matches ALL partitions
                                      on the disk (i.e. keep everything)
    """
    node_map = {p["node"]: p["partuuid"] for p in existing}
    partuuid_set = {p["partuuid"] for p in existing}

    upper = spec.upper()

    # 1. Disk GUID — caller interprets None returns as "keep all"
    if upper == disk_guid:
        return "__DISK_GUID__"

    # 2. Bare PARTUUID string (no path separators)
    if upper in partuuid_set:
        return upper

    # 3. Path — resolve symlinks so by-partuuid and by-id links all collapse
    #    to the real device node first.
    try:
        real = os.path.realpath(spec)
    except OSError:
        return None

    if real in node_map:
        return node_map[real]

    return None


# ---------------------------------------------------------------------------
# Partition deletion
# ---------------------------------------------------------------------------


def delete_partitions(device: str, partitions: list[dict]) -> None:
    """
    Unmount and delete the given partitions from *device* using sfdisk --delete.
    Does nothing if *partitions* is empty.
    """
    if not partitions:
        return

    mount_map = get_partition_mountpoints(device)
    unmount_partitions(partitions, mount_map)

    partnos = [p["partno"] for p in partitions]
    sorted_nos = sorted(partnos)
    print(
        f"Deleting partition(s): {', '.join(str(n) for n in sorted_nos)}",
        file=sys.stderr,
    )
    result = subprocess.run(
        ["sfdisk", "--delete", device] + [str(n) for n in sorted_nos],
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout, end="", file=sys.stderr)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        die(f"sfdisk --delete exited with status {result.returncode}")

    refresh_kernel_partition_table(device)


def apply_deletion_mode(
    device: str,
    disk_guid: str,
    keep_specs: list[str] | None,
) -> None:
    """
    Inspect existing partitions and delete the appropriate ones.

    keep_specs is None         → delete everything
    keep_specs is not None     → delete all whose PARTUUID is not in keep_specs
    """
    existing = get_device_partitions(device)

    if not existing:
        print("No existing partitions found — nothing to delete.", file=sys.stderr)
        return

    if keep_specs is None:
        partitions_to_delete = existing

    else:  # delete-all-except
        keep_uuids: set[str] = set()
        keep_all = False
        for spec in keep_specs or []:
            resolved = resolve_spec_to_partuuid(spec, existing, disk_guid)
            if resolved == "__DISK_GUID__":
                keep_all = True
                print(
                    f"  spec '{spec}' matches the disk GUID — keeping all partitions.",
                    file=sys.stderr,
                )
                break
            if resolved:
                keep_uuids.add(resolved)
            else:
                print(
                    f"  spec '{spec}' did not match any partition on {device}"
                    " — ignoring.",
                    file=sys.stderr,
                )

        if keep_all:
            return

        kept = [p for p in existing if p["partuuid"] in keep_uuids]
        deleted = [p for p in existing if p["partuuid"] not in keep_uuids]

        if kept:
            print(
                "Keeping: " + ", ".join(p["node"] for p in kept),
                file=sys.stderr,
            )
        partitions_to_delete = deleted

    delete_partitions(device, partitions_to_delete)


# ---------------------------------------------------------------------------
# sfdisk append
# ---------------------------------------------------------------------------


def build_sfdisk_append_script(
    sector_size: int,
    efi_uuid: str,
    boot_uuid: str,
    root_uuid: str,
) -> str:
    """
    Build the sfdisk(8) append script.

    With --append sfdisk places new partitions after the last existing one.
    Omitting 'size' on the last entry consumes all remaining space.
    """
    one_gib_sectors = ONE_GIB // sector_size

    lines = [
        f'size={one_gib_sectors}, type={TYPE_EFI},   uuid={efi_uuid},  name="EFI"',
        f'size={one_gib_sectors}, type={TYPE_LINUX},  uuid={boot_uuid}, name="boot"',
        f'type={TYPE_LINUX},  uuid={root_uuid}, name="root"',
    ]
    return "\n".join(lines) + "\n"


def run_sfdisk_append(device: str, script: str) -> None:
    """Append partitions and request a kernel re-read."""
    print("sfdisk append script:", file=sys.stderr)
    print("─" * 60, file=sys.stderr)
    print(script, end="", file=sys.stderr)
    print("─" * 60, file=sys.stderr)

    result = subprocess.run(
        ["sfdisk", "--append", "--no-reread", "--no-tell-kernel", device],
        input=script,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout, end="", file=sys.stderr)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        die(f"sfdisk exited with status {result.returncode}")

    refresh_kernel_partition_table(device)


# ---------------------------------------------------------------------------
# Node resolution
# ---------------------------------------------------------------------------


def resolve_nodes_by_partuuid(
    device: str,
    partuuids: list[str],
) -> dict[str, str]:
    """
    Poll lsblk until every PARTUUID in *partuuids* has a visible kernel node.
    Returns {PARTUUID: "/dev/nodeX"}.  Exits on timeout.
    """
    wanted = {u.upper() for u in partuuids}
    found: dict[str, str] = {}

    for _ in range(10):
        partitions = get_device_partitions(device)
        for p in partitions:
            if p["partuuid"] in wanted:
                found[p["partuuid"]] = p["node"]
        if found.keys() == wanted:
            return found
        time.sleep(0.5)

    missing = wanted - found.keys()
    die("Could not resolve kernel nodes for PARTUUIDs: " + ", ".join(missing))


# ---------------------------------------------------------------------------
# CLI & main
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Configuration validation
# ---------------------------------------------------------------------------


def parse_bool(raw: str, name: str) -> bool:
    """
    Parse a runner-substituted boolean string.

    Accepts (case-insensitive): "true"/"1"/"yes"  → True
                                "false"/"0"/"no"  → False
    Anything else is a configuration error.
    """
    normalised = raw.strip().lower()
    if normalised in ("true", "1", "yes"):
        return True
    if normalised in ("false", "0", "no"):
        return False
    die(f"{name} must be a boolean string (true/false/yes/no/1/0), got: {raw!r}")


def parse_spec_list(raw: str) -> list[str] | None:
    """
    Parse a runner-substituted comma-separated list of partition specs.

    Returns None for an empty / whitespace-only string (meaning: not set).
    Strips whitespace from each individual spec.
    """
    stripped = raw.strip()
    if not stripped:
        return None
    return [s.strip() for s in stripped.split(",") if s.strip()]


def validate_config() -> tuple[str, bool, list[str] | None]:
    """
    Parse and validate the module-level configuration variables.

    Returns (disk, delete_all, keep_specs) where keep_specs is only
    populated when delete_all is True and ALL_EXCEPT is non-empty.
    """
    disk = DISK.strip()
    if not disk:
        die("DISK must be a non-empty string (device path or GPT disk GUID).")

    delete_all = parse_bool(DELETE_ALL, "DELETE_ALL")

    # ALL_EXCEPT is only meaningful when DELETE_ALL is true — don't even
    # look at it otherwise.
    keep_specs = parse_spec_list(ALL_EXCEPT) if delete_all else None

    return disk, delete_all, keep_specs


def main() -> None:
    disk_arg, delete_all, keep_specs = validate_config()

    device = resolve_device(disk_arg)

    if device != disk_arg:
        print(f"Resolved      : {disk_arg!r} → {device}", file=sys.stderr)

    # ------------------------------------------------------------------
    # Query sector size and disk GUID.
    # ------------------------------------------------------------------
    sector_size = query_sector_size(device)
    disk_guid = query_disk_guid(device)
    print(f"Device      : {device}", file=sys.stderr)
    print(f"Sector size : {sector_size} bytes", file=sys.stderr)
    print(f"Disk GUID   : {disk_guid}", file=sys.stderr)

    # ------------------------------------------------------------------
    # Report deletion intent.
    # ------------------------------------------------------------------
    if delete_all:
        if keep_specs:
            print(
                f"Mode        : delete all except: {', '.join(keep_specs)}",
                file=sys.stderr,
            )
        else:
            print(
                "Mode        : delete all existing partitions, then append",
                file=sys.stderr,
            )
    else:
        print(
            "Mode        : append only (existing partitions untouched)", file=sys.stderr
        )

    # ------------------------------------------------------------------
    # Pre-generate UUIDs.
    # ------------------------------------------------------------------
    efi_uuid = make_uuid()
    boot_uuid = make_uuid()
    root_uuid = make_uuid()

    print("Pre-generated partition UUIDs:", file=sys.stderr)
    print(f"  EFI  : {efi_uuid}", file=sys.stderr)
    print(f"  boot : {boot_uuid}", file=sys.stderr)
    print(f"  root : {root_uuid}", file=sys.stderr)

    # ------------------------------------------------------------------
    # Optional deletion pass.
    # ------------------------------------------------------------------
    if delete_all:
        apply_deletion_mode(device, disk_guid, keep_specs=keep_specs)

    # ------------------------------------------------------------------
    # Append the three new partitions.
    # ------------------------------------------------------------------
    sfdisk_script = build_sfdisk_append_script(
        sector_size, efi_uuid, boot_uuid, root_uuid
    )
    run_sfdisk_append(device, sfdisk_script)

    # ------------------------------------------------------------------
    # Resolve actual kernel node names by PARTUUID.
    # ------------------------------------------------------------------
    print("Resolving partition nodes via lsblk...", file=sys.stderr)
    node_map = resolve_nodes_by_partuuid(device, [efi_uuid, boot_uuid, root_uuid])

    # ------------------------------------------------------------------
    # Emit JSON result on stdout.
    # ------------------------------------------------------------------
    result = {
        "device": device,
        "disk_guid": disk_guid,
        "sector_size": sector_size,
        "partitions": {
            "efi": {"node": node_map[efi_uuid], "partuuid": efi_uuid},
            "boot": {"node": node_map[boot_uuid], "partuuid": boot_uuid},
            "root": {"node": node_map[root_uuid], "partuuid": root_uuid},
        },
    }
    print(json.dumps(result, indent=2))
    write_output_files(efi_uuid, boot_uuid, root_uuid)


OUTPUT_DIR = "/tmp/wingone_vars"


def write_output_files(efi_uuid: str, boot_uuid: str, root_uuid: str) -> None:
    """
    Write two files to OUTPUT_DIR:

      partition_uuids      — plain key=value record of the three PARTUUIDs
      partitioning_ks      — Kickstart snippet for EFI, boot, and root
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- partition_uuids ---
    uuids_path = os.path.join(OUTPUT_DIR, "partition_uuids")
    uuids_content = (
        f"EFI_PARTUUID={efi_uuid.lower()}\n"
        f"BOOT_PARTUUID={boot_uuid.lower()}\n"
        f"ROOT_PARTUUID={root_uuid.lower()}\n"
    )
    _write(uuids_path, uuids_content)

    # --- partitioning_ks ---
    ks_path = os.path.join(OUTPUT_DIR, "partitioning_ks")
    ks_content = (
        f"# EFI\n"
        f"part /boot/efi --fstype=efi --label=efi --onpart=/dev/disk/by-partuuid/{efi_uuid.lower()}\n"
        f"\n"
        f"# boot\n"
        f"part /boot --fstype=ext4 --label=fedora_boot --onpart=/dev/disk/by-partuuid/{boot_uuid.lower()}\n"
        f"\n"
        f"# root\n"
        f"part btrfs.01 --onpart=/dev/disk/by-partuuid/{root_uuid.lower()}\n"
        f"btrfs none --label=fedora btrfs.01\n"
        f"btrfs / --subvol --name=root fedora\n"
        f"btrfs /home --subvol --name=home fedora\n"
        f"btrfs /var --subvol --name=var fedora\n"
    )
    _write(ks_path, ks_content)


def _write(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)
    print(f"Written       : {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
