import APP_INFO

ln_btn_next = "Weiter"
ln_btn_back = "Zurück"
ln_btn_quit = "Beenden"
ln_btn_start = "Starten"
ln_btn_restart_now = "Jetzt neustarten"
ln_btn_restart_later = "Später neustarten"

ln_check_running = "Systemkompatibilität wird überprüft. Bitte warten..."
ln_check_ram = "Wird überprüft: Verfügbare RAM-Kapazität"
ln_check_uefi = "Wird überprüft: UEFI-Konformität"
ln_check_space = "Wird überprüft: Verfügbaren Speicherplatz"
ln_check_resizable = "Wird überprüft: Veränderbarkeit des Systemlaufwerks"
ln_check_bitlocker = "Wird überprüft: den Bitlocker-Status des Systemlaufwerks"

ln_install_running = "Installieren..."

ln_error_title = "%s kann auf Ihrem System nicht ausgeführt werden" % APP_INFO.SW_NAME
ln_error_list = "Folgende Voraussetzungen fehlen:"
ln_error_uefi_0 = "Ihr System unterstützt (oder verwendet) UEFI-Boot nicht."
ln_error_uefi_9 = "UEFI-Boot-Unterstützung konnte nicht verifiziert werden."
ln_error_totalram_0 = "Ihr System hat nicht genügend RAM-Kapazität."
ln_error_totalram_9 = "Verfügbare RAM-Kapazität konnte nicht geprüft werden."
ln_error_space_0 = "Nicht genügend Speicherplatz auf dem Systemlaufwerk."
ln_error_space_9 = "Der verfügbare Speicherplatz auf dem Systemlaufwerk konnte nicht überprüft werden."
ln_error_resizable_0 = "Die Größenänderung des Systemlaufwerks konnte nicht überprüft werden."
ln_error_resizable_9 = "Nicht genug Platz zum Verkleinern auf dem Systemlaufwerk."
ln_error_bitlocker_0 = "Fehler beim Prüfen, ob auf dem Systemlaufwerk Bitlocker aktiviert ist."
ln_error_bitlocker_9 = "Auf dem Systemlaufwerk ist Bitlocker aktiviert. Kompatibilität kann nicht gesichert werden"

ln_install_question = "Wie möchten Sie %s installieren?" % APP_INFO.distro_name

ln_install_options = ("%s automatisch installieren (%s Desktop)"
                      % (APP_INFO.distro_flavors_names[0], APP_INFO.distro_flavors_de[0]),
                      "%s automatisch installieren (%s Desktop)"
                      % (APP_INFO.distro_flavors_names[1], APP_INFO.distro_flavors_de[1]),
                      "Erweitert: Net-install verwenden & Pakete später auswählen")
ln_install_help = "Hilfe mir zu entscheiden"

ln_adv_confirm = "Erweiterte Option ausgewählt..."
ln_adv_confirm_text = "Ich habe eine erweiterte Option ausgewählt und weiß, was ich tue"

ln_windows_question = "Okay! Was soll ich mit Windows und Ihren Datein tun?"
ln_windows_options = ("%s neben Windows installieren" % APP_INFO.distro_name,
                      "Windows entfernen und meine Bibliothek (Musik, Fotos, Videos) nach %s migrieren" % APP_INFO.distro_name,
                      "Lösche Windows und alle meine Daten und starte neu mit %s" % APP_INFO.distro_name,
                      "Erweitert: Nichts tun und mich später partitionieren lassen")
ln_windows_option1_disabled = "%s (nicht genug Speicherplatz)" % ln_windows_options[1]

ln_verify_question = "Das wird getan. Klicken Sie auf %s, sobald Sie bereit sind." % ln_btn_start
ln_add_import_wifi = "Meine WLAN-Netzwerke nach %s exportieren" % APP_INFO.distro_name
ln_add_auto_restart = "Automatisch neustarten"
ln_show_advanced = "Erweiterte Einstellungen anzeigen"
ln_adv_torrent = "Torrent zum Download verwenden"

ln_old_download_detected = "Nicht abgeschlossene Installation erkannt"
ln_old_download_detected_text = "Eine nicht abgeschlossene Installation erkannt, zuvor heruntergeladene Dateien verwenden? " \
                                "(wählen Sie 'Nein', um zu bereinigen und einen neuen Download zu starten)"

ln_job_starting_download = "Download wird gestartet"
ln_dl_timeleft = "Verbleibende Zeit: "
ln_dl_speed = "Geschwindigkeit: "

ln_job_dl_install_media = "Installationsmedium werden heruntergeladen"
ln_job_creating_tmp_part = "Temporäre Boot-Partition für Installationsmedium wird erstellt..."
ln_job_copying_to_tmp_part = "Installationsmediumdateien werden auf temporäre Boot-Partition kopiert..."
ln_job_adding_tmp_boot_entry = "Boot-Eintrag wird hinzugefügt..."

ln_finished_title = "Neustart erforderlich"
ln_finished_text = "Ein Neustart ist erforderlich, um die Installation fortzusetzen, Klicken Sie auf " \
                   "'%s', um jetzt neu zu starten oder '%s' " \
                   "um später manuell neuzustarten" % (ln_btn_restart_now, ln_btn_restart_later)
ln_finished_text_restarting_now = "Automatischer Neustart in %s Sekunden"