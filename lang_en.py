from APP_INFO import *

lang_btn_next = "Next"
lang_btn_quit = "Quit"
lang_btn_start = "Start"

lang_check_running = "Checking System requirements. please wait..."
lang_install_running = "Installing..."

lang_error_title = SW_NAME + "can't run on your system"
lang_error_uefi_0 = 'Your system does not support (or is not using) UEFI boot.'
lang_error_uefi_9 = "UEFI boot support could not be verified."
lang_error_totalram_0 = "Your system does not have sufficient RAM capacity."
lang_error_totalram_9 = "Failed to check available RAM capacity."
lang_error_space_0 = "Not enough space on your system drive. Free up some space and try again later"
lang_error_space_9 = "Failed to check available disk space on your system drive."
lang_error_resizable_0 = "Failed to check system drive resizability."
lang_error_resizable_9 = "Not enough shrink room on system drive."

lang_install_question = "How do you wanna install " + distro_name + "?"


lang_install_options = [0, "Quick Install with KDE Desktop",
                        "Quick Install with GNOME Desktop",
                        "Advanced: Let me configure my applets later"]

lang_windows_question = "Got it, what about Windows and your data?"

lang_windows_options = [0, "Install " + distro_name + " alongside Windows",
                        "Remove Windows & migrate my Library (Music, Photos, Videos) to " + distro_name,
                        "Nuke Windows and all data and start fresh with " + distro_name,
                        "Advanced: Do nothing and let me partition later"]
lang_windows_option1_disabled = lang_windows_options[1] + ' (not enough space)'

lang_verify_question = "This is what is going to be done. Click " + lang_btn_start + " once ready"


lang_job_downloading_install_media = "Downloading install media"