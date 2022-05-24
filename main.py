from multiprocessing import Process, Queue
import functions as fn
import procedure as prc
import multilingual
import tkinter_templates as tkt
from tkinter_templates import tk, ttk, FONTS
from APP_INFO import *
from autoinst import langtable, get_locales_and_langs_sorted_with_names, all_timezones, get_available_keymaps, \
    get_keymaps

#   DRIVER CODE   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
CURRENT_DIR = fn.get_current_dir_path()
app = tkt.init_tkinter(SW_NAME)
tkt.stylize(app, theme_dir=CURRENT_DIR + '/theme/azure-dark.tcl', theme_name='azure')
#   MAIN CONTAINER & FRAMES   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
CONTAINER = ttk.Frame(app)
CONTAINER.pack()
vTitleText = tk.StringVar(app)
def gui_builder(frames=None):
    return tkt.build_main_gui_frames(CONTAINER, vTitleText,  left_frame_img_path='resources\\left_frame.png', frames=frames)
TOP_FRAME, MID_FRAME, LEFT_FRAME = gui_builder()
#   INITIALIZING GLOBAL VARIABLES /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
GLOBAL_QUEUE = Queue()
COMPATIBILITY_RESULTS = {}
COMPATIBILITY_CHECK_STATUS = 0
INSTALLER_STATUS = None
IP_LOCALE = []
INSTALL_OPTIONS = {'spin': {}, 'spin_index': -2, 'auto_restart': False, 'torrent': False, 'live_img_url': ''}
AUTOINST = {'is_on': True, 'method': '', 'dualboot_size': dualboot_required_space,
            'export_wifi': True, 'enable_encryption': False, 'encryption_pass': '',
            'locale': '', 'timezone': '', 'keymap_timezone_source': 'select', 'keymap': '', 'keymap_type': '',
            'username': '', 'fullname': ''}
DOWNLOAD_PATH = ''
INSTALL_ISO_NAME = 'install_media.iso'
LIVE_ISO_NAME = 'live_os.iso'
LIVE_ISO_PATH = ''
INSTALL_ISO_PATH = ''
TMP_PARTITION_LETTER = ''
ARIA2C_LOCATION = ''
TMP_PARTITION_LABEL = 'FEDORA-INST'  # Max 12 Chars
GRUB_CONFIG_DIR = CURRENT_DIR + '\\resources\\grub_conf\\'
# Tkinter variables, the '_t' suffix means Toggle
ALL_SPINS = []
ACCEPTED_SPINS = []
LIVE_OS_INSTALLER_SPIN = None
# autoinstaller variables
USERNAME_WINDOWS = ''


#   MULTI-LINGUAL /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
def language_handler(new_language=None, current_page=None):
    global DI_VAR, LN, TOP_FRAME, MID_FRAME, LEFT_FRAME
    if new_language is None: new_language = lang_var.get()
    DI_VAR, LN = multilingual.change_lang(new_lang=new_language)
    gui_builder(frames=[TOP_FRAME, LEFT_FRAME, MID_FRAME])
    if current_page is not None:
        return current_page()


language_handler(new_language='English')
lang_var = tk.StringVar()
LANG_LIST = tkt.add_lang_list(TOP_FRAME, lang_var, multilingual.available_languages.keys())


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
                fn.rmdir(DOWNLOAD_PATH)
            tkt.app_quite()
    else:
        question = tkt.open_popup(parent=app, title_txt=LN.job_checksum_mismatch,
                                  msg_txt=LN.job_checksum_mismatch_txt % dl_hash,
                                  primary_btn_str=LN.btn_yes, secondary_btn_str=LN.btn_no)
        if question:
            pass
        else:
            question = tkt.open_popup(parent=app, title_txt=LN.cleanup_question,
                                      msg_txt=LN.cleanup_question_txt,
                                      primary_btn_str=LN.btn_yes, secondary_btn_str=LN.btn_no)
            if question:
                fn.rmdir(DOWNLOAD_PATH)
            tkt.app_quite()


