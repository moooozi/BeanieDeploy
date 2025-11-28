from dataclasses import dataclass
from typing import Optional


@dataclass
class Kickstart:
    partition_method: str = ""
    live_img_url: str = ""
    is_encrypted: bool = False
    passphrase: str = ""
    tpm_auto_unlock: bool = False
    locale: str = ""
    timezone: str = ""
    keymap_type: str = ""
    keymap: str = ""
    ostree_args: str = ""
    wifi_profiles_dir_name: Optional[list] = None
    root_guid: Optional[str] = None
    boot_guid: Optional[str] = None

    def __post_init__(self):
        if self.wifi_profiles_dir_name is None:
            self.wifi_profiles_dir_name = []
