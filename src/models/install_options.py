from dataclasses import dataclass
from typing import Optional

from config.settings import PartitioningMethod


@dataclass
class InstallOptions:
    spin_index: int = -1
    auto_restart: bool = False
    torrent: bool = False
    export_wifi: bool = True
    partition_method: Optional[PartitioningMethod] = None
