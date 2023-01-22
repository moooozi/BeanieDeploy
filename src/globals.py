import types

Megabyte = 1024 * 1024
Gigabyte = 1024 * 1024 * 1024

APP_SW_NAME = "Lnixify"
APP_SW_VERSION = '0.1-alpha'
APP_minimal_required_space = 4 * Gigabyte
APP_dualboot_required_space = 35 * Gigabyte
APP_additional_failsafe_space = 2 * Gigabyte
APP_temp_part_failsafe_space = 0.15 * Gigabyte
APP_minimal_required_ram = 2 * Gigabyte
APP_linux_boot_partition_size = 1 * Gigabyte  # (minimum recommended 0.5)
APP_linux_efi_partition_size = 100 * Megabyte  # (recommended=200, minimum=50)
APP_default_efi_file_path = r"\EFI\BOOT\BOOTX64.EFI"
APP_FEDORA_GEO_IP_URL = 'https://geoip.fedoraproject.org/city'
APP_AVAILABLE_SPINS_LIST = 'https://gitlab.com/win2linux/lnitest/-/raw/main/fedora_spins.json'
APP_TPM2_TOOLS_RPM_DL_LINK = 'https://download.fedoraproject.org/pub/fedora/linux/releases/36/Everything/x86_64/os/Packages/t/tpm2-tools-5.2-2.fc36.x86_64.rpm'
APP_live_img_path = '/LiveOS/squashfs.img'
APP_live_img_url = 'file:///run/install/repo' + APP_live_img_path

LIVE_ISO_NAME = 'live_os.iso'
INSTALL_ISO_NAME = 'install_media.iso'

PATH = types.SimpleNamespace()
PATH.CURRENT_DIR = '%CURRENT_DIR%'
PATH.DOWNLOADS_DIR = '%DOWNLOADS_DIR%'
PATH.WORK_DIR = '%DOWNLOADS_DIR%\\win2linux_tmpdir'
PATH.RPM_SOURCE_DIR = PATH.WORK_DIR + '\\rpm'
PATH.ARIA2C = '%CURRENT_DIR%\\resources\\aria2c.exe'
PATH.LIVE_ISO = PATH.WORK_DIR + '\\' + LIVE_ISO_NAME
PATH.INSTALL_ISO = PATH.WORK_DIR + '\\' + INSTALL_ISO_NAME
PATH.RELATIVE_GRUB_CFG = r'EFI\BOOT\grub.cfg'
PATH.RPM_DEST_DIR_NAME = 'ADDITIONAL_RPMs'
PATH.RELATIVE_KICKSTART = 'ks.cfg'

COMPATIBILITY_RESULTS = types.SimpleNamespace()
IP_LOCALE = {}
ALL_SPINS = []
ACCEPTED_SPINS = []

ACCEPTED_ARCHITECTURES = ('amd64',)
AVAILABLE_INSTALL_METHODS = ('dualboot', 'clean', 'custom')
INSTALLER_STATUS = None

INSTALL_OPTIONS = types.SimpleNamespace()
INSTALL_OPTIONS.spin_index = -1
INSTALL_OPTIONS.auto_restart = False
INSTALL_OPTIONS.torrent = False
INSTALL_OPTIONS.export_wifi = True
INSTALL_OPTIONS.keymap_timezone_source = 'select'

KICKSTART = types.SimpleNamespace()
KICKSTART.partition_method = ''
KICKSTART.live_img_url = ''
KICKSTART.is_encrypted = False
KICKSTART.passphrase = ''
KICKSTART.tpm_auto_unlock = False
KICKSTART.lang = ''
KICKSTART.timezone = ''
KICKSTART.keymap_type = ''
KICKSTART.keymap = ''
KICKSTART.ostree_args = ''
KICKSTART.wifi_profiles = []

PARTITION = types.SimpleNamespace()
PARTITION.make_root_partition = False
PARTITION.shrink_space = None
PARTITION.tmp_part_size = 0
PARTITION.temp_part_label = 0
PARTITION.boot_part_size = 0
PARTITION.efi_part_size = 0

