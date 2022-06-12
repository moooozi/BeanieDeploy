SW_NAME = "Lnixify"
SW_VERSION = '0.1-alpha'
minimal_required_space = 4  # Gigabyte
dualboot_required_space = 35  # Gigabyte
additional_failsafe_space = 2  # Gigabyte
temp_part_failsafe_space = 0.15  # Gigabyte
minimal_required_ram = 4  # Gigabyte
linux_boot_partition_size = 1  # Gigabyte (minimum recommended 0.5)
linux_efi_partition_size = 100  # Megabyte (recommended=200, minimum=50)
default_efi_file_path = r"\EFI\BOOT\BOOTX64.EFI"
FEDORA_GEO_IP_URL = 'https://geoip.fedoraproject.org/city'
AVAILABLE_SPINS_LIST = 'https://gitlab.com/win2linux/lnitest/-/raw/main/fedora_spins.json'
live_img_path = '/LiveOS/squashfs.img'
live_img_url = 'file:///run/install/repo' + live_img_path
