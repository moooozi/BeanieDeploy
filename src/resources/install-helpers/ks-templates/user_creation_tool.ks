# User setup service for first-boot
# requires: log_dir, username, fullname
# Installs a systemd service that runs before SDDM on first boot to prompt for password
# Note: install-helpers dir is mounted at /run/install/repo/install-helpers/
%post --interpreter=/bin/bash --logfile={log_dir}/post_user_creation_tool_setup --nochroot

HELPERS_DIR=/run/install/repo/install-helpers
TARGET=/mnt/sysimage

# Install the user-creator script and firstboot service into the target system
install -m 0755 "$HELPERS_DIR/first-boot/beanie-user-creator.py" \
    "$TARGET/usr/local/bin/beanie-user-creator.py"
install -m 0644 "$HELPERS_DIR/first-boot/beanie-firstboot.service" \
    "$TARGET/etc/systemd/system/beanie-firstboot.service"

# Enable the service the standard way
chroot "$TARGET" systemctl enable beanie-firstboot.service

# Write pre-filled defaults if a username or fullname was provided
if [ -n "{username}" ] || [ -n "{fullname}" ]; then
    cat > "$TARGET/etc/beanie_user_creator" <<'BEANIE_DEFS_EOF'
USERNAME={username}
FULLNAME={fullname}
BEANIE_DEFS_EOF
fi

%end
