from dataclasses import dataclass

from config.settings import PartitioningMethod


@dataclass
class InstallOptions:
    spin_index: int = -1
    auto_restart: bool = False
    torrent: bool = False
    export_wifi: bool = True
    partition_method: PartitioningMethod | None = None
