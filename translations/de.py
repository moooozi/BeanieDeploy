import APP_INFO

ln_btn_next = "Weiter"
ln_btn_back = "Zurück"
ln_btn_quit = "Beenden"
ln_btn_start = "Starten"

ln_check_running = "Systemkompatibilität wird überprüft. Bitte warten..."
ln_install_running = "Installieren..."

ln_error_title = "%s kann auf Ihrem System nicht ausgeführt werden" % APP_INFO.SW_NAME
ln_error_list = "Folgende Voraussetzungen fehlen:"
ln_error_uefi_0 = "Ihr System unterstützt (oder verwendet) UEFI-Boot nicht."
ln_error_uefi_9 = "UEFI-Boot-Unterstützung konnte nicht verifiziert werden."
ln_error_totalram_0 = "Ihr System hat nicht genügend RAM-Kapazität."
ln_error_totalram_9 = "Verfügbare RAM-Kapazität konnte nicht geprüft werden."
ln_error_space_0 = "Nicht genügend Speicherplatz auf Ihrem Systemlaufwerk. Geben Sie Speicherplatz frei und versuchen Sie es erneut."
ln_error_space_9 = "Der verfügbare Speicherplatz auf Ihrem Systemlaufwerk konnte nicht überprüft werden."
ln_error_resizable_0 = "Die Größenänderung des Systemlaufwerks konnte nicht überprüft werden."
ln_error_resizable_9 = "Nicht genug Platz zum Verkleinern auf dem Systemlaufwerk."
ln_error_bitlocker_0 = "Fehler beim Prüfen, ob auf dem Systemlaufwerk Bitlocker aktiviert ist."
ln_error_bitlocker_9 = "Auf dem Systemlaufwerk ist Bitlocker aktiviert. Kompatibilität kann nicht gesichert werden"

ln_install_question = "Wie möchten Sie %s installieren?" % APP_INFO.distro_name

ln_install_options = [0, "Schnellinstallation mit KDE-Desktop",
                      "Schnellinstallation mit GNOME Desktop",
                      "Erweitert: Lassen Sie mich meine Apps später konfigurieren"]

ln_windows_question = "Verstanden, was ist mit Windows und Ihren Daten?"

ln_windows_options = [0, "%s neben Windows installieren" % APP_INFO.distro_name,
                      "Windows entfernen und meine Bibliothek (Musik, Fotos, Videos) nach %s migrieren" % APP_INFO.distro_name,
                      "Lösche Windows und alle Daten und starte neu mit %s" % APP_INFO.distro_name,
                      "Erweitert: Nichts tun und mich später partitionieren lassen"]
ln_windows_option1_disabled = "%s (nicht genug Platz)" % ln_windows_options[1]

ln_verify_question = "Das wird getan. Klicken Sie auf %s, sobald Sie fertig sind." % ln_btn_start

ln_job_downloading_install_media = "Installationsmedien werden heruntergeladen"