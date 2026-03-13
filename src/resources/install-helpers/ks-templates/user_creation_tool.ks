# User setup service for first-boot
# requires: log_dir, username, fullname, is_ostree
# Installs a systemd service that runs before SDDM on first boot to prompt for password
# Note: install-helpers dir is mounted at /run/install/repo/install-helpers/
%post --interpreter=/bin/bash --logfile={log_dir}/post_user_creation_tool_setup --nochroot

HELPERS_DIR=/run/install/repo/install-helpers
TARGET=/mnt/sysimage
IS_OSTREE="{is_ostree}"

if [ "$IS_OSTREE" = "yes" ]; then
    SCRIPT_DIR="$TARGET/var/usrlocal/bin"
    SCRIPT_PATH="/var/usrlocal/bin/beanie-user-creator.py"
else
    SCRIPT_DIR="$TARGET/usr/local/bin"
    SCRIPT_PATH="/usr/local/bin/beanie-user-creator.py"
fi

# Install the user-creator script and firstboot service into the target system
install -d "$SCRIPT_DIR" "$TARGET/etc/systemd/system"
install -m 0755 "$HELPERS_DIR/first-boot/beanie-user-creator.py" \
    "$SCRIPT_DIR/beanie-user-creator.py"
install -m 0644 "$HELPERS_DIR/first-boot/beanie-firstboot.service" \
    "$TARGET/etc/systemd/system/beanie-firstboot.service"

# Match unit ExecStart to the installed script path
sed -i "s|^ExecStart=.*|ExecStart=/usr/bin/python3 $SCRIPT_PATH|" \
    "$TARGET/etc/systemd/system/beanie-firstboot.service"

# Enable service in the target root
systemctl --root="$TARGET" enable beanie-firstboot.service

# Write pre-filled defaults if a username or fullname was provided
if [ -n "{username}" ] || [ -n "{fullname}" ]; then
    cat > "$TARGET/etc/beanie_user_creator" <<'BEANIE_DEFS_EOF'
USERNAME={username}
FULLNAME={fullname}
BEANIE_DEFS_EOF
fi

%end
