#!/bin/bash
# Usage: ./find_disk_by_guid.sh <disk-guid>
# Example: ./find_disk_by_guid.sh 45e577b8-7714-47e7-8750-2b64166fb4d8

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <disk-guid>"
    exit 2
fi

GUID="$1"
DISK_PATH=$(lsblk -ndo PATH,PTUUID | awk -v guid="$GUID" '$2==guid {print $1}')

if [ -z "$DISK_PATH" ]; then
    echo "Error: Disk with GUID $GUID not found."
    exit 1
else
    echo "$DISK_PATH"
    exit 0
fi
