import os
import winreg
from data_units import DataUnit
import functions as fn
import types


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


class CompatibilityResults:
    pass


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
COMPATIBILITY_RESULTS = CompatibilityResults()
IP_LOCALE = {}
ALL_SPINS = []
ACCEPTED_SPINS = []
ACCEPTED_ARCHITECTURES = ("amd64",)
AVAILABLE_INSTALL_METHODS = ("dualboot", "replace_win", "custom")
INSTALLER_STATUS = None
INSTALL_OPTIONS = InstallOptions()
KICKSTART = Kickstart()
PARTITION = Partition()
TMP_PARTITION_LETTER = ""
Literal = types
LIVE_OS_INSTALLER_SPIN = None
USERNAME_WINDOWS = ""
SELECTED_SPIN = None
UI = UI()

DUMMY_ALL_SPING = [
    {
        "name": "Fedora Workstation",
        "is_recommended": True,
        "is_default": True,
        "version": "36",
        "desktop": "GNOME",
        "size": 2018148352,
        "is_auto_installable": True,
        "is_live_img": True,
        "dl_link": "https://download.fedoraproject.org/pub/fedora/linux/releases/36/Workstation/x86_64/iso/Fedora-Workstation-Live-x86_64-36-1.5.iso",
        "hash256": "80169891cb10c679cdc31dc035dab9aae3e874395adc5229f0fe5cfcc111cc8c",
        "torrent_link": "https://torrent.fedoraproject.org/torrents/Fedora-Workstation-Live-x86_64-36.torrent",
    },
    {
        "name": "Fedora KDE Spin",
        "version": "36",
        "desktop": "KDE Plasma",
        "size": 2214592512,
        "is_auto_installable": True,
        "is_live_img": True,
        "dl_link": "https://download.fedoraproject.org/pub/fedora/linux/releases/36/Spins/x86_64/iso/Fedora-KDE-Live-x86_64-36-1.5.iso",
        "hash256": "b1da6062ee2e90695557f93a3e13a594884d8ab08ac48a93118eca68bc9108a8",
        "torrent_link": "https://torrent.fedoraproject.org/torrents/Fedora-KDE-Live-x86_64-36.torrent",
    },
    {
        "name": "Fedora Silverblue",
        "version": "36",
        "desktop": "GNOME",
        "size": 2762833920,
        "is_auto_installable": True,
        "dl_link": "https://download.fedoraproject.org/pub/fedora/linux/releases/36/Silverblue/x86_64/iso/Fedora-Silverblue-ostree-x86_64-36-1.5.iso",
        "hash256": "c8bac5756017c08135f7ff1be346584eba72e8c74e2842e7e1fc89dd26222dbe",
        "torrent_link": "https://torrent.fedoraproject.org/torrents/Fedora-Silverblue-ostree-x86_64-36.torrent",
        "ostree_args": '--osname="fedora" --remote="fedora" --url="file:///ostree/repo" --ref="fedora/36/x86_64/silverblue" --nogpg',
    },
    {
        "name": "Fedora Kinoite",
        "version": "36",
        "desktop": "KDE Plasma",
        "size": 2980511744,
        "is_auto_installable": True,
        "dl_link": "https://download.fedoraproject.org/pub/fedora/linux/releases/36/Kinoite/x86_64/iso/Fedora-Kinoite-ostree-x86_64-36-1.5.iso",
        "hash256": "9a7e538961ae22c0f85a88fed240dbdc8b82452340fe8a83d66c0c84c28813e4",
        "torrent_link": "https://torrent.fedoraproject.org/torrents/Fedora-Kinoite-ostree-x86_64-36.torrent",
        "ostree_args": '--osname="fedora" --remote="fedora" --url="file:///ostree/repo" --ref="fedora/36/x86_64/kinoite" --nogpg',
    },
    {
        "name": "Fedora Everything",
        "version": "36",
        "size": 702545920,
        "is_advanced": True,
        "is_base_netinstall": True,
        "dl_link": "https://download.fedoraproject.org/pub/fedora/linux/releases/36/Everything/x86_64/iso/Fedora-Everything-netinst-x86_64-36-1.5.iso",
        "hash256": "85cb450443d68d513b41e57b0bd818a740279dac5dfc09c68e681ff8a3006404",
    },
]
DUMMY_IP_LOCALE = {
    "time_zone": "Europe/Berlin",
    "country_code3": "DEU",
    "country_code": "DE",
    "country_name": "Germany",
}
