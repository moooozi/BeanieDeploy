from types import SimpleNamespace

INSTALL_OPTIONS = {'spin': {}, 'spin_index': -1, 'auto_restart': False, 'torrent': False, 'live_img_url': ''}
AUTOINST = {'is_on': True, 'method': '', 'dualboot_size': 'bb',
            'export_wifi': True, 'enable_encryption': False, 'encryption_pass': '',
            'locale': '', 'timezone': '', 'keymap_timezone_source': 'select', 'keymap': '', 'keymap_type': '',
            'username': '', 'fullname': ''}
ss = SimpleNamespace(**AUTOINST)


print(ss)