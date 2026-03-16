# Partition resize service for first boot
# Deletes a temporary partition and expands the root btrfs to fill remaining space.
# requires: log_dir, tmp_part_uuid, is_ostree
# Note: install-helpers dir is mounted at /run/install/repo/install-helpers/
%post --interpreter=/usr/bin/python3 --logfile={log_dir}/post_partition_resize_setup_nochroot --nochroot
import os
import shutil
from pathlib import Path

helpers_dir = Path("/run/install/repo/install-helpers")
target      = Path("/mnt/sysimage")

staging_rel = Path("var/lib/beanie-install")
staging_dir = target / staging_rel

is_ostree = "{is_ostree}" == "yes"
if is_ostree:
    script_rel = Path("var/usrlocal/bin/beanie-partition-resize.py")
else:
    script_rel = Path("usr/local/bin/beanie-partition-resize.py")

script_dest = target / script_rel

service_staging_dest = staging_dir / "beanie-partition-resize.service"

# Install the service script into the target filesystem.
script_dest.parent.mkdir(parents=True, exist_ok=True)
staging_dir.mkdir(parents=True, exist_ok=True)

shutil.copy2(helpers_dir / "partition-resize/beanie-partition-resize.py", script_dest)
script_dest.chmod(0o755)

shutil.copy2(helpers_dir / "partition-resize/beanie-partition-resize.service", service_staging_dest)
service_staging_dest.chmod(0o644)

# Update ExecStart in the copied service to match the install path.
execstart = f"ExecStart=/usr/bin/python3 /{script_rel.as_posix()}"
lines = service_staging_dest.read_text(encoding="utf-8").splitlines()
with service_staging_dest.open("w", encoding="utf-8", newline="\n") as fh:
    for line in lines:
        if line.startswith("ExecStart="):
            fh.write(execstart + "\n")
        else:
            fh.write(line + "\n")

# Copy partition UUIDs from the installer's /tmp into the target so the
# service can read them on the installed system.
src_uuids = Path("/tmp/beanie_vars/partition_uuids")
dst_uuids = staging_dir / "partition_uuids"
if src_uuids.exists():
    shutil.copy2(src_uuids, dst_uuids)
    dst_uuids.chmod(0o644)
    print(f"[partition_resize] Copied partition_uuids → {dst_uuids}")
else:
    # Abort — without the ROOT_PARTUUID we cannot safely resize anything.
    raise RuntimeError(f"partition_uuids not found at {src_uuids}; cannot continue.")

# Substitute the tmp partition UUID placeholder directly into the script.
content = script_dest.read_text(encoding="utf-8")
content = content.replace("{tmp_part_uuid_placeholder}", "{tmp_part_uuid}")  # runner expands this
script_dest.write_text(content, encoding="utf-8")

print(f"[partition_resize] Script installed  → {script_dest}")
print(f"[partition_resize] Service staged    → {service_staging_dest}")
%end


%post --logfile={log_dir}/post_partition_resize_enable
install -D -m 0644 \
    /var/lib/beanie-install/beanie-partition-resize.service \
    /etc/systemd/system/beanie-partition-resize.service
systemctl daemon-reload
systemctl enable beanie-partition-resize.service
%end
