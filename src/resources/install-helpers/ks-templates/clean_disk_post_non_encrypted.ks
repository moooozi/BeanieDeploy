# Post-install script for CLEAN_DISK: Clean up tmp partition and extend root
# requires: tmp_part_uuid, sys_drive_uuid, log_dir

%post --logfile={log_dir}/ks-post-clean.log
# Force unmount and erase tmp partition
umount /dev/disk/by-partuuid/{tmp_part_uuid} 2>/dev/null || true
wipefs -a /dev/disk/by-partuuid/{tmp_part_uuid}
parted $(lsblk -no pkname /dev/disk/by-partuuid/{tmp_part_uuid}) rm $(lsblk -no partn /dev/disk/by-partuuid/{tmp_part_uuid})
# Resize partition
SYSPART_DEV=$(lsblk -no name /dev/disk/by-partuuid/{sys_drive_uuid})
parted /dev/$(lsblk -no pkname /dev/$SYSPART_DEV) resizepart $(lsblk -no partn /dev/$SYSPART_DEV) 100%

# Extend Btrfs filesystem to fill partition
btrfs filesystem resize max /
%end