
btn_next = "Next"
btn_yes = "Yes"
btn_no = "No"
btn_back = "Back"
btn_quit = "Quit"
btn_cancel = "Cancel"
btn_continue = "Continue"
btn_abort = "Abort"
btn_confirm = "Confirm"
btn_install = "Install"
btn_restart_now = "Restart now"
btn_restart_later = "Restart later"
btn_retry = "Retry"

check_available_downloads = "Checking available downloads"
check_existing_download_files = "Checking for existing files from previous installs"
check_running = "Checking System compatibility. please wait..."
check_ram = "Checking available RAM capacity"
check_uefi = "Checking UEFI compliance"
check_space = "Checking available space"
check_resizable = "Checking system drive resizability"

error_title = "%s can't run on your system"
error_list = "Following issues detected:"
error_arch_0 = "This device's CPU architecture is incompatible."
error_arch_9 = "CPU architecture could not be verified."
error_uefi_0 = "Your system does not support (or is not using) UEFI boot."
error_uefi_9 = "UEFI boot support could not be verified."
error_totalram_0 = "Your system does not have sufficient RAM capacity."
error_totalram_9 = "Failed to check available RAM capacity."
error_space_0 = "Not enough space on your system drive. Free up space and try again"
error_space_9 = "Failed to check available disk space on your system drive."
error_resizable_0 = "Not enough shrink room on system drive."
error_resizable_9 = "Failed to check system drive resizability."

startup_sentence = "Let's get started. "
desktop_question = "Which Desktop Environment do you prefer?"
desktop_hints = {'KDE Plasma': "Powerful, highly customizable and feature-rich, Windows-like layout by default",
                 'GNOME': "Default for Fedora. Minimal and stable, touchpad & touchscreen optimized"}
lang = "Language"
locale = "Locale"
recommended = "Recommended"
adv = "Advanced"
net_install = "Network Install"
warn_space = "Not enough space"
warn_not_available = "Not available"
total_download = "Total download: %sGB"
init_download = "Initial download: %sGB"

install_running = "Installing..."
install_auto = "Quick & guided install"
install_help = "Help me decide"
title_autoinst2 = "Choose your language and locale"
title_autoinst3 = "Choose your timezone and keyboard layout"
title_autoinst4 = "Create your local user account"

additional_setup_now = "Setup your locale, Timezone and keyboard layout now"

selected_spin = "Selected Spin"
choose_fedora_spin = "Choose a Fedora Spin"
encrypted_root = "Encrypt the new operating system"
entry_encrypt_passphrase = "Set encryption passphrase"

encrypt_reminder_txt = "You will be asked to enter encryption passphase before the installation begins"
encryption_tpm_unlock = "Auto-unlock with TPM2"

entry_username = "Username"
entry_fullname = "Full name (optional)"
password_reminder_txt = "(You will be able to set password for your user account after the installation)"

list_keymaps = "Keyboard Layout"
list_timezones = "Timezone"

immutable_system = "Immutable system image"
choose_spin_instead = "Choose distro instead"

windows_question = "Okay! How should %s be installed?"
windows_options = {'dualboot': 'Install alongside Windows',
                   'replace_win': 'Install and replace Windows',
                   'custom': 'Custom installation and partitioning'}
dualboot_size_txt = "Reserved space for %s:"
verify_question = "This is what is going to happen. Click %s to start installing" % btn_install
verify_text = {
    'no_autoinst': "%s will be downloaded and will boot on the next restart to begin custom installation.",
    'autoinst_dualboot': "%s will be downloaded and installed alongside Windows on next restart.",
    'autoinst_clean': "%s will be downloaded and installed on next restart.",
    'autoinst_keep_data': "Your existing data will not be affected.",
    'autoinst_rm_all': "Everything on this device will be erased.",
    'autoinst_wifi': "Existing Wi-Fi profiles will be added in %s."
}
add_import_wifi = "Export my Wi-Fi networks to %s"
add_auto_restart = "Restart automatically"
add_torrent = "Use torrent whenever possible"
more_options = "More options"

job_starting_download = "Starting download..."
downloads_number = "File %s out of %s"
job_dl_install_media = "Downloading install media..."
dl_timeleft = "Time left"
dl_speed = "Speed"

keymap_tz_option = "The default timezone and keyboard layout for %s"
keymap_tz_ip_description = "(Your IP region)"
keymap_tz_selected_description = "(Your selected locale)"
keymap_tz_custom = "Choose timezone and keyboard layout"

job_checksum = "Checking downloaded file's integrity"
job_checksum_failed = "Integrity check failed"
job_checksum_failed_txt = "Failed to check downloaded file integrity, continue anyways?"
job_checksum_mismatch = "Checksum Mismatch"
job_checksum_mismatch_txt = "The downloaded file has an unexpected SHA256-Hash and cannot be trusted.\n" \
                            "\nFile Hash:\n%s\n" \
                            "Expected Hash:\n%s\n\n" \
                            "This usually means that the downloaded file is either unsafe or corrupted." \
                            "\nTry to download again?"

job_creating_tmp_part = "Creating temporary boot partition for installer media..."
job_copying_to_tmp_part = "Copying required installer media files to temporary boot partition..."
job_adding_tmp_boot_entry = "Adding boot entry..."

cleanup_question = "Clean up downloaded files?"
cleanup_question_txt = "These files are not useful anymore unless you plan to reuse the app later.\nDelete them?"
finished_title = "Restart required"
finished_text = "A restart is required to continue installation, " \
                   "click '%s' to restart now or '%s' to manually restart later" % (btn_restart_now, btn_restart_later)
finished_text_restarting_now = "Automatic restart in %s seconds"
