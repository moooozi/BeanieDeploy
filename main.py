import types
import multiprocessing
import APP_INFO
import globals as GV
import functions as fn
import procedure as prc
import translations.en as LN
import tkinter.ttk as ttk
import tkinter as tk
import tkinter_templates as tkt
from APP_INFO import *
import autoinst

#   INIT CODE   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
app = tkt.init_tkinter(SW_NAME)  # initialize tkinter
PATH = prc.init_paths(GV.PATH)
tkt.stylize(app, theme_dir=PATH.CURRENT_DIR + '/resources/style/theme/azure-dark.tcl', theme_name='azure')  # use tkinter theme
GLOBAL_QUEUE = multiprocessing.Queue()
#   MAIN CONTAINER & FRAMES   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
CONTAINER = ttk.Frame(app)
CONTAINER.pack()
vTitleText = tk.StringVar(app)
TOP_FRAME, MID_FRAME, LEFT_FRAME = tkt.build_main_gui_frames(CONTAINER)
ttk.Label(LEFT_FRAME, image=tk.PhotoImage(file=PATH.CURRENT_DIR + r'\resources\left_frame.gif')).pack()


def run_async_function(function, callback=None, queue=GLOBAL_QUEUE, args=(), kwargs=None, wait_for_result=None):
    """
    run a function without blocking the GUI
    :param function: the function
    :param callback: callback function to handle Queue communication
    :param queue: the Queue object
    :param args: arguments to be passed to th function
    :param kwargs: keyworded-arguments to be passed to th function
    :param wait_for_result: wait for certain queue output
    :return: returns the first output from queue if no callback is specified, or the return of the callback if specified
    """
    if kwargs is None: kwargs = {}
    if queue: kwargs['queue'] = queue
    while queue.qsize(): queue.get()
    multiprocessing.Process(target=function, args=args, kwargs=kwargs).start()
    while True:
        while not queue.qsize(): app.after(100, app.update())
        if callback:
            call = callback(queue.get())
            if call: return call
        elif wait_for_result:
            if queue.get() == wait_for_result:
                break
        else:
            return queue.get()


def download_and_track_spin(tracker_var, spin, progress_bar=None, progress_factor: float = 1,
                            do_torrent_dl: bool = False, new_file_path=None, queue=GLOBAL_QUEUE):
    filename = fn.get_file_name_from_url(spin.dl_link)
    aria2_kwargs = {'aria2_path': PATH.ARIA2C, 'destination': PATH.WORK_DIR}
    if do_torrent_dl and spin.torrent_link:  # if torrent is selected and a torrent link is available
        aria2_kwargs['url'] = spin.torrent_link
        aria2_kwargs['is_torrent'] = True
    else:  # if torrent is not selected or not available (direct download)
        aria2_kwargs['url'] = spin.dl_link
        aria2_kwargs['is_torrent'] = False

    def callback(result):
        if result == 'OK':
            return 1
        if progress_bar:
            progress_bar['value'] = result['%'] * progress_factor
        tracker_var.set(LN.job_dl_install_media + '\n%s\n%s: %s/s, %s: %s' % (result['size'], LN.dl_speed,
                                                                              result['speed'], LN.dl_timeleft,
                                                                              result['eta']))
    run_async_function(fn.download_with_aria2, kwargs=aria2_kwargs, callback=callback)
    file_path = fn.find_file_by_name(filename, PATH.WORK_DIR)
    if new_file_path:
        fn.move_and_replace(file_path, new_file_path)
        file_path = new_file_path

    hash_result = run_async_function(fn.check_hash, kwargs={'file_path': file_path, 'sha256_hash': spin.hash256})
    return file_path, hash_result


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
                fn.rmdir(PATH.WORK_DIR)
            fn.app_quit()
    else:
        question = tkt.open_popup(parent=app, title_txt=LN.job_checksum_mismatch,
                                  msg_txt=LN.job_checksum_mismatch_txt % dl_hash,
                                  primary_btn_str=LN.btn_retry, secondary_btn_str=LN.btn_abort)
        if not question:
            question = tkt.open_popup(parent=app, title_txt=LN.cleanup_question,
                                      msg_txt=LN.cleanup_question_txt,
                                      primary_btn_str=LN.btn_yes, secondary_btn_str=LN.btn_no)
            if question:
                fn.rmdir(PATH.WORK_DIR)
            fn.app_quit()
    return go_next


