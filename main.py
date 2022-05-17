from multiprocessing import Process, Queue

import functions as fn
import multilingual
import tkinter_templates as tkt
from tkinter_templates import tk, ttk, FONTS
from APP_INFO import *
from autoinst import get_available_translations, langtable, get_locales_and_langs_sorted_with_names, all_timezones, \
    detect_locale, get_available_keymaps
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
INSTALLER_STATUS = 0
IP_LOCALE = []
AUTOINST = {'locale': '', 'timezone': '', 'keymap': '', 'username': '', 'fullname': ''}
DOWNLOAD_PATH = ''
ISO_NAME = 'install_media.iso'
ISO_PATH = ''
MOUNT_ISO_LETTER = ''
TMP_PARTITION_LETTER = ''
TMP_PARTITION_LABEL = 'FEDORA-INST'  # Max 12 Chars
GRUB_CONFIG_DIR = CURRENT_DIR + '\\resources\\grub_conf\\'
# Tkinter variables, the '_t' suffix means Toggle
vDist = tk.IntVar(app, -2)
vAutoinst_t = tk.IntVar(app, 1)
vAutoinst_option = tk.IntVar(app, -1)
vAutoinst_Wifi_t = tk.IntVar(app, 1)
vAutoinst_Encrypt_t = tk.IntVar(app, 0)
vAutoinst_additional_setup_t = tk.IntVar(app, 0)

