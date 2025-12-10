# Post-install script for CLEAN_DISK: Clean up tmp partition and extend root
# requires: tmp_part_uuid, log_dir, sys_drive_uuid

%post --logfile={log_dir}/ks-post-clean_encrypted.log
# Force unmount and erase tmp partition
umount /dev/disk/by-partuuid/{tmp_part_uuid} 2>/dev/null || true
wipefs -a /dev/disk/by-partuuid/{tmp_part_uuid}
parted $(lsblk -no pkname /dev/disk/by-partuuid/{tmp_part_uuid}) rm $(lsblk -no partn /dev/disk/by-partuuid/{tmp_part_uuid})
# Extend LUKS partition to fill disk
LUKS_DEV=$(lsblk -no name /dev/disk/by-partuuid/{sys_drive_uuid})
parted /dev/$(lsblk -no pkname /dev/$LUKS_DEV) resizepart $(lsblk -no partn /dev/$LUKS_DEV) 100%
# Resize LUKS container
cryptsetup resize /dev/disk/by-partuuid/{sys_drive_uuid}
# Extend Btrfs filesystem to fill partition
btrfs filesystem resize max /
%end