from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.partition import PartitioningMethod


@dataclass
class PartitioningConfig:
    method: PartitioningMethod | None = None
    is_encrypted: bool = False
    passphrase: str = ""
    root_guid: str | None = None
    boot_guid: str | None = None
    sys_disk_uuid: str | None = None
    sys_drive_uuid: str | None = None
    sys_efi_uuid: str | None = None
    tmp_part_uuid: str | None = None


@dataclass
class LocaleConfig:
    locale: str = ""
    timezone: str = ""
    keymaps: list[str] = field(default_factory=list)


@dataclass
class KickstartConfig:
    partitioning: PartitioningConfig = field(default_factory=PartitioningConfig)
    locale_settings: LocaleConfig = field(default_factory=LocaleConfig)
    live_img_url: str = ""
    ostree_args: str = ""
    wifi_profiles_dir_name: str | None = None
    user_full_name: str = ""
    user_username: str = ""
