from multiprocessing import Process, Queue
import APP_INFO
import globals as GV
import functions as fn
import procedure as prc
from multilingual import DI_VAR
import translations.en as LN
import tkinter_templates as tkt
from tkinter_templates import tk, ttk, FONTS
from APP_INFO import *
from dict_vars import *
import autoinst 

#   INIT CODE   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
app = tkt.init_tkinter(SW_NAME)  # initialize tkinter
CURRENT_DIR = fn.get_current_dir_path()
tkt.stylize(app, theme_dir=CURRENT_DIR + '/theme/azure-dark.tcl', theme_name='azure')  # use tkinter theme
GLOBAL_QUEUE = Queue()
#   MAIN CONTAINER & FRAMES   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
CONTAINER = ttk.Frame(app)
CONTAINER.pack()
vTitleText = tk.StringVar(app)
TOP_FRAME, MID_FRAME, LEFT_FRAME = tkt.build_main_gui_frames(CONTAINER)
ttk.Label(LEFT_FRAME, image=tk.PhotoImage(file=CURRENT_DIR + r'\resources\left_frame.gif')).pack()
#   INITIALIZING GLOBAL VARIABLES /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
GV.GRUB_CONFIG_PATH_DEFUALT =  GV.GRUB_CONFIG_PATH_DEFUALT.replace('%CURRENT_DIR%', CURRENT_DIR)
GV.GRUB_CONFIG_PATH_AUTOINST = GV.GRUB_CONFIG_PATH_AUTOINST.replace('%CURRENT_DIR%', CURRENT_DIR)
GV.NVIDIA_SCRIPT_PATH = GV.NVIDIA_SCRIPT_PATH.replace('%CURRENT_DIR%', CURRENT_DIR)


def download_hash_handler(dl_hash):
    go_next = False
    if dl_hash == 1:
        go_next = True
    elif dl_hash == -1:
        question = tkt.open_popup(parent=app, title_txt=LN.job_checksum_failed,
                                  msg_txt=LN.job_checksum_failed_txt,
                                  primary_btn_str=LN.btn_yes, secondary_btn_str=LN.btn_no)
        if question:
            go_next = True
        else:
            question = tkt.open_popup(parent=app, title_txt=LN.cleanup_question,
                                      msg_txt=LN.cleanup_question_txt,
                                      primary_btn_str=LN.btn_yes, secondary_btn_str=LN.btn_no)
            if question:
                fn.rmdir(GV.DOWNLOAD_PATH)
            tkt.app_quite()
    else:
        question = tkt.open_popup(parent=app, title_txt=LN.job_checksum_mismatch,
                                  msg_txt=LN.job_checksum_mismatch_txt % dl_hash,
                                  primary_btn_str=LN.btn_yes, secondary_btn_str=LN.btn_no)
        if not question:
            question = tkt.open_popup(parent=app, title_txt=LN.cleanup_question,
                                      msg_txt=LN.cleanup_question_txt,
                                      primary_btn_str=LN.btn_yes, secondary_btn_str=LN.btn_no)
            if question:
                fn.rmdir(GV.DOWNLOAD_PATH)
            tkt.app_quite()
    return go_next


