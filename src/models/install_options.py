from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.partition import PartitioningMethod


@dataclass
class InstallOptions:
    spin_index: int = -1
    auto_restart: bool = False
    torrent: bool = False
    export_wifi: bool = True
    partition_method: PartitioningMethod | None = None
