import APP_INFO


ln_btn_next = "Next"
ln_btn_yes = "Yes"
ln_btn_no = "No"
ln_btn_back = "Back"
ln_btn_quit = "Quit"
ln_btn_cancel = "Cancel"
ln_btn_abort = "Abort"
ln_btn_confirm = "Confirm"
ln_btn_install = "Install now"
ln_btn_restart_now = "Restart now"
ln_btn_restart_later = "Restart later"
ln_btn_dl_again = "Download Again"
ln_btn_continue_anyways = "Continue anyways"


ln_check_running = "Checking System compatibility. please wait..."
ln_check_ram = "Checking available RAM capacity"
ln_check_uefi = "Checking UEFI compliance"
ln_check_space = "Checking available space"
ln_check_resizable = "Checking system drive resizability"
ln_check_bitlocker = "Checking system drive bitlocker status"

ln_error_title = "%s can't run on your system"
ln_error_list = "Following issues detected:"
ln_error_arch_0 = "This device's CPU architecture is incompatible."
ln_error_arch_9 = "CPU architecture could not be verified."
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

ln_recommended = "Recommended"
ln_adv = "Advanced"
ln_net_install = "Network Install"
ln_warn_space = "Not enough space"
ln_total_download = "Total download: %sGB"
ln_init_download = "Initial download: %sGB"

ln_install_running = "Installing..."
ln_install_question = "How do you want to install Linux?"
ln_install_auto = "Quick & guided install"
ln_install_help = "Help me decide"

ln_adv_confirm = "Advanced option selected..."
ln_adv_confirm_text = "I selected an advanced option and I know what I'm doing"

ln_windows_question = "Okay! How should %s be installed?"
ln_windows_options = ('Install alongside Windows',
                      'Remove Windows & migrate my Library (Music, Photos, Videos)',
                      'Nuke Windows and all data and start fresh')

ln_verify_question = "This is what is going to happen. Click %s once ready" % ln_btn_install
ln_verify_text = \
    (
     "%s will be downloaded",
     (" and booted after restart to begin installation", " and installed"),
     (" alongside Windows", " replacing Windows", ", and will remove everything, including Windows"),
     ("None of your files will be deleted or changed in any way",
      "Everything on system drive (%s:\\) will be removed, this usually includes your Library folders (Downloads, Videos, Music, Pictures, etc)",
      "Everything on this device will be removed ")
    )

ln_add_import_wifi = "Export my Wi-Fi networks to the new OS"
ln_add_auto_restart = "Restart automatically"
ln_add_torrent = "Download using torrent"
ln_more_options = "More options"

ln_old_download_detected = "Previously downloaded files found"
ln_old_download_detected_text = "Do you wish to use these previously downloaded files? " \
                                "(if not, these files will be deleted and a new download will start)"

ln_job_starting_download = "Starting download..."

ln_job_dl_install_media = "Downloading install media..."
ln_dl_timeleft = "Time left: "
ln_dl_speed = "Speed: "

ln_job_checksum = "Checking downloaded file's integrity"
ln_job_checksum_failed = "Integrity check failed"
ln_job_checksum_failed_txt = "Failed to check downloaded file integrity, continue anyways?"
ln_job_checksum_mismatch = "Checksum Mismatch"
ln_job_checksum_mismatch_txt = "The downloaded file has bad fingerprint (Hash) and cannot be trusted.\n\nFile Hash:\n%s\n" \
                               "Expected Hash:\n%s\n\n" \
                               "This could also mean the downloaded file is corrupted"

ln_job_creating_tmp_part = "Creating temporary boot partition for installer media..."
ln_job_copying_to_tmp_part = "Copying required installer media files to temporary boot partition..."
ln_job_adding_tmp_boot_entry = "Adding boot entry..."

ln_cleanup_question = "Clean up downloaded files?"
ln_cleanup_question_txt = "These files are not useful anymore unless you plan to reuse the app later.\n\nDelete them?"
ln_finished_title = "Restart required"
ln_finished_text = "A restart is required to continue installation, " \
                   "click '%s' to restart now or '%s' to manually restart later" % (ln_btn_restart_now, ln_btn_restart_later)
ln_finished_text_restarting_now = "Automatic restart in %s seconds"
