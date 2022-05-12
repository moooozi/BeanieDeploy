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
    return tkt.build_main_gui_frames(CONTAINER, vTitleText,  left_frame_img_path='resources/left_frame.png', frames=frames)
TOP_FRAME, MID_FRAME, LEFT_FRAME = gui_builder()
#   INITIALIZING GLOBAL VARIABLES /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
GLOBAL_QUEUE = Queue()
COMPATIBILITY_RESULTS = {}
COMPATIBILITY_CHECK_STATUS = 0
INSTALLER_STATUS = 0
IP_LOCALE = []
AUTOINST = {}
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
vAutorestart_t = tk.IntVar(app, 0)
vTorrent_t = tk.IntVar(app, 0)
# autoinstaller variables
vKeymap_timezone_source = tk.IntVar(app, value=1)
vAutoinst_Keyboard = tk.StringVar(app)
vAutoinst_Timezone = tk.StringVar(app)
vAutoinst_Fullname = tk.StringVar(app)
vAutoinst_Username = tk.StringVar(app)
vAutoinst_dualboot_size = tk.StringVar(app)
Autoinst_SELECTED_LOCALE = ''
USERNAME_WINDOWS = ''
lang_var = tk.StringVar()
LANG_LIST = tkt.add_lang_list(TOP_FRAME, lang_var, multilingual.available_languages.keys())


#   MULTI-LINGUAL /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
def language_handler(new_language=None, current_page=None):
    global DI_VAR, LN, TOP_FRAME, MID_FRAME, LEFT_FRAME
    if new_language is None: new_language = lang_var.get()
    DI_VAR, LN = multilingual.change_lang(new_lang=new_language)
    gui_builder(frames=[TOP_FRAME, LEFT_FRAME, MID_FRAME])
    if current_page is not None:
        return current_page()


