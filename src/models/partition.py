from dataclasses import dataclass
from enum import Enum


class PartitioningMethod(Enum):
    """Enumeration of available partitioning methods."""

    DUALBOOT = "dualboot"
    REPLACE_WIN = "replace_win"
    CLEAN_DISK = "clean_disk"
    CUSTOM = "custom"


@dataclass
class Partition:
    make_root_partition: bool = False
    shrink_space: int = 0
    tmp_part_size: int = 0
    temp_part_label: str = "FEDORA-INST"  # Max 12 Chars
    boot_part_size: int = 0
