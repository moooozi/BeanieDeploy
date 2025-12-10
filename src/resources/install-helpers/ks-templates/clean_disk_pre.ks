# Pre-install script for CLEAN_DISK: Delete all partitions except specified ones
# requires: sys_drive_uuid, sys_efi_uuid, tmp_part_uuid, log_dir

%pre --logfile={log_dir}/ks-pre-clean.log
# Find the disk containing the sys_drive_uuid partition
DISK=$(lsblk -no pkname /dev/disk/by-partuuid/{sys_drive_uuid})
# List all partitions on the disk
PARTITIONS=$(lsblk -no name /dev/$DISK | grep -E "^${DISK}p?[0-9]+$")
# Partitions to keep
KEEP_PARTS='/dev/disk/by-partuuid/{sys_drive_uuid} /dev/disk/by-partuuid/{sys_efi_uuid} /dev/disk/by-partuuid/{tmp_part_uuid}'
# Delete partitions not in keep list
for PART in $PARTITIONS; do
    PART_UUID=$(blkid -s PARTUUID -o value /dev/$PART)
    if [[ ! " $KEEP_PARTS " =~ " /dev/disk/by-partuuid/$PART_UUID " ]]; then
        echo "Deleting partition /dev/$PART"
        parted /dev/$DISK rm $(echo $PART | sed 's/.*[a-z]//')
    fi
done
%end