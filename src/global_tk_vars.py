import tkinter as tk
import globals as GV
import main

distro_var = tk.StringVar(main.app, GV.UI.desktop)
export_wifi_toggle_var = tk.BooleanVar(main.app, GV.INSTALL_OPTIONS.export_wifi)
rpm_fusion_toggle_var = tk.BooleanVar(main.app, GV.KICKSTART.enable_rpm_fusion)
enable_encryption_toggle_var = tk.BooleanVar(main.app, GV.KICKSTART.is_encrypted)
encrypt_pass_toggle_var = tk.BooleanVar(main.app)
custom_timezone_var = tk.StringVar(main.app, GV.KICKSTART.timezone)
custom_keymap_var = tk.StringVar(main.app)
job_var = tk.StringVar()
install_job_var = tk.StringVar(main.app)
# selected_locale = tk.StringVar(main.app)

install_method_var = tk.StringVar(main.app, GV.KICKSTART.partition_method)
dualboot_size_var = tk.StringVar(main.app)
restarting_text_var = tk.StringVar()
auto_restart_toggle_var = tk.BooleanVar(main.app, GV.INSTALL_OPTIONS.auto_restart)
torrent_toggle_var = tk.BooleanVar(main.app, GV.INSTALL_OPTIONS.torrent)
encrypt_passphrase_var = tk.StringVar(main.app, GV.KICKSTART.passphrase)
encryption_tpm_unlock_toggle_var = tk.BooleanVar(main.app, GV.KICKSTART.tpm_auto_unlock)

fullname = tk.StringVar(main.app, GV.KICKSTART.fullname)
username = tk.StringVar(main.app, GV.KICKSTART.username)