def main():
    def page_check():
        """The page on which is decided whether the app can run on the device or not"""
        # ************** Multilingual support *************************************************************************
        def current_page(): page_check()
        def change_callback(*args): language_handler(current_page=current_page)
        LANG_LIST.bind('<<ComboboxSelected>>', change_callback)
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        title = tkt.add_page_title(MID_FRAME, LN.check_running)

        progressbar_check = ttk.Progressbar(MID_FRAME, orient='horizontal', length=550, mode='determinate')
        progressbar_check.pack(pady=25)
        job_var = tk.StringVar()
        tkt.add_text_label(MID_FRAME, var=job_var, pady=0, padx=10)
        app.update()
        # Request elevation (admin) if not running as admin
        fn.get_admin()
        global COMPATIBILITY_RESULTS, COMPATIBILITY_CHECK_STATUS, IP_LOCALE, ACCEPTED_SPINS, ALL_SPINS
        # COMPATIBILITY_RESULTS = {'uefi': 1, 'ram': 34359738368, 'space': 133264248832, 'resizable': 432008358400, 'arch': 'amd64'}
        # COMPATIBILITY_RESULTS = {'uefi': 0, 'ram': 3434559, 'space': 1332642488, 'resizable': 4320083, 'arch': 'arm'}
        if not COMPATIBILITY_RESULTS:
            if not COMPATIBILITY_CHECK_STATUS:
                Process(target=prc.compatibility_test, args=(minimal_required_space, GLOBAL_QUEUE,)).start()
                # Try to detect GEO-IP locale while compatibility check is running. Timeout once check has finished
                Process(target=fn.get_json, args=(FEDORA_GEO_IP_URL, GLOBAL_QUEUE,)).start()
                Process(target=fn.get_json, args=(AVAILABLE_SPINS_LIST, GLOBAL_QUEUE,)).start()
                COMPATIBILITY_CHECK_STATUS = 1
            if COMPATIBILITY_CHECK_STATUS == 1:
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
                        ALL_SPINS = queue_out
                    elif isinstance(queue_out, dict) and queue_out.keys() >= {"country_code", "time_zone"}:
                        IP_LOCALE = (queue_out['country_code'], queue_out['time_zone'])
                    elif isinstance(queue_out, dict) and queue_out.keys() >= {"arch", "uefi"}:
                        COMPATIBILITY_RESULTS = queue_out
                        COMPATIBILITY_CHECK_STATUS = 2
                        job_var.set(LN.check_available_downloads)
                        progressbar_check['value'] = 95
                    if COMPATIBILITY_RESULTS and ALL_SPINS:
                        break
        errors = []
        if COMPATIBILITY_RESULTS['arch'] == -1: errors.append(LN.error_arch_9)
        elif COMPATIBILITY_RESULTS['arch'] != 'amd64': errors.append(LN.error_arch_0)
        if COMPATIBILITY_RESULTS['uefi'] == -1: errors.append(LN.error_uefi_9)
        elif COMPATIBILITY_RESULTS['uefi'] != 1: errors.append(LN.error_uefi_0)
        if COMPATIBILITY_RESULTS['ram'] == -1: errors.append(LN.error_totalram_9)
        elif COMPATIBILITY_RESULTS['ram'] < fn.gigabyte(minimal_required_ram): errors.append(LN.error_totalram_0)
        if COMPATIBILITY_RESULTS['space'] == -1: errors.append(LN.error_space_9)
        elif COMPATIBILITY_RESULTS['space'] < fn.gigabyte(minimal_required_space): errors.append(LN.error_space_0)
        if COMPATIBILITY_RESULTS['resizable'] == -1: errors.append(LN.error_resizable_9)
        elif COMPATIBILITY_RESULTS['resizable'] < fn.gigabyte(minimal_required_space): errors.append(LN.error_resizable_0)

        if not errors:
            global DOWNLOAD_PATH, INSTALL_ISO_PATH, LIVE_ISO_PATH, USERNAME_WINDOWS, ACCEPTED_SPINS,\
                LIVE_OS_INSTALLER_SPIN, ARIA2C_LOCATION
            live_os_installer_index, ACCEPTED_SPINS = prc.parse_spins(ALL_SPINS)
            LIVE_OS_INSTALLER_SPIN = ACCEPTED_SPINS[live_os_installer_index]
            DOWNLOAD_PATH = fn.get_user_home_dir() + "\\win2linux_tmpdir"
            INSTALL_ISO_PATH = DOWNLOAD_PATH + "\\" + INSTALL_ISO_NAME
            LIVE_ISO_PATH = DOWNLOAD_PATH + "\\" + LIVE_ISO_NAME
            ARIA2C_LOCATION = CURRENT_DIR + '\\resources\\aria2c.exe'
            USERNAME_WINDOWS = fn.get_windows_username()
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
        # ************** Multilingual support *************************************************************************
        def page_name(): page_1()
        def change_callback(*args): language_handler(current_page=page_name)
        LANG_LIST.bind('<<ComboboxSelected>>', change_callback)
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set('Welcome to Lnixify')
        tkt.generic_page_layout(MID_FRAME, LN.distro_question, LN.btn_next, lambda: next_btn_action())
        spin_var = tk.IntVar(app, INSTALL_OPTIONS['spin_index'])
        autoinstall_toggle_var = tk.BooleanVar(app, AUTOINST['is_on'])

        for index, dist in enumerate(ACCEPTED_SPINS):
            txt = ''  # Generating Text for each list member of installable flavors/distros
            if dist['is_advanced']: txt += LN.adv + ': '
            txt += '%s %s' % (dist['name'], dist['version'])
            if dist['desktop']: txt += ' (%s)' % dist['desktop']
            if dist['is_netinstall']: txt += ' (%s)' % LN.net_install
            if dist['is_recommended']:
                if spin_var.get() == -2: spin_var.set(index)  # If unset, set it to the default recommended entry
                txt += ' (%s)' % LN.recommended
            temp_frame = ttk.Frame(MID_FRAME)
            temp_frame.pack(fill="x", pady=5)
            radio = tkt.add_radio_btn(temp_frame, txt, spin_var, index, ipady=0, side=DI_VAR['l'], command=lambda: validate_input())
            if dist['is_live_img']:
                total_size = LIVE_OS_INSTALLER_SPIN['size'] + dist['size']
            else:
                total_size = dist['size']
            if dist['is_netinstall']:
                dl_size_txt = LN.init_download % fn.byte_to_gb(total_size)
            else:
                dl_size_txt = LN.total_download % fn.byte_to_gb(total_size)
            ttk.Label(temp_frame, wraplength=540, justify="center", text=dl_size_txt,
                      font=FONTS['tiny'], foreground='#3aa9ff').pack(padx=5, anchor=DI_VAR['e'], side=DI_VAR['r'])
            if COMPATIBILITY_RESULTS['resizable'] < dist['size']:
                radio.configure(state='disabled')
                ttk.Label(temp_frame, wraplength=540, justify="center", text=LN.warn_space,
                          font=FONTS['tiny'], foreground='#ff4a4a').pack(padx=5, anchor=DI_VAR['e'], side=DI_VAR['r'])
                if spin_var.get() == [index]:
                    spin_var.set(-1)

        check_autoinst = tkt.add_check_btn(MID_FRAME, LN.install_auto, autoinstall_toggle_var, pady=40)
        # BUGFIX
        if not ACCEPTED_SPINS[spin_var.get()]['is_auto_installable']:
            check_autoinst.configure(state='disabled')
            autoinstall_toggle_var.set(False)

        def validate_input(*args):
            if ACCEPTED_SPINS[spin_var.get()]['is_advanced']:
                question = tkt.open_popup(parent=app, title_txt=LN.adv_confirm, msg_txt=LN.adv_confirm_text,
                                          primary_btn_str=LN.btn_continue, secondary_btn_str=LN.btn_cancel)
                if not question: spin_var.set(-1)
                else: pass
            if ACCEPTED_SPINS[spin_var.get()]['is_auto_installable']:
                check_autoinst.configure(state='enabled')
                autoinstall_toggle_var.set(True)
            else:
                check_autoinst.configure(state='disabled')
                autoinstall_toggle_var.set(False)

        def next_btn_action(*args):
            if spin_var.get() == -1: return -1
            else:
                LANG_LIST.pack_forget()
                INSTALL_OPTIONS['spin_index'] = spin_var.get()
                INSTALL_OPTIONS['spin'] = ACCEPTED_SPINS[INSTALL_OPTIONS['spin_index']]
                if INSTALL_OPTIONS['spin']['is_live_img']:
                    INSTALL_OPTIONS['live_img_url'] = live_img_url
                AUTOINST['is_on'] = autoinstall_toggle_var.get()
                if autoinstall_toggle_var.get():
                    return page_autoinst1()
                else:
                    return page_verify()

    # page_autoinst1
    def page_autoinst1():
        """the autoinstall page on which you choose whether to install alongside windows or start clean install"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set(LN.install_auto)
        tkt.generic_page_layout(MID_FRAME, LN.windows_question % INSTALL_OPTIONS['spin']['name'],
                                LN.btn_next, lambda: next_btn_action(),
                                LN.btn_back, lambda: page_1())

        autoinst_method_var = tk.StringVar(app, AUTOINST['method'])
        dualboot_size_var = tk.StringVar(app, str(AUTOINST['dualboot_size']))

        r1_frame = ttk.Frame(MID_FRAME)
        r1_frame.pack(fill="x")
        r1_autoinst = tkt.add_radio_btn(r1_frame, LN.windows_options[0], autoinst_method_var, 'dualboot',
                                        lambda: show_dualboot_options(True), side=DI_VAR['l'])
        r1_space = ttk.Label(r1_frame, wraplength=540, justify="center", text=LN.warn_space, font=FONTS['tiny'],
                             foreground='#ff4a4a')
        entry1_frame = ttk.Frame(MID_FRAME)
        entry1_frame.pack(fill='x', padx=10)
        tkt.add_radio_btn(MID_FRAME, LN.windows_options[1], autoinst_method_var, 'clean',
                          lambda: show_dualboot_options(False))

        min_size = dualboot_required_space
        max_size = fn.byte_to_gb(COMPATIBILITY_RESULTS['resizable'] - INSTALL_OPTIONS['spin']['size']) - additional_failsafe_space
        max_size = round(max_size, 2)
        float_regex = r'^[0-9]*\.?[0-9]{0,3}$'  # max 3 decimal digits
        size_dualboot_txt_pre = ttk.Label(entry1_frame, wraplength=540, justify=DI_VAR['l'],
                                          text=LN.dualboot_size_txt, font=FONTS['tiny'])
        size_dualboot_entry = ttk.Entry(entry1_frame, width=10, textvariable=dualboot_size_var)
        size_dualboot_txt_post = ttk.Label(entry1_frame, wraplength=540, justify=DI_VAR['l'],
                                           text='(%sGB - %sGB)' % (min_size, max_size), font=FONTS['tiny'])
        tkt.var_tracer(dualboot_size_var, "write",
                       lambda *args: fn.validate_with_regex(dualboot_size_var, regex=float_regex, mode='fix'))

        # LOGIC
        space_dualboot = fn.gigabyte(dualboot_required_space + additional_failsafe_space) + INSTALL_OPTIONS['spin']['size']
        if COMPATIBILITY_RESULTS['resizable'] < space_dualboot:
            r1_space.pack(padx=20, side=DI_VAR['l'])
            r1_autoinst.configure(state='disabled')

        def show_dualboot_options(is_true: bool):
            if is_true:
                size_dualboot_txt_pre.grid(pady=5, padx=(10, 0), column=0, row=0, sticky=DI_VAR['w'])
                size_dualboot_entry.grid(pady=5, padx=5, column=1, row=0)
                size_dualboot_txt_post.grid(pady=5, padx=(0, 0), column=2, row=0, sticky=DI_VAR['w'])
            else:
                size_dualboot_txt_pre.grid_forget()
                size_dualboot_entry.grid_forget()
                size_dualboot_txt_post.grid_forget()

        if autoinst_method_var.get() == 'dualboot': show_dualboot_options(True)  # GUI bugfix

        def next_btn_action(*args):
            if autoinst_method_var.get() == 'dualboot':
                syntax_valid = fn.validate_with_regex(dualboot_size_var, regex=float_regex,
                                                      mode='read') not in (False, 'empty')
                if syntax_valid and min_size <= float(dualboot_size_var.get()) <= max_size:
                    AUTOINST['dualboot_size'] = float(dualboot_size_var.get())
                else:
                    return -1
            elif autoinst_method_var.get() == 'clean':
                pass
            else:
                return -1
            AUTOINST['method'] = autoinst_method_var.get()
            return page_autoinst2()

    def page_autoinst2():
        """the autoinstall page on which you choose whether to install alongside windows or start clean install"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set(LN.install_auto)
        tkt.generic_page_layout(MID_FRAME, LN.windows_question % INSTALL_OPTIONS['spin']['name'],
                                LN.btn_next, lambda: next_btn_action(),
                                LN.btn_back, lambda: page_autoinst1())

        # tkt.add_check_btn(MID_FRAME, LN.additional_setup_now, vAutoinst_additional_setup_t)
        export_wifi_toggle_var = tk.BooleanVar(app, AUTOINST['export_wifi'])
        enable_encryption_toggle_var = tk.BooleanVar(app, AUTOINST['enable_encryption'])
        encrypt_passphrase_var = tk.StringVar(app, AUTOINST['encryption_pass'])

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
                AUTOINST['export_wifi'] = export_wifi_toggle_var.get()
                AUTOINST['enable_encryption'] = enable_encryption_toggle_var.get()
                if AUTOINST['enable_encryption']:
                    AUTOINST['encryption_pass'] = encrypt_passphrase_var.get()
                page_autoinst_addition_1()

    # page_autoinst2
    def page_autoinst_addition_1():
        """the autoinstall page on which you choose your language and locale"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        tkt.generic_page_layout(MID_FRAME, LN.title_autoinst2,
                                LN.btn_next, lambda: next_btn_action(),
                                LN.btn_back, lambda: page_autoinst2())
        if IP_LOCALE:
            langs_and_locales = get_locales_and_langs_sorted_with_names(territory=IP_LOCALE[0])
        else:
            langs_and_locales = get_locales_and_langs_sorted_with_names()

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
            if langtable.parse_locale(selected_locale).language:
                AUTOINST['locale'] = selected_locale
                return page_autoinst_addition_2()

    def page_autoinst_addition_2():
        """the autoinstall page on which you choose your timezone and keyboard layout"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        tkt.generic_page_layout(MID_FRAME, LN.title_autoinst3,
                                LN.btn_next, lambda: next_btn_action(),
                                LN.btn_back, lambda: page_autoinst_addition_1())

        custom_timezone_var = tk.StringVar(app, AUTOINST['timezone'])
        custom_keymap_var = tk.StringVar(app)
        if AUTOINST['keymap_type'] == 'vc':
            custom_keymap_var.set(AUTOINST['keymap'])

        keymap_timezone_source_var = tk.StringVar(app, AUTOINST['keymap_timezone_source'])

        chosen_locale_name = langtable.language_name(languageId=AUTOINST['locale'])
        if IP_LOCALE:
            locale_from_ip = langtable.list_locales(territoryId=IP_LOCALE[0])[0]
            locale_from_ip_name = langtable.language_name(languageId=locale_from_ip)
            if locale_from_ip != AUTOINST['locale']:
                tkt.add_radio_btn(MID_FRAME, LN.keymap_tz_option % locale_from_ip_name, keymap_timezone_source_var,
                                  'ip', command=lambda: spawn_more_widgets())

        tkt.add_radio_btn(MID_FRAME, LN.keymap_tz_option % chosen_locale_name, keymap_timezone_source_var, 'select', lambda: spawn_more_widgets())
        tkt.add_radio_btn(MID_FRAME, LN.keymap_tz_custom, keymap_timezone_source_var, 'custom', lambda: spawn_more_widgets())

        timezone_all = sorted(all_timezones())
        lists_frame = ttk.Frame(MID_FRAME)
        timezone_txt = ttk.Label(lists_frame, wraplength=540, justify=DI_VAR['l'], text=LN.list_timezones, font=FONTS['tiny'])
        timezone_list = ttk.Combobox(lists_frame, name="timezone", textvariable=custom_timezone_var)
        timezone_list['values'] = tuple(timezone_all)
        timezone_list['state'] = 'readonly'

        all_keymaps = get_available_keymaps()

        keyboards_txt = ttk.Label(lists_frame, wraplength=540, justify=DI_VAR['l'], text=LN.list_keymaps, font=FONTS['tiny'])
        keyboard_list = ttk.Combobox(lists_frame, name="keyboard", textvariable=custom_keymap_var)
        keyboard_list['values'] = tuple(all_keymaps)
        keyboard_list['state'] = 'readonly'

        if IP_LOCALE:
            timezone_list.set(IP_LOCALE[1])

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
                AUTOINST['keymap'] = custom_keymap_var.get()
                AUTOINST['keymap_type'] = 'vc'
                AUTOINST['timezone'] = custom_timezone_var.get()
            AUTOINST['keymap_timezone_source'] = keymap_timezone_source_var.get()
            page_verify()

    def page_verify():
        """the page on which you get to review your selection before starting to install"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set('')
        tkt.generic_page_layout(MID_FRAME, LN.verify_question,
                                LN.btn_install, lambda: next_btn_action(),
                                LN.btn_back, lambda: validate_back_page())

        auto_restart_toggle_var = tk.BooleanVar(app, INSTALL_OPTIONS['auto_restart'])
        torrent_toggle_var = tk.BooleanVar(app, INSTALL_OPTIONS['torrent'])

        # GETTING ARGUMENTS READY
        tmp_part_size: int = INSTALL_OPTIONS['spin']['size'] + fn.gigabyte(temp_part_failsafe_space)
        if INSTALL_OPTIONS['spin']['is_live_img']:
            tmp_part_size += LIVE_OS_INSTALLER_SPIN['size']
        if AUTOINST['export_wifi']:
            wifi_profiles = prc.get_wifi_profiles(DOWNLOAD_PATH)
        else:
            wifi_profiles = None
        part_kwargs = {"tmp_part_size": tmp_part_size, "temp_part_label": TMP_PARTITION_LABEL, "queue": GLOBAL_QUEUE}
        if AUTOINST['is_on']:
            if AUTOINST['keymap_timezone_source'] == 'ip':
                AUTOINST['keymap'] = get_keymaps(territory=IP_LOCALE[0])[0]
                AUTOINST['keymap_type'] = 'xlayout'
                AUTOINST['timezone'] = langtable.list_timezones(territoryId=IP_LOCALE[0])[0]
            elif AUTOINST['keymap_timezone_source'] == 'select':
                AUTOINST['keymap'] = get_keymaps(lang=AUTOINST['locale'])[0]
                AUTOINST['keymap_type'] = 'xlayout'
                AUTOINST['timezone'] = langtable.list_timezones(languageId=AUTOINST['locale'])[0]
            elif AUTOINST['keymap_timezone_source'] == 'custom':
                pass
            ks_kwargs = {'ostree_args': INSTALL_OPTIONS['spin']['ostree_args'],
                         'is_encrypted': AUTOINST['enable_encryption'],
                         'passphrase': AUTOINST['encryption_pass'],
                         'wifi_profiles': wifi_profiles,
                         'keymap': AUTOINST['keymap'],
                         'keymap_type': AUTOINST['keymap_type'],
                         'lang': AUTOINST['locale'],
                         'timezone': AUTOINST['timezone'],
                         'username': AUTOINST['username'],
                         'fullname': AUTOINST['fullname'],
                         'live_img_url': INSTALL_OPTIONS['live_img_url']}
            if AUTOINST['method'] == 'dualboot':
                part_kwargs["shrink_space"] = fn.gigabyte(AUTOINST['dualboot_size'])
                part_kwargs["boot_part_size"] = fn.gigabyte(linux_boot_partition_size)
                part_kwargs["efi_part_size"] = fn.megabyte(linux_efi_partition_size)
        else:
            ks_kwargs = {}
        if INSTALL_OPTIONS['spin']['is_live_img']:
            installer_img = LIVE_OS_INSTALLER_SPIN
            live_os = INSTALL_OPTIONS['spin']
            live_os_size = live_os['size']
            total_download_size = live_os['size'] + installer_img['size']
        else:
            installer_img = INSTALL_OPTIONS['spin']
            live_os = None
            live_os_size = 0
            total_download_size = installer_img['size']
        installer_dl_percent_factor = installer_img['size'] / total_download_size * 0.90
        live_img_dl_factor = live_os_size / total_download_size * 0.90

        installation = {'ks_kwargs': ks_kwargs, 'part_kwargs': part_kwargs, 'installer_img': installer_img,
                        'is_live_img': INSTALL_OPTIONS['spin']['is_live_img'],
                        'live_img': live_os,
                        'installer_img_dl_percent_factor': installer_dl_percent_factor,
                        'live_img_dl_factor': live_img_dl_factor}
        print(installation)
        # Constructing user verification text based on user's selections  ++++++++++++++++++++++++++++++++++++++++++++++
        review_sel = []
        if AUTOINST['is_on'] == 0:
            review_sel.append(LN.verify_text['no_autoinst'] % INSTALL_OPTIONS['spin']['name'])
        else:
            if AUTOINST['method'] == 'dualboot':
                review_sel.append(LN.verify_text['autoinst_dualboot'] % INSTALL_OPTIONS['spin']['name'])
                review_sel.append(LN.verify_text['autoinst_keep_data'])
            elif AUTOINST['method'] == 'clean':
                review_sel.append(LN.verify_text['autoinst_clean'] % INSTALL_OPTIONS['spin']['name'])
                review_sel.append(LN.verify_text['autoinst_rm_all'])
            if AUTOINST['export_wifi']:
                review_sel.append(LN.verify_text['autoinst_wifi'] % INSTALL_OPTIONS['spin']['name'])
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
            if not AUTOINST['is_on']:
                page_1()
            else:
                page_autoinst_addition_2()

        def next_btn_action(*args):
            INSTALL_OPTIONS['auto_restart'] = auto_restart_toggle_var.get()
            INSTALL_OPTIONS['torrent'] = torrent_toggle_var.get()
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

        global INSTALLER_STATUS, TMP_PARTITION_LETTER
        # checking if files from previous runs are present and if so, ask if user wishes to use them.
        INSTALLER_STATUS = 5
        TMP_PARTITION_LETTER = 'G'
        # INSTALL STARTING
        while INSTALLER_STATUS not in (0, -1, -2):
            if INSTALLER_STATUS is None:  # first step, start the download
                while GLOBAL_QUEUE.qsize(): GLOBAL_QUEUE.get()  # to empty the queue
                progressbar_install['value'] = 0
                job_var.set(LN.job_starting_download)
                app.update()
                fn.mkdir(DOWNLOAD_PATH)
                is_torrent_dl = INSTALL_OPTIONS['torrent']
                download_status_var = tk.StringVar()
                installer_exist = False
                live_img_exist = False
                if fn.check_if_exists(INSTALL_ISO_PATH):
                    if fn.check_hash(INSTALL_ISO_PATH, installer_img['hash256']) == 1:
                        installer_exist = True
                    else:
                        fn.rm(INSTALL_ISO_PATH)
                if is_live_img:
                    if fn.check_if_exists(LIVE_ISO_PATH):
                        if fn.check_hash(LIVE_ISO_PATH, live_img['hash256']) == 1:
                            live_img_exist = True
                        else:
                            fn.rm(INSTALL_ISO_PATH)
                if not installer_exist:
                    dl_hash = prc.start_download(main_gui=app, aria2location=ARIA2C_LOCATION, dl_path=DOWNLOAD_PATH, spin=installer_img,
                                                 iso_file_new_name=INSTALL_ISO_NAME, do_spread_files_in_dir=True,
                                                 progress_bar=progressbar_install,
                                                 progress_factor=installer_img_dl_percent_factor, status_shared_var=job_var,
                                                 ln_speed=LN.dl_speed, ln_job=LN.job_dl_install_media, ln_dl_timeleft=LN.dl_timeleft,
                                                 queue=GLOBAL_QUEUE, do_torrent_dl=is_torrent_dl)
                    job_var.set(LN.job_checksum)
                    download_hash_handler(dl_hash)
                if not is_live_img:
                    INSTALLER_STATUS = 2
                else:
                    if not live_img_exist:
                        dl_hash = prc.start_download(main_gui=app, aria2location=ARIA2C_LOCATION, dl_path=DOWNLOAD_PATH,
                                                     spin=live_img,
                                                     iso_file_new_name=LIVE_ISO_NAME, do_spread_files_in_dir=True,
                                                     progress_bar=progressbar_install, progress_factor=live_img_dl_factor,
                                                     status_shared_var=download_status_var,
                                                     ln_speed=LN.dl_speed, ln_job=LN.job_dl_install_media,
                                                     ln_dl_timeleft=LN.dl_timeleft,
                                                     queue=GLOBAL_QUEUE, do_torrent_dl=is_torrent_dl)
                        job_var.set(LN.job_checksum)
                        download_hash_handler(dl_hash)
                    INSTALLER_STATUS = 2

            if INSTALLER_STATUS == 2:  # step 2: create temporary boot partition
                while GLOBAL_QUEUE.qsize(): GLOBAL_QUEUE.get()  # to empty the queue
                app.protocol("WM_DELETE_WINDOW", False)  # prevent closing the app during partition

                Process(target=prc.partition_procedure, kwargs=part_kwargs).start()
                job_var.set(LN.job_creating_tmp_part)
                progressbar_install['value'] = 92
                INSTALLER_STATUS = 3

            if INSTALLER_STATUS == 3:  # while creating partition is ongoing...
                while not GLOBAL_QUEUE.qsize():
                    app.after(200, app.update())
                tmp_part_result = GLOBAL_QUEUE.get()
                if tmp_part_result[0] != 1:
                    return
                else:
                    TMP_PARTITION_LETTER = tmp_part_result[1]
                    INSTALLER_STATUS = 4

            if INSTALLER_STATUS == 4:  # step 3: mount iso and copy files to temporary boot partition
                while GLOBAL_QUEUE.qsize(): GLOBAL_QUEUE.get()  # to empty the queue
                app.protocol("WM_DELETE_WINDOW", None)  # re-enable closing the app
                job_var.set(LN.job_copying_to_tmp_part)
                progressbar_install['value'] = 94
                installer_mount_letter = fn.mount_iso(INSTALL_ISO_PATH)
                source_files = installer_mount_letter + ':\\'
                destination_files = TMP_PARTITION_LETTER + ':\\'
                Process(target=fn.copy_files, args=(source_files, destination_files, GLOBAL_QUEUE,)).start()
                while not GLOBAL_QUEUE.qsize(): app.after(200, app.update())
                if GLOBAL_QUEUE.get() == 1: pass  # NEED EDIT
                if is_live_img:
                    live_img_mount_letter = fn.mount_iso(LIVE_ISO_PATH)
                    source_file = live_img_mount_letter + ':\\LiveOS\\'
                    destination = TMP_PARTITION_LETTER + ':\\LiveOS\\'
                    Process(target=fn.copy_files, args=(source_file, destination, GLOBAL_QUEUE,)).start()
                    while not GLOBAL_QUEUE.qsize():
                        app.after(200, app.update())
                    if GLOBAL_QUEUE.get() == 1: pass
                INSTALLER_STATUS = 5

            if INSTALLER_STATUS == 5:  # step 4: adding boot entry
                while GLOBAL_QUEUE.qsize(): GLOBAL_QUEUE.get()  # to empty the queue
                job_var.set(LN.job_adding_tmp_boot_entry)
                progressbar_install['value'] = 98
                if AUTOINST['is_on']: grub_cfg_file = GRUB_CONFIG_DIR + 'grub_autoinst.cfg'
                else: grub_cfg_file = GRUB_CONFIG_DIR + 'grub_default.cfg'
                grub_cfg_file_path = TMP_PARTITION_LETTER + ':\\EFI\\BOOT\\grub.cfg'
                fn.set_file_readonly(grub_cfg_file_path, False)
                fn.copy_and_rename_file(grub_cfg_file, grub_cfg_file_path)
                grub_cfg_txt = prc.build_grub_cfg_file(TMP_PARTITION_LABEL, AUTOINST['is_on'])
                fn.set_file_readonly(grub_cfg_file_path, False)
                grub_cfg = open(grub_cfg_file_path, 'w')
                grub_cfg.write(grub_cfg_txt)
                grub_cfg.close()
                fn.set_file_readonly(grub_cfg_file_path, True)

                if AUTOINST['is_on']:
                    kickstart_txt = prc.build_autoinstall_ks_file(**ks_kwargs)
                    if kickstart_txt:
                        kickstart = open(TMP_PARTITION_LETTER + ':\\ks.cfg', 'w')
                        kickstart.write(kickstart_txt)
                        kickstart.close()
                app.protocol("WM_DELETE_WINDOW", False)  # prevent closing the app
                if AUTOINST['method'] == 'dualboot':
                    is_new_boot_order_permanent = False
                else:
                    is_new_boot_order_permanent = True
                Process(target=prc.add_boot_entry, args=(default_efi_file_path, TMP_PARTITION_LETTER,
                                                         is_new_boot_order_permanent, GLOBAL_QUEUE,)).start()
                INSTALLER_STATUS = 7

            if INSTALLER_STATUS == 7:  # while adding boot entry is ongoing...
                while not GLOBAL_QUEUE.qsize():
                    app.after(200, app.update())
                if GLOBAL_QUEUE.get() == 1:
                    INSTALLER_STATUS = 8
            if INSTALLER_STATUS == 8:  # step 5: clean up iso and other downloaded files since install is complete
                fn.unmount_iso(INSTALL_ISO_PATH)
                fn.unmount_iso(LIVE_ISO_PATH)
                # fn.rmdir(DOWNLOAD_PATH)
                INSTALLER_STATUS = 9

            if INSTALLER_STATUS == 9:  # step 6: redirect to next page
                app.protocol("WM_DELETE_WINDOW", None)  # re-enable closing the app
                INSTALLER_STATUS = 0

        return page_restart_required()

    def page_restart_required():
        """the page on which user is prompted to restart the device to continue installation (boot into install media)"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set('')
        LANG_LIST.pack(anchor=DI_VAR['nw'], padx=10, pady=10)
        tkt.generic_page_layout(MID_FRAME, LN.finished_title,
                                LN.btn_restart_now, lambda: [fn.restart_windows(), tkt.app_quite()],
                                LN.btn_restart_later, lambda: tkt.app_quite())
        text_var = tk.StringVar()
        tkt.add_text_label(MID_FRAME, text=LN.finished_text, font=FONTS['small'], pady=10)
        tkt.add_text_label(MID_FRAME, var=text_var, font=FONTS['small'], pady=10)

        if INSTALL_OPTIONS['auto_restart']:
            time_left = 10
            while time_left > 0:
                text_var.set(LN.finished_text_restarting_now % (int(time_left)))
                time_left = time_left - 0.2
                app.after(200, app.update())
            fn.restart_windows()
            tkt.app_quite()

    page_check()
    app.mainloop()


if __name__ == '__main__': main()
