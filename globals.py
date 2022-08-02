from types import SimpleNamespace

import APP_INFO


GRUB_CONFIG_PATH_DEFUALT = '%CURRENT_DIR%\\resources\\grub_conf\\grub_default.cfg'
GRUB_CONFIG_PATH_AUTOINST = '%CURRENT_DIR%\\resources\\grub_conf\\grub_autoinst.cfg'
NVIDIA_SCRIPT_PATH = '%CURRENT_DIR%\\resources\\nvidia_inst'

COMPATIBILITY_RESULTS = {}
COMPATIBILITY_CHECK_STATUS = 0
INSTALLER_STATUS = None
IP_LOCALE = []
INSTALL_OPTIONS = SimpleNamespace(spin={}, spin_index=-1, auto_restart=False, torrent=False, live_img_url='')
AUTOINST = SimpleNamespace(is_on=True, method='', dualboot_size=APP_INFO.dualboot_required_space, export_wifi=True,
                           enable_encryption=False, encryption_pass='', locale='', timezone='',
                           keymap_timezone_source='select', keymap='', keymap_type='', username='', fullname='')
DOWNLOAD_PATH = ''
INSTALL_ISO_NAME = 'install_media.iso'
LIVE_ISO_NAME = 'live_os.iso'
LIVE_ISO_PATH = ''
INSTALL_ISO_PATH = ''
TMP_PARTITION_LETTER = ''
ARIA2C_LOCATION = ''
TMP_PARTITION_LABEL = 'FEDORA-INST'  # Max 12 Chars


# Tkinter variables, the '_t' suffix means Toggle
ALL_SPINS = []
ACCEPTED_SPINS = []
LIVE_OS_INSTALLER_SPIN = None
# autoinstaller variables
USERNAME_WINDOWS = ''
