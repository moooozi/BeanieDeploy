btn_next = "Weiter"
btn_yes = "Ja"
btn_no = "Nein"
btn_back = "Zurück"
btn_quit = "Beenden"
btn_cancel = "Abbrechen"
btn_continue = "Weiter"
btn_abort = "Abbruch"
btn_confirm = "Bestätigen"
btn_install = "Jetzt installieren"
btn_restart_now = "Jetzt neu starten"
btn_restart_later = "Später neu starten"
btn_dl_again = "Erneut herunterladen"

check_running = "Überprüfe die Systemkompatibilität. Bitte warten..."
check_ram = "Überprüfe verfügbare RAM-Kapazität"
check_uefi = "Überprüfe die UEFI-Konformität"
check_space = "Überprüfe verfügbaren Speicherplatz"
check_resizable = "Veränderbarkeit des Systemlaufwerks prüfen"
check_bitlocker = "Überprüfe den Bitlocker-Status des Systemlaufwerks"

error_title = "%s kann auf Ihrem System nicht ausgeführt werden"
error_list = "Folgende Probleme erkannt:"
error_arch_0 = "Die CPU-Architektur dieses Geräts ist nicht kompatibel."
error_arch_9 = "CPU-Architektur konnte nicht verifiziert werden."
error_uefi_0 = "Ihr System unterstützt (oder verwendet) UEFI-Boot nicht."
error_uefi_9 = "UEFI-Boot-Unterstützung konnte nicht verifiziert werden."
error_totalram_0 = "Ihr System hat nicht genügend RAM-Kapazität."
error_totalram_9 = "Verfügbare RAM-Kapazität konnte nicht geprüft werden."
error_space_0 = "Nicht genügend Speicherplatz auf Ihrem Systemlaufwerk. Geben Sie Speicherplatz frei und versuchen Sie es erneut."
error_space_9 = "Der verfügbare Speicherplatz auf Ihrem Systemlaufwerk konnte nicht überprüft werden."
error_resizable_0 = "Nicht genug Speicherplatz auf dem Systemlaufwerk."
error_resizable_9 = "Die Größenänderung des Systemlaufwerks konnte nicht überprüft werden."
error_bitlocker_0 = "Systemlaufwerk hat Bitlocker aktiviert. Kompatibilität kann nicht gewährleistet werden"
error_bitlocker_9 = "Bitlocker-Status des Systemlaufwerks konnte nicht überprüft werden."

lang = "Sprache"
locale = "Gebietsschema"
recommended = "empfohlen"
adv = "Erweitert"
net_install = "Netzwerkinstallation"
warn_space = "Nicht genug Speicherplatz"
total_download = "Download insgesamt: %sGB"
init_download = "Erster Download: %sGB"

install_running = "Installieren..."
distro_question = "Welche Version von Fedora möchten Sie installieren?"
install_auto = "Schnelle & geführte Installation"
install_help = "Hilfe bei der Entscheidung"
title_autoinst2 = "Wählen Sie Ihre Sprache und Ihr Gebietsschema"
title_autoinst3 = "Wählen Sie Ihre Zeitzone und Ihr Tastaturlayout"
title_autoinst4 = "Erstellen Sie Ihr lokales Benutzerkonto"

entry_username = "Benutzername"
entry_fullname = "Vollständiger Name (optional)"
password_reminder_txt = "(Sie können nach der Installation ein Passwort für Ihr Benutzerkonto festlegen)"

list_keymaps = "Tastaturlayout"
list_timezones = "Zeitzone"

adv_confirm = "Erweiterte Option ausgewählt..."
adv_confirm_text = "Diese Option wird neuen Benutzern nicht empfohlen."

windows_question = "Okay! Wie soll %s installiert werden?"
windows_options = ('Neben Windows installieren',
                   'Alles löschen und neu anfangen')
dualboot_size_txt = "Größe:"
verify_question = "Das wird passieren. Klicken Sie auf %s, sobald Sie fertig sind." % btn_install
verify_text = {
    'no_autoinst': "%s wird heruntergeladen und beim nächsten Neustart gestartet, um die benutzerdefinierte Installation zu beginnen.",
    'autoinst_dualboot': "%s wird beim nächsten Neustart zusammen mit Windows heruntergeladen und installiert.",
    'autoinst_clean': "%s wird heruntergeladen und beim nächsten Neustart installiert.",
    'autoinst_keep_data': "Keine Ihrer Dateien wird gelöscht oder in irgendeiner Weise verändert.",
    'autoinst_rm_all': "Alles auf diesem Gerät wird gelöscht.",
    'autoinst_wifi': "Vorhandene WLAN-Profile werden nach %s exportiert."
}
add_import_wifi = "Meine WLAN-Netzwerke in das neue Betriebssystem exportieren"
add_auto_restart = "Automatisch neu starten"
add_torrent = "Herunterladen mit Torrent"
more_options = "Weitere Optionen"

old_download_detected = "Zuvor heruntergeladene Dateien gefunden"
old_download_detected_text = "Möchten Sie diese zuvor heruntergeladenen Dateien verwenden? " \
                             "(wenn nicht, werden diese Dateien gelöscht und ein neuer Download wird gestartet)"

job_starting_download = "Starte Download..."

job_dl_install_media = "Installationsmedien werden heruntergeladen..."
dl_timeleft = "Verbleibende Zeit"
dl_speed = "Geschwindigkeit"

keymap_tz_option = "%s - Standardzeitzone und Tastaturlayout für diese Region verwenden"
keymap_tz_custom = "Benutzerdefinierte Zeitzone und Tastaturlayout"

job_checksum = "Überprüfe die Integrität der heruntergeladenen Datei"
job_checksum_failed = "Integritätsprüfung fehlgeschlagen"
job_checksum_failed_txt = "Fehler beim Überprüfen der Integrität der heruntergeladenen Datei, trotzdem fortfahren?"
job_checksum_mismatch = "Nicht übereinstimmende Prüfsumme"
job_checksum_mismatch_txt = "Die heruntergeladene Datei hat einen ungültigen Fingerabdruck (Hash) und ist nicht vertrauenswürdig.\n\nDatei-Hash:\n%s\n" \
                               "Erwarteter Hash:\n%s\n\n" \
                               "Dies könnte auch bedeuten, dass die heruntergeladene Datei beschädigt ist"

job_creating_tmp_part = "Temporäre Bootpartition für Installationsmedium erstellen..."
job_copying_to_tmp_part = "Erforderliche Installationsmediendateien werden auf temporäre Boot-Partition kopiert..."
job_adding_tmp_boot_entry = "Starteintrag wird hinzugefügt..."

cleanup_question = "Heruntergeladene Dateien bereinigen?"
cleanup_question_txt = "Diese Dateien sind nicht mehr nützlich, es sei denn, Sie planen, die App später wiederzuverwenden.\n\nSie löschen?"
finished_title = "Neustart erforderlich"
finished_text = "Ein Neustart ist erforderlich, um die Installation fortzusetzen, " \
                    "Klicken Sie auf '%s', um jetzt neu zu starten, oder auf '%s', um später manuell neu zu starten" % (btn_restart_now, btn_restart_later)
finished_text_restarting_now = "Automatischer Neustart in %s Sekunden"