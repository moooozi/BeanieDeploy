# User setup service for first-boot
# requires: log_dir, username, fullname, is_ostree
# Installs a systemd service that runs before SDDM on first boot to prompt for password
# Note: install-helpers dir is mounted at /run/install/repo/install-helpers/
%post --interpreter=/usr/bin/python3 --logfile={log_dir}/post_user_creation_tool_setup_nochroot --nochroot

import os
import shutil
from pathlib import Path

helpers_dir = Path("/run/install/repo/install-helpers")
target = Path("/mnt/sysimage")
staging_rel = Path("var/lib/beanie-install")
staging_dir = target / staging_rel

is_ostree = "{is_ostree}" == "yes"
if is_ostree:
    script_rel = Path("var/usrlocal/bin/beanie-firstboot.py")
else:
    script_rel = Path("usr/local/bin/beanie-firstboot.py")

script_dest = target / script_rel
service_staging_dest = staging_dir / "beanie-firstboot.service"

# Print and log symlink status for OSTree path debugging.
etc_path = target / "etc"
print(f"[user_creation_tool] etc path: {etc_path}")
print(f"[user_creation_tool] etc exists: {etc_path.exists()}")
print(f"[user_creation_tool] etc is symlink: {etc_path.is_symlink()}")
if etc_path.is_symlink():
    print(f"[user_creation_tool] etc symlink target: {os.readlink(etc_path)}")
print(f"[user_creation_tool] etc resolved path: {etc_path.resolve(strict=False)}")

# Install script and service into the target filesystem.
script_dest.parent.mkdir(parents=True, exist_ok=True)
staging_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(helpers_dir / "first-boot/beanie-firstboot.py", script_dest)
script_dest.chmod(0o755)
shutil.copy2(helpers_dir / "first-boot/beanie-firstboot.service", service_staging_dest)
service_staging_dest.chmod(0o644)

# Update ExecStart in the copied service to match install path.
execstart = f"ExecStart=/usr/bin/python3 /{script_rel.as_posix()}"
lines = service_staging_dest.read_text(encoding="utf-8").splitlines()
with service_staging_dest.open("w", encoding="utf-8", newline="\n") as f:
    for line in lines:
        if line.startswith("ExecStart="):
            f.write(execstart + "\n")
        else:
            f.write(line + "\n")

# Write pre-filled defaults if provided.
username = "{username}"
fullname = "{fullname}"
if username or fullname:
    defaults_path = staging_dir / "beanie_firstboot.conf"
    defaults_path.write_text(
        f"USERNAME={username}\nFULLNAME={fullname}\n",
        encoding="utf-8",
    )

%end

%post --logfile={log_dir}/post_user_creation_tool_enable

install -D -m 0644 /var/lib/beanie-install/beanie-firstboot.service /etc/systemd/system/beanie-firstboot.service

if [ -f /var/lib/beanie-install/beanie_firstboot.conf ]; then
    install -D -m 0644 /var/lib/beanie-install/beanie_firstboot.conf /etc/beanie_firstboot.conf
fi

systemctl daemon-reload
systemctl enable beanie-firstboot.service

%end
