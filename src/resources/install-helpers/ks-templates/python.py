import shutil
import subprocess
from pathlib import Path

helpers_dir = Path("/run/install/repo/install-helpers")
target = Path("/mnt/sysimage")

is_ostree = "{is_ostree}" == "yes"
if is_ostree:
    script_rel = Path("var/usrlocal/bin/beanie-user-creator.py")
else:
    script_rel = Path("usr/local/bin/beanie-user-creator.py")

script_dest = target / script_rel
service_dest = target / "etc/systemd/system/beanie-firstboot.service"

# Install script and service into the target filesystem.
script_dest.parent.mkdir(parents=True, exist_ok=True)
service_dest.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(helpers_dir / "first-boot/beanie-user-creator.py", script_dest)
script_dest.chmod(0o755)
shutil.copy2(helpers_dir / "first-boot/beanie-firstboot.service", service_dest)
service_dest.chmod(0o644)

# Update ExecStart in the copied service to match install path.
execstart = f"ExecStart=/usr/bin/python3 /{script_rel.as_posix()}"
lines = service_dest.read_text(encoding="utf-8").splitlines()
with service_dest.open("w", encoding="utf-8", newline="\n") as f:
    for line in lines:
        if line.startswith("ExecStart="):
            f.write(execstart + "\n")
        else:
            f.write(line + "\n")

# Enable service in the target root.
print(
    subprocess.run(
        ["chroot", str(target), "systemctl", "daemon-reload"],
        capture_output=True,
        text=True,
    )
)
print(
    subprocess.run(
        ["chroot", str(target), "systemctl", "enable", "beanie-firstboot.service"],
        capture_output=True,
        text=True,
    )
)

# Write pre-filled defaults if provided.
username = "{username}"
fullname = "{fullname}"
if username or fullname:
    defaults_path = target / "etc/beanie_user_creator"
    defaults_path.write_text(
        f"USERNAME={username}\nFULLNAME={fullname}\n",
        encoding="utf-8",
    )