vAutorestart_t = tk.IntVar(app, 0)
vTorrent_t = tk.IntVar(app, 0)
# autoinstaller variables
vKeymap_timezone_source = tk.IntVar(app, value=1)
vAutoinst_Keyboard = tk.StringVar(app)
vAutoinst_Timezone = tk.StringVar(app)
vAutoinst_Fullname = tk.StringVar(app, '')
vAutoinst_Username = tk.StringVar(app, '')
vAutoinst_Encrypt_Passphrase = tk.StringVar(app)
vAutoinst_dualboot_size = tk.StringVar(app)
Autoinst_SELECTED_LOCALE = ''
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
        fn.get_admin(app)
        global COMPATIBILITY_RESULTS, COMPATIBILITY_CHECK_STATUS, IP_LOCALE
        # COMPATIBILITY_RESULTS = {'uefi': 1, 'ram': 34359738368, 'space': 133264248832, 'resizable': 432008358400, 'arch': 'amd64'}
        # COMPATIBILITY_RESULTS = {'uefi': 0, 'ram': 3434559, 'space': 1332642488, 'resizable': 4320083, 'arch': 'arm'}
        if not COMPATIBILITY_RESULTS:
            if not COMPATIBILITY_CHECK_STATUS:
                Process(target=fn.compatibility_test, args=(minimal_required_space, GLOBAL_QUEUE,)).start()
                # Try to detect GEO-IP locale while compatibility check is running. Timeout once check has finished
                Process(target=detect_locale, args=(GLOBAL_QUEUE,)).start()
                COMPATIBILITY_CHECK_STATUS = 1
            if COMPATIBILITY_CHECK_STATUS == 1:
                while True:
                    while not GLOBAL_QUEUE.qsize(): app.after(200, app.update())
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
                    elif isinstance(queue_out, tuple) and queue_out[0] == 'detect_locale':
                        IP_LOCALE = queue_out[1:]
                    elif isinstance(queue_out, dict):
                        COMPATIBILITY_RESULTS = queue_out
                        print(COMPATIBILITY_RESULTS)
                        COMPATIBILITY_CHECK_STATUS = 2
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
            global DOWNLOAD_PATH, ISO_PATH, USERNAME_WINDOWS
            DOWNLOAD_PATH = fn.get_user_home_dir() + "\\win2linux_tmpdir"
            ISO_PATH = DOWNLOAD_PATH + "\\" + ISO_NAME
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
        tkt.generic_page_layout(MID_FRAME, LN.distro_question, LN.btn_next, lambda: validate_next_page())

        for index, dist in enumerate(dists):
            txt = ''  # Generating Text for each list member of installable flavors/distros
            if dist['advanced']: txt += LN.adv + ': '
            txt += '%s %s' % (dist['name'], dist['version'])
            if dist['de']: txt += ' (%s)' % dist['de']
            if dist['netinstall']: txt += ' (%s)' % LN.net_install
            if dist['recommended']:
                if vDist.get() == -2: vDist.set(index)  # If unset, set it to the default recommended entry
                txt += ' (%s)' % LN.recommended
            temp_frame = ttk.Frame(MID_FRAME)
            temp_frame.pack(fill="x", pady=5)
            radio = tkt.add_radio_btn(temp_frame, txt, vDist, index, ipady=0, side=DI_VAR['l'], command=lambda: validate_input())
            if dist['netinstall']: dl_size_txt = LN.init_download % dist['size']
            else: dl_size_txt = LN.total_download % dist['size']
            ttk.Label(temp_frame, wraplength=540, justify="center", text=dl_size_txt,
                      font=FONTS['tiny'], foreground='#3aa9ff').pack(padx=5, anchor=DI_VAR['e'], side=DI_VAR['r'])
            if COMPATIBILITY_RESULTS['resizable'] < fn.gigabyte(dist['size']):
                radio.configure(state='disabled')
                ttk.Label(temp_frame, wraplength=540, justify="center", text=LN.warn_space,
                          font=FONTS['tiny'], foreground='#ff4a4a').pack(padx=5, anchor=DI_VAR['e'], side=DI_VAR['r'])
                if vDist.get() == [index]:
                    vDist.set(-1)

        check_autoinst = tkt.add_check_btn(MID_FRAME, LN.install_auto, vAutoinst_t, pady=40)
        # BUGFIX
        if not dists[vDist.get()]['auto-installable']:
            check_autoinst.configure(state='disabled')
            vAutoinst_t.set(0)

        def validate_input(*args):
            if dists[vDist.get()]['advanced']:
                question = tkt.open_popup(parent=app, title_txt=LN.adv_confirm, msg_txt=LN.adv_confirm_text,
                                          primary_btn_str=LN.btn_continue, secondary_btn_str=LN.btn_cancel)
                if not question: vDist.set(-1)
                else: pass
            if dists[vDist.get()]['auto-installable']:
                check_autoinst.configure(state='enabled')
                vAutoinst_t.set(1)
            else:
                check_autoinst.configure(state='disabled')
                vAutoinst_t.set(0)

        def validate_next_page(*args):
            if vDist.get() == -1: return -1
            else:
                LANG_LIST.pack_forget()
                if vAutoinst_t.get():
                    return page_autoinst1()
                else:
                    return page_verify()

    # page_autoinst1
    def page_autoinst1():
        """the autoinstall page on which you choose whether to install alongside windows or start clean install"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set(LN.install_auto)
        tkt.generic_page_layout(MID_FRAME, LN.windows_question % dists[vDist.get()]['name'],
                                LN.btn_next, lambda: validate_next_page(),
                                LN.btn_back, lambda: page_1())

        r1_frame = ttk.Frame(MID_FRAME)
        r1_frame.pack(fill="x")
        r1_autoinst = tkt.add_radio_btn(r1_frame, LN.windows_options[0], vAutoinst_option, 0, lambda: show_dualboot_options(True)
                                        , side=DI_VAR['l'])
        r1_space = ttk.Label(r1_frame, wraplength=540, justify="center", text=LN.warn_space, font=FONTS['tiny'],
                             foreground='#ff4a4a')
        entry1_frame = ttk.Frame(MID_FRAME)
        entry1_frame.pack(fill='x', padx=10)
        tkt.add_radio_btn(MID_FRAME, LN.windows_options[1], vAutoinst_option, 1, lambda: show_dualboot_options(False))

        min_size = dualboot_required_space
        max_size = fn.byte_to_gb(COMPATIBILITY_RESULTS['resizable']) - dists[vDist.get()]['size'] - additional_failsafe_space
        max_size = round(max_size, 2)
        float_regex = r'^[0-9]*\.?[0-9]{0,3}$'  # max 3 decimal digits
        size_dualboot_txt_pre = ttk.Label(entry1_frame, wraplength=540, justify=DI_VAR['l'],
                                          text=LN.dualboot_size_txt, font=FONTS['tiny'])
        size_dualboot_entry = ttk.Entry(entry1_frame, width=10, textvariable=vAutoinst_dualboot_size)
        size_dualboot_txt_post = ttk.Label(entry1_frame, wraplength=540, justify=DI_VAR['l'],
                                           text='(%sGB - %sGB)' % (min_size, max_size), font=FONTS['tiny'])
        tkt.var_tracer(vAutoinst_dualboot_size, "write",
                       lambda *args: fn.validate_with_regex(vAutoinst_dualboot_size, regex=float_regex, mode='fix'))

        # LOGIC
        space_dualboot = fn.gigabyte(dists[vDist.get()]['size'] + dualboot_required_space + additional_failsafe_space)
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

        if vAutoinst_option.get() == 0: show_dualboot_options(True)  # GUI bugfix

        def validate_next_page(*args):
            if vAutoinst_option.get() == 1: pass
            elif vAutoinst_option.get() == 0:
                syntax_valid = fn.validate_with_regex(vAutoinst_dualboot_size, regex=float_regex,
                                                      mode='read') not in (False, 'empty')
                if syntax_valid:
                    is_dualboot_size_valid = min_size <= float(vAutoinst_dualboot_size.get()) <= max_size
                else:
                    is_dualboot_size_valid = False
                if not is_dualboot_size_valid:
                    return -1
            else:
                return -1
            return page_autoinst2()

    def page_autoinst2():
        """the autoinstall page on which you choose whether to install alongside windows or start clean install"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set(LN.install_auto)
        tkt.generic_page_layout(MID_FRAME, LN.windows_question % dists[vDist.get()]['name'],
                                LN.btn_next, lambda: validate_next_page(),
                                LN.btn_back, lambda: page_autoinst1())

        # tkt.add_check_btn(MID_FRAME, LN.additional_setup_now, vAutoinst_additional_setup_t)

        tkt.add_check_btn(MID_FRAME, LN.add_import_wifi, vAutoinst_Wifi_t, pady=(5, 0))
        tkt.add_check_btn(MID_FRAME, LN.encrypted_root, vAutoinst_Encrypt_t, lambda: show_encrypt_options(vAutoinst_Encrypt_t))

        only_digit_regex = r'^[0-9]+$'  # digits
        entry2_frame = ttk.Frame(MID_FRAME)

        encrypt_pass_pre = ttk.Label(entry2_frame, wraplength=540, justify=DI_VAR['l'],
                                     text=LN.entry_encrypt_passphrase_pre, font=FONTS['tiny'])
        encrypt_passphrase_entry = ttk.Entry(entry2_frame, show="\u2022", width=10,
                                             textvariable=vAutoinst_Encrypt_Passphrase)
        encrypt_pass_post = ttk.Label(entry2_frame, wraplength=540, justify=DI_VAR['l'],
                                      text=LN.entry_encrypt_passphrase_post, font=FONTS['tiny'])
        tkt.var_tracer(vAutoinst_Encrypt_Passphrase, "write",
                       lambda *args: fn.validate_with_regex(vAutoinst_Encrypt_Passphrase,
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
                       show_not_matched_warning(not verify_match(pass_confirm_var, vAutoinst_Encrypt_Passphrase)))

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
        show_encrypt_options(vAutoinst_Encrypt_t)

        def validate_next_page(*args):
            if vAutoinst_Encrypt_t.get() and not verify_match(vAutoinst_Encrypt_Passphrase, pass_confirm_var):
                return
            elif vAutoinst_additional_setup_t.get() == 0:
                page_verify()
            elif vAutoinst_additional_setup_t.get() == 1:
                page_autoinst_addition_1()

    # page_autoinst2
    def page_autoinst_addition_1():
        """the autoinstall page on which you choose your language and locale"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        tkt.generic_page_layout(MID_FRAME, LN.title_autoinst2,
                                LN.btn_next, lambda: validate_next_page(),
                                LN.btn_back, lambda: page_autoinst2())
        all_languages = get_available_translations()
        if IP_LOCALE:
            langs_and_locales = get_locales_and_langs_sorted_with_names(territory=IP_LOCALE[0], other_langs=all_languages)
        else:
            langs_and_locales = get_locales_and_langs_sorted_with_names(other_langs=all_languages)

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

        def validate_next_page(*args):
            selected_locale = locale_list_fedora.focus()
            if langtable.parse_locale(selected_locale).language:
                AUTOINST['locale'] = selected_locale
                return page_autoinst_addition_2()

    def page_autoinst_addition_2():
        """the autoinstall page on which you choose your timezone and keyboard layout"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        tkt.generic_page_layout(MID_FRAME, LN.title_autoinst3,
                                LN.btn_next, lambda: validate_next_page(),
                                LN.btn_back, lambda: page_autoinst_addition_1())

        chosen_locale_name = langtable.language_name(languageId=Autoinst_SELECTED_LOCALE)
        if IP_LOCALE:
            locale_from_ip = langtable.list_locales(territoryId=IP_LOCALE[0])[0]
            locale_from_ip_name = langtable.language_name(languageId=locale_from_ip)
            if locale_from_ip != Autoinst_SELECTED_LOCALE:
                tkt.add_radio_btn(MID_FRAME, LN.keymap_tz_option % locale_from_ip_name, vKeymap_timezone_source,
                                  0, command=lambda: spawn_more_widgets())

        tkt.add_radio_btn(MID_FRAME, LN.keymap_tz_option % chosen_locale_name, vKeymap_timezone_source, 1, lambda: spawn_more_widgets())
        tkt.add_radio_btn(MID_FRAME, LN.keymap_tz_custom, vKeymap_timezone_source, 2, lambda: spawn_more_widgets())

        timezone_all = sorted(all_timezones())
        lists_frame = ttk.Frame(MID_FRAME)
        timezone_txt = ttk.Label(lists_frame, wraplength=540, justify=DI_VAR['l'], text=LN.list_timezones, font=FONTS['tiny'])
        timezone_list = ttk.Combobox(lists_frame, name="timezone", textvariable=vAutoinst_Timezone)
        timezone_list['values'] = tuple(timezone_all)
        timezone_list['state'] = 'readonly'

        keyboards_all = []

        if IP_LOCALE:
            local_keyboards = langtable.list_keyboards(territoryId=IP_LOCALE[0])
            for keyboard in local_keyboards:
                if keyboard not in keyboards_all:
                    keyboards_all.append(keyboard)
        all_keymaps = get_available_keymaps()
        for keyboard in all_keymaps:
            if keyboard not in keyboards_all:
                keyboards_all.append(keyboard)
        keyboards_txt = ttk.Label(lists_frame, wraplength=540, justify=DI_VAR['l'], text=LN.list_keymaps, font=FONTS['tiny'])
        keyboard_list = ttk.Combobox(lists_frame, name="keyboard", textvariable=vAutoinst_Keyboard)
        keyboard_list['values'] = tuple(keyboards_all)
        keyboard_list['state'] = 'readonly'

        if IP_LOCALE:
            timezone_list.set(IP_LOCALE[1])
            keyboard_list.set(keyboards_all[0])

        def spawn_more_widgets(*args):
            if vKeymap_timezone_source.get() == 2:
                lists_frame.pack(fill='x', padx=20)
                keyboards_txt.grid(pady=5, padx=5, column=0, row=1, sticky=DI_VAR['w'])
                keyboard_list.grid(pady=5, padx=5, column=1, row=1)
                timezone_txt.grid(pady=5, padx=5, column=0, row=0, sticky=DI_VAR['w'])
                timezone_list.grid(pady=5, padx=5, column=1, row=0)
            else:
                lists_frame.pack_forget()

        def validate_next_page(*args):
            if vKeymap_timezone_source.get() == 0:
                AUTOINST['keymap'] = langtable.list_keyboards(territoryId=IP_LOCALE[0])[0]
                AUTOINST['timezone'] = langtable.list_timezones(territoryId=IP_LOCALE[0])[0]
            elif vKeymap_timezone_source.get() == 1:
                AUTOINST['keymap'] = langtable.list_keyboards(languageId=Autoinst_SELECTED_LOCALE)[0]
                AUTOINST['timezone'] = langtable.list_timezones(languageId=Autoinst_SELECTED_LOCALE)[0]
            elif vKeymap_timezone_source.get() == 2:
                AUTOINST['keymap'] = vAutoinst_Keyboard.get()
                AUTOINST['timezone'] = vAutoinst_Timezone.get()
            if AUTOINST['keymap'] and AUTOINST['timezone']:
                page_verify()

    def page_verify():
        """the page on which you get to review your selection before starting to install"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set('')
        tkt.generic_page_layout(MID_FRAME, LN.verify_question,
                                LN.btn_next, lambda: page_installing(),
                                LN.btn_back, lambda: validate_back_page())
        # Constructing user verification text based on user's selections  ++++++++++++++++++++++++++++++++++++++++++++++
        review_sel = []
        if vAutoinst_t.get() == 0:
            review_sel.append(LN.verify_text['no_autoinst'] % dists[vDist.get()]['name'])
        else:
            if vAutoinst_option.get() == 0:
                review_sel.append(LN.verify_text['autoinst_dualboot'] % dists[vDist.get()]['name'])
                review_sel.append(LN.verify_text['autoinst_keep_data'])
            elif vAutoinst_option.get() == 1:
                review_sel.append(LN.verify_text['autoinst_clean'] % dists[vDist.get()]['name'])
                review_sel.append(LN.verify_text['autoinst_rm_all'])
            if vAutoinst_Wifi_t.get():
                review_sel.append(LN.verify_text['autoinst_wifi'] % dists[vDist.get()]['name'])
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        review_tree = ttk.Treeview(MID_FRAME, columns='error', show='', height=3)
        review_tree.pack(anchor=DI_VAR['w'], ipady=5, pady=10, padx=(0, 5), fill='x')
        review_tree.configure(selectmode='none')

        for i in range(len(review_sel)):
            review_tree.insert('', index='end', iid=str(i), values=(review_sel[i],))
        # additions options (checkboxes)
        c2_add = ttk.Checkbutton(MID_FRAME, text=LN.add_auto_restart, variable=vAutorestart_t, onvalue=1, offvalue=0)
        c2_add.pack(anchor=DI_VAR['w'])
        c3_add = ttk.Checkbutton(MID_FRAME, text=LN.add_torrent, variable=vTorrent_t, onvalue=1, offvalue=0)
        more_options_btn = ttk.Label(MID_FRAME, justify="center", text=LN.more_options, font=FONTS['tiny'], foreground='#3aa9ff')
        more_options_btn.pack(pady=10, padx=10, anchor=DI_VAR['w'])
        more_options_btn.bind("<Button-1>",
                              lambda x: (more_options_btn.destroy(), c3_add.pack(anchor=DI_VAR['w'])))

        def validate_back_page(*args):
            if not vAutoinst_t.get():
                page_1()
            elif vAutoinst_additional_setup_t.get():
                page_autoinst_addition_2()
            else:
                page_autoinst2()

    def page_installing():
        """the page on which the initial installation (creating bootable media) takes place"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set(LN.install_running)
        progressbar_install = ttk.Progressbar(MID_FRAME, orient='horizontal', length=550, mode='determinate')
        progressbar_install.pack(pady=25)
        job_var = tk.StringVar()
        current_job = ttk.Label(MID_FRAME, wraplength=540, justify=DI_VAR['l'], textvariable=job_var, font=FONTS['small'])
        current_job.pack(padx=10, anchor=DI_VAR['w'])

        global INSTALLER_STATUS, MOUNT_ISO_LETTER, TMP_PARTITION_LETTER
        # checking if files from previous runs are present and if so, ask if user wishes to use them.
        if fn.check_file_if_exists(ISO_PATH) == 'True':
            question = tkt.open_popup(parent=app, title_txt=LN.old_download_detected, msg_txt=LN.old_download_detected_text,
                                      primary_btn_str=LN.btn_yes, secondary_btn_str=LN.btn_no)
            if question:
                INSTALLER_STATUS = 2
            else:
                fn.remove_folder(DOWNLOAD_PATH)
        # GETTING ARGUMENTS READY
        tmp_part_size: int = fn.gigabyte(dists[vDist.get()]['size'] + temp_part_failsafe_space)
        if vAutoinst_Wifi_t.get():
            wifi_profiles = fn.get_wifi_profiles()
        else:
            wifi_profiles = None
        part_kwargs = {"tmp_part_size": tmp_part_size, "temp_part_label": TMP_PARTITION_LABEL, "queue": GLOBAL_QUEUE}
        if vAutoinst_t.get():
            ks_kwargs = {'ostree_args': dists[vDist.get()]['ostree'],
                         'encrypted': bool(vAutoinst_Encrypt_t.get()),
                         'passphrase': vAutoinst_Encrypt_Passphrase.get(),
                         'wifi_profiles': wifi_profiles,
                         'keymap': AUTOINST['keymap'],
                         'lang': AUTOINST['locale'],
                         'timezone': AUTOINST['timezone'],
                         'username': AUTOINST['username'],
                         'fullname': AUTOINST['fullname']}
            if vAutoinst_option.get() == 0:
                part_kwargs["shrink_space"] = fn.gigabyte(float(vAutoinst_dualboot_size.get()))
                part_kwargs["boot_part_size"] = fn.gigabyte(linux_boot_partition_size)
                part_kwargs["efi_part_size"] = fn.megabyte(linux_efi_partition_size)
        else:
            ks_kwargs = {}

        while True:
            if not INSTALLER_STATUS:  # first step, start the download
                while GLOBAL_QUEUE.qsize(): GLOBAL_QUEUE.get()  # to empty the queue
                progressbar_install['value'] = 0
                job_var.set(LN.job_starting_download)
                app.update()
                fn.create_dir(DOWNLOAD_PATH)

                aria2_location = CURRENT_DIR + '\\resources\\aria2c.exe'
                if vTorrent_t.get() and dists[vDist.get()]['torrent']:
                    # if torrent is selected and a torrent link is available
                    args = (aria2_location, dists[vDist.get()]['torrent'], DOWNLOAD_PATH, 1, GLOBAL_QUEUE,)
                else:
                    # if torrent is not selected or not available (direct download)
                    args = (aria2_location, dists[vDist.get()]['dl_link'], DOWNLOAD_PATH, 0, GLOBAL_QUEUE,)
                Process(target=fn.download_with_aria2, args=args).start()
                INSTALLER_STATUS = 1
            if INSTALLER_STATUS == 1:  # While downloading, track download stats...
                while True:
                    while not GLOBAL_QUEUE.qsize(): app.after(500, app.update())
                    while GLOBAL_QUEUE.qsize() != 1: GLOBAL_QUEUE.get()
                    dl_status = GLOBAL_QUEUE.get()
                    if dl_status == 'OK':
                        INSTALLER_STATUS = 3
                        break
                    progressbar_install['value'] = dl_status['%'] * 0.90
                    txt = LN.job_dl_install_media + '\n%s\n%s: %s/s, %s: %s' % (dl_status['size'], LN.dl_speed,
                                                                                dl_status['speed'], LN.dl_timeleft,
                                                                                dl_status['eta'])
                    job_var.set(txt)
                    app.after(200, app.update())
                fn.move_files_to_dir(DOWNLOAD_PATH, DOWNLOAD_PATH)
                fn.rename_file(DOWNLOAD_PATH, '*.iso', ISO_NAME)
                INSTALLER_STATUS = 2

            if INSTALLER_STATUS == 2:  # step 2: create temporary boot partition
                while GLOBAL_QUEUE.qsize(): GLOBAL_QUEUE.get()  # to empty the queue
                Process(target=fn.check_hash, args=(ISO_PATH, dists[vDist.get()]['hash256'], GLOBAL_QUEUE,)).start()
                job_var.set(LN.job_checksum)
                progressbar_install['value'] = 90
                while not GLOBAL_QUEUE.qsize(): app.after(50, app.update())
                out = GLOBAL_QUEUE.get()
                if out == 1: INSTALLER_STATUS = 2.5
                elif out == -1:
                    question = tkt.open_popup(parent=app, title_txt=LN.job_checksum_failed, msg_txt=LN.job_checksum_failed_txt,
                                              primary_btn_str=LN.btn_yes, secondary_btn_str=LN.btn_no)
                    if question: INSTALLER_STATUS = 2.5
                    else:
                        question = tkt.open_popup(parent=app, title_txt=LN.cleanup_question, msg_txt=LN.cleanup_question_txt,
                                                  primary_btn_str=LN.btn_yes, secondary_btn_str=LN.btn_no)
                        if question: fn.remove_folder(DOWNLOAD_PATH)
                        tkt.app_quite()
                else:
                    question = tkt.open_popup(parent=app, title_txt=LN.job_checksum_mismatch,
                                              msg_txt=LN.job_checksum_mismatch_txt % out,
                                              primary_btn_str=LN.btn_yes, secondary_btn_str=LN.btn_no)
                    if question == 1: pass
                    if question == 2: INSTALLER_STATUS = 2.5
                    if question == 0:
                        question = tkt.open_popup(parent=app, title_txt=LN.cleanup_question, msg_txt=LN.cleanup_question_txt,
                                                  primary_btn_str=LN.btn_yes, secondary_btn_str=LN.btn_no)
                        if question: fn.remove_folder(DOWNLOAD_PATH)
                        else: tkt.app_quite()
            if INSTALLER_STATUS == 2.5:  # step 2: create temporary boot partition
                while GLOBAL_QUEUE.qsize(): GLOBAL_QUEUE.get()  # to empty the queue
                app.protocol("WM_DELETE_WINDOW", False)  # prevent closing the app during partition

                Process(target=fn.partition_procedure, kwargs=part_kwargs).start()
                job_var.set(LN.job_creating_tmp_part)
                progressbar_install['value'] = 92
                INSTALLER_STATUS = 3
            if INSTALLER_STATUS == 3:  # while creating partition is ongoing...
                while not GLOBAL_QUEUE.qsize():
                    app.after(200, app.update())
                tmp_part_result = GLOBAL_QUEUE.get()
                if tmp_part_result[0] == 1:
                    TMP_PARTITION_LETTER = tmp_part_result[1]
                    INSTALLER_STATUS = 4
                else: return
            if INSTALLER_STATUS == 4:  # step 3: mount iso and copy files to temporary boot partition
                while GLOBAL_QUEUE.qsize(): GLOBAL_QUEUE.get()  # to empty the queue
                app.protocol("WM_DELETE_WINDOW", None)  # re-enable closing the app
                MOUNT_ISO_LETTER = fn.mount_iso(ISO_PATH)
                source_files = MOUNT_ISO_LETTER + ':\\'
                destination_files = TMP_PARTITION_LETTER + ':\\'
                Process(target=fn.copy_files, args=(source_files, destination_files, GLOBAL_QUEUE,)).start()
                job_var.set(LN.job_copying_to_tmp_part)
                progressbar_install['value'] = 94
                INSTALLER_STATUS = 5
            if INSTALLER_STATUS == 5:  # while copying files is ongoing...
                while not GLOBAL_QUEUE.qsize():
                    app.after(200, app.update())
                if GLOBAL_QUEUE.get() == 1:
                    INSTALLER_STATUS = 6
            if INSTALLER_STATUS == 6:  # step 4: adding boot entry
                while GLOBAL_QUEUE.qsize(): GLOBAL_QUEUE.get()  # to empty the queue
                job_var.set(LN.job_adding_tmp_boot_entry)
                progressbar_install['value'] = 98
                if vAutoinst_t.get(): grub_cfg_file = GRUB_CONFIG_DIR + 'grub_autoinst.cfg'
                else: grub_cfg_file = GRUB_CONFIG_DIR + 'grub_default.cfg'
                grub_cfg_file_path = TMP_PARTITION_LETTER + ':\\EFI\\BOOT\\grub.cfg'
                fn.copy_one_file(grub_cfg_file, grub_cfg_file_path)
                grub_cfg_txt = fn.build_grub_cfg_file(TMP_PARTITION_LABEL, vAutoinst_t.get())
                fn.set_file_readonly(grub_cfg_file_path, False)
                grub_cfg = open(grub_cfg_file_path, 'w')
                grub_cfg.write(grub_cfg_txt)
                grub_cfg.close()
                fn.set_file_readonly(grub_cfg_file_path, True)

                if vAutoinst_t.get():
                    kickstart_txt = fn.build_autoinstall_ks_file(**ks_kwargs)
                    if kickstart_txt:
                        kickstart = open(TMP_PARTITION_LETTER + ':\\ks.cfg', 'w')
                        kickstart.write(kickstart_txt)
                        kickstart.close()
                app.protocol("WM_DELETE_WINDOW", False)  # prevent closing the app
                Process(target=fn.add_boot_entry, args=(default_efi_file_path, TMP_PARTITION_LETTER,
                                                        vAutoinst_option.get(), GLOBAL_QUEUE,)).start()
                INSTALLER_STATUS = 7
            if INSTALLER_STATUS == 7:  # while adding boot entry is ongoing...
                while not GLOBAL_QUEUE.qsize():
                    app.after(200, app.update())
                if GLOBAL_QUEUE.get() == 1:
                    INSTALLER_STATUS = 8
            if INSTALLER_STATUS == 8:  # step 5: clean up iso and other downloaded files since install is complete
                fn.unmount_iso(ISO_PATH)
                fn.remove_folder(DOWNLOAD_PATH)
                INSTALLER_STATUS = 9
            if INSTALLER_STATUS == 9:  # step 6: redirect to next page
                app.protocol("WM_DELETE_WINDOW", None)  # re-enable closing the app
                break

        return page_restart_required()

    def page_restart_required():
        """the page on which user is promoted to restart the device to continue installation (boot into install media)"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        LANG_LIST.pack(anchor=DI_VAR['nw'], padx=10, pady=10)
        tkt.generic_page_layout(MID_FRAME, LN.finished_title,
                                LN.btn_restart_now, lambda: [fn.restart_windows(), tkt.app_quite()],
                                LN.btn_restart_later, lambda: tkt.app_quite())
        text_var = tk.StringVar()
        tkt.add_text_label(MID_FRAME, text=LN.finished_text, font=FONTS['small'], pady=10)
        tkt.add_text_label(MID_FRAME, var=text_var, font=FONTS['small'], pady=10)

        if vAutorestart_t.get():
            time_left = 10
            while time_left > 0:
                text_var.set(LN.finished_text_restarting_now % (int(time_left)))
                time_left = time_left - 0.4
                app.after(400, app.update())
            fn.restart_windows()
            tkt.app_quite()

    page_check()
    app.mainloop()


if __name__ == '__main__': main()