def main():
    fn.log('%s v%s' % (APP_INFO.SW_NAME, APP_INFO.SW_VERSION), mode='w')
    fn.log('################################################################\n'
           'IMPORTANT: DO NOT CLOSE THIS CONSOLE WINDOW WHILE APP IS RUNNING\n'
           '################################################################\n\n')

    def page_check():
        """The page on which is decided whether the app can run on the device or not"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        title = tkt.add_page_title(MID_FRAME, LN.check_running)

        progressbar_check = ttk.Progressbar(MID_FRAME, orient='horizontal', length=550, mode='determinate')
        progressbar_check.pack(pady=25)
        job_var = tk.StringVar()
        tkt.add_text_label(MID_FRAME, var=job_var, pady=0, padx=10)
        app.update()
        fn.get_admin()  # Request elevation (admin) if not running as admin
        # GV.COMPATIBILITY_RESULTS = {'uefi': 1, 'ram': 34359738368, 'space': 133264248832, 'resizable': 432008358400, 'arch': 'amd64'}
        # GV.COMPATIBILITY_RESULTS = {'uefi': 0, 'ram': 3434559, 'space': 1332642488, 'resizable': 4320083, 'arch': 'arm'}
        if not GV.COMPATIBILITY_RESULTS:
            if not GV.COMPATIBILITY_CHECK_STATUS:
                Process(target=prc.compatibility_test, args=(minimal_required_space, GLOBAL_QUEUE,)).start()
                # Try to detect GEO-IP locale while compatibility check is running. Timeout once check has finished
                Process(target=fn.get_json, args=(FEDORA_GEO_IP_URL, GLOBAL_QUEUE,)).start()
                Process(target=fn.get_json, args=(AVAILABLE_SPINS_LIST, GLOBAL_QUEUE,)).start()
                GV.COMPATIBILITY_CHECK_STATUS = 1
            if GV.COMPATIBILITY_CHECK_STATUS == 1:
                while True:
                    while not GLOBAL_QUEUE.qsize(): app.after(100, app.update())
                    queue_out = GLOBAL_QUEUE.get()
                    if queue_out == 'arch':
                        progressbar_check['value'] = 10
                    elif queue_out == 'uefi':
                        job_var.set(LN.check_uefi)
                        progressbar_check['value'] = 20
                    elif queue_out == 'ram':
                        job_var.set(LN.check_ram)
                        progressbar_check['value'] = 30
                    elif queue_out == 'space':
                        job_var.set(LN.check_space)
                        progressbar_check['value'] = 50
                    elif queue_out == 'resizable':
                        job_var.set(LN.check_resizable)
                        progressbar_check['value'] = 80
                    elif isinstance(queue_out, list):
                        GV.ALL_SPINS = queue_out
                    elif isinstance(queue_out, dict) and queue_out.keys() >= {"country_code", "time_zone"}:
                        GV.IP_LOCALE = (queue_out['country_code'], queue_out['time_zone'])
                    elif isinstance(queue_out, dict) and queue_out.keys() >= {"arch", "uefi"}:
                        GV.COMPATIBILITY_RESULTS = queue_out
                        GV.COMPATIBILITY_CHECK_STATUS = 2
                        job_var.set(LN.check_available_downloads)
                        progressbar_check['value'] = 95
                    if GV.COMPATIBILITY_RESULTS and GV.ALL_SPINS:
                        break
        fn.log('\nInitial Test completed, results:')
        for key, value in GV.COMPATIBILITY_RESULTS.items():
            fn.log('%s: %s' % (str(key), str(value)))
        if fn.detect_nvidia():
            fn.log('\nWarning: NVIDIA Graphics card was detected')
        errors = []
        if GV.COMPATIBILITY_RESULTS['arch'] == -1: errors.append(LN.error_arch_9)
        elif GV.COMPATIBILITY_RESULTS['arch'] != 'amd64': errors.append(LN.error_arch_0)
        if GV.COMPATIBILITY_RESULTS['uefi'] == -1: errors.append(LN.error_uefi_9)
        elif GV.COMPATIBILITY_RESULTS['uefi'] != 1: errors.append(LN.error_uefi_0)
        if GV.COMPATIBILITY_RESULTS['ram'] == -1: errors.append(LN.error_totalram_9)
        elif GV.COMPATIBILITY_RESULTS['ram'] < fn.gigabyte(minimal_required_ram): errors.append(LN.error_totalram_0)
        if GV.COMPATIBILITY_RESULTS['space'] == -1: errors.append(LN.error_space_9)
        elif GV.COMPATIBILITY_RESULTS['space'] < fn.gigabyte(minimal_required_space): errors.append(LN.error_space_0)
        if GV.COMPATIBILITY_RESULTS['resizable'] == -1: errors.append(LN.error_resizable_9)
        elif GV.COMPATIBILITY_RESULTS['resizable'] < fn.gigabyte(minimal_required_space): errors.append(LN.error_resizable_0)

        if not errors:
            #global DOWNLOAD_PATH, INSTALL_ISO_PATH, LIVE_ISO_PATH, USERNAME_WINDOWS, ACCEPTED_SPINS,LIVE_OS_INSTALLER_SPIN, ARIA2C_LOCATION
            live_os_installer_index, GV.ACCEPTED_SPINS = prc.parse_spins(GV.ALL_SPINS)
            GV.LIVE_OS_INSTALLER_SPIN = GV.ACCEPTED_SPINS[live_os_installer_index]
            GV.DOWNLOAD_PATH = fn.get_user_home_dir() + "\\win2linux_tmpdir"
            GV.INSTALL_ISO_PATH = GV.DOWNLOAD_PATH + "\\" + GV.INSTALL_ISO_NAME
            GV.LIVE_ISO_PATH = GV.DOWNLOAD_PATH + "\\" + GV.LIVE_ISO_NAME
            GV.ARIA2C_LOCATION = CURRENT_DIR + '\\resources\\aria2c.exe'
            GV.USERNAME_WINDOWS = fn.get_windows_username()
            return page_1()
        else:
            title.destroy()
            progressbar_check.destroy()
            tkt.add_page_title(MID_FRAME, LN.error_title % SW_NAME, pady=20)
            tkt.add_text_label(MID_FRAME, LN.error_list, pady=10)

            errors_tree = ttk.Treeview(MID_FRAME, columns='error', show='', height=6)
            errors_tree.pack(anchor=DI_VAR['w'], ipady=5, padx=(0, 5), fill='x')
            errors_tree.configure(selectmode='none')
            for i in range(len(errors)):
                errors_tree.insert('', index='end', iid=str(i), values=(errors[i],))

            tkt.add_secondary_btn(MID_FRAME, LN.btn_quit, lambda: tkt.app_quite())

    # page_1
    def page_1():
        """the page on which you choose which distro/flaver and whether Autoinstall should be on or off"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set('Welcome to Lnixify')
        tkt.generic_page_layout(MID_FRAME, LN.desktop_question, LN.btn_next, lambda: next_btn_action())
        desktop_var = tk.StringVar(app, 'unset')
        immutable_toggle_var = tk.BooleanVar(app, False)
        available_desktop = []
        dict_spins_with_fullname_keys = []
        for dist in GV.ACCEPTED_SPINS:
            spin_fullname = dist[NAME] + ' ' + dist['version']
            dict_spins_with_fullname_keys.append(spin_fullname)
            if dist['desktop'] and dist['desktop'] not in available_desktop:
                available_desktop.append(dist['desktop'])
        temp_frame = ttk.Frame(MID_FRAME)
        temp_frame.pack(fill="x", pady=5)

        for desktop in available_desktop:
            temp_frame = ttk.Frame(MID_FRAME)
            temp_frame.pack(fill="x", pady=5)
            tkt.add_radio_btn(temp_frame, desktop, desktop_var, desktop, ipady=0, side=DI_VAR['l'],
                              command=lambda: validate_input())
            if desktop in LN.desktop_hints.keys():
                ttk.Label(temp_frame, wraplength=540, justify="center", text=LN.desktop_hints[desktop],
                          font=FONTS['tiny'], foreground='#3aa9ff').pack(padx=5, anchor=DI_VAR['e'], side=DI_VAR['r'])

        tkt.add_radio_btn(MID_FRAME, LN.choose_spin_instead, desktop_var, 'else',
                          command=lambda: validate_input())

        combolist_spin = ttk.Combobox(MID_FRAME, values=dict_spins_with_fullname_keys, state='readonly')
        combolist_spin.set(LN.choose_fedora_spin)
        combolist_spin.bind("<<ComboboxSelected>>", lambda *args: validate_input())
        combolist_spin.pack(padx=40, pady=5, anchor=DI_VAR['w'])
        some_frame = tk.Frame(MID_FRAME)
        some_frame2 = tk.Frame(MID_FRAME)

        spin_name_var = tk.StringVar(app)
        spin_size_var = tk.StringVar(app)
        tkt.add_text_label(some_frame, var=spin_name_var, font=FONTS['tiny'], foreground='#529d53', pady=2)
        tkt.add_text_label(some_frame, var=spin_size_var, font=FONTS['tiny'], foreground='#529d53', pady=2)
        some_frame.pack(side=DI_VAR['r'], fill="x", pady=5)
        some_frame2.pack(side=DI_VAR['l'], fill="x", pady=5)

        def validate_input(*args):
            if desktop_var.get() == 'else':
                combolist_spin.pack(padx=40, pady=5, anchor=DI_VAR['w'])
                if combolist_spin.get() in dict_spins_with_fullname_keys:
                    spin_index = dict_spins_with_fullname_keys.index(combolist_spin.get())
                else:
                    spin_index = None
            else:
                combolist_spin.pack_forget()
                spin_index = None
                for index, dist in enumerate(GV.ACCEPTED_SPINS):
                    if dist[DESKTOP] == desktop_var.get():
                        if bool(immutable_toggle_var.get()) == bool(dist[OSTREE_ARGS]):
                            spin_index = index
            if spin_index is not None:
                GV.INSTALL_OPTIONS.spin = GV.ACCEPTED_SPINS[spin_index]
                if GV.INSTALL_OPTIONS.spin['is_live_img']:
                    GV.INSTALL_OPTIONS.live_img_url = live_img_url

                if GV.INSTALL_OPTIONS.spin['is_live_img']:
                    total_size = GV.LIVE_OS_INSTALLER_SPIN['size'] + GV.INSTALL_OPTIONS.spin['size']
                else:
                    total_size = GV.INSTALL_OPTIONS.spin['size']
                if GV.INSTALL_OPTIONS.spin[IS_BASE_NET_INSTALL]:
                    dl_size_txt = LN.init_download % fn.byte_to_gb(total_size)
                else:
                    dl_size_txt = LN.total_download % fn.byte_to_gb(total_size)
                spin_name_var.set('%s: %s' % (LN.selected_spin, GV.INSTALL_OPTIONS.spin[NAME]))
                spin_size_var.set(dl_size_txt)
            return spin_index

        def next_btn_action(*args):
            if validate_input() is None:
                return -1
            fn.log('\nFedora Spin was selected (based on user\'s preference), spin details:')
            # LOG #############################################
            for key, value in GV.INSTALL_OPTIONS.spin.items():
                fn.log('%s: %s' % (str(key), str(value)))
            # #################################################
            return page_install_method()

    # page_autoinst1
    def page_install_method():
        """the autoinstall page on which you choose whether to install alongside windows or start clean install"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set(LN.install_auto)
        tkt.generic_page_layout(MID_FRAME, LN.windows_question % GV.INSTALL_OPTIONS.spin[NAME],
                                LN.btn_next, lambda: next_btn_action(),
                                LN.btn_back, lambda: page_1())

        install_method_var = tk.StringVar(app, GV.INSTALL_OPTIONS.install_method)
        dualboot_size_var = tk.StringVar(app, str(GV.AUTOINST.dualboot_size))

        r1_frame = ttk.Frame(MID_FRAME)
        r1_frame.pack(fill='x')
        r1_autoinst_dualboot = tkt.add_radio_btn(r1_frame, LN.windows_options['dualboot'],
                                                 install_method_var, 'dualboot', lambda: show_dualboot_options(True),
                                                 pack=False)
        r1_autoinst_dualboot.grid(ipady=5, column=0, row=0, sticky=DI_VAR['w'])
        r1_warning = ttk.Label(r1_frame, wraplength=540, justify="center", text='', font=FONTS['tiny'],
                               foreground='#ff4a4a')
        r1_warning.grid(padx=20, column=1, row=0, sticky=DI_VAR['w'])
        r2_autoinst_clean = tkt.add_radio_btn(r1_frame, LN.windows_options['clean'], install_method_var, 'clean',
                                              lambda: show_dualboot_options(False), pack=False)
        r2_autoinst_clean.grid(ipady=5, column=0, row=2, sticky=DI_VAR['w'])
        r2_warning = ttk.Label(r1_frame, wraplength=540, justify="center", text='', font=FONTS['tiny'],
                               foreground='#ff4a4a')
        r2_warning.grid(padx=20, column=1, row=2, sticky=DI_VAR['w'])
        r3_custom = tkt.add_radio_btn(r1_frame, LN.windows_options['custom'], install_method_var, 'custom', lambda: show_dualboot_options(False), pack=False)
        r3_custom.grid(ipady=5, column=0, row=3, sticky=DI_VAR['w'])

        min_size = dualboot_required_space
        max_size = fn.byte_to_gb(GV.COMPATIBILITY_RESULTS['resizable'] - GV.INSTALL_OPTIONS.spin['size']) - additional_failsafe_space
        max_size = round(max_size, 2)
        float_regex = r'^[0-9]*\.?[0-9]{0,3}$'  # max 3 decimal digits
        entry1_frame = ttk.Frame(r1_frame)
        entry1_frame.grid(row=1, column=0, columnspan=4, padx=10)
        size_dualboot_txt_pre = ttk.Label(entry1_frame, wraplength=540, justify=DI_VAR['l'],
                                          text=LN.dualboot_size_txt, font=FONTS['tiny'])
        size_dualboot_entry = ttk.Entry(entry1_frame, width=10, textvariable=dualboot_size_var)
        size_dualboot_txt_post = ttk.Label(entry1_frame, wraplength=540, justify=DI_VAR['l'],
                                           text='(%sGB - %sGB)' % (min_size, max_size), font=FONTS['tiny'])
        tkt.var_tracer(dualboot_size_var, "write",
                       lambda *args: fn.validate_with_regex(dualboot_size_var, regex=float_regex, mode='fix'))

        # LOGIC
        space_dualboot = fn.gigabyte(dualboot_required_space + additional_failsafe_space) + GV.INSTALL_OPTIONS.spin['size']
        if GV.COMPATIBILITY_RESULTS['resizable'] < space_dualboot:
            r1_warning.config(text=LN.warn_space)
            r1_autoinst_dualboot.configure(state='disabled')
        if not GV.INSTALL_OPTIONS.spin['is_auto_installable']:
            r1_warning.config(text=LN.warn_not_available)
            r2_warning.config(text=LN.warn_not_available)
            r1_autoinst_dualboot.configure(state='disabled')
            r2_autoinst_clean.configure(state='disabled')
        app.update_idletasks()

        def show_dualboot_options(is_true: bool):
            if is_true:
                size_dualboot_txt_pre.grid(pady=5, padx=(10, 0), column=0, row=0, sticky=DI_VAR['w'])
                size_dualboot_entry.grid(pady=5, padx=5, column=1, row=0)
                size_dualboot_txt_post.grid(pady=5, padx=(0, 0), column=2, row=0, sticky=DI_VAR['w'])
            else:
                size_dualboot_txt_pre.grid_forget()
                size_dualboot_entry.grid_forget()
                size_dualboot_txt_post.grid_forget()

        if install_method_var.get() == 'dualboot': show_dualboot_options(True)  # GUI bugfix

        def next_btn_action(*args):
            if install_method_var.get() not in GV.AVAILABLE_INSTALL_METHODS:
                return -1
            GV.INSTALL_OPTIONS.install_method = install_method_var.get()
            if install_method_var.get() == 'dualboot':
                syntax_valid = fn.validate_with_regex(dualboot_size_var, regex=float_regex,
                                                      mode='read') not in (False, 'empty')
                if syntax_valid and min_size <= float(dualboot_size_var.get()) <= max_size:
                    GV.AUTOINST.dualboot_size = float(dualboot_size_var.get())
                else:
                    return -1
            if install_method_var.get() == 'custom':
                return page_verify()
            else:
                return page_autoinst2()

    def page_autoinst2():
        """the autoinstall page on which you choose whether to install alongside windows or start clean install"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set(LN.install_auto)
        tkt.generic_page_layout(MID_FRAME, LN.windows_question % GV.INSTALL_OPTIONS.spin[NAME],
                                LN.btn_next, lambda: next_btn_action(),
                                LN.btn_back, lambda: page_install_method())

        # tkt.add_check_btn(MID_FRAME, LN.additional_setup_now, vAutoinst_additional_setup_t)
        export_wifi_toggle_var = tk.BooleanVar(app, GV.AUTOINST.export_wifi)
        enable_encryption_toggle_var = tk.BooleanVar(app, GV.AUTOINST.enable_encryption)
        encrypt_passphrase_var = tk.StringVar(app, GV.AUTOINST.encryption_pass)

        tkt.add_check_btn(MID_FRAME, LN.add_import_wifi, export_wifi_toggle_var, pady=(5, 0))
        tkt.add_check_btn(MID_FRAME, LN.encrypted_root, enable_encryption_toggle_var,
                          lambda: show_encrypt_options(enable_encryption_toggle_var))

        only_digit_regex = r'^[0-9]+$'  # digits
        entry2_frame = ttk.Frame(MID_FRAME)

        encrypt_pass_pre = ttk.Label(entry2_frame, wraplength=540, justify=DI_VAR['l'],
                                     text=LN.entry_encrypt_passphrase_pre, font=FONTS['tiny'])
        encrypt_passphrase_entry = ttk.Entry(entry2_frame, show="\u2022", width=10,
                                             textvariable=encrypt_passphrase_var)
        encrypt_pass_post = ttk.Label(entry2_frame, wraplength=540, justify=DI_VAR['l'],
                                      text=LN.entry_encrypt_passphrase_post, font=FONTS['tiny'])
        tkt.var_tracer(encrypt_passphrase_var, "write",
                       lambda *args: fn.validate_with_regex(encrypt_passphrase_var,
                                                            regex=only_digit_regex, mode='fix'))
        pass_confirm_var = tk.StringVar()
        encrypt_pass_confirm_pre = ttk.Label(entry2_frame, wraplength=540, justify=DI_VAR['l'],
                                             text=LN.entry_encrypt_passphrase_confirm_pre, font=FONTS['tiny'])
        encrypt_pass_confirm_entry = ttk.Entry(entry2_frame, show="\u2022", width=10, textvariable=pass_confirm_var)
        encrypt_pass_confirm_not_matched = ttk.Label(entry2_frame, wraplength=540, justify=DI_VAR['l'],
                                                     text=LN.not_matched, font=FONTS['tiny'], foreground='#ff4a4a')
        encrypt_pass_note = ttk.Label(entry2_frame, wraplength=540, justify=DI_VAR['l'],
                                      text=LN.encrypt_reminder_txt, font=FONTS['tiny'])
        tkt.var_tracer(pass_confirm_var, "write",
                       lambda *args:
                       show_not_matched_warning(not verify_match(pass_confirm_var, encrypt_passphrase_var)))

        encrypt_pass_pre.grid(pady=5, padx=(10, 0), column=0, row=0, sticky=DI_VAR['w'])
        encrypt_passphrase_entry.grid(pady=5, padx=5, column=1, row=0)
        encrypt_pass_post.grid(pady=5, padx=(0, 0), column=2, row=0, sticky=DI_VAR['w'])
        encrypt_pass_confirm_pre.grid(pady=5, padx=(10, 0), column=0, row=1, sticky=DI_VAR['w'])
        encrypt_pass_confirm_entry.grid(pady=5, padx=5, column=1, row=1)
        encrypt_pass_note.grid(pady=5, padx=(0, 0), column=0, columnspan=4, row=2, sticky=DI_VAR['w'])

        # LOGIC
        def show_not_matched_warning(is_true: bool):
            if is_true: encrypt_pass_confirm_not_matched.grid(pady=5, padx=(0, 0), column=2, row=1, sticky=DI_VAR['w'])
            else: encrypt_pass_confirm_not_matched.grid_forget()

        def verify_match(var1, var2):
            if var1.get() == '':
                return ''
            elif var1.get() == var2.get():
                return True
            else:
                return False

        def show_encrypt_options(var):
            if var.get():
                entry2_frame.pack(fill='x')
            else:
                entry2_frame.pack_forget()
        show_encrypt_options(enable_encryption_toggle_var)

        def next_btn_action(*args):
            if enable_encryption_toggle_var.get() and not verify_match(encrypt_passphrase_var, pass_confirm_var):
                return
            else:
                GV.AUTOINST.export_wifi = export_wifi_toggle_var.get()
                GV.AUTOINST.enable_encryption = enable_encryption_toggle_var.get()
                if GV.AUTOINST.enable_encryption:
                    GV.AUTOINST.encryption_pass = encrypt_passphrase_var.get()
                page_autoinst_addition_1()

    # page_autoinst2
    def page_autoinst_addition_1():
        """the autoinstall page on which you choose your language and locale"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        tkt.generic_page_layout(MID_FRAME, LN.title_autoinst2,
                                LN.btn_next, lambda: next_btn_action(),
                                LN.btn_back, lambda: page_autoinst2())
        if GV.IP_LOCALE:
            langs_and_locales = autoinst.get_locales_and_langs_sorted_with_names(territory=GV.IP_LOCALE[0])
        else:
            langs_and_locales = autoinst.get_locales_and_langs_sorted_with_names()

        temp_frame = ttk.Frame(MID_FRAME)
        temp_frame.pack()
        lang_list_fedora = ttk.Treeview(temp_frame, columns='lang', show='headings', height=8)
        lang_list_fedora.heading('lang', text=LN.lang)
        lang_list_fedora.pack(anchor=DI_VAR['w'], side=DI_VAR['l'], ipady=5, padx=5)
        locale_list_fedora = ttk.Treeview(temp_frame, columns='locale', show='headings', height=8)
        locale_list_fedora.heading('locale', text=LN.locale)
        locale_list_fedora.pack(anchor=DI_VAR['w'], side=DI_VAR['l'], ipady=5, padx=5)

        for i in range(len(langs_and_locales)):
            lang_list_fedora.insert(parent='', index='end', iid=str(i), values=('%s (%s)' % langs_and_locales[i][0][:2],))

        def on_lang_click(*args):
            for item in locale_list_fedora.get_children():
                locale_list_fedora.delete(item)
            for locale in langs_and_locales[int(lang_list_fedora.focus())][1]:
                locale_list_fedora.insert(parent='', index='end', iid=locale[2], values=locale[1:2])
        lang_list_fedora.bind('<<TreeviewSelect>>', on_lang_click)

        def next_btn_action(*args):
            selected_locale = locale_list_fedora.focus()
            if autoinst.langtable.parse_locale(selected_locale).language:
                GV.AUTOINST.locale = selected_locale
                return page_autoinst_addition_2()

    def page_autoinst_addition_2():
        """the autoinstall page on which you choose your timezone and keyboard layout"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        tkt.generic_page_layout(MID_FRAME, LN.title_autoinst3,
                                LN.btn_next, lambda: next_btn_action(),
                                LN.btn_back, lambda: page_autoinst_addition_1())

        custom_timezone_var = tk.StringVar(app, GV.AUTOINST.timezone)
        custom_keymap_var = tk.StringVar(app)
        if GV.AUTOINST.keymap_type == 'vc':
            custom_keymap_var.set(GV.AUTOINST.keymap)

        keymap_timezone_source_var = tk.StringVar(app, GV.AUTOINST.keymap_timezone_source)

        chosen_locale_name = autoinst.langtable.language_name(languageId=GV.AUTOINST.locale)
        if GV.IP_LOCALE:
            locale_from_ip = autoinst.langtable.list_locales(territoryId=GV.IP_LOCALE[0])[0]
            locale_from_ip_name = autoinst.langtable.language_name(languageId=locale_from_ip)
            if locale_from_ip != GV.AUTOINST.locale:
                tkt.add_radio_btn(MID_FRAME, LN.keymap_tz_option % locale_from_ip_name, keymap_timezone_source_var,
                                  'ip', command=lambda: spawn_more_widgets())

        tkt.add_radio_btn(MID_FRAME, LN.keymap_tz_option % chosen_locale_name, keymap_timezone_source_var, 'select', lambda: spawn_more_widgets())
        tkt.add_radio_btn(MID_FRAME, LN.keymap_tz_custom, keymap_timezone_source_var, 'custom', lambda: spawn_more_widgets())

        timezone_all = sorted(autoinst.all_timezones())
        lists_frame = ttk.Frame(MID_FRAME)
        timezone_txt = ttk.Label(lists_frame, wraplength=540, justify=DI_VAR['l'], text=LN.list_timezones, font=FONTS['tiny'])
        timezone_list = ttk.Combobox(lists_frame, name="timezone", textvariable=custom_timezone_var)
        timezone_list['values'] = tuple(timezone_all)
        timezone_list['state'] = 'readonly'

        all_keymaps = autoinst.get_available_keymaps()

        keyboards_txt = ttk.Label(lists_frame, wraplength=540, justify=DI_VAR['l'], text=LN.list_keymaps, font=FONTS['tiny'])
        keyboard_list = ttk.Combobox(lists_frame, name="keyboard", textvariable=custom_keymap_var)
        keyboard_list['values'] = tuple(all_keymaps)
        keyboard_list['state'] = 'readonly'

        if GV.IP_LOCALE:
            timezone_list.set(GV.IP_LOCALE[1])

        def spawn_more_widgets(*args):
            if keymap_timezone_source_var.get() == 'custom':
                lists_frame.pack(fill='x', padx=20)
                keyboards_txt.grid(pady=5, padx=5, column=0, row=1, sticky=DI_VAR['w'])
                keyboard_list.grid(pady=5, padx=5, column=1, row=1)
                timezone_txt.grid(pady=5, padx=5, column=0, row=0, sticky=DI_VAR['w'])
                timezone_list.grid(pady=5, padx=5, column=1, row=0)
            else:
                lists_frame.pack_forget()

        def next_btn_action(*args):
            if keymap_timezone_source_var.get() == 'custom':
                GV.AUTOINST.keymap = custom_keymap_var.get()
                GV.AUTOINST.keymap_type = 'vc'
                GV.AUTOINST.timezone = custom_timezone_var.get()
            GV.AUTOINST.keymap_timezone_source = keymap_timezone_source_var.get()
            page_verify()

    def page_verify():
        """the page on which you get to review your selection before starting to install"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set('')
        tkt.generic_page_layout(MID_FRAME, LN.verify_question,
                                LN.btn_install, lambda: next_btn_action(),
                                LN.btn_back, lambda: validate_back_page())

        auto_restart_toggle_var = tk.BooleanVar(app, GV.INSTALL_OPTIONS.auto_restart)
        torrent_toggle_var = tk.BooleanVar(app, GV.INSTALL_OPTIONS.torrent)

        # GETTING ARGUMENTS READY
        tmp_part_size: int = GV.INSTALL_OPTIONS.spin['size'] + fn.gigabyte(temp_part_failsafe_space)
        if GV.INSTALL_OPTIONS.spin['is_live_img']:
            tmp_part_size += GV.LIVE_OS_INSTALLER_SPIN['size']
        if GV.AUTOINST.export_wifi:
            wifi_profiles = prc.get_wifi_profiles(GV.DOWNLOAD_PATH)
        else:
            wifi_profiles = None
        part_kwargs = {"tmp_part_size": tmp_part_size, "temp_part_label": GV.TMP_PARTITION_LABEL, "queue": GLOBAL_QUEUE}
        if GV.INSTALL_OPTIONS.install_method != 'custom':
            if GV.AUTOINST.keymap_timezone_source == 'ip':
                GV.AUTOINST.keymap = autoinst.get_keymaps(territory=GV.IP_LOCALE[0])[0]
                GV.AUTOINST.keymap_type = 'xlayout'
                GV.AUTOINST.timezone = autoinst.langtable.list_timezones(territoryId=GV.IP_LOCALE[0])[0]
            elif GV.AUTOINST.keymap_timezone_source == 'select':
                GV.AUTOINST.keymap = autoinst.get_keymaps(lang=GV.AUTOINST.locale)[0]
                GV.AUTOINST.keymap_type = 'xlayout'
                GV.AUTOINST.timezone = autoinst.langtable.list_timezones(languageId=GV.AUTOINST.locale)[0]
            elif GV.AUTOINST.keymap_timezone_source == 'custom':
                pass
            ks_kwargs = {'ostree_args': GV.INSTALL_OPTIONS.spin['ostree_args'],
                         'is_encrypted': GV.AUTOINST.enable_encryption,
                         'passphrase': GV.AUTOINST.encryption_pass,
                         'wifi_profiles': wifi_profiles,
                         'keymap': GV.AUTOINST.keymap,
                         'keymap_type': GV.AUTOINST.keymap_type,
                         'lang': GV.AUTOINST.locale,
                         'timezone': GV.AUTOINST.timezone,
                         'username': GV.AUTOINST.username,
                         'fullname': GV.AUTOINST.fullname,
                         'live_img_url': GV.INSTALL_OPTIONS.live_img_url}
            if GV.INSTALL_OPTIONS.install_method == 'dualboot':
                part_kwargs["shrink_space"] = fn.gigabyte(GV.AUTOINST.dualboot_size)
                part_kwargs["boot_part_size"] = fn.gigabyte(linux_boot_partition_size)
                part_kwargs["efi_part_size"] = fn.megabyte(linux_efi_partition_size)
            # LOG #################################################################
            fn.log('\nKickstart arguments (sensitive data sensored):')
            for key, value in ks_kwargs.items():
                if key in ('passphrase', 'fullname', 'username', 'wifi_profiles'):
                    if not value:
                        continue
                    fn.log('%s: (sensitive data)' % key)
                else:
                    fn.log('%s: %s' % (key, value))
            fn.log('\nPartitioning details:')
            for key, value in part_kwargs.items():
                fn.log('%s: %s' % (key, value))
            #######################################################################
        else:
            ks_kwargs = {}
        if GV.INSTALL_OPTIONS.spin['is_live_img']:
            installer_img = GV.LIVE_OS_INSTALLER_SPIN
            live_os = GV.INSTALL_OPTIONS.spin
            live_os_size = live_os['size']
            total_download_size = live_os['size'] + installer_img['size']
        else:
            installer_img = GV.INSTALL_OPTIONS.spin
            live_os = None
            live_os_size = 0
            total_download_size = installer_img['size']
        installer_dl_percent_factor = installer_img['size'] / total_download_size * 0.90
        live_img_dl_factor = live_os_size / total_download_size * 0.90

        installation = {'ks_kwargs': ks_kwargs, 'part_kwargs': part_kwargs, 'installer_img': installer_img,
                        'is_live_img': GV.INSTALL_OPTIONS.spin['is_live_img'],
                        'live_img': live_os,
                        'installer_img_dl_percent_factor': installer_dl_percent_factor,
                        'live_img_dl_factor': live_img_dl_factor}

        # Constructing user verification text based on user's selections  ++++++++++++++++++++++++++++++++++++++++++++++
        review_sel = []
        if GV.INSTALL_OPTIONS.install_method == 'custom':
            review_sel.append(LN.verify_text['no_autoinst'] % GV.INSTALL_OPTIONS.spin[NAME])
        else:
            if GV.INSTALL_OPTIONS.install_method == 'dualboot':
                review_sel.append(LN.verify_text['autoinst_dualboot'] % GV.INSTALL_OPTIONS.spin[NAME])
                review_sel.append(LN.verify_text['autoinst_keep_data'])
            elif GV.INSTALL_OPTIONS.install_method == 'clean':
                review_sel.append(LN.verify_text['autoinst_clean'] % GV.INSTALL_OPTIONS.spin[NAME])
                review_sel.append(LN.verify_text['autoinst_rm_all'])
            if GV.AUTOINST.export_wifi:
                review_sel.append(LN.verify_text['autoinst_wifi'] % GV.INSTALL_OPTIONS.spin[NAME])
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        review_tree = ttk.Treeview(MID_FRAME, columns='error', show='', height=3)
        review_tree.pack(anchor=DI_VAR['w'], ipady=5, pady=10, padx=(0, 5), fill='x')
        review_tree.configure(selectmode='none')

        for i in range(len(review_sel)):
            review_tree.insert('', index='end', iid=str(i), values=(review_sel[i],))
        # additions options (checkboxes)
        c2_add = ttk.Checkbutton(MID_FRAME, text=LN.add_auto_restart, variable=auto_restart_toggle_var, onvalue=1, offvalue=0)
        c2_add.pack(anchor=DI_VAR['w'])
        c3_add = ttk.Checkbutton(MID_FRAME, text=LN.add_torrent, variable=torrent_toggle_var, onvalue=1, offvalue=0)
        more_options_btn = ttk.Label(MID_FRAME, justify="center", text=LN.more_options, font=FONTS['tiny'], foreground='#3aa9ff')
        more_options_btn.pack(pady=10, padx=10, anchor=DI_VAR['w'])
        more_options_btn.bind("<Button-1>",
                              lambda x: (more_options_btn.destroy(), c3_add.pack(anchor=DI_VAR['w'])))

        def validate_back_page(*args):
            if GV.INSTALL_OPTIONS.install_method == 'custom':
                page_install_method()
            else:
                page_autoinst_addition_2()

        def next_btn_action(*args):
            GV.INSTALL_OPTIONS.auto_restart = auto_restart_toggle_var.get()
            GV.INSTALL_OPTIONS.torrent = torrent_toggle_var.get()
            return page_installing(**installation)

    def page_installing(ks_kwargs: dict, part_kwargs: dict,
                        installer_img, installer_img_dl_percent_factor: float,
                        is_live_img: bool, live_img=None, live_img_dl_factor: float = 0):
        """the page on which the initial installation (creating bootable media) takes place"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set(LN.install_running)
        progressbar_install = ttk.Progressbar(MID_FRAME, orient='horizontal', length=550, mode='determinate')
        progressbar_install.pack(pady=25)
        job_var = tk.StringVar()
        current_job = ttk.Label(MID_FRAME, wraplength=540, justify=DI_VAR['l'], textvariable=job_var, font=FONTS['small'])
        current_job.pack(padx=10, anchor=DI_VAR['w'])


        # INSTALL STARTING
        while GV.INSTALLER_STATUS not in (0, -1, -2):
            if GV.INSTALLER_STATUS is None:  # first step, start the download
                while GLOBAL_QUEUE.qsize(): GLOBAL_QUEUE.get()  # to empty the queue
                progressbar_install['value'] = 0
                job_var.set(LN.job_starting_download)
                app.update()
                fn.mkdir(GV.DOWNLOAD_PATH)
                is_torrent_dl = GV.INSTALL_OPTIONS.torrent
                # checking if files from previous runs are present
                installer_exist = prc.check_valid_existing_file(GV.INSTALL_ISO_PATH, installer_img['hash256'])
                live_img_exist = prc.check_valid_existing_file(GV.LIVE_ISO_PATH, live_img['hash256'])

                if not installer_exist:
                    while True:
                        dl_hash = prc.start_download(main_gui=app, aria2location=GV.ARIA2C_LOCATION, dl_path=GV.DOWNLOAD_PATH,
                                                     spin=installer_img,
                                                     iso_file_new_name=GV.INSTALL_ISO_NAME,
                                                     progress_bar=progressbar_install,
                                                     progress_factor=installer_img_dl_percent_factor, status_shared_var=job_var,
                                                     ln_speed=LN.dl_speed, ln_job=LN.job_dl_install_media, ln_dl_timeleft=LN.dl_timeleft,
                                                     queue=GLOBAL_QUEUE, do_torrent_dl=is_torrent_dl)
                        job_var.set(LN.job_checksum)
                        if download_hash_handler(dl_hash): break  # re-download if file checksum didn't match expected
                if not is_live_img:
                    GV.INSTALLER_STATUS = 2
                else:
                    if not live_img_exist:
                        while True:
                            dl_hash = prc.start_download(main_gui=app, aria2location=GV.ARIA2C_LOCATION, dl_path=GV.DOWNLOAD_PATH,
                                                         spin=live_img,
                                                         iso_file_new_name=GV.LIVE_ISO_NAME,
                                                         progress_bar=progressbar_install,
                                                         progress_factor=live_img_dl_factor, status_shared_var=job_var,
                                                         ln_speed=LN.dl_speed, ln_job=LN.job_dl_install_media,
                                                         ln_dl_timeleft=LN.dl_timeleft,
                                                         queue=GLOBAL_QUEUE, do_torrent_dl=is_torrent_dl)
                            job_var.set(LN.job_checksum)
                            if download_hash_handler(dl_hash): break  # re-download if file checksum didn't match expected
                    GV.INSTALLER_STATUS = 2

            if GV.INSTALLER_STATUS == 2:  # step 2: create temporary boot partition
                while GLOBAL_QUEUE.qsize(): GLOBAL_QUEUE.get()  # to empty the queue
                app.protocol("WM_DELETE_WINDOW", False)  # prevent closing the app during partition

                Process(target=prc.partition_procedure, kwargs=part_kwargs).start()
                job_var.set(LN.job_creating_tmp_part)
                progressbar_install['value'] = 92
                GV.INSTALLER_STATUS = 3

            if GV.INSTALLER_STATUS == 3:  # while creating partition is ongoing...
                while not GLOBAL_QUEUE.qsize():
                    app.after(200, app.update())
                tmp_part_result = GLOBAL_QUEUE.get()
                if tmp_part_result[0] != 1:
                    return
                else:
                    GV.TMP_PARTITION_LETTER = tmp_part_result[1]
                    GV.INSTALLER_STATUS = 4

            if GV.INSTALLER_STATUS == 4:  # step 3: mount iso and copy files to temporary boot partition
                while GLOBAL_QUEUE.qsize(): GLOBAL_QUEUE.get()  # to empty the queue
                app.protocol("WM_DELETE_WINDOW", None)  # re-enable closing the app
                job_var.set(LN.job_copying_to_tmp_part)
                progressbar_install['value'] = 94
                installer_mount_letter = fn.mount_iso(GV.INSTALL_ISO_PATH)
                source_files = installer_mount_letter + ':\\'
                destination_files = GV.TMP_PARTITION_LETTER + ':\\'
                Process(target=fn.copy_files, args=(source_files, destination_files, GLOBAL_QUEUE,)).start()
                while not GLOBAL_QUEUE.qsize(): app.after(200, app.update())
                if GLOBAL_QUEUE.get() == 1: pass  # NEED EDIT
                if is_live_img:
                    live_img_mount_letter = fn.mount_iso(GV.LIVE_ISO_PATH)
                    source_file = live_img_mount_letter + ':\\LiveOS\\'
                    destination = GV.TMP_PARTITION_LETTER + ':\\LiveOS\\'
                    Process(target=fn.copy_files, args=(source_file, destination, GLOBAL_QUEUE,)).start()
                    while not GLOBAL_QUEUE.qsize():
                        app.after(200, app.update())
                    if GLOBAL_QUEUE.get() == 1: pass
                GV.INSTALLER_STATUS = 5

            if GV.INSTALLER_STATUS == 5:  # step 4: adding boot entry
                while GLOBAL_QUEUE.qsize(): GLOBAL_QUEUE.get()  # to empty the queue
                job_var.set(LN.job_adding_tmp_boot_entry)
                progressbar_install['value'] = 98
                if GV.INSTALL_OPTIONS.install_method != 'custom': grub_cfg_file = GV.GRUB_CONFIG_PATH_AUTOINST
                else: grub_cfg_file = GV.GRUB_CONFIG_PATH_DEFUALT
                grub_cfg_dest_path = GV.TMP_PARTITION_LETTER + ':\\EFI\\BOOT\\grub.cfg'
                fn.set_file_readonly(grub_cfg_dest_path, False)
                fn.copy_and_rename_file(grub_cfg_file, grub_cfg_dest_path)
                grub_cfg_txt = prc.build_grub_cfg_file(GV.TMP_PARTITION_LABEL, GV.INSTALL_OPTIONS.install_method != 'custom')
                fn.set_file_readonly(grub_cfg_dest_path, False)
                grub_cfg = open(grub_cfg_dest_path, 'w')
                grub_cfg.write(grub_cfg_txt)
                grub_cfg.close()
                fn.set_file_readonly(grub_cfg_dest_path, True)
                nvidia_script_dest_path = GV.TMP_PARTITION_LETTER + ':\\lnixify\\nvidia_inst'
                fn.copy_and_rename_file(GV.NVIDIA_SCRIPT_PATH, nvidia_script_dest_path)

                if GV.INSTALL_OPTIONS.install_method != 'custom':
                    kickstart_txt = prc.build_autoinstall_ks_file(**ks_kwargs)
                    if kickstart_txt:
                        kickstart = open(GV.TMP_PARTITION_LETTER + ':\\ks.cfg', 'w')
                        kickstart.write(kickstart_txt)
                        kickstart.close()
                app.protocol("WM_DELETE_WINDOW", False)  # prevent closing the app
                if GV.INSTALL_OPTIONS.install_method == 'dualboot':
                    is_new_boot_order_permanent = False
                else:
                    is_new_boot_order_permanent = True
                Process(target=prc.add_boot_entry, args=(default_efi_file_path, GV.TMP_PARTITION_LETTER,
                                                         is_new_boot_order_permanent, GLOBAL_QUEUE,)).start()
                GV.INSTALLER_STATUS = 7

            if GV.INSTALLER_STATUS == 7:  # while adding boot entry is ongoing...
                while not GLOBAL_QUEUE.qsize():
                    app.after(200, app.update())
                if GLOBAL_QUEUE.get() == 1:
                    GV.INSTALLER_STATUS = 8
            if GV.INSTALLER_STATUS == 8:  # step 5: clean up iso and other downloaded files since install is complete
                fn.unmount_iso(GV.INSTALL_ISO_PATH)
                fn.unmount_iso(GV.LIVE_ISO_PATH)
                fn.remove_drive_letter(GV.TMP_PARTITION_LETTER)
                # fn.rmdir(DOWNLOAD_PATH)
                fn.set_windows_time_to_utc()
                GV.INSTALLER_STATUS = 9

            if GV.INSTALLER_STATUS == 9:  # step 6: redirect to next page
                app.protocol("WM_DELETE_WINDOW", None)  # re-enable closing the app
                GV.INSTALLER_STATUS = 0

        return page_restart_required()

    def page_restart_required():
        """the page on which user is prompted to restart the device to continue installation (boot into install media)"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set('')
        tkt.generic_page_layout(MID_FRAME, LN.finished_title,
                                LN.btn_restart_now, lambda: [fn.restart_windows(), tkt.app_quite()],
                                LN.btn_restart_later, lambda: tkt.app_quite())
        text_var = tk.StringVar()
        tkt.add_text_label(MID_FRAME, text=LN.finished_text, font=FONTS['small'], pady=10)
        tkt.add_text_label(MID_FRAME, var=text_var, font=FONTS['small'], pady=10)

        if GV.INSTALL_OPTIONS.auto_restart:
            time_left = 10
            while time_left > 0:
                text_var.set(LN.finished_text_restarting_now % (int(time_left)))
                time_left = time_left - 0.2
                app.after(200, app.update())
            fn.restart_windows()
            tkt.app_quite()

    page_check()
    #fn.get_admin()
    #print('"%s"' % fn.get_user_home_dir())
    app.mainloop()


if __name__ == '__main__': main()
