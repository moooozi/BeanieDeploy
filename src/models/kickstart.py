from dataclasses import dataclass, field
from typing import Optional, Literal

from config.settings import PartitioningMethod


@dataclass
class PartitioningConfig:
    method: Optional[PartitioningMethod] = None
    is_encrypted: bool = False
    passphrase: str = ""
    root_guid: Optional[str] = None
    boot_guid: Optional[str] = None
    sys_drive_uuid: Optional[str] = None
    sys_efi_uuid: Optional[str] = None


@dataclass
class LocaleConfig:
    locale: str = ""
    timezone: str = ""
    keymap_type: Literal["vc", "xlayout"] = "vc"
    keymap: str = ""


@dataclass
class KickstartConfig:
    partitioning: PartitioningConfig = field(default_factory=PartitioningConfig)
    locale_settings: LocaleConfig = field(default_factory=LocaleConfig)
    live_img_url: str = ""
    ostree_args: str = ""
    wifi_profiles_dir_name: Optional[str] = None
