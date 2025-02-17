# German translations
btn_next = "Weiter"
btn_yes = "Ja"
btn_no = "Nein"
btn_back = "Zurück"
btn_quit = "Beenden"
btn_cancel = "Abbrechen"
btn_continue = "Fortsetzen"
btn_abort = "Abbrechen"
btn_confirm = "Bestätigen"
btn_install = "Installieren"
btn_restart_now = "Jetzt neu starten"
btn_restart_later = "Später neu starten"
btn_retry = "Erneut versuchen"

check_available_downloads = "Verfügbare Downloads prüfen"
check_existing_download_files = (
    "Prüfen auf vorhandene Dateien aus früheren Installationen"
)
check_running = "Systemkompatibilität wird geprüft. Bitte warten..."
check_ram = "Verfügbare RAM-Kapazität prüfen"
check_uefi = "UEFI-Konformität prüfen"
check_space = "Verfügbaren Speicherplatz prüfen"
check_resizable = "Prüfen, ob das Systemlaufwerk verkleinert werden kann"

error_title = "%s kann auf Ihrem System nicht ausgeführt werden"
error_list = "Folgende Probleme wurden erkannt:"
error_arch_0 = "Die CPU-Architektur dieses Geräts ist nicht kompatibel."
error_arch_9 = "Die CPU-Architektur konnte nicht überprüft werden."
error_uefi_0 = "Ihr System unterstützt keinen (oder verwendet keinen) UEFI-Boot."
error_uefi_9 = "Die Unterstützung für UEFI-Boot konnte nicht überprüft werden."
error_totalram_0 = "Ihr System hat nicht genügend RAM-Kapazität."
error_totalram_9 = "Die verfügbare RAM-Kapazität konnte nicht überprüft werden."
error_space_0 = "Nicht genügend Speicherplatz auf Ihrem Systemlaufwerk. Machen Sie Platz frei und versuchen Sie es erneut"
error_space_9 = "Der verfügbare Speicherplatz auf Ihrem Systemlaufwerk konnte nicht überprüft werden."
error_resizable_0 = "Nicht genügend Verkleinerungsraum auf dem Systemlaufwerk."
error_resizable_9 = (
    "Die Verkleinerbarkeit des Systemlaufwerks konnte nicht überprüft werden."
)

info_about_selection = "Informationen zur Auswahl:"
desktop_question = "Wählen Sie Ihre bevorzugte Distribution."
desktop_hints = {
    "KDE Plasma": "KDE ist sehr funktionsreich, hochgradig anpassbar und hat standardmäßig ein Windows-ähnliches Layout",
    "GNOME": "Die GNOME-Desktop-Umgebung ist minimal und sehr stabil, optimiert für Touchpad & Touchscreen",
}
lang = "Sprache"
locale = "Gebietsschema"
recommended = "Empfohlen"
adv = "Erweitert"
net_install = "Netzwerkinstallation"
warn_space = "Nicht genug Platz"
warn_not_available = "Nicht verfügbar"
total_download = "Gesamter Download: %sGB"
init_download = "Erster Download: %sGB"

install_running = "Installation läuft..."
install_auto = "Schnelle & geführte Installation"
install_help = "Hilfe bei der Entscheidung"
title_autoinst2 = "Wählen Sie Ihre Sprache und Ihr Gebietsschema"
title_autoinst3 = "Wählen Sie Ihre Zeitzone und Tastaturbelegung"
title_autoinst4 = "Erstellen Sie Ihr lokales Benutzerkonto"

additional_setup_now = (
    "Richten Sie jetzt Ihr Gebietsschema, Ihre Zeitzone und Ihre Tastaturbelegung ein"
)

selected_dist = "Ausgewählte Distribution"
desktop_environment = "Desktop"
choose_distro = "Wählen Sie eine Distribution"
encrypted_root = "Verschlüsseln Sie das neue Betriebssystem"
entry_encrypt_passphrase = "Verschlüsselungspasswort festlegen"

encrypt_reminder_txt = (
    "Sie werden später aufgefordert, das Verschlüsselungspasswort einzugeben"
)
encryption_tpm_unlock = "Automatische Entsperrung mit TPM2"

entry_username = "Benutzername"
entry_fullname = "Vollständiger Name (optional)"
password_reminder_txt = (
    "Sie können das Passwort für Ihr Benutzerkonto nach der Installation festlegen"
)

list_keymaps = "Tastaturbelegung"
list_timezones = "Zeitzone"

