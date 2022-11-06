import tkinter as tk
import globals as GV
from init import app as tkinter


desktop_var = tk.StringVar(tkinter, GV.UI.desktop)
export_wifi_toggle_var = tk.BooleanVar(tkinter, GV.INSTALL_OPTIONS.export_wifi)
enable_encryption_toggle_var = tk.BooleanVar(tkinter, GV.KICKSTART.is_encrypted)
encrypt_pass_toggle_var = tk.BooleanVar(tkinter)
custom_timezone_var = tk.StringVar(tkinter, GV.KICKSTART.timezone)
custom_keymap_var = tk.StringVar(tkinter)
keymap_timezone_source_var = tk.StringVar(tkinter, GV.INSTALL_OPTIONS.keymap_timezone_source)
job_var = tk.StringVar()
install_job_var = tk.StringVar(tkinter)
selected_locale = tk.StringVar(tkinter)


install_method_var = tk.StringVar(tkinter, GV.KICKSTART.partition_method)
dualboot_size_var = tk.StringVar(tkinter, 46)
restarting_text_var = tk.StringVar()
auto_restart_toggle_var = tk.BooleanVar(tkinter, GV.INSTALL_OPTIONS.auto_restart)
torrent_toggle_var = tk.BooleanVar(tkinter, GV.INSTALL_OPTIONS.torrent)
encrypt_passphrase_var = tk.StringVar(tkinter, GV.KICKSTART.passphrase)
encryption_tpm_unlock_toggle_var = tk.BooleanVar(tkinter, GV.KICKSTART.tpm_auto_unlock)