TMP_PARTITION_LETTER = ''
TMP_PARTITION_LABEL = 'FEDORA-INST'  # Max 12 Chars
Literal: types
LIVE_OS_INSTALLER_SPIN = None
USERNAME_WINDOWS = ''
SELECTED_SPIN = None

UI = types.SimpleNamespace()
UI.DI_VAR = {'w': 'w', 'e': 'e', 'ne': 'ne', 'se': 'se', 'sw': 'sw', 'nw': 'nw', 'l': 'left', 'r': 'right'}
UI.desktop = 'unset'
UI.combo_list_spin = ''
UI.width = 1000


DUMMY_ALL_SPING = [{'name': 'Fedora Workstation', 'version': '36', 'desktop': 'GNOME', 'size': 2018148352, 'is_auto_installable': True, 'is_live_img': True, 'dl_link': 'https://download.fedoraproject.org/pub/fedora/linux/releases/36/Workstation/x86_64/iso/Fedora-Workstation-Live-x86_64-36-1.5.iso', 'hash256': '80169891cb10c679cdc31dc035dab9aae3e874395adc5229f0fe5cfcc111cc8c', 'torrent_link': 'https://torrent.fedoraproject.org/torrents/Fedora-Workstation-Live-x86_64-36.torrent'}, {'name': 'Fedora KDE Spin', 'version': '36', 'desktop': 'KDE Plasma', 'size': 2214592512, 'is_auto_installable': True, 'is_live_img': True, 'dl_link': 'https://download.fedoraproject.org/pub/fedora/linux/releases/36/Spins/x86_64/iso/Fedora-KDE-Live-x86_64-36-1.5.iso', 'hash256': 'b1da6062ee2e90695557f93a3e13a594884d8ab08ac48a93118eca68bc9108a8', 'torrent_link': 'https://torrent.fedoraproject.org/torrents/Fedora-KDE-Live-x86_64-36.torrent'}, {'name': 'Fedora Silverblue', 'version': '36', 'desktop': 'GNOME', 'size': 2762833920, 'is_auto_installable': True, 'dl_link': 'https://download.fedoraproject.org/pub/fedora/linux/releases/36/Silverblue/x86_64/iso/Fedora-Silverblue-ostree-x86_64-36-1.5.iso', 'hash256': 'c8bac5756017c08135f7ff1be346584eba72e8c74e2842e7e1fc89dd26222dbe', 'torrent_link': 'https://torrent.fedoraproject.org/torrents/Fedora-Silverblue-ostree-x86_64-36.torrent', 'ostree_args': '--osname="fedora" --remote="fedora" --url="file:///ostree/repo" --ref="fedora/36/x86_64/silverblue" --nogpg'}, {'name': 'Fedora Kinoite', 'version': '36', 'desktop': 'KDE Plasma', 'size': 2980511744, 'is_auto_installable': True, 'dl_link': 'https://download.fedoraproject.org/pub/fedora/linux/releases/36/Kinoite/x86_64/iso/Fedora-Kinoite-ostree-x86_64-36-1.5.iso', 'hash256': '9a7e538961ae22c0f85a88fed240dbdc8b82452340fe8a83d66c0c84c28813e4', 'torrent_link': 'https://torrent.fedoraproject.org/torrents/Fedora-Kinoite-ostree-x86_64-36.torrent', 'ostree_args': '--osname="fedora" --remote="fedora" --url="file:///ostree/repo" --ref="fedora/36/x86_64/kinoite" --nogpg'}, {'name': 'Fedora Everything', 'version': '36', 'size': 702545920, 'is_advanced': True, 'is_base_netinstall': True, 'dl_link': 'https://download.fedoraproject.org/pub/fedora/linux/releases/36/Everything/x86_64/iso/Fedora-Everything-netinst-x86_64-36-1.5.iso', 'hash256': '85cb450443d68d513b41e57b0bd818a740279dac5dfc09c68e681ff8a3006404'}]
DUMMY_IP_LOCALE = {"time_zone": "Europe/Berlin", "country_code3": "DEU", "country_code": "DE", "country_name": "Germany"}