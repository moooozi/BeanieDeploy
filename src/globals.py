import os
from typing import List
import winreg
from compatibility_checks import Check
from data_units import DataUnit
import functions as fn
import types

from models.spin import Spin


APP_SW_NAME = "BeanieDeploy"
APP_SW_VERSION = "Snapshot"
APP_MINIMAL_REQUIRED_SPACE = DataUnit.from_gigabytes(4)
APP_DUALBOOT_REQUIRED_SPACE = DataUnit.from_gigabytes(35)
APP_ADDITIONAL_FAILSAFE_SPACE = DataUnit.from_gigabytes(2)
APP_TEMP_PART_FAILSAFE_SPACE = DataUnit.from_gigabytes(0.15)
APP_MINIMAL_REQUIRED_RAM = DataUnit.from_gigabytes(2)
APP_LINUX_BOOT_PARTITION_SIZE = DataUnit.from_gigabytes(1)
APP_LINUX_EFI_PARTITION_SIZE = DataUnit.from_megabytes(500)
APP_DEFAULT_EFI_FILE_PATH = r"\EFI\BOOT\BOOTX64.EFI"
APP_FEDORA_GEO_IP_URL = "https://geoip.fedoraproject.org/city"
FEDORA_BASE_DOWNLOAD_URL = "https://download.fedoraproject.org"
FEDORA_TORRENT_DOWNLOAD_URL = "https://torrent.fedoraproject.org"
APP_AVAILABLE_SPINS_LIST = (
    "https://gitlab.com/win2linux/lnitest/-/raw/main/fedora_spins.json"
)
RPM_FUSION_FREE = (
    "https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-%s.noarch.rpm"
)
RPM_FUSION_NON_FREE = "https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-%s.noarch.rpm"
APP_TPM2_TOOLS_RPM_DL_LINK = "https://download.fedoraproject.org/pub/fedora/linux/releases/36/Everything/x86_64/os/Packages/t/tpm2-tools-5.2-2.fc36.x86_64.rpm"
APP_LIVE_IMG_PATH = "/LiveOS/squashfs.img"
APP_LIVE_IMG_URL = "file:///run/install/repo" + APP_LIVE_IMG_PATH

LIVE_ISO_NAME = "live_os.iso"
INSTALL_ISO_NAME = "install_media.iso"

ADDITIONAL_RPM_DIR_NAME = "ADDITIONAL_RPMs"
WIFI_PROFILES_DIR_NAME = "WIFI_PROFILES"


class PathConfig:
    def __init__(self):
        self.CURRENT_DIR = os.path.dirname(__file__)
        self.DOWNLOADS_DIR = self._get_user_downloads_folder()
        self.WORK_DIR = f"{self.DOWNLOADS_DIR}\\win2linux_tmpdir"
        self.WIFI_PROFILES_DIR = f"{self.WORK_DIR}\\{WIFI_PROFILES_DIR_NAME}"
        self.RPM_SOURCE_DIR = rf"{self.WORK_DIR}\{ADDITIONAL_RPM_DIR_NAME}"
        self.SCRIPTS = rf"{self.CURRENT_DIR}\resources\\scripts"
        self.APP_ICON = rf"{self.CURRENT_DIR}\resources\\style\\app-icon.ico"
        self.LIVE_ISO = rf"{self.WORK_DIR}\{LIVE_ISO_NAME}"
        self.INSTALL_ISO = rf"{self.WORK_DIR}\{INSTALL_ISO_NAME}"
        self.RELATIVE_GRUB_CFG = r"EFI\BOOT\grub.cfg"
        self.RELATIVE_KICKSTART = "ks.cfg"
        self.RELATIVE_BOOTMGR_HELPER = (
            rf"{self.CURRENT_DIR}\resources\\bootmgrhelper.exe"
        )

    @staticmethod
    def _get_user_downloads_folder():
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
        ) as key:
            downloads_dir = winreg.QueryValueEx(
                key, "{374DE290-123F-4565-9164-39C4925E467B}"
            )[0]
        return downloads_dir


class InstallOptions:
    def __init__(self):
        self.spin_index = -1
        self.auto_restart = False
        self.torrent = False
        self.export_wifi = True


class Kickstart:
    def __init__(self):
        self.partition_method = ""
        self.live_img_url = APP_LIVE_IMG_URL
        self.is_encrypted = False
        self.passphrase = ""
        self.tpm_auto_unlock = False
        self.locale = ""
        self.timezone = ""
        self.keymap_type = ""
        self.keymap = ""
        self.ostree_args = ""
        self.fullname = ""
        self.username = ""
        self.wifi_profiles_dir_name = []
        self.enable_rpm_fusion = False


class Partition:
    def __init__(self):
        self.make_root_partition = False
        self.shrink_space = None
        self.tmp_part_size = 0
        self.temp_part_label = "FEDORA-INST"  # Max 12 Chars
        self.boot_part_size = 0
        self.efi_part_size = 0


class UI:
    def __init__(self):
        self.DI_VAR = {
            "w": "w",
            "e": "w",
            "ne": "ne",
            "nw": "nw",
            "se": "se",
            "sw": "sw",
            "nse": "nse",
            "nsw": "nsw",
            "l": "left",
            "r": "right",
        }
        self.desktop = ""
        self.combo_list_spin = ""
        self.width = 1000


PATH = PathConfig()
DONE_CHECKS = None
IP_LOCALE = {}
ALL_SPINS = []
ACCEPTED_SPINS: List[Spin] = []
ACCEPTED_ARCHITECTURES = ("amd64",)
AVAILABLE_INSTALL_METHODS = ("dualboot", "replace_win", "custom")
INSTALLER_STATUS = None
INSTALL_OPTIONS = InstallOptions()
KICKSTART = Kickstart()
PARTITION = Partition()
TMP_PARTITION_LETTER = ""
LIVE_OS_INSTALLER_SPIN: Spin = None
SELECTED_SPIN: Spin = None

USERNAME_WINDOWS = ""
UI = UI()