immutable_system = "Unveränderliches Systemabbild"

something_else = "Etwas anderes"

windows_question = "Okay! Wie soll %s installiert werden?"
windows_options = {
    "dualboot": "Neben Windows installieren",
    "replace_win": "Installieren und Windows ersetzen",
    "custom": "Benutzerdefinierte Installation und Partitionierung",
}
dualboot_size_txt = "Reservierter Speicherplatz für %s:"
warn_backup_files_txt = "Sichern Sie Ihre Dateien! Alles in %s wird dauerhaft gelöscht"
verify_question = (
    "Das wird passieren. Klicken Sie auf %s, um die Installation zu starten"
    % btn_install
)
verify_text = {
    "no_autoinst": "%s wird heruntergeladen und startet beim nächsten Neustart, um die benutzerdefinierte Installation zu beginnen.",
    "autoinst_dualboot": "%s wird heruntergeladen und neben Windows installiert.",
    "autoinst_replace_win": "%s wird heruntergeladen und installiert, um Windows zu ersetzen.",
    "autoinst_keep_data": "Ihre bestehenden Daten werden nicht beeinträchtigt.",
    "autoinst_rm_all": "Alles auf diesem Gerät wird gelöscht.",
    "autoinst_wifi": "Bestehende Wi-Fi-Profile werden in %s hinzugefügt.",
}
add_import_wifi = "Exportieren Sie meine Wi-Fi-Netzwerke nach %s"
enable_rpm_fusion = "Zusätzliche Repositories für erweiterte Software- und Multimedia-Codec-Unterstützung aktivieren"
add_auto_restart = "Automatisch neu starten"
add_torrent = "Verwenden Sie Torrent, wann immer möglich"
more_options = "Weitere Optionen"

distro_hint = {
    "Fedora Workstation": "Die Hauptausgabe von Fedora mit der GNOME-Desktop-Umgebung",
    "Fedora KDE Plasma": "Fedora mit der KDE-Desktop-Umgebung",
}

job_starting_download = "Download wird gestartet..."
downloads_number = "Datei %s von %s"
job_dl_install_media = "Installationsmedium wird heruntergeladen..."
dl_timeleft = "Verbleibende Zeit"
dl_speed = "Geschwindigkeit"
dl_file_size = "Dateigröße"

keymap_tz_option = "Die Standardzeitzone und Tastaturbelegung für %s"
keymap_tz_ip_description = "(Ihre IP-Region)"
keymap_tz_selected_description = "(Ihr ausgewähltes Gebietsschema)"
keymap_tz_custom = "Zeitzone und Tastaturbelegung auswählen"

job_checksum = "Überprüfung der Integrität der heruntergeladenen Datei"
job_checksum_failed = "Integritätsprüfung fehlgeschlagen"
job_checksum_failed_txt = "Die Überprüfung der Integrität der heruntergeladenen Datei ist fehlgeschlagen, trotzdem fortfahren?"
job_checksum_mismatch = "Checksummen-Unstimmigkeit"
job_checksum_mismatch_txt = (
    "Die heruntergeladene Datei hat einen unerwarteten SHA256-Hash und kann nicht vertraut werden.\n"
    "\nDatei-Hash:\n%s"
    "\nErwarteter Hash:\n%s\n"
    "\nDies bedeutet in der Regel, dass die Datei nicht ordnungsgemäß heruntergeladen wurde."
    "\nVersuchen Sie, erneut herunterzuladen?"
)

job_creating_tmp_part = (
    "Erstellen einer temporären Bootpartition für Installationsmedien..."
)
job_copying_to_tmp_part = "Kopieren der erforderlichen Installationsmedien-Dateien auf die temporäre Bootpartition..."
job_adding_tmp_boot_entry = "Hinzufügen eines Boot-Eintrags..."

cleanup_question = "Heruntergeladene Dateien bereinigen?"
cleanup_question_txt = "Diese Dateien sind nicht mehr nützlich, es sei denn, Sie planen, die App später wieder zu verwenden.\nLöschen?"
finished_title = "Neustart erforderlich"
finished_text = (
    "Ein Neustart ist erforderlich, um die Installation fortzusetzen, "
    "klicken Sie auf '%s', um jetzt neu zu starten oder auf '%s', um später manuell neu zu starten"
    % (btn_restart_now, btn_restart_later)
)
finished_text_restarting_now = "Automatischer Neustart in %s Sekunden"

lang_question = "Jetzt geht's los, wählen Sie Ihre bevorzugte App-Sprache."
