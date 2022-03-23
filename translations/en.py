
import APP_INFO

ln_btn_next = "Next"
ln_btn_back = "Back"
ln_btn_quit = "Quit"
ln_btn_start = "Start"

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
ln_error_resizable_0 = "Failed to check system drive resizability."
ln_error_resizable_9 = "Not enough shrink room on system drive."
ln_error_bitlocker_0 = "Failed to check whether system drive has bitlocker enabled."
ln_error_bitlocker_9 = "System drive has Bitlocker enabled. Compatibility cannot be ensured"

ln_install_question = "How do you want to install %s?" % APP_INFO.distro_name

ln_install_options = [0, "Quick Install with KDE Desktop",
                      "Quick Install with GNOME Desktop",
                      "Advanced: Let me configure my applets later"]
ln_install_help = "Help me decide"
ln_install_text = "GNOME and KDE are the two biggest desktop enviroment projects in Linux.\n" \
                  "GNOME is minimal, non-distractive, stable, functional and beautiful." \
                  "GNOME apps look very integrated and has great touch-screens support. " \
                  "Generally GNOME gives you fewer options and very few " \
                  "customization room, and rather aims to provide out-of-the-box experience." \
                  "GNOME has different layout than Windows\n" \
                  "KDE is customizable, beautiful and customizable and....did I mention customizable?\n" \
                  "By default, it has similar desktop layout to Windows, but it can be endlessly configured to look " \
                  "like whatever you want it to, whether its Mac, Windows, GNOME or something else. With as many " \
                  "desktop elements and effects as it can gets, KDE leaves no desire if you like to customize every " \
                  "aspect of your desktop, or use predefined theme to make it your own, gorgeous-looking desktop \n\n" \
                  "Both desktops are mature and great at doing what they do they don't share the exact same goals and " \
                  "ideologies. So choose whichever fits you best\n" \
                  "Choose GNOME if you want a beautiful, integrated, rock-stable desktop for what is is, " \
                  "better optimized for touch-screens, you don't like having too many options, and don't mind getting" \
                  " used to a new desktop layout\n\n" \
                  "Choose KDE if you want a beautiful, familiar-looking desktop by default" \
                  " that gives you a lot of options and has endless possibilities" \


ln_windows_question = "Got it, what about Windows and your data?"
ln_windows_options = [0, "Install %s alongside Windows" % APP_INFO.distro_name,
                      "Remove Windows & migrate my Library (Music, Photos, Videos) to %s" % APP_INFO.distro_name,
                      "Nuke Windows and all data and start fresh with %s" % APP_INFO.distro_name,
                      "Advanced: Do nothing and let me partition later"]
ln_windows_option1_disabled = "%s (not enough space)" % ln_windows_options[1]

ln_verify_question = "This is what is going to be done. Click %s once ready" % ln_btn_start

ln_job_downloading_install_media = "Downloading install media"