language_handler(new_language='English')


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

        progressbar_check = ttk.Progressbar(MID_FRAME, orient='horizontal', length=550, mode='indeterminate')
        progressbar_check.pack(pady=25)
        progressbar_check.start(10)
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
                    while not GLOBAL_QUEUE.qsize(): app.after(10, app.update())
                    queue_out = GLOBAL_QUEUE.get()
                    if queue_out == 'arch': pass
                    elif queue_out == 'uefi': job_var.set(LN.check_uefi)
                    elif queue_out == 'ram': job_var.set(LN.check_ram)
                    elif queue_out == 'space': job_var.set(LN.check_space)
                    elif queue_out == 'resizable': job_var.set(LN.check_resizable)
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
            title.pack_forget()
            progressbar_check.pack_forget()
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
        tkt.add_page_title(MID_FRAME, LN.distro_question)

        for index, distro in enumerate(distros['name']):
            txt = ''  # Generating Text for each list member of installable flavors/distros
            if distros['advanced'][index]: txt += LN.adv + ': '
            txt += distro + ' %s' % distros['version'][index]
            if distros['de'][index]: txt += ' (%s)' % distros['de'][index]
            if distros['netinstall'][index]: txt += ' (%s)' % LN.net_install
            if distros['recommended'][index]:
                if vDist.get() == -2: vDist.set(index)  # If unset, set it to the default recommended entry
                txt += ' (%s)' % LN.recommended
            temp_frame = ttk.Frame(MID_FRAME)
            temp_frame.pack(fill="x", pady=5)
            radio = tkt.add_radio_btn(temp_frame, txt, vDist, index, ipady=0, side=DI_VAR['l'], command=lambda: validate_input())
            if distros['netinstall'][index]: dl_size_txt = LN.init_download % distros['size'][index]
            else: dl_size_txt = LN.total_download % distros['size'][index]
            ttk.Label(temp_frame, wraplength=540, justify="center", text=dl_size_txt,
                      font=FONTS['tiny'], foreground='#3aa9ff').pack(padx=5, anchor=DI_VAR['e'], side=DI_VAR['r'])
            if COMPATIBILITY_RESULTS['resizable'] < fn.gigabyte(distros['size'][index]):
                radio.configure(state='disabled')
                ttk.Label(temp_frame, wraplength=540, justify="center", text=LN.warn_space,
                          font=FONTS['tiny'], foreground='#ff4a4a').pack(padx=5, anchor=DI_VAR['e'], side=DI_VAR['r'])
                if vDist.get() == [index]:
                    vDist.set(-1)

        check_autoinst = tkt.add_check_btn(MID_FRAME, LN.install_auto, vAutoinst_t, pady=40)
        tkt.add_primary_btn(MID_FRAME, LN.btn_next, lambda: validate_next_page())
        # BUGFIX
        if not distros['auto-installable'][vDist.get()]:
            check_autoinst.configure(state='disabled')
            vAutoinst_t.set(0)

        def validate_input(*args):
            if distros['advanced'][vDist.get()]:
                question = tkt.open_popup(parent=app, title_txt=LN.adv_confirm, msg_txt=LN.adv_confirm_text,
                                          primary_btn_str=LN.btn_continue, secondary_btn_str=LN.btn_cancel)
                if not question: vDist.set(-1)
                else: pass
            if distros['auto-installable'][vDist.get()]:
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
        tkt.add_page_title(MID_FRAME, LN.windows_question % distros['name'][vDist.get()])

        r1_frame = ttk.Frame(MID_FRAME)
        r1_frame.pack(fill="x")
        r1_autoinst = tkt.add_radio_btn(r1_frame, LN.windows_options[0], vAutoinst_option, 0, lambda: show_dualboot_options(True))
        r1_space = ttk.Label(r1_frame, wraplength=540, justify="center", text=LN.warn_space, font=FONTS['tiny'],
                             foreground='#ff4a4a')
        entry_frame = ttk.Frame(MID_FRAME)
        entry_frame.pack(fill='x', padx=10)
        tkt.add_radio_btn(MID_FRAME, LN.windows_options[1], vAutoinst_option, 1, lambda: show_dualboot_options(False))
        tkt.add_check_btn(MID_FRAME, LN.add_import_wifi, vAutoinst_Wifi_t)

        min_size = dualboot_required_space
        max_size = fn.byte_to_gb(COMPATIBILITY_RESULTS['resizable']) - distros['size'][vDist.get()] - additional_failsafe_space
        max_size = round(max_size, 2)
        float_regex = r'^[0-9]*\.?[0-9]{0,3}$'  # max 3 decimal digits
        size_dualboot_txt_pre = ttk.Label(entry_frame, wraplength=540, justify=DI_VAR['l'],
                                          text=LN.dualboot_size_txt, font=FONTS['tiny'])
        size_dualboot_txt_post = ttk.Label(entry_frame, wraplength=540, justify=DI_VAR['l'],
                                           text='(%sGB - %sGB)' % (min_size, max_size), font=FONTS['tiny'])
        size_dualboot_entry = ttk.Entry(entry_frame, width=10, textvariable=vAutoinst_dualboot_size)
        tkt.var_tracer(vAutoinst_dualboot_size, "write",
                       lambda *args: fn.validate_with_regex(vAutoinst_dualboot_size, regex=float_regex, mode='fix'))
        # LOGIC
        space_dualboot = fn.gigabyte(distros['size'][vDist.get()] + dualboot_required_space + additional_failsafe_space)
        if COMPATIBILITY_RESULTS['resizable'] < space_dualboot:
            r1_space.pack(padx=20, anchor=DI_VAR['e'], side=DI_VAR['l'])
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

        tkt.add_primary_btn(MID_FRAME, LN.btn_next, lambda: validate_next_page())
        tkt.add_secondary_btn(MID_FRAME, LN.btn_next, lambda: page_1())

    # page_autoinst2
    def page_autoinst2():
        """the autoinstall page on which you choose your language and locale"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        tkt.add_page_title(MID_FRAME, LN.title_autoinst2)

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
            global Autoinst_SELECTED_LOCALE
            Autoinst_SELECTED_LOCALE = locale_list_fedora.focus()
            if langtable.parse_locale(Autoinst_SELECTED_LOCALE).language:
                return page_autoinst3()

        tkt.add_primary_btn(MID_FRAME, LN.btn_next, lambda: validate_next_page())
        tkt.add_secondary_btn(MID_FRAME, LN.btn_next, lambda: page_autoinst1())

    def page_autoinst3():
        """the autoinstall page on which you choose your timezone and keyboard layout"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        tkt.add_page_title(MID_FRAME, LN.title_autoinst3)
        
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

        tkt.add_primary_btn(MID_FRAME, LN.btn_next, lambda: validate_next_page())
        tkt.add_secondary_btn(MID_FRAME, LN.btn_next, lambda: page_autoinst2())

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
                page_autoinst4()

    def page_autoinst4():
        """the autoinstall page on which you choose your input your username and fullname"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        tkt.add_page_title(MID_FRAME, LN.title_autoinst4)

        # Regex Syntax *****
        portable_fs_chars = r'a-zA-Z0-9._-'
        _name_base = r'[a-zA-Z0-9._][' + portable_fs_chars + r']{0,30}([' + portable_fs_chars + r']|\$)?'
        username_regex = r'^' + _name_base + '$'
        fullname_regex = r'^[^:]*$'
        # Only allow username and fullname that meet the regex syntax above
        tkt.var_tracer(vAutoinst_Fullname, "write", lambda *args: fn.validate_with_regex(vAutoinst_Fullname, regex=fullname_regex, mode='fix'))
        tkt.var_tracer(vAutoinst_Username, "write", lambda *args: fn.validate_with_regex(vAutoinst_Username, regex=username_regex, mode='fix'))

        entries_frame = ttk.Frame(MID_FRAME)
        fullname_txt = ttk.Label(entries_frame, wraplength=540, justify=DI_VAR['l'], text=LN.entry_fullname, font=FONTS['tiny'])
        fullname_entry = ttk.Entry(entries_frame, width=40, textvariable=vAutoinst_Fullname)
        username_txt = ttk.Label(entries_frame, wraplength=540, justify=DI_VAR['l'], text=LN.entry_username, font=FONTS['tiny'])
        username_entry = ttk.Entry(entries_frame, width=40, textvariable=vAutoinst_Username)

        entries_frame.pack(fill='x', padx=20)
        fullname_txt.grid(pady=5, padx=5, column=0, row=0, sticky=DI_VAR['w'])
        fullname_entry.grid(pady=5, padx=5, column=1, row=0)
        username_txt.grid(pady=5, padx=5, column=0, row=1, sticky=DI_VAR['w'])
        username_entry.grid(pady=5, padx=5, column=1, row=1)

        password_reminder = ttk.Label(MID_FRAME, wraplength=540, justify=DI_VAR['l'], text=LN.password_reminder_txt, font=FONTS['tiny'])
        password_reminder.pack(pady=10, padx=20, anchor=DI_VAR['w'])

        tkt.add_primary_btn(MID_FRAME, LN.btn_next, lambda: validate_next_page())
        tkt.add_secondary_btn(MID_FRAME, LN.btn_next, lambda: page_autoinst3())

        if not vAutoinst_Username.get():
            username_entry.insert(index=0, string=USERNAME_WINDOWS)
            username_entry.select_range(start=0, end=999)

        def validate_next_page(*args):
            # Username cannot be empty
            is_username_valid = fn.validate_with_regex(vAutoinst_Username, regex=username_regex, mode='read') not in (False, 'empty')
            is_fullname_valid = fn.validate_with_regex(vAutoinst_Fullname, regex=fullname_regex, mode='read')
            if is_username_valid and is_fullname_valid:
                page_verify()

    def page_verify():
        """the page on which you get to review your selection before starting to install"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set('')
        tkt.add_page_title(MID_FRAME, LN.verify_question)

        # Constructing user verification text based on user's selections  ++++++++++++++++++++++++++++++++++++++++++++++
        review_sel = []
        if vAutoinst_t.get() == 0:
            review_sel.append(LN.verify_text['no_autoinst'])
        else:
            if vAutoinst_option.get() == 0:
                review_sel.append(LN.verify_text['autoinst_dualboot'] % distros['name'][vDist.get()])
                review_sel.append(LN.verify_text['autoinst_keep_data'])
            elif vAutoinst_option.get() == 1:
                review_sel.append(LN.verify_text['autoinst_clean'] % distros['name'][vDist.get()])
                review_sel.append(LN.verify_text['autoinst_rm_sys'] % fn.get_sys_drive_letter())
            elif vAutoinst_option.get() == 2:
                review_sel.append(LN.verify_text['autoinst_clean'] % distros['name'][vDist.get()])
                review_sel.append(LN.verify_text['autoinst_rm_all'])
            if vAutoinst_Wifi_t.get():
                review_sel.append(LN.verify_text['autoinst_wifi'] % distros['name'][vDist.get()])
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
                              lambda x: (more_options_btn.pack_forget(), c3_add.pack(anchor=DI_VAR['w'])))

        def validate_back_page(*args):
            if vAutoinst_t.get(): page_autoinst4()
            else: page_1()

        tkt.add_primary_btn(MID_FRAME, LN.btn_next, lambda: page_installing())
        tkt.add_secondary_btn(MID_FRAME, LN.btn_next, lambda: validate_back_page())

    def page_installing():
        """the  page on which the initial installation (creating bootable media) takes place"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set(LN.install_running)
        # title = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'], text=LN.install_running, font=FONTS['medium'])
        # title.pack(pady=35, anchor=di_var['w'])
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
        while True:
            if not INSTALLER_STATUS:  # first step, start the download
                while GLOBAL_QUEUE.qsize(): GLOBAL_QUEUE.get()  # to empty the queue
                progressbar_install['value'] = 0
                job_var.set(LN.job_starting_download)
                app.update()
                fn.create_dir(DOWNLOAD_PATH)

                aria2_location = CURRENT_DIR + '\\resources\\aria2c.exe'
                if vTorrent_t.get() and distros['torrent'][vDist.get()]:
                    # if torrent is selected and a torrent link is available
                    args = (aria2_location, distros['torrent'][vDist.get()], DOWNLOAD_PATH, 1, GLOBAL_QUEUE,)
                else:
                    # if torrent is not selected or not available (direct download)
                    args = (aria2_location, distros['dl_link'][vDist.get()], DOWNLOAD_PATH, 0, GLOBAL_QUEUE,)
                Process(target=fn.download_with_aria2, args=args).start()
                INSTALLER_STATUS = 1
            if INSTALLER_STATUS == 1:  # While downloading, track download stats...
                while True:
                    while not GLOBAL_QUEUE.qsize(): app.after(50, app.update())
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
                    app.after(100, app.update())
                fn.move_files_to_dir(DOWNLOAD_PATH, DOWNLOAD_PATH)
                fn.rename_file(DOWNLOAD_PATH, '*.iso', ISO_NAME)
                INSTALLER_STATUS = 2

            if INSTALLER_STATUS == 2:  # step 2: create temporary boot partition
                while GLOBAL_QUEUE.qsize(): GLOBAL_QUEUE.get()  # to empty the queue
                Process(target=fn.check_hash, args=(ISO_PATH, distros['hash256'][vDist.get()], GLOBAL_QUEUE,)).start()
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
                tmp_part_size: int = fn.gigabyte(distros['size'][vDist.get()] + temp_part_failsafe_space)
                app.protocol("WM_DELETE_WINDOW", False)  # prevent closing the app during partition
                Process(target=fn.create_temp_boot_partition, args=(tmp_part_size, GLOBAL_QUEUE,
                                                                    fn.gigabyte(int(vAutoinst_dualboot_size.get())),)).start()
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
                    app.after(100, app.update())
                if GLOBAL_QUEUE.get() == 1:
                    INSTALLER_STATUS = 6
            if INSTALLER_STATUS == 6:  # step 4: adding boot entry
                while GLOBAL_QUEUE.qsize(): GLOBAL_QUEUE.get()  # to empty the queue
                job_var.set(LN.job_adding_tmp_boot_entry)
                progressbar_install['value'] = 98
                if vAutoinst_t.get(): grub_cfg_file = GRUB_CONFIG_DIR + 'grub_autoinst.cfg'
                else: grub_cfg_file = GRUB_CONFIG_DIR + 'grub_default.cfg'
                fn.copy_one_file(grub_cfg_file, TMP_PARTITION_LETTER + ':\\EFI\\BOOT\\grub.cfg')
                grub_cfg_txt = fn.build_grub_cfg_file(TMP_PARTITION_LABEL, vAutoinst_t.get())
                grub_cfg = open(TMP_PARTITION_LETTER + ':\\EFI\\BOOT\\grub.cfg', 'w')
                grub_cfg.write(grub_cfg_txt)
                grub_cfg.close()
                kickstart_txt = fn.build_autoinstall_ks_file(AUTOINST['keymap'], Autoinst_SELECTED_LOCALE, AUTOINST['timezone'],
                                                             distros['ostree'][vDist.get()], vAutoinst_Username.get(),
                                                             vAutoinst_Fullname.get())
                kickstart = open(TMP_PARTITION_LETTER + ':\\ks.cfg', 'w')
                kickstart.write(kickstart_txt)
                kickstart.close()
                app.protocol("WM_DELETE_WINDOW", False)  # prevent closing the app
                Process(target=fn.add_boot_entry, args=(default_efi_file_path, TMP_PARTITION_LETTER, GLOBAL_QUEUE,)).start()
                INSTALLER_STATUS = 7
            if INSTALLER_STATUS == 7:  # while adding boot entry is ongoing...
                while not GLOBAL_QUEUE.qsize():
                    app.after(100, app.update())
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
        tkt.add_page_title(MID_FRAME, LN.finished_title)

        text_var = tk.StringVar()
        tkt.add_text_label(MID_FRAME, text=LN.finished_text, font=FONTS['small'], pady=10)
        tkt.add_text_label(MID_FRAME, var=text_var, font=FONTS['small'], pady=10)
        if vAutorestart_t.get():
            time_left = 10
            while time_left > 0:
                text_var.set(LN.finished_text_restarting_now % (int(time_left)))
                time_left = time_left - 0.01
                app.after(10, app.update())
            fn.restart_windows()
            tkt.app_quite()

        tkt.add_primary_btn(MID_FRAME, LN.btn_restart_now, lambda: (fn.restart_windows(), tkt.app_quite()))
        tkt.add_secondary_btn(MID_FRAME, LN.btn_restart_later, lambda: tkt.app_quite())

    page_check()
    app.mainloop()


if __name__ == '__main__': main()