def main():
    fn.log('%s v%s' % (APP_INFO.SW_NAME, APP_INFO.SW_VERSION), mode='w')
    fn.log('################################################################\n'
           'IMPORTANT: DO NOT CLOSE THIS CONSOLE WINDOW WHILE APP IS RUNNING\n'
           '################################################################\n\n')

    def page_check(compatibility_test=True):
        """The page on which is decided whether the app can run on the device or not"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        title = tkt.add_page_title(MID_FRAME, LN.check_running)

        progressbar_check = tkt.add_progress_bar(MID_FRAME)
        job_var = tk.StringVar()
        tkt.add_text_label(MID_FRAME, var=job_var, pady=0, padx=10)
        app.update()    # update tkinter GUI
        if not compatibility_test:
            GV.COMPATIBILITY_RESULTS.uefi = 1
            GV.COMPATIBILITY_RESULTS.ram = 34359738368
            GV.COMPATIBILITY_RESULTS.space = 133264248832
            GV.COMPATIBILITY_RESULTS.resizable = 432008358400
            GV.COMPATIBILITY_RESULTS.arch = 'amd64'

        def callback_compatibility(result):
            if result == 'arch':
                progressbar_check['value'] = 10
            elif result == 'uefi':
                job_var.set(LN.check_uefi)
                progressbar_check['value'] = 20
            elif result == 'ram':
                job_var.set(LN.check_ram)
                progressbar_check['value'] = 30
            elif result == 'space':
                job_var.set(LN.check_space)
                progressbar_check['value'] = 50
            elif result == 'resizable':
                job_var.set(LN.check_resizable)
                progressbar_check['value'] = 80
            elif isinstance(result, dict) and result.keys() >= {"arch", "uefi"}:
                GV.COMPATIBILITY_RESULTS.__init__(**result)
                job_var.set(LN.check_available_downloads)
                progressbar_check['value'] = 95
                return 1

        def callback_spinlist(result):
            if isinstance(result, tuple) and result[0] == 'spin_list':
                GV.ALL_SPINS = result[1]
                return 1

        def callback_geo_up(result):
            if isinstance(result, tuple) and result[0] == 'geo_ip':
                GV.IP_LOCALE = result[1]
                return 1

        if not vars(GV.COMPATIBILITY_RESULTS):
            fn.get_admin()  # Request elevation (admin) if not running as admin
            run_async_function(prc.compatibility_test, callback=callback_compatibility, args=(minimal_required_space,))
        if not GV.ALL_SPINS:
            run_async_function(fn.get_json, callback=callback_spinlist, kwargs={'url': AVAILABLE_SPINS_LIST, 'named': 'spin_list'})
        if not GV.IP_LOCALE:
            run_async_function(fn.get_json, callback=callback_geo_up, kwargs={'url': FEDORA_GEO_IP_URL, 'named': 'geo_ip'})
            # Try to detect GEO-IP locale while compatibility check is running. Timeout once check has finished
        # LOG #########################################################
        fn.log('\nInitial Test completed, results:')
        for key, value in vars(GV.COMPATIBILITY_RESULTS).items():
            fn.log('%s: %s' % (str(key), str(value)))
        if fn.detect_nvidia():
            fn.log('\nNote: NVIDIA Graphics card detected')
        # #############################################################
        errors = []
        if GV.COMPATIBILITY_RESULTS.arch == -1: errors.append(LN.error_arch_9)
        elif GV.COMPATIBILITY_RESULTS.arch not in GV.ACCEPTED_ARCHITECTURES: errors.append(LN.error_arch_0)
        if GV.COMPATIBILITY_RESULTS.uefi == -1: errors.append(LN.error_uefi_9)
        elif GV.COMPATIBILITY_RESULTS.uefi != 1: errors.append(LN.error_uefi_0)
        if GV.COMPATIBILITY_RESULTS.ram == -1: errors.append(LN.error_totalram_9)
        elif GV.COMPATIBILITY_RESULTS.ram < fn.gigabyte(minimal_required_ram): errors.append(LN.error_totalram_0)
        if GV.COMPATIBILITY_RESULTS.space == -1: errors.append(LN.error_space_9)
        elif GV.COMPATIBILITY_RESULTS.space < fn.gigabyte(minimal_required_space): errors.append(LN.error_space_0)
        if GV.COMPATIBILITY_RESULTS.resizable == -1: errors.append(LN.error_resizable_9)
        elif GV.COMPATIBILITY_RESULTS.resizable < fn.gigabyte(minimal_required_space): errors.append(LN.error_resizable_0)

        if not errors:
            live_os_installer_index, GV.ACCEPTED_SPINS = prc.parse_spins(GV.ALL_SPINS)
            if live_os_installer_index is not None:
                GV.LIVE_OS_INSTALLER_SPIN = GV.ACCEPTED_SPINS[live_os_installer_index]
            GV.USERNAME_WINDOWS = fn.get_windows_username()
            return page_1()
        else:
            title.destroy()
            progressbar_check.destroy()
            tkt.add_page_title(MID_FRAME, LN.error_title % SW_NAME, pady=20)
            tkt.add_text_label(MID_FRAME, LN.error_list, pady=10)

            errors_tree = ttk.Treeview(MID_FRAME, columns='error', show='', height=6)
            errors_tree.pack(anchor=GV.UI.DI_VAR['w'], ipady=5, padx=(0, 5), fill='x')
            errors_tree.configure(selectmode='none')
            for i in range(len(errors)):
                errors_tree.insert('', index='end', iid=str(i), values=(errors[i],))

            tkt.add_secondary_btn(MID_FRAME, LN.btn_quit, lambda: fn.app_quit())

    # page_1
    def page_1():
        """the page on which you choose which distro/flaver and whether Autoinstall should be on or off"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set('Welcome to Lnixify')
        tkt.generic_page_layout(MID_FRAME, LN.desktop_question, LN.btn_next, lambda: next_btn_action())
        desktop_var = tk.StringVar(app, GV.UI.desktop)
        immutable_toggle_var = tk.BooleanVar(app, False)
        available_desktop = []
        dict_spins_with_fullname_keys = []
        for dist in GV.ACCEPTED_SPINS:
            spin_fullname = dist.name + ' ' + dist.version
            dict_spins_with_fullname_keys.append(spin_fullname)
            if dist.desktop and dist.desktop not in available_desktop:
                available_desktop.append(dist.desktop)
        frame_desktop = ttk.Frame(MID_FRAME)
        frame_desktop.pack(fill="x")
        for index, desktop in enumerate(available_desktop):
            tkt.add_radio_btn(frame_desktop, desktop, desktop_var, desktop, command=lambda: validate_input(),
                              pack=False).grid(ipady=5, row=index, column=0, sticky=GV.UI.DI_VAR['w'])
            if desktop in LN.desktop_hints.keys():
                ttk.Label(frame_desktop, wraplength=540, justify="center", text=LN.desktop_hints[desktop],
                          font=tkt.FONTS.tiny, foreground='#3aa9ff').grid(ipadx=5, row=index, column=1, sticky=GV.UI.DI_VAR['w'])
        tkt.add_radio_btn(frame_desktop, LN.choose_spin_instead, desktop_var, 'else', command=lambda: validate_input(),
                          pack=False).grid(ipady=5, row=len(available_desktop), column=0, sticky=GV.UI.DI_VAR['w'])

        combo_list_spin = ttk.Combobox(MID_FRAME, values=dict_spins_with_fullname_keys, state='readonly')
        combo_list_spin.bind("<<ComboboxSelected>>", lambda *args: validate_input())
        if not GV.UI.combo_list_spin: combo_list_spin.set(LN.choose_fedora_spin)
        else: combo_list_spin.set(GV.UI.combo_list_spin)
        frame_spin_info = tk.Frame(MID_FRAME)
        frame_spin_info.pack(side=GV.UI.DI_VAR['r'], fill="x", pady=5)
        selected_spin_info_tree = ttk.Treeview(frame_spin_info, columns='info', show='', height=2)
        selected_spin_info_tree.configure(selectmode='none')

        def validate_input(*args):
            if desktop_var.get() == 'else':
                combo_list_spin.pack(padx=40, pady=5, anchor=GV.UI.DI_VAR['w'])
                if combo_list_spin.get() in dict_spins_with_fullname_keys:
                    spin_index = dict_spins_with_fullname_keys.index(combo_list_spin.get())
                else:
                    spin_index = None
            else:
                combo_list_spin.pack_forget()
                spin_index = None
                for index, dist in enumerate(GV.ACCEPTED_SPINS):
                    if dist.desktop == desktop_var.get():
                        if bool(immutable_toggle_var.get()) == bool(dist.ostree_args):
                            spin_index = index
            if spin_index is not None:
                GV.SELECTED_SPIN = GV.ACCEPTED_SPINS[spin_index]
                if GV.SELECTED_SPIN.is_live_img:
                    GV.INSTALL_OPTIONS.live_img_url = live_img_url

                if GV.SELECTED_SPIN.is_live_img:
                    total_size = GV.LIVE_OS_INSTALLER_SPIN.size + GV.SELECTED_SPIN.size
                else:
                    total_size = GV.SELECTED_SPIN.size
                if GV.SELECTED_SPIN.is_base_netinstall:
                    dl_size_txt = LN.init_download % fn.byte_to_gb(total_size)
                else:
                    dl_size_txt = LN.total_download % fn.byte_to_gb(total_size)
                dl_spin_name_text = '%s: %s %s' % (LN.selected_spin, GV.SELECTED_SPIN.name, GV.SELECTED_SPIN.version)
                selected_spin_info_tree.pack(anchor=GV.UI.DI_VAR['w'], ipady=5, padx=(0, 0), fill='x')
                selected_spin_info_tree.delete(*selected_spin_info_tree.get_children())
                selected_spin_info_tree.insert('', index='end', iid='name', values=(dl_spin_name_text,))
                selected_spin_info_tree.insert('', index='end', iid='size', values=(dl_size_txt,))
            return spin_index

        validate_input()

        def next_btn_action(*args):
            if validate_input() is None:
                return -1
            GV.UI.combo_list_spin = combo_list_spin.get()
            GV.UI.desktop = desktop_var.get()  # Saving UI settings
            # LOG #############################################
            fn.log('\nFedora Spin has been selected, spin details:')

            for key, value in vars(GV.SELECTED_SPIN).items():
                fn.log('  -> %s: %s' % (str(key), str(value)))
            # #################################################
            return page_install_method()

    # page_autoinst1
    def page_install_method():
        """the autoinstall page on which you choose whether to install alongside windows or start clean install"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set(LN.install_auto)
        tkt.generic_page_layout(MID_FRAME, LN.windows_question % GV.SELECTED_SPIN.name,
                                LN.btn_next, lambda: next_btn_action(),
                                LN.btn_back, lambda: page_1())

        install_method_var = tk.StringVar(app, GV.INSTALL_OPTIONS.install_method)
        dualboot_size_var = tk.StringVar(app, str(GV.AUTOINST.dualboot_size))

        radio_buttons = ttk.Frame(MID_FRAME)
        radio_buttons.pack(fill='x')
        r1_autoinst_dualboot = tkt.add_radio_btn(radio_buttons, LN.windows_options['dualboot'],
                                                 install_method_var, 'dualboot', lambda: show_dualboot_options(True),
                                                 pack=False)
        r1_autoinst_dualboot.grid(ipady=5, column=0, row=0, sticky=GV.UI.DI_VAR['w'])
        r1_warning = ttk.Label(radio_buttons, wraplength=540, justify="center", text='', font=tkt.FONTS.tiny,
                               foreground='#ff4a4a')
        r1_warning.grid(padx=20, column=1, row=0, sticky=GV.UI.DI_VAR['w'])
        r2_autoinst_clean = tkt.add_radio_btn(radio_buttons, LN.windows_options['clean'], install_method_var, 'clean',
                                              lambda: show_dualboot_options(False), pack=False)
        r2_autoinst_clean.grid(ipady=5, column=0, row=2, sticky=GV.UI.DI_VAR['w'])
        r2_warning = ttk.Label(radio_buttons, wraplength=540, justify="center", text='', font=tkt.FONTS.tiny,
                               foreground='#ff4a4a')
        r2_warning.grid(padx=20, column=1, row=2, sticky=GV.UI.DI_VAR['w'])
        r3_custom = tkt.add_radio_btn(radio_buttons, LN.windows_options['custom'], install_method_var, 'custom', lambda: show_dualboot_options(False), pack=False)
        r3_custom.grid(ipady=5, column=0, row=3, sticky=GV.UI.DI_VAR['w'])

        min_size = dualboot_required_space
        max_size = fn.byte_to_gb(GV.COMPATIBILITY_RESULTS.resizable - GV.SELECTED_SPIN.size) - additional_failsafe_space
        max_size = round(max_size, 2)
        float_regex = r'^[0-9]*\.?[0-9]{0,3}$'  # max 3 decimal digits
        entry1_frame = ttk.Frame(radio_buttons)
        entry1_frame.grid(row=1, column=0, columnspan=4, padx=10)
        size_dualboot_txt_pre = ttk.Label(entry1_frame, wraplength=540, justify=GV.UI.DI_VAR['l'],
                                          text=LN.dualboot_size_txt, font=tkt.FONTS.tiny)
        size_dualboot_entry = ttk.Entry(entry1_frame, width=10, textvariable=dualboot_size_var)
        size_dualboot_txt_post = ttk.Label(entry1_frame, wraplength=540, justify=GV.UI.DI_VAR['l'],
                                           text='(%sGB - %sGB)' % (min_size, max_size), font=tkt.FONTS.tiny)
        tkt.var_tracer(dualboot_size_var, "write",
                       lambda *args: fn.validate_with_regex(dualboot_size_var, regex=float_regex, mode='fix'))

        # LOGIC
        space_dualboot = fn.gigabyte(dualboot_required_space + additional_failsafe_space) + GV.SELECTED_SPIN.size
        if GV.COMPATIBILITY_RESULTS.resizable < space_dualboot:
            r1_warning.config(text=LN.warn_space)
            r1_autoinst_dualboot.configure(state='disabled')
        if not GV.SELECTED_SPIN.is_auto_installable:
            r1_warning.config(text=LN.warn_not_available)
            r2_warning.config(text=LN.warn_not_available)
            r1_autoinst_dualboot.configure(state='disabled')
            r2_autoinst_clean.configure(state='disabled')
        app.update_idletasks()

        def show_dualboot_options(is_true: bool):
            if is_true:
                size_dualboot_txt_pre.grid(pady=5, padx=(10, 0), column=0, row=0, sticky=GV.UI.DI_VAR['w'])
                size_dualboot_entry.grid(pady=5, padx=5, column=1, row=0)
                size_dualboot_txt_post.grid(pady=5, padx=(0, 0), column=2, row=0, sticky=GV.UI.DI_VAR['w'])
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
        tkt.generic_page_layout(MID_FRAME, LN.windows_question % GV.SELECTED_SPIN.name,
                                LN.btn_next, lambda: next_btn_action(),
                                LN.btn_back, lambda: page_install_method())

        # tkt.add_check_btn(MID_FRAME, LN.additional_setup_now, vAutoinst_additional_setup_t)
        export_wifi_toggle_var = tk.BooleanVar(app, GV.AUTOINST.export_wifi)
        enable_encryption_toggle_var = tk.BooleanVar(app, GV.AUTOINST.enable_encryption)
        encrypt_passphrase_var = tk.StringVar(app, GV.AUTOINST.encryption_pass)
        encryption_tpm_unlock_toggle_var = tk.BooleanVar(app, GV.AUTOINST.encryption_tpm_unlock)

        tkt.add_check_btn(MID_FRAME, LN.add_import_wifi, export_wifi_toggle_var, pady=(5, 0))
        tkt.add_check_btn(MID_FRAME, LN.encrypted_root, enable_encryption_toggle_var,
                          lambda: show_encrypt_options(enable_encryption_toggle_var))

        only_digit_regex = r'^[0-9]+$'  # digits
        entry2_frame = ttk.Frame(MID_FRAME)

        encrypt_pass_pre = ttk.Label(entry2_frame, wraplength=540, justify=GV.UI.DI_VAR['l'],
                                     text=LN.entry_encrypt_passphrase_pre, font=tkt.FONTS.tiny)
        encrypt_passphrase_entry = ttk.Entry(entry2_frame, show="\u2022", width=10, textvariable=encrypt_passphrase_var)
        tkt.var_tracer(encrypt_passphrase_var, "write",
                       lambda *args: fn.validate_with_regex(encrypt_passphrase_var,
                                                            regex=only_digit_regex, mode='fix'))
        pass_confirm_var = tk.StringVar()
        encrypt_pass_confirm_pre = ttk.Label(entry2_frame, wraplength=540, justify=GV.UI.DI_VAR['l'],
                                             text=LN.entry_encrypt_passphrase_confirm_pre, font=tkt.FONTS.tiny)
        encrypt_pass_confirm_entry = ttk.Entry(entry2_frame, show="\u2022", width=10, textvariable=pass_confirm_var)
        encrypt_pass_confirm_not_matched = ttk.Label(entry2_frame, wraplength=540, justify=GV.UI.DI_VAR['l'],
                                                     text=LN.not_matched, font=tkt.FONTS.tiny, foreground='#ff4a4a')
        tpm_unlock = tkt.add_check_btn(entry2_frame, LN.encryption_tpm_unlock, encryption_tpm_unlock_toggle_var, pack=False)

        tkt.var_tracer(pass_confirm_var, "write",
                       lambda *args:
                       show_not_matched_warning(pass_confirm_var.get() != encrypt_passphrase_var.get()))

        encrypt_pass_pre.grid(column=0, row=0, sticky=GV.UI.DI_VAR['w'])
        encrypt_passphrase_entry.grid(pady=2, padx=5, column=1, row=0)
        encrypt_pass_confirm_pre.grid(column=0, row=1, sticky=GV.UI.DI_VAR['w'])
        encrypt_pass_confirm_entry.grid(pady=2, padx=5, column=1, row=1)
        tpm_unlock.grid(column=0, row=2, sticky=GV.UI.DI_VAR['w'])

        # LOGIC
        def show_not_matched_warning(is_true: bool):
            if is_true: encrypt_pass_confirm_not_matched.grid(pady=5, padx=(0, 0), column=2, row=1, sticky=GV.UI.DI_VAR['w'])
            else: encrypt_pass_confirm_not_matched.grid_forget()

        def show_encrypt_options(var):
            if var.get():
                entry2_frame.pack(fill='x', padx=(40, 0))
            else:
                entry2_frame.pack_forget()
        show_encrypt_options(enable_encryption_toggle_var)

        def next_btn_action(*args):
            if enable_encryption_toggle_var.get() and not (encrypt_passphrase_var.get() == pass_confirm_var.get() != ''):
                return
            else:
                GV.AUTOINST.export_wifi = export_wifi_toggle_var.get()
                GV.AUTOINST.enable_encryption = enable_encryption_toggle_var.get()
                GV.AUTOINST.encryption_pass = encrypt_passphrase_var.get()
                GV.AUTOINST.encryption_tpm_unlock = encryption_tpm_unlock_toggle_var.get()
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
            langs_and_locales = autoinst.get_locales_and_langs_sorted_with_names(territory=GV.IP_LOCALE['country_code'])
        else:
            langs_and_locales = autoinst.get_locales_and_langs_sorted_with_names()

        temp_frame = ttk.Frame(MID_FRAME)
        temp_frame.pack()
        lang_list_fedora = ttk.Treeview(temp_frame, columns='lang', show='headings', height=8)
        lang_list_fedora.heading('lang', text=LN.lang)
        lang_list_fedora.pack(anchor=GV.UI.DI_VAR['w'], side=GV.UI.DI_VAR['l'], ipady=5, padx=5)
        locale_list_fedora = ttk.Treeview(temp_frame, columns='locale', show='headings', height=8)
        locale_list_fedora.heading('locale', text=LN.locale)
        locale_list_fedora.pack(anchor=GV.UI.DI_VAR['w'], side=GV.UI.DI_VAR['l'], ipady=5, padx=5)

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
            locale_from_ip = autoinst.langtable.list_locales(territoryId=GV.IP_LOCALE['country_code'])[0]
            locale_from_ip_name = autoinst.langtable.language_name(languageId=locale_from_ip)
            if locale_from_ip != GV.AUTOINST.locale:
                tkt.add_radio_btn(MID_FRAME, LN.keymap_tz_option % locale_from_ip_name, keymap_timezone_source_var,
                                  'ip', command=lambda: spawn_more_widgets())

        tkt.add_radio_btn(MID_FRAME, LN.keymap_tz_option % chosen_locale_name, keymap_timezone_source_var, 'select', lambda: spawn_more_widgets())
        tkt.add_radio_btn(MID_FRAME, LN.keymap_tz_custom, keymap_timezone_source_var, 'custom', lambda: spawn_more_widgets())

        timezone_all = sorted(autoinst.all_timezones())
        lists_frame = ttk.Frame(MID_FRAME)
        timezone_txt = ttk.Label(lists_frame, wraplength=540, justify=GV.UI.DI_VAR['l'], text=LN.list_timezones, font=tkt.FONTS.tiny)
        timezone_list = ttk.Combobox(lists_frame, name="timezone", textvariable=custom_timezone_var)
        timezone_list['values'] = tuple(timezone_all)
        timezone_list['state'] = 'readonly'

        all_keymaps = autoinst.get_available_keymaps()

        keyboards_txt = ttk.Label(lists_frame, wraplength=540, justify=GV.UI.DI_VAR['l'], text=LN.list_keymaps, font=tkt.FONTS.tiny)
        keyboard_list = ttk.Combobox(lists_frame, name="keyboard", textvariable=custom_keymap_var)
        keyboard_list['values'] = tuple(all_keymaps)
        keyboard_list['state'] = 'readonly'

        if GV.IP_LOCALE:
            timezone_list.set(GV.IP_LOCALE['time_zone'])

        def spawn_more_widgets(*args):
            if keymap_timezone_source_var.get() == 'custom':
                lists_frame.pack(fill='x', padx=20)
                keyboards_txt.grid(pady=5, padx=5, column=0, row=1, sticky=GV.UI.DI_VAR['w'])
                keyboard_list.grid(pady=5, padx=5, column=1, row=1)
                timezone_txt.grid(pady=5, padx=5, column=0, row=0, sticky=GV.UI.DI_VAR['w'])
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
        tmp_part_size: int = GV.SELECTED_SPIN.size + fn.gigabyte(temp_part_failsafe_space)
        if GV.SELECTED_SPIN.is_live_img:
            tmp_part_size += GV.LIVE_OS_INSTALLER_SPIN.size
        if GV.AUTOINST.export_wifi:
            wifi_profiles = prc.get_wifi_profiles(PATH.WORK_DIR)
        else:
            wifi_profiles = None
        kickstart = types.SimpleNamespace()
        partition = types.SimpleNamespace()

        partition.tmp_part_size = tmp_part_size
        partition.temp_part_label = GV.TMP_PARTITION_LABEL

        if GV.INSTALL_OPTIONS.install_method != 'custom':
            if GV.AUTOINST.keymap_timezone_source == 'ip':
                GV.AUTOINST.keymap = autoinst.get_keymaps(territory=GV.IP_LOCALE['country_code'])[0]
                GV.AUTOINST.keymap_type = 'xlayout'
                GV.AUTOINST.timezone = autoinst.langtable.list_timezones(territoryId=GV.IP_LOCALE['country_code'])[0]
            elif GV.AUTOINST.keymap_timezone_source == 'select':
                GV.AUTOINST.keymap = autoinst.get_keymaps(lang=GV.AUTOINST.locale)[0]
                GV.AUTOINST.keymap_type = 'xlayout'
                GV.AUTOINST.timezone = autoinst.langtable.list_timezones(languageId=GV.AUTOINST.locale)[0]
            elif GV.AUTOINST.keymap_timezone_source == 'custom':
                pass
            kickstart.ostree_args = GV.SELECTED_SPIN.ostree_args
            kickstart.is_encrypted = GV.AUTOINST.enable_encryption
            kickstart.passphrase = GV.AUTOINST.encryption_pass
            kickstart.wifi_profiles = wifi_profiles
            kickstart.keymap = GV.AUTOINST.keymap
            kickstart.keymap_type = GV.AUTOINST.keymap_type
            kickstart.lang = GV.AUTOINST.locale
            kickstart.timezone = GV.AUTOINST.timezone
            kickstart.username = GV.AUTOINST.username
            kickstart.fullname = GV.AUTOINST.fullname
            kickstart.live_img_url = GV.INSTALL_OPTIONS.live_img_url
            kickstart.partition_method = GV.INSTALL_OPTIONS.install_method
            if GV.INSTALL_OPTIONS.install_method == 'dualboot':
                partition.shrink_space = fn.gigabyte(GV.AUTOINST.dualboot_size)
                partition.boot_part_size = fn.gigabyte(linux_boot_partition_size)
                partition.efi_part_size = fn.megabyte(linux_efi_partition_size)
            # LOG ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            fn.log('\nKickstart arguments (sensitive data sensored):')
            for key, value in vars(kickstart).items():
                if key in ('passphrase', 'fullname', 'username', 'wifi_profiles'):
                    if not value:
                        continue
                    fn.log('%s: (sensitive data)' % key)
                else:
                    fn.log('%s: %s' % (key, value))
            fn.log('\nPartitioning details:')
            for key, value in vars(partition).items():
                if key == 'queue': continue
                fn.log('%s: %s' % (key, value))
            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        else:
            kickstart = {}
        if GV.SELECTED_SPIN.is_live_img:
            installer_img = GV.LIVE_OS_INSTALLER_SPIN
            live_os = GV.SELECTED_SPIN
            live_os_size = live_os.size
            total_download_size = live_os.size + installer_img.size
        else:
            installer_img = GV.SELECTED_SPIN
            live_os = None
            live_os_size = 0
            total_download_size = installer_img.size
        installer_dl_percent_factor = installer_img.size / total_download_size * 0.90
        live_img_dl_factor = live_os_size / total_download_size * 0.90

        # Constructing user verification text based on user's selections  ++++++++++++++++++++++++++++++++++++++++++++++
        review_sel = []
        if GV.INSTALL_OPTIONS.install_method == 'custom':
            review_sel.append(LN.verify_text['no_autoinst'] % GV.SELECTED_SPIN.name)
        else:
            if GV.INSTALL_OPTIONS.install_method == 'dualboot':
                review_sel.append(LN.verify_text['autoinst_dualboot'] % GV.SELECTED_SPIN.name)
                review_sel.append(LN.verify_text['autoinst_keep_data'])
            elif GV.INSTALL_OPTIONS.install_method == 'clean':
                review_sel.append(LN.verify_text['autoinst_clean'] % GV.SELECTED_SPIN.name)
                review_sel.append(LN.verify_text['autoinst_rm_all'])
            if GV.AUTOINST.export_wifi:
                review_sel.append(LN.verify_text['autoinst_wifi'] % GV.SELECTED_SPIN.name)
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        review_tree = ttk.Treeview(MID_FRAME, columns='error', show='', height=3)
        review_tree.pack(anchor=GV.UI.DI_VAR['w'], ipady=5, pady=10, padx=(0, 5), fill='x')
        review_tree.configure(selectmode='none')

        for i in range(len(review_sel)):
            review_tree.insert('', index='end', iid=str(i), values=(review_sel[i],))
        # additions options (checkboxes)
        c2_add = ttk.Checkbutton(MID_FRAME, text=LN.add_auto_restart, variable=auto_restart_toggle_var, onvalue=1, offvalue=0)
        c2_add.pack(anchor=GV.UI.DI_VAR['w'])
        c3_add = ttk.Checkbutton(MID_FRAME, text=LN.add_torrent, variable=torrent_toggle_var, onvalue=1, offvalue=0)
        more_options_btn = ttk.Label(MID_FRAME, justify="center", text=LN.more_options, font=tkt.FONTS.tiny, foreground='#3aa9ff')
        more_options_btn.pack(pady=10, padx=10, anchor=GV.UI.DI_VAR['w'])
        more_options_btn.bind("<Button-1>",
                              lambda x: (more_options_btn.destroy(), c3_add.pack(anchor=GV.UI.DI_VAR['w'])))

        def validate_back_page(*args):
            if GV.INSTALL_OPTIONS.install_method == 'custom':
                page_install_method()
            else:
                page_autoinst_addition_2()

        def next_btn_action(*args):
            GV.INSTALL_OPTIONS.auto_restart = auto_restart_toggle_var.get()
            GV.INSTALL_OPTIONS.torrent = torrent_toggle_var.get()
            return page_installing(ks_kwargs=vars(kickstart), part_kwargs=vars(partition), installer_img=installer_img,
                                   installer_img_dl_percent_factor=installer_dl_percent_factor,
                                   live_img=live_os, live_img_dl_factor=live_img_dl_factor,
                                   is_live_img=GV.SELECTED_SPIN.is_live_img)

    def page_installing(ks_kwargs: dict, part_kwargs: dict,
                        installer_img, installer_img_dl_percent_factor: float,
                        is_live_img: bool, live_img=None, live_img_dl_factor: float = 0):
        """the page on which the initial installation (creating bootable media) takes place"""
        tkt.clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set(LN.install_running)
        progressbar_install = tkt.add_progress_bar(MID_FRAME)
        job_var = tk.StringVar(app)
        tkt.add_text_label(MID_FRAME, var=job_var, pady=0, padx=10)
        # INSTALL STARTING
        while GV.INSTALLER_STATUS not in (0, -1, -2):
            if GV.INSTALLER_STATUS is None:  # first step, start the download
                progressbar_install['value'] = 0
                job_var.set(LN.job_starting_download)
                app.update()
                fn.mkdir(PATH.WORK_DIR)
                is_torrent_dl = GV.INSTALL_OPTIONS.torrent
                installer_exist = prc.check_valid_existing_file(PATH.INSTALL_ISO, installer_img.hash256)
                live_img_exist = prc.check_valid_existing_file(PATH.LIVE_ISO, live_img.hash256)
                if not installer_exist:
                    while True:
                        file_path, checksum = download_and_track_spin(spin=installer_img,
                                                                      progress_bar=progressbar_install,
                                                                      progress_factor=installer_img_dl_percent_factor,
                                                                      tracker_var=job_var,
                                                                      new_file_path=PATH.INSTALL_ISO,
                                                                      do_torrent_dl=is_torrent_dl)
                        job_var.set(LN.job_checksum)
                        if download_hash_handler(checksum):
                            break  # re-download if file checksum didn't match expected, continue otherwise
                if is_live_img and not live_img_exist:
                    while True:
                        file_path, checksum = download_and_track_spin(spin=live_img,
                                                                      progress_bar=progressbar_install,
                                                                      progress_factor=live_img_dl_factor,
                                                                      tracker_var=job_var,
                                                                      new_file_path=PATH.LIVE_ISO,
                                                                      do_torrent_dl=is_torrent_dl)
                        job_var.set(LN.job_checksum)
                        if download_hash_handler(checksum):
                            break  # re-download if file checksum didn't match expected, continue otherwise
                if GV.AUTOINST.encryption_tpm_unlock:
                    aria2_kwargs = {'aria2_path': PATH.ARIA2C, 'url': TPM2_TOOLS_RPM_DL_LINK, 'destination': PATH.RPM_SOURCE_DIR}
                    run_async_function(fn.download_with_aria2, kwargs=aria2_kwargs, wait_for_result='OK')

                GV.INSTALLER_STATUS = 2

            if GV.INSTALLER_STATUS == 2:  # step 2: create temporary boot partition
                app.protocol("WM_DELETE_WINDOW", False)  # prevent closing the app during partition
                job_var.set(LN.job_creating_tmp_part)
                progressbar_install['value'] = 92
                tmp_part_result = run_async_function(prc.partition_procedure, kwargs=part_kwargs)
                if tmp_part_result[0] != 1:
                    return
                else:
                    GV.TMP_PARTITION_LETTER = tmp_part_result[1]
                    GV.INSTALLER_STATUS = 4

            if GV.INSTALLER_STATUS == 4:  # step 3: mount iso and copy files to temporary boot partition
                app.protocol("WM_DELETE_WINDOW", None)  # re-enable closing the app
                job_var.set(LN.job_copying_to_tmp_part)
                progressbar_install['value'] = 94
                installer_mount_letter = fn.mount_iso(PATH.INSTALL_ISO)
                source_files = installer_mount_letter + ':\\'
                destination = GV.TMP_PARTITION_LETTER + ':\\'
                run_async_function(fn.copy_files, kwargs={'source': source_files, 'destination': destination})
                if is_live_img:
                    live_img_mount_letter = fn.mount_iso(PATH.LIVE_ISO)
                    source_files = live_img_mount_letter + ':\\LiveOS\\'
                    destination = GV.TMP_PARTITION_LETTER + ':\\LiveOS\\'
                    run_async_function(fn.copy_files, kwargs={'source': source_files, 'destination': destination})

                rpm_dest_path = GV.TMP_PARTITION_LETTER + ':\\%s\\%s' % PATH.RELATIVE_RPM_DEST_DIR
                run_async_function(fn.copy_files, kwargs={'source': PATH.RPM_SOURCE_DIR, 'destination': rpm_dest_path})

                job_var.set(LN.job_adding_tmp_boot_entry)
                progressbar_install['value'] = 98
                if GV.INSTALL_OPTIONS.install_method != 'custom': grub_cfg_file = PATH.GRUB_CONFIG_AUTOINST
                else: grub_cfg_file = PATH.GRUB_CONFIG_DEFUALT
                grub_cfg_dest_path = GV.TMP_PARTITION_LETTER + ':\\' + PATH.RELATIVE_GRUB_CFG
                fn.set_file_readonly(grub_cfg_dest_path, False)
                fn.copy_and_rename_file(grub_cfg_file, grub_cfg_dest_path)
                grub_cfg_txt = prc.build_grub_cfg_file(GV.TMP_PARTITION_LABEL, GV.INSTALL_OPTIONS.install_method != 'custom')
                fn.set_file_readonly(grub_cfg_dest_path, False)
                grub_cfg = open(grub_cfg_dest_path, 'w')
                grub_cfg.write(grub_cfg_txt)
                grub_cfg.close()
                fn.set_file_readonly(grub_cfg_dest_path, True)
                nvidia_script_dest_path = GV.TMP_PARTITION_LETTER + ':\\%s' % PATH.RELATIVE_NVIDIA_SCRIPT
                fn.copy_and_rename_file(PATH.NVIDIA_SCRIPT, nvidia_script_dest_path)

                if GV.INSTALL_OPTIONS.install_method != 'custom':
                    kickstart_txt = prc.build_autoinstall_ks_file(**ks_kwargs)
                    if kickstart_txt:
                        kickstart = open(GV.TMP_PARTITION_LETTER + ':\\%s' % PATH.RELATIVE_KICKSTART, 'w')
                        kickstart.write(kickstart_txt)
                        kickstart.close()
                app.protocol("WM_DELETE_WINDOW", False)  # prevent closing the app
                if GV.INSTALL_OPTIONS.install_method == 'clean':
                    is_new_boot_order_permanent = True
                else:
                    is_new_boot_order_permanent = False
                boot_kwargs = {'boot_efi_file_path': default_efi_file_path, 'boot_drive_letter': GV.TMP_PARTITION_LETTER,
                          'is_permanent': is_new_boot_order_permanent}
                run_async_function(prc.add_boot_entry, kwargs=boot_kwargs)
                # step 5: clean up iso and other downloaded files since install is complete
                fn.unmount_iso(PATH.INSTALL_ISO)
                fn.unmount_iso(PATH.LIVE_ISO)
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
                                LN.btn_restart_now, lambda: fn.quit_and_restart_windows(),
                                LN.btn_restart_later, lambda: fn.app_quit())
        text_var = tk.StringVar()
        tkt.add_text_label(MID_FRAME, text=LN.finished_text, font=tkt.FONTS.small, pady=10)
        tkt.add_text_label(MID_FRAME, var=text_var, font=tkt.FONTS.small, pady=10)

        def countdown_to_restart(time):
            time -= 1
            if time > 0:
                text_var.set(LN.finished_text_restarting_now % (int(time)))
                app.after(1000, countdown_to_restart, time)
            else:
                fn.quit_and_restart_windows()

        if GV.INSTALL_OPTIONS.auto_restart:
            countdown_to_restart(10)

    page_check()
    #page_1()
    app.mainloop()


if __name__ == '__main__': main()
