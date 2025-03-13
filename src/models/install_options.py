from dataclasses import dataclass


@dataclass
class InstallOptions:
    spin_index: int = -1
    auto_restart: bool = False
    torrent: bool = False
    export_wifi: bool = True
