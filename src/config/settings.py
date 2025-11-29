"""
Application configuration management.
Replaces the chaotic globals.py with proper configuration handling.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import winreg
from enum import Enum


class PartitioningMethod(Enum):
    """Enumeration of available partitioning methods."""
    DUALBOOT = "dualboot"
    REPLACE_WIN = "replace_win"
    CUSTOM = "custom"


# Import DataUnit after enum to avoid circular import
from models.data_units import DataUnit


@dataclass(frozen=True)
class AppConfig:
    """Core application configuration."""
    
    name: str = "BeanieDeploy"
    version: str = "Snapshot"
    
    # Space requirements
    minimal_required_space: DataUnit = field(default_factory=lambda: DataUnit.from_gigabytes(4))
    dualboot_required_space: DataUnit = field(default_factory=lambda: DataUnit.from_gigabytes(35))
    additional_failsafe_space: DataUnit = field(default_factory=lambda: DataUnit.from_gigabytes(2))
    temp_part_failsafe_space: DataUnit = field(default_factory=lambda: DataUnit.from_gigabytes(0.15))
    
    # RAM requirements
    minimal_required_ram: DataUnit = field(default_factory=lambda: DataUnit.from_gigabytes(2))
    
    # Partition sizes
    linux_boot_partition_size: DataUnit = field(default_factory=lambda: DataUnit.from_gigabytes(1))
    linux_efi_partition_size: DataUnit = field(default_factory=lambda: DataUnit.from_megabytes(500))
    
    # Paths
    default_efi_file_path: str = r"\EFI\BOOT\BOOTX64.EFI"
    live_img_path: str = "/LiveOS/squashfs.img"
    
    # Directory names
    wifi_profiles_dir_name: str = "WIFI_PROFILES"
    
    # ISO filenames
    live_iso_name: str = "live_os.iso"
    install_iso_name: str = "install_media.iso"
    
    @property
    def live_img_url(self) -> str:
        return f"file:///run/install/repo{self.live_img_path}"


@dataclass(frozen=True)
class UrlConfig:
    """External URLs and endpoints."""
    
    fedora_geo_ip: str = "https://geoip.fedoraproject.org/city"
    fedora_torrent_download: str = "https://torrent.fedoraproject.org"
    available_spins_list: str = "https://fedoraproject.org/releases.json"
    
    # Specific package URLs


@dataclass
class PathConfig:
    """File and directory paths."""
    
    current_dir: Path = field(init=False)
    downloads_dir: Path = field(init=False)
    work_dir: Path = field(init=False)
    wifi_profiles_dir: Path = field(init=False)
    scripts_dir: Path = field(init=False)
    app_icon_path: Path = field(init=False)
    live_iso_path: Path = field(init=False)
    install_iso_path: Path = field(init=False)
    grub_cfg_relative: str = field(init=False)
    kickstart_relative: str = field(init=False)
    bootmgr_helper_relative: Path = field(init=False)
    
    def __post_init__(self):
        self.current_dir = Path(__file__).parent.parent
        self.downloads_dir = self._get_user_downloads_folder()
        self.work_dir = self.downloads_dir / "win2linux_tmpdir"
        self.wifi_profiles_dir = self.work_dir / "WIFI_PROFILES"
        self.scripts_dir = self.current_dir / "resources" / "scripts"
        self.app_icon_path = self.current_dir / "resources" / "style" / "app-icon.ico"
        self.live_iso_path = self.work_dir / "live_os.iso"
        self.install_iso_path = self.work_dir / "install_media.iso"
        self.grub_cfg_relative = r"EFI\BOOT\grub.cfg"
        self.kickstart_relative = "ks.cfg"
        self.bootmgr_helper_relative = self.current_dir / "resources" / "bootmgrhelper.exe"
    
    @staticmethod
    def _get_user_downloads_folder() -> Path:
        """Get the user's Downloads folder from Windows registry."""
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
            ) as key:
                downloads_dir = winreg.QueryValueEx(
                    key, "{374DE290-123F-4565-9164-39C4925E467B}"
                )[0]
                return Path(downloads_dir)
        except (OSError, FileNotFoundError):
            # Fallback to user's home directory
            return Path.home() / "Downloads"


@dataclass(frozen=True)
class SystemRequirementsConfig:
    """System requirements configuration."""
    
    # Space requirements for EFI files (measured 12.7MB for EFI directory + 5MB safety buffer)
    required_efi_space_mb: int = 18


@dataclass(frozen=True)
class UIConfig:
    """UI-related configuration."""
    
    # Window dimensions
    width: int = 850
    height: int = 580
    min_width: int = 800  # width - 50
    min_height: int = 530  # height - 50
    max_width: int = 1450  # width + 600
    max_height: int = 780  # height + 200
    width_offset: int = 400
    height_offset: int = 400
    top_frame_height: int = 80
    left_frame_width: int = 0
    
    # DPI scaling
    dpi_scaling_factor: float = 1.35
    
    # Fonts (calculated based on DPI)
    font_large: tuple[str, int] = field(init=False)
    font_medium: tuple[str, int] = field(init=False)
    font_small: tuple[str, int] = field(init=False)
    font_smaller: tuple[str, int] = field(init=False)
    font_tiny: tuple[str, int] = field(init=False)
    
    # Colors
    color_background: str = "#856ff8"
    color_red: str = "#e81123"
    color_blue: str = "#0067b8"
    color_green: str = "#008009"
    
    # Other UI settings
    max_width: int = 1000
    accepted_architectures: tuple[str, ...] = ("amd64",)
    
    def __post_init__(self):
        # Calculate fonts based on DPI scaling
        factor = self.dpi_scaling_factor
        object.__setattr__(self, 'font_large', ("Arial", int(24 * factor)))
        object.__setattr__(self, 'font_medium', ("Arial Bold", int(16 * factor)))
        object.__setattr__(self, 'font_small', ("Arial", int(13 * factor)))
        object.__setattr__(self, 'font_smaller', ("Arial", int(12 * factor)))
        object.__setattr__(self, 'font_tiny', ("Arial", int(11 * factor)))


class ConfigManager:
    """Centralized configuration manager to replace globals."""
    
    def __init__(self):
        self.app = AppConfig()
        self.urls = UrlConfig()
        self.paths = PathConfig()
        self.ui = UIConfig()
        self.system_requirements = SystemRequirementsConfig()
    
    @classmethod
    def create_default(cls) -> "ConfigManager":
        """Create a default configuration instance."""
        return cls()
    
    def update_version(self, version: str) -> None:
        """Update the application version."""
        # Since AppConfig is frozen, we need to replace it
        object.__setattr__(self.app, 'version', version)


# Global configuration instance (to be injected where needed)
_config: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = ConfigManager.create_default()
    return _config


def set_config(config: ConfigManager) -> None:
    """Set the global configuration instance (for testing)."""
    global _config
    _config = config
