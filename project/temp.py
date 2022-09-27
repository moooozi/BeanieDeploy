
ln_install_text = "GNOME and KDE are the two biggest desktop environment projects for Linux.\n" \
                  "GNOME is minimal, non-distractive, stable, functional and beautiful." \
                  "GNOME apps look very integrated and GNOME has great touch-screens support. " \
                  "Generally GNOME gives you fewer options and very few " \
                  "customization room, and rather aims to provide out-of-the-box experience." \
                  "GNOME has different layout than Windows\n" \
                  "KDE is customizable, beautiful and customizable and....did I mention customizable?\n" \
                  "By default, it has similar desktop layout to Windows, but it can be endlessly configured to look " \
                  "like whatever you want it to, whether its Mac, Windows, GNOME or something else. With as many " \
                  "desktop elements and effects as it can gets, KDE leaves no desire if you like to customize every " \
                  "aspect of your desktop, or use predefined theme to make it your own, gorgeous-looking desktop \n\n" \
                  "Both desktops are mature and great at doing what they do but they do they don't share the exact same " \
                  "goals and ideologies. So choose whichever fits you best\n" \
                  "Choose GNOME if you want a beautiful, integrated, rock-stable desktop for what is is, " \
                  "better optimized for touch-screens, you don't like having too many options, and don't mind getting" \
                  " used to a new desktop layout\n\n" \
                  "Choose KDE if you want a beautiful, familiar-looking desktop by default" \
                  " that gives you a lot of options and endless possibilities" \



def download_file2(app_path, url, destination):
    arg = r' --dir="' + destination + '" ' + url
    p = subprocess.Popen(app_path + arg, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True,
                         universal_newlines=True)
    while True:
        output = p.stdout.readline()
        if output == '' and p.poll() is not None:
            return 0
        if output:
            if '(OK):download completed' in output:
                print('done')
                return 1
            else:
                st = output.strip()
                try:
                    print('percent: %', st[:st.index('%) CN:')][st.index('(')+1:])
                    print('size: ', st[:st.index('%) CN:')][st.index('MiB/') + 4:-5])
                    print('downloaded: ', st[:st.index('%) CN:')][st.index(' ') + 1:st.index('MiB/') + 1])
                    print('speed: ', st[st.index(' DL:'):][4:st.index('iB') - 5])  # speed
                    print(output.strip())
                except (ValueError, IndexError): pass

    rc = p.poll()
    print('rc ', rc)


download_file2(r'C:\aria2c.exe', 'https://download.fedoraproject.org/pub/fedora/linux/releases/35/Everything/x86_64/iso/Fedora-Everything-netinst-x86_64-35-1.2.iso', 'C:\\resources')

if not installer_status:
    while queue1.qsize(): queue1.get()  # to empty the queue
    progressbar_install['value'] = 0
    job_var.set(ln.ln_job_starting_download)
    app.update()
    create_dir(download_path)
    Process(target=download_file, args=(APP_INFO.url_direct_dl, install_media_path, queue1,)).start()
    while not queue1.qsize():
        app.after(100, app.update())
    job_id = queue1.get()
    print(job_id)
    INSTALLER_STATUS = 1

if INSTALLER_STATUS == 1:
    dl_status = track_download(job_id)
    while dl_status[0] != dl_status[1]:
        dl_status = track_download(job_id)
        percent = (int(dl_status[1]) * 100) / int(dl_status[0])
        progressbar_install['value'] = percent * 0.92
        job_var.set(ln.ln_job_downloading_install_media + r'(%' + str(round(percent, 1)) + ')')
        app.after(500, app.update())
    finish_download(job_id)
    rename_file(download_path, '*.iso', downloaded_iso_name)
    INSTALLER_STATUS = 2

    '''and compatibility_results['resizable'] == 1'''

