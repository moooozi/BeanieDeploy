import types

Megabyte = 1024 * 1024
Gigabyte = 1024 * 1024 * 1024
APP = types.SimpleNamespace()
APP.SW_NAME = "Lnixify"
APP.SW_VERSION = '0.1-alpha'
APP.minimal_required_space = 4 * Gigabyte
APP.dualboot_required_space = 35 * Gigabyte
APP.additional_failsafe_space = 2 * Gigabyte
APP.temp_part_failsafe_space = 0.15 * Gigabyte
APP.minimal_required_ram = 2 * Gigabyte
APP.linux_boot_partition_size = 1 * Gigabyte  # (minimum recommended 0.5)
APP.linux_efi_partition_size = 100 * Megabyte  # (recommended=200, minimum=50)
APP.default_efi_file_path = r"\EFI\BOOT\BOOTX64.EFI"
APP.FEDORA_GEO_IP_URL = 'https://geoip.fedoraproject.org/city'
APP.AVAILABLE_SPINS_LIST = 'https://gitlab.com/win2linux/lnitest/-/raw/main/fedora_spins.json'
APP.TPM2_TOOLS_RPM_DL_LINK = 'https://download.fedoraproject.org/pub/fedora/linux/releases/36/Everything/x86_64/os/Packages/t/tpm2-tools-5.2-2.fc36.x86_64.rpm'
APP.live_img_path = '/LiveOS/squashfs.img'
APP.live_img_url = 'file:///run/install/repo' + APP.live_img_path

LIVE_ISO_NAME = 'live_os.iso'
INSTALL_ISO_NAME = 'install_media.iso'

PATH = types.SimpleNamespace()
PATH.CURRENT_DIR = '%CURRENT_DIR%'
PATH.DOWNLOADS_DIR = '%DOWNLOADS_DIR%'
PATH.WORK_DIR = '%DOWNLOADS_DIR%\\win2linux_tmpdir'
PATH.RPM_SOURCE_DIR = PATH.WORK_DIR + '\\rpm'
PATH.GRUB_CONFIG_DEFUALT = '%CURRENT_DIR%\\resources\\grub_conf\\grub_default.cfg'
PATH.GRUB_CONFIG_AUTOINST = '%CURRENT_DIR%\\resources\\grub_conf\\grub_autoinst.cfg'
PATH.NVIDIA_SCRIPT = '%CURRENT_DIR%\\resources\\nvidia_inst'
PATH.ARIA2C = '%CURRENT_DIR%\\resources\\aria2c.exe'
PATH.LIVE_ISO = PATH.WORK_DIR + '\\' + LIVE_ISO_NAME
PATH.INSTALL_ISO = PATH.WORK_DIR + '\\' + INSTALL_ISO_NAME
PATH.RELATIVE_GRUB_CFG = r'EFI\BOOT\grub.cfg'
PATH.RELATIVE_NVIDIA_SCRIPT = r'lnixify\nvidia_inst'
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
KICKSTART.tpm_auto_unlock = True
KICKSTART.lang = ''
KICKSTART.timezone = ''
KICKSTART.keymap_type = ''
KICKSTART.keymap = ''
KICKSTART.ostree_args = ''
KICKSTART.wifi_profiles = []

PARTITION = types.SimpleNamespace()
PARTITION.shrink_space = APP.dualboot_required_space
PARTITION.tmp_part_size = None
PARTITION.temp_part_label = None
PARTITION.boot_part_size = None
PARTITION.efi_part_size = None

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
