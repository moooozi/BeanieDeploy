SW_NAME = "Lnixify"

minimal_required_space = 0.8
minimal_equired_ram = 4

default_efi_file_path = "\EFI\BOOT\BOOTX64.EFI"
distros = [
 # (name, version, DE, iso size, is auto-installable?, is recommended?, is advanced? , '', direct-dl-link, torrent-file-link )
 # ( 0  ,    1   , 2 ,    3    ,           4         ,       5        ,        6     , 7 ,     8         ,         9         )
 ('Fedora Silverblue', '36', 'GNOME', 2.7, True, True, False, '',
  'https://dl.fedoraproject.org/pub/fedora/linux/development/36/Silverblue/x86_64/iso/Fedora-Silverblue-ostree-x86_64-36-20220416.n.0.iso',
  'https://torrent.fedoraproject.org/torrents/Fedora-Silverblue-ostree-x86_64-36_Beta.torrent'),

 ('Fedora Kinoite', '36', 'KDE', 2.9, True, False, False, '',
  'https://dl.fedoraproject.org/pub/fedora/linux/development/36/Kinoite/x86_64/iso/Fedora-Kinoite-ostree-x86_64-36-20220416.n.0.iso',
  'https://torrent.fedoraproject.org/torrents/Fedora-Kinoite-ostree-x86_64-36_Beta.torrent'),

 ('Fedora Everything', '36', 'Net-install', 0.75, False, False, True, '',
  'https://dl.fedoraproject.org/pub/fedora/linux/development/36/Kinoite/x86_64/iso/Fedora-Kinoite-ostree-x86_64-36-20220416.n.0.iso',
  ''),

]
required_ram = 4
efi_file_path = "\EFI\BOOT\BOOTX64.EFI"