def open_popup(popup_type, title, txt):
    top = tk.Toplevel(app)
    width = 300
    height = 300
    screen_width = top.winfo_screenwidth()
    screen_height = top.winfo_screenheight()
    x_coordinate = (screen_width / 2) - (width / 2)
    y_coordinate = (screen_height / 2) - (height / 2)

    top.geometry("%dx%d+%d+%d" % (width, height,
                                   x_coordinate, y_coordinate))
    top.overrideredirect(True)
    top.attributes('-topmost', True)
    top.title(title)
    btn_var = tk.IntVar(top, -2)

    def validate_input(var, allowed_char=None, is_username=False):

        if var.get() != '':
            if allowed_char and any((char not in allowed_char) for char in var.get()):
                txt = ''
                for char in var.get():
                    if char in allowed_char:
                        txt += char
                var.set(txt)
            if is_username:
                portable_fs_chars = r'a-zA-Z0-9._-'
                _name_base = r'[a-zA-Z0-9._][' + portable_fs_chars + r']{0,30}([' + portable_fs_chars + r']|\$)?'
                name_valid = re.compile(r'^' + _name_base + '$')
                while True:
                    if re.match(name_valid, var.get()): break
                    var.set(var.get()[:-1])


"""
def download_file_legacy():  # DEPRECATE METHOD, REPLACED WITH aria2 ***********************************************

    def download_file(url, destination, queue):
        arg = '(Start-BitsTransfer -Source "' + url + '" -Destination "' + destination + '" -Priority normal -Asynchronous).JobId'
        job_id = str(subprocess.run(
            [r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[86:122]
        queue.put(job_id)


    def get_download_size(job_id):
        arg = '(Get-BitsTransfer | ? { $_.JobId -eq "' + job_id + '" }).bytestotal'
        return str(subprocess.run(
            [r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[2:-5]


    def get_downloaded_size(job_id):
        arg = '(Get-BitsTransfer | ? { $_.JobId -eq "' + job_id + '" }).bytestransferred'
        return str(subprocess.run(
            [r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout)[2:-5]


    def track_download(job_id):
        dl_size = get_download_size(job_id)
        already_downloaded = get_downloaded_size(job_id)
        return [dl_size, already_downloaded]


    def finish_download(job_id):
        arg = '(Get-BitsTransfer | ? { $_.JobId -eq "' + job_id + '" }) | Complete-BitsTransfer'
        return subprocess.run([r'powershell.exe', arg], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
"""

if not COMPATIBILITY_RESULTS:
    if not COMPATIBILITY_CHECK_STATUS:
        var_compatibility_test = tk.Variable()
        Process(target=fn.compatibility_test, args=(minimal_required_space, var_compatibility_test,)).start()
        # Try to detect GEO-IP locale while compatibility check is running. Timeout once check has finished
        Process(target=detect_locale, args=(var_compatibility_test,)).start()
        COMPATIBILITY_CHECK_STATUS = 1


        def trace_results(var):
            global IP_LOCALE, COMPATIBILITY_RESULTS
            queue_out = var.get()
            if queue_out == 'arch':
                pass
            elif queue_out == 'uefi':
                job_var.set(LN.check_uefi)
            elif queue_out == 'ram':
                job_var.set(LN.check_ram)
            elif queue_out == 'space':
                job_var.set(LN.check_space)
            elif queue_out == 'resizable':
                job_var.set(LN.check_resizable)
            elif isinstance(queue_out, tuple) and queue_out[0] == 'detect_locale':
                IP_LOCALE = queue_out[1:]
            elif isinstance(queue_out, dict):
                COMPATIBILITY_RESULTS = queue_out
                return app.destroy()


        tkt.var_tracer(var_compatibility_test, mode='w', cb=trace_results(var_compatibility_test))
        app.mainloop()

def check_if_file_exists_and_if_yes_pop_question(file_path):
    if fn.check_if_exists(file_path):
        question = tkt.open_popup(parent=app, title_txt=LN.old_download_detected,
                                  msg_txt=LN.old_download_detected_text,
                                  primary_btn_str=LN.btn_yes, secondary_btn_str=LN.btn_no)
        if question:
            return True
        else:
            fn.rm(file_path)
            return False
    else:
        return False




if dist['is_live_img']:
    total_size = LIVE_OS_INSTALLER_SPIN[SIZE] + dist[SIZE]
else:
    total_size = dist[SIZE]
if dist[IS_BASE_NET_INSTALL]:
    dl_size_txt = LN.init_download % fn.byte_to_gb(total_size)
else:
    dl_size_txt = LN.total_download % fn.byte_to_gb(total_size)