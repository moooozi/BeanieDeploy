import types
import APP_INFO

PATH = types.SimpleNamespace()
PATH.CURRENT_DIR = '%CURRENT_DIR%'
PATH.DOWNLOADS_DIR = '%DOWNLOADS_DIR%'
PATH.WORK_DIR = '%DOWNLOADS_DIR%\\win2linux_tmpdir'
PATH.GRUB_CONFIG_DEFUALT = '%CURRENT_DIR%\\resources\\grub_conf\\grub_default.cfg'
PATH.GRUB_CONFIG_AUTOINST = '%CURRENT_DIR%\\resources\\grub_conf\\grub_autoinst.cfg'
PATH.NVIDIA_SCRIPT = '%CURRENT_DIR%\\resources\\nvidia_inst'
PATH.ARIA2C = '%CURRENT_DIR%\\resources\\aria2c.exe'
PATH.LIVE_ISO = PATH.WORK_DIR + '\\live_os.iso'
PATH.INSTALL_ISO = PATH.WORK_DIR + '\\install_media.iso'
PATH.RELATIVE_GRUB_CFG = r'EFI\BOOT\grub.cfg'
PATH.RELATIVE_NVIDIA_SCRIPT = r'lnixify\nvidia_inst'
PATH.RELATIVE_KICKSTART = 'ks.cfg'
COMPATIBILITY_RESULTS = types.SimpleNamespace()
IP_LOCALE = {}

ACCEPTED_ARCHITECTURES = ('amd64',)
AVAILABLE_INSTALL_METHODS = ('dualboot', 'clean', 'custom')
INSTALLER_STATUS = None
INSTALL_OPTIONS = types.SimpleNamespace(install_method='', spin_index=-1, auto_restart=False, torrent=False, live_img_url='')
AUTOINST = types.SimpleNamespace(dualboot_size=APP_INFO.dualboot_required_space, export_wifi=True,
                                 enable_encryption=False, encryption_pass='', encryption_tpm_unlock=True,
                                 locale='', timezone='', keymap_timezone_source='select', keymap='', keymap_type='',
                                 username='', fullname='')
TMP_PARTITION_LETTER = ''
TMP_PARTITION_LABEL = 'FEDORA-INST'  # Max 12 Chars
ALL_SPINS = []
ACCEPTED_SPINS = []
LIVE_OS_INSTALLER_SPIN = None
USERNAME_WINDOWS = ''

SELECTED_SPIN = None

UI = types.SimpleNamespace()
UI.DI_VAR = {'w': 'w', 'e': 'e', 'ne': 'ne', 'se': 'se', 'sw': 'sw', 'nw': 'nw', 'l': 'left', 'r': 'right'}
UI.desktop = 'unset'
UI.combo_list_spin = ''
