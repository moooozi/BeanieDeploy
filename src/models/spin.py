from dataclasses import dataclass


@dataclass
class Spin:
    name: str
    size: str
    hash256: str
    dl_link: str
    is_live_img: bool = False
    version: str = ""
    desktop: str = ""
    is_auto_installable: bool = False
    is_advanced: bool = False
    torrent_link: str = ""
    ostree_args: str = ""
    is_base_netinstall: bool = False
    is_default: bool = False
    is_featured: bool = False
