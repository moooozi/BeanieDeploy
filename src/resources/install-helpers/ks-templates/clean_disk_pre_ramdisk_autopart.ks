# BeanieDeploy RAMDISK: wipe disk and autopart install
# requires: DISK_UUID_PLACEHOLDER, log_dir, should_encrypt

%pre --logfile={log_dir}/ks-pre-clean_disk_pre_ramdisk_autopart.log
#!/bin/bash

# The UUID will be replaced with the actual disk UUID by BeanieDeploy's config_builder.py
GUID="{DISK_UUID_PLACEHOLDER}"
TMP_DIR="/tmp/beanie_vars"
mkdir -p "$TMP_DIR"
echo "$GUID" > "$TMP_DIR/disk_guid"
DISK=$(/run/install/repo/install-helpers/scripts/find_disk_by_guid.sh "$GUID")
if [ $? -ne 0 ]; then
    echo "ERROR: Disk with GUID $GUID not found." >&2
    exit 1
fi
echo "$DISK" > "$TMP_DIR/install_disk"

# Generate dynamic partitioning commands
echo "ignoredisk --only-use=$DISK" > "$TMP_DIR/partition_cmds"
echo "clearpart --all --initlabel --drives=$DISK" >> "$TMP_DIR/partition_cmds"
if [ "{should_encrypt}" = "yes" ]; then
    echo "autopart --encrypted" >> "$TMP_DIR/partition_cmds"
else
    echo "autopart" >> "$TMP_DIR/partition_cmds"
fi
%end

%include /tmp/beanie_vars/partition_cmds
