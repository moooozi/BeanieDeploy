
import APP_INFO

ln_btn_next = "Next"
ln_btn_back = "Back"
ln_btn_quit = "Quit"
ln_btn_start = "Start"
ln_btn_restart_now = "Restart now"
ln_btn_restart_later = "Restart later"

ln_check_running = "Checking System compatibility. please wait..."
ln_install_running = "Installing..."

ln_error_title = "%s can't run on your system" % APP_INFO.SW_NAME
ln_error_list = "Following requirements are missing:"
ln_error_uefi_0 = "Your system does not support (or is not using) UEFI boot."
ln_error_uefi_9 = "UEFI boot support could not be verified."
ln_error_totalram_0 = "Your system does not have sufficient RAM capacity."
ln_error_totalram_9 = "Failed to check available RAM capacity."
ln_error_space_0 = "Not enough space on your system drive. Free up space and try again"
ln_error_space_9 = "Failed to check available disk space on your system drive."
ln_error_resizable_0 = "Not enough shrink room on system drive."
ln_error_resizable_9 = "Failed to check system drive resizability."
ln_error_bitlocker_0 = "System drive has Bitlocker enabled. Compatibility cannot be ensured"
ln_error_bitlocker_9 = "Failed to verify system drive bitlocker status."

ln_install_question = "How do you want to install %s?" % APP_INFO.distro_name

ln_install_options = ["Quick Install with KDE Desktop",
                      "Quick Install with GNOME Desktop",
                      "Advanced: Let me configure my applets later"]
ln_install_help = "Help me decide"

ln_windows_question = "Got it, what about Windows and your data?"
ln_windows_options = ["Install %s alongside Windows" % APP_INFO.distro_name,
                      "Remove Windows & migrate my Library (Music, Photos, Videos) to %s" % APP_INFO.distro_name,
                      "Nuke Windows and all data and start fresh with %s" % APP_INFO.distro_name,
                      "Advanced: Do nothing and let me partition later"]
ln_windows_option1_disabled = "%s (not enough space)" % ln_windows_options[0]

ln_verify_question = "This is what is going to be done. Click %s once ready" % ln_btn_start
ln_addition_import_wifi = "Import my Wi-Fi networks to Linux"
ln_addition_auto_restart = "Restart automatically"


ln_job_starting_download = "Starting download..."
ln_job_downloading_install_media = "Downloading install media..."
ln_job_creating_tmp_part = "Creating temporary boot partition for installer media..."
ln_job_copying_to_tmp_part = "Copying required installer media files to temporary boot partition..."
ln_job_adding_tmp_boot_entry = "Adding boot entry..."

ln_finished_title = "Restart required"
ln_finished_text = "A restart is required to continue installation, " \
                   "click %s to restart now or %s manually restart later" % (ln_btn_restart_now, ln_btn_restart_later)
ln_finished_text_restarting_now = "Automatic restart in %s seconds"
