"""
Application configuration management.
Replaces the chaotic globals.py with proper configuration handling.
"""

import winreg
from dataclasses import dataclass, field
from pathlib import Path

# import multilingual  # Moved to property to avoid circular import
from models.data_units import DataUnit


@dataclass(frozen=True)
class AppConfig:
    """Core application configuration."""

    name: str = "BeanieDeploy"
    version: str = "Snapshot"
    supported_version: str = "43"  # Supported Fedora version

    # Space requirements
    minimal_required_space: DataUnit = field(
        default_factory=lambda: DataUnit.from_gigabytes(4)
    )
    dualboot_required_space: DataUnit = field(
        default_factory=lambda: DataUnit.from_gigabytes(35)
    )
    additional_failsafe_space: DataUnit = field(
        default_factory=lambda: DataUnit.from_gigabytes(2)
    )
    temp_part_failsafe_space: DataUnit = field(
        default_factory=lambda: DataUnit.from_gigabytes(0.15)
    )

    # RAM requirements
    minimal_required_ram: DataUnit = field(
        default_factory=lambda: DataUnit.from_gigabytes(2)
    )

    # Partition sizes
    linux_boot_partition_size: DataUnit = field(
        default_factory=lambda: DataUnit.from_gigabytes(1)
    )
    linux_efi_partition_size: DataUnit = field(
        default_factory=lambda: DataUnit.from_megabytes(500)
    )

    # Paths
    default_efi_file_path: str = r"\EFI\BOOT\BOOTX64.EFI"
    live_img_path: str = "LiveOS/squashfs.img"

    # Directory names
    wifi_profiles_dir_name: str = "WIFI_PROFILES"

    # ISO filenames
    live_iso_name: str = "live_os.iso"
    install_iso_name: str = "install_media.iso"

    @property
    def live_img_url(self) -> str:
        return f"file:///run/install/repo/{self.live_img_path}"


@dataclass(frozen=True)
class UrlConfig:
    """External URLs and endpoints."""

    fedora_geo_ip: str = "https://geoip.fedoraproject.org/city"
    fedora_torrent_download: str = "https://torrent.fedoraproject.org"
    available_spins_list: str = "https://fedoraproject.org/releases.json"

    # Specific package URLs


@dataclass(frozen=True)
class PathConfig:
    """File and directory paths."""

    @property
    def current_dir(self) -> Path:
        return Path(__file__).parent.parent

    @property
    def downloads_dir(self) -> Path:
        return self._get_user_downloads_folder()

    @property
    def work_dir(self) -> Path:
        return self.downloads_dir / "win2linux_tmpdir"

    @property
    def wifi_profiles_dir(self) -> Path:
        return self.work_dir / "WIFI_PROFILES"

    @property
    def app_icon_path(self) -> Path:
        return self.current_dir / "resources" / "style" / "app-icon.ico"

    @property
    def grub_cfg_relative(self) -> str:
        return r"EFI\BOOT\grub.cfg"

    @property
    def kickstart_relative(self) -> str:
        return "ks.cfg"

    @property
    def install_helpers_dir(self) -> Path:
        return self.current_dir / "resources" / "install-helpers"

    @property
    def install_helpers_ks_dir(self) -> Path:
        return self.install_helpers_dir / "ks-templates"

    @property
    def install_helpers_scripts_dir(self) -> Path:
        return self.install_helpers_dir / "scripts"

    @property
    def log_dir(self) -> str:
        return "/tmp/beanie_logs"

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


Color = tuple[str, str]


@dataclass(frozen=True)
class ColorConfig:
    """Color configuration with light and dark variants."""

    background: Color = ("#E2E2E2", "#181818")
    btn_background: Color = ("#C8C8C8", "#2D2D2D")
    btn_background_hover: Color = ("#BFBFBF", "#3A3A3A")
    btn_background_txt: Color = ("#000000", "#FFFFFF")
    element_bg: Color = ("#CFCFCF", "#212121")
    element_bg_hover: Color = ("#C2C2C2", "#2A2A2A")
    red: Color = ("#e81123", "#ff4a4a")
    green: Color = ("#008009", "#5dd25e")
    primary: Color = ("#3B8ED0", "#2171B0")


@dataclass(frozen=True)
class FontsConfig:
    """Font configuration."""

    large: tuple[str, int] = ("Roboto Bold", 26)
    medium: tuple[str, int] = ("Roboto Bold", 22)
    small: tuple[str, int] = ("Roboto", 18)
    smaller: tuple[str, int] = ("Roboto", 16)
    tiny: tuple[str, int] = ("Roboto", 13)


@dataclass(frozen=True)
class UIConfig:
    """UI-related configuration."""

    # Window dimensions
    width: int = 850
    height: int = 580
    margin_bottom: int = 10
    margin_button_bar: int = 10
    margin_side: int = 20
    margin_title_top: int = 40
    margin_title_bottom: int = 20
    # Colors
    colors: ColorConfig = field(default_factory=lambda: ColorConfig())
    fonts: FontsConfig = field(default_factory=lambda: FontsConfig())

    # Other UI settings
    accepted_architectures: tuple[str, ...] = ("amd64",)

    @property
    def di(self):
        import multilingual

        return multilingual.get_di_var()


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
        object.__setattr__(self.app, "version", version)


# Global configuration instance (to be injected where needed)
_config: ConfigManager | None = None


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
