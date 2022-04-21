import urllib.request

SW_NAME = "Lnixify"

minimal_required_space = 0.8  # Gigabyte
dualboot_required_space = 6450  # Gigabyte
minimal_required_ram = 5.5  # Gigabyte
default_efi_file_path = "\EFI\BOOT\BOOTX64.EFI"
url = "https://speed.hetzner.de/100MB.bin"

distros = {
    'name': ('Fedora Silverblue', 'Fedora Kinoite', 'Fedora Everything'),
    'version': ('36', '36', '36'),
    'de': ('GNOME', 'KDE', ''),
    'size': [0, 0, 0],
    'auto-installable': (True, True, False),
    'recommended': (True, False, False),
    'advanced': (False, False, True),
    'netinstall': (False, False, True),
    'dl_link':
        (
        'https://download.fedoraproject.org/pub/fedora/linux/releases/35/Silverblue/x86_64/iso/Fedora-Silverblue-ostree-x86_64-35-1.2.iso',
        'https://download.fedoraproject.org/pub/fedora/linux/releases/35/Kinoite/x86_64/iso/Fedora-Kinoite-ostree-x86_64-35-1.2.iso',
        'https://download.fedoraproject.org/pub/fedora/linux/releases/35/Everything/x86_64/iso/Fedora-Everything-netinst-x86_64-35-1.2.iso'),
    'hash256': ('76a2b19ae9b49a6647c8b7cda37f6002c109d89771c3b673498d19974c0626a0',
                '',
                ''),
    'torrent': ('',
                '',
                '')
}

# Update sizes
def update_sizes(dists):
    for i, distro in enumerate(dists):
        dists[i][3] = urllib.request.urlopen(distro[8]).length
        return dists
