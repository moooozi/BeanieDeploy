SW_NAME = "Lnixify"
minimal_required_space = 4  # Gigabyte
dualboot_required_space = 35  # Gigabyte
additional_failsafe_space = 2  # Gigabyte
temp_part_failsafe_space = 0.15  # Gigabyte
minimal_required_ram = 5.5  # Gigabyte
linux_boot_partition_size = 1  # Gigabyte
linux_efi_partition_size = 100  # Megabyte
default_efi_file_path = r"\EFI\BOOT\BOOTX64.EFI"

distros = {
    'name': ('Fedora Silverblue', 'Fedora Kinoite', 'Fedora Everything'),
    'version': ('36', '36', '36'),
    'de': ('GNOME', 'KDE', ''),
    'size': (2.6, 2.8, 0.8),
    'auto-installable': (True, True, False),
    'recommended': (False, False, False),
    'advanced': (False, False, True),
    'netinstall': (False, False, True),
    'dl_link':
        (
        'https://download.fedoraproject.org/pub/fedora/linux/releases/36/Silverblue/x86_64/iso/Fedora-Silverblue-ostree-x86_64-36-1.5.iso',
        'https://download.fedoraproject.org/pub/fedora/linux/releases/36/Kinoite/x86_64/iso/Fedora-Kinoite-ostree-x86_64-36-1.5.iso',
        'https://download.fedoraproject.org/pub/fedora/linux/releases/36/Everything/x86_64/iso/Fedora-Everything-netinst-x86_64-36-1.5.iso'
        ),
    'hash256': ('c8bac5756017c08135f7ff1be346584eba72e8c74e2842e7e1fc89dd26222dbe',
                '9a7e538961ae22c0f85a88fed240dbdc8b82452340fe8a83d66c0c84c28813e4',
                '85cb450443d68d513b41e57b0bd818a740279dac5dfc09c68e681ff8a3006404'),
    'torrent': ('https://torrent.fedoraproject.org/torrents/Fedora-Silverblue-ostree-x86_64-36.torrent',
                'https://torrent.fedoraproject.org/torrents/Fedora-Kinoite-ostree-x86_64-36.torrent',
                ''),
    'ostree': ('--osname="fedora" --remote="fedora" --url="file:///ostree/repo" --ref="fedora/36/x86_64/silverblue" --nogpg',
               '--osname="fedora" --remote="fedora" --url="file:///ostree/repo" --ref="fedora/36/x86_64/kinoite" --nogpg',
               ''),
}
