# from APP_INFO import *
import ctypes
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk
from multiprocessing import Process, Queue
from autoinst import get_available_translations, get_xlated_timezone, langtable, get_locales_and_langs_sorted_with_names, all_timezones, detect_locale, \
    get_available_keymaps
from APP_INFO import *
from multilingual import language_list, change_lang
import functions as fn
from style import *
#   DRIVER CODE   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
app = tk.Tk()
app.title(SW_NAME)
app.geometry(str("%sx%s" % (MAXWIDTH, MAXHEIGHT)))
CURRENT_DIR = str(Path(__file__).parent.absolute())
# app.iconbitmap("yourimage.ico")
app.resizable(False, False)
app.option_add('*Font', 'Ariel 11')
#   STYLE     /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
style = ttk.Style(app)
app.tk.call('source', CURRENT_DIR + '/theme/azure-dark.tcl')
style.theme_use('azure')
style.configure("Accentbutton", foreground='white')
style.configure("Togglebutton", foreground='white')
#   MAIN CONTAINER & FRAMES   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
CONTAINER = tk.Frame(app)
TOP_FRAME = tk.Frame(CONTAINER, height=100, width=MAXWIDTH, background=top_background)
LEFT_FRAME = tk.Frame(CONTAINER, width=200, height=MAXHEIGHT)
MID_FRAME = tk.Frame(CONTAINER, height=700)
vTitleText = tk.StringVar(app)
TOP_TITLE = ttk.Label(TOP_FRAME, justify='center', textvariable=vTitleText, font=LARGEFONT, background=top_background)
left_frame_img = tk.PhotoImage(file='resources/leftframe.png')
left_frame_label = tk.Label(LEFT_FRAME, image=left_frame_img)
#   INITIALIZING GLOBAL VARIABLES /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
GLOBAL_QUEUE = Queue()
COMPATIBILITY_RESULTS = {}
COMPATIBILITY_CHECK_STATUS = 0
INSTALLER_STATUS = 0
IP_LOCALE = []
AUTOINST = {}
DOWNLOAD_PATH = ''
ISO_NAME = ''
ISO_PATH = ''
MOUNT_ISO_LETTER = ''
TMP_PARTITION_LETTER = ''
GRUB_CONFIG_DIR = CURRENT_DIR + '\\resources\\grub_conf\\'
# Tkinter variables, the '_t' suffix means Toggle
vDist = tk.IntVar(app, -2)
vAutoinst_t = tk.IntVar(app, 1)
vAutoinst_option = tk.IntVar(app, -1)
vWifi_t = tk.IntVar(app, 1)
vAutorestart_t = tk.IntVar(app, 0)
vTorrent_t = tk.IntVar(app, 0)
# autoinstaller variables
vKeymap_timezone_source = tk.IntVar(app, value=1)
vKeyboard = tk.StringVar(app)
vTimezone = tk.StringVar(app)
vFullname = tk.StringVar(app)
vUsername = tk.StringVar(app)
SELECTED_LOCALE = ''
USERNAME_WINDOWS = ''
#   MULTI-LINGUAL /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
lang_var = tk.StringVar()
LANG_LIST = ttk.Combobox(TOP_FRAME, name="language", textvariable=lang_var, background=top_background)
LANG_LIST['values'] = tuple(language_list.keys())
LANG_LIST['state'] = 'readonly'
# Set to English initially
LANG_LIST.set('English')
DI_VAR, LN = change_lang('English')
CURRENT_LANGUAGE = language_list['English']


def build_container():
    """Used to build or rebuild the main frames after language change to a language with different direction
(see function right_to_left_lang)"""
    CONTAINER.pack(side="top", fill="both", expand=True)
    TOP_FRAME.pack(fill="x", expand=1)
    TOP_FRAME.pack_propagate(False)
    LANG_LIST.pack(anchor=DI_VAR['w'], side='left', padx=30)
    TOP_TITLE.pack(anchor='center', side='left', padx=15)
    LEFT_FRAME.pack(fill="y", side=DI_VAR['l'])
    LEFT_FRAME.pack_propagate(False)
    left_frame_label.pack(side='bottom')
    MID_FRAME.pack(fill="both", expand=1, padx=15, pady=20)
    MID_FRAME.pack_propagate(False)


def open_popup(question_type, title_txt, msg_txt, regex=None):
    """
Pops up window to get input from user and freezes the main GUI while waiting for response
    :type regex: Pattern[str]
    :param question_type: can be a 'yes-no','cancel-confirm', 'abort-retry-continue', and 'entry' for text input
    :param title_txt: the title for the popup in big font
    :param msg_txt: the smaller text beneath the title
    :return:
    """
    pop = tk.Toplevel(app)
    border_frame = tk.Frame(pop, highlightbackground="gray", highlightthickness=1)
    pop_frame = tk.Frame(border_frame)
    btn_true_txt = ''
    btn_false_txt = ''
    btn_danger_txt = ''
    if question_type == 'cancel-confirm':
        btn_true_txt = LN.btn_confirm
        btn_false_txt = LN.btn_cancel
    elif question_type == 'cancel-continue':
        btn_true_txt = LN.btn_continue
        btn_false_txt = LN.btn_cancel
    elif question_type in ('abort-retry-continue', 'arc'):
        btn_true_txt = LN.btn_dl_again
        btn_false_txt = LN.btn_abort
        btn_danger_txt = LN.btn_continue
    elif question_type in ('yes-no', 'yn'):
        btn_true_txt = LN.btn_yes
        btn_false_txt = LN.btn_no
    elif question_type == 'entry':
        btn_true_txt = LN.btn_confirm
        btn_false_txt = LN.btn_cancel
    else: return -2

    pop_var = tk.IntVar()
    x = app.winfo_x()
    y = app.winfo_y()
    if len(msg_txt) > 120:
        geometry = "600x300+%d+%d" % (x+125, y+125)
        msg_font = VERYSMALLFONT
    else:
        geometry = "600x250+%d+%d" % (x+125, y+160)
        msg_font = SMALLFONT
    pop.geometry(geometry)
    pop.overrideredirect(True)
    pop.focus_set()
    pop.grab_set()
    border_frame.pack(expand=1, fill='both', pady=5, padx=5)
    pop_frame.pack(expand=1, fill='both', pady=5, padx=10)
    title = ttk.Label(pop_frame, wraplength=600, font=('Mistral 18 bold'), justify=DI_VAR['l'], text=title_txt)
    title.pack(pady=20, anchor=DI_VAR['w'])
    msg = ttk.Label(pop_frame, wraplength=600, justify=DI_VAR['l'], text=msg_txt, font=msg_font)
    msg.pack(pady=10, anchor=DI_VAR['w'])
    if question_type == 'entry':
        temp_frame = ttk.Frame(pop_frame)
        temp_frame.pack(fill='x', pady=(20, 0))
        entry_var = tk.StringVar(pop)
        entry = ttk.Entry(temp_frame, width=20, textvariable=entry_var)
        entry.pack(padx=(20, 10), anchor=DI_VAR['w'], side=DI_VAR['l'])
        if regex:
            entry_var.trace_add('write', lambda *args: fn.validate_with_regex(var=entry_var, regex=regex, mode='fix'))
        entry_suffix = ttk.Label(temp_frame, text='GB', font=msg_font)
        entry_suffix.pack(anchor=DI_VAR['w'], side=DI_VAR['l'])
    btn_true = ttk.Button(pop_frame, text=btn_true_txt, style="Accentbutton", command=lambda *args: validate_pop_input(1))
    btn_true.pack(anchor=DI_VAR['se'], side=DI_VAR['r'], ipadx=15, padx=10)
    btn_false = ttk.Button(pop_frame, text=btn_false_txt, command=lambda *args: validate_pop_input(0))
    btn_false.pack(anchor=DI_VAR['se'], side=DI_VAR['r'], padx=5)
    btn_danger = ttk.Button(pop_frame, text=btn_danger_txt, style="Dangerbutton", command=lambda *args: validate_pop_input(2))
    more_options_btn = ttk.Label(pop_frame, justify="center", text=LN.more_options, font=VERYSMALLFONT, foreground='#3aa9ff')
    more_options_btn.bind("<Button-1>",
                          lambda *args: (more_options_btn.pack_forget(),
                                         btn_danger.pack(anchor=DI_VAR['se'], side=DI_VAR['r'], padx=5)))
    if btn_danger_txt: more_options_btn.pack(anchor=DI_VAR['se'], side=DI_VAR['r'], padx=5, pady=8)

    def validate_pop_input(inputted):
        pop_var.set(inputted)
        pop.destroy()
    pop.wait_window()
    if question_type == 'entry' and pop_var.get() == 1:
        return entry_var.get()
    return pop_var.get()


def language_handler(new_language=None, current_page=None):
    global DI_VAR, LN, CURRENT_LANGUAGE
    if new_language is None: new_language = lang_var.get()
    if new_language == CURRENT_LANGUAGE: return
    DI_VAR, LN = change_lang(new_lang=new_language)
    CURRENT_LANGUAGE = new_language
    build_container()
    if current_page is not None: return current_page()


def main():
    def page_check():
        """The page on which is decided whether the app can run on the device or not"""
        # ************** Multilingual support *************************************************************************
        def page_name(): page_check()
        def change_callback(*args): language_handler(current_page=page_name)
        LANG_LIST.bind('<<ComboboxSelected>>', change_callback)
        clear_frame(MID_FRAME)
        # *************************************************************************************************************
        title = ttk.Label(MID_FRAME, wraplength=540, justify=DI_VAR['l'], text=LN.check_running, font=MEDIUMFONT)
        title.pack(pady=35, anchor=DI_VAR['w'])
        progressbar_check = ttk.Progressbar(MID_FRAME, orient='horizontal', length=550, mode='indeterminate')
        progressbar_check.pack(pady=25)
        progressbar_check.start(10)
        job_var = tk.StringVar()
        current_job = ttk.Label(MID_FRAME, wraplength=540, justify=DI_VAR['l'], textvariable=job_var, font=SMALLFONT)
        current_job.pack(padx=10, anchor=DI_VAR['w'])
        # Request elevation (admin) if not running as admin
        if not ctypes.windll.shell32.IsUserAnAdmin():
            app.update()
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            quit()
        global COMPATIBILITY_RESULTS, COMPATIBILITY_CHECK_STATUS, IP_LOCALE
        COMPATIBILITY_RESULTS = {'uefi': 1, 'ram': 34359738368, 'space': 133264248832, 'resizable': 432008358400, 'bitlocker': 1, 'arch': 'amd64'}
        if not COMPATIBILITY_RESULTS:
            if not COMPATIBILITY_CHECK_STATUS:
                Process(target=fn.compatibility_test, args=(minimal_required_space, GLOBAL_QUEUE,)).start()
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
                    elif queue_out == 'bitlocker': job_var.set(LN.check_bitlocker)
                    elif isinstance(queue_out, tuple) and queue_out[0] == 'detect_locale':
                        IP_LOCALE = queue_out[1:]
                    elif isinstance(queue_out, dict):
                        COMPATIBILITY_RESULTS = queue_out
                        print(COMPATIBILITY_RESULTS)
                        COMPATIBILITY_CHECK_STATUS = 2
                        break
        # if not LOCALE_IP: LOCALE_IP = ('US', 'America/New_York')
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
        if COMPATIBILITY_RESULTS['bitlocker'] == -1: errors.append(LN.error_bitlocker_9)
        elif COMPATIBILITY_RESULTS['bitlocker'] == 0: errors.append(LN.error_bitlocker_0)

        if not errors:
            global DOWNLOAD_PATH, ISO_NAME, ISO_PATH, USERNAME_WINDOWS
            DOWNLOAD_PATH = fn.get_user_home_dir() + "\\win2linux_tmpdir"
            ISO_NAME = 'install_media.iso'
            ISO_PATH = DOWNLOAD_PATH + "\\" + ISO_NAME
            USERNAME_WINDOWS = fn.get_windows_username()
            page_1()
        else:
            title.pack_forget()
            progressbar_check.pack_forget()
            title = ttk.Label(MID_FRAME, wraplength=540, justify=DI_VAR['l'], text=LN.error_title % SW_NAME,
                              font=MEDIUMFONT)
            title.pack(pady=35, anchor=DI_VAR['nw'])

            errors_text_label = ttk.Label(MID_FRAME, wraplength=540, justify=DI_VAR['l'], text=LN.error_list + '\n',
                                          font=SMALLFONT)
            errors_text_label.pack(padx=10, anchor=DI_VAR['w'])

            errors_listed = 'x  ' + ("\nx  ".join(errors))
            errors_text = tk.Text(MID_FRAME, spacing1=6, height=6)
            errors_text.insert(1.0, errors_listed)
            errors_text.configure(state='disabled')
            errors_text.pack(padx=10, pady=5, anchor=DI_VAR['w'])

            btn_quit = ttk.Button(MID_FRAME, text=LN.btn_quit, command=lambda: app.destroy())
            btn_quit.pack(anchor=DI_VAR['se'], side=DI_VAR['r'], ipadx=15, padx=10)

    # page_1
    def page_1():
        # ************** Multilingual support *************************************************************************
        def page_name(): page_1()
        def change_callback(*args): language_handler(current_page=page_name)
        LANG_LIST.bind('<<ComboboxSelected>>', change_callback)
        clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set('Welcome to Lnixify')
        title = ttk.Label(MID_FRAME, wraplength=540, justify=DI_VAR['l'], text=LN.install_question, font=MEDIUMFONT)
        title.pack(pady=35, anchor=DI_VAR['w'])

        for index, distro in enumerate(distros['name']):
            txt = ''  # Generating Text for each list member of installable flavors/distros
            if distros['advanced'][index]: txt += LN.adv + ': '
            txt += distro + ' %s' % distros['version'][index]
            if distros['de'][index]: txt += ' (%s)' % distros['de'][index]
            if distros['netinstall'][index]: txt += ' (%s)' % LN.net_install
            if distros['recommended'][index]:
                if vDist.get() == -2: vDist.set(index)  # If unset, set it to the default recommended entry
                if distros['auto-installable'][index]: vAutoinst_t.set(1)  # by default turn on autoinstall if supported
                txt += ' (%s)' % LN.recommended
            temp_frame = ttk.Frame(MID_FRAME)
            temp_frame.pack(fill="x", pady=5)
            radio = ttk.Radiobutton(temp_frame, text=txt, variable=vDist, value=index, command=lambda: validate_input())
            radio.pack(anchor=DI_VAR['w'], side=DI_VAR['l'])
            if distros['netinstall'][index]: dl_size_txt = LN.init_download % distros['size'][index]
            else: dl_size_txt = LN.total_download % distros['size'][index]
            ttk.Label(temp_frame, wraplength=540, justify="center", text=dl_size_txt,
                      font=VERYSMALLFONT, foreground='#3aa9ff').pack(padx=5, anchor=DI_VAR['e'], side=DI_VAR['r'])
            if COMPATIBILITY_RESULTS['resizable'] < fn.gigabyte(distros['size'][index]):
                radio.configure(state='disabled')
                ttk.Label(temp_frame, wraplength=540, justify="center", text=LN.warn_space,
                          font=VERYSMALLFONT, foreground='#ff4a4a').pack(padx=5, anchor=DI_VAR['e'], side=DI_VAR['r'])
                if distros['recommended'][index]:
                    vDist.set(-1)

        c1_autoinst = ttk.Checkbutton(MID_FRAME, text=LN.install_auto, variable=vAutoinst_t, onvalue=1, offvalue=0)
        c1_autoinst.pack(anchor=DI_VAR['w'], pady=40)
        btn_next = ttk.Button(MID_FRAME, text=LN.btn_next, style="Accentbutton", command=lambda: validate_next_page())
        btn_next.pack(anchor=DI_VAR['se'], side=DI_VAR['r'], ipadx=15, padx=10)

        def validate_input(*args):
            if distros['advanced'][vDist.get()]:
                question = open_popup('cancel-continue', LN.adv_confirm, LN.adv_confirm_text)
                print('hi')
                if not question: vDist.set(-1)
                else: pass
            if distros['auto-installable'][vDist.get()]:
                c1_autoinst['state'] = 'enabled'
                vAutoinst_t.set(1)
            else:
                c1_autoinst['state'] = 'disabled'
                vAutoinst_t.set(0)

        def validate_next_page(*args):
            if vDist.get() == -1: return
            if vAutoinst_t.get(): return page_autoinst1()
            return page_verify()

    # page_autoinst1
    def page_autoinst1():
        # ************** Multilingual support *************************************************************************
        def page_name(): page_autoinst1()
        def change_callback(*args): language_handler(current_page=page_name)
        LANG_LIST.bind('<<ComboboxSelected>>', change_callback)
        clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set(LN.install_auto)
        title = ttk.Label(MID_FRAME, wraplength=540, justify=DI_VAR['l'],
                          text=LN.windows_question % distros['name'][vDist.get()], font=MEDIUMFONT)
        title.pack(pady=35, anchor=DI_VAR['w'])

        r1_frame = ttk.Frame(MID_FRAME)
        r1_frame.pack(fill="x")
        r1_autoinst = ttk.Radiobutton(r1_frame, text=LN.windows_options[0], variable=vAutoinst_option, value=0,
                                      command=lambda: ask_dualboot_size())
        r1_autoinst.pack(anchor=DI_VAR['w'], side=DI_VAR['l'], ipady=5)
        r1_space = ttk.Label(r1_frame, wraplength=540, justify="center", text=LN.warn_space, font=VERYSMALLFONT,
                             foreground='#ff4a4a')
        r2_autoinst = ttk.Radiobutton(MID_FRAME, text=LN.windows_options[1], variable=vAutoinst_option, value=1)
        r2_autoinst.pack(anchor=DI_VAR['w'], ipady=5)
        r3_autoinst = ttk.Radiobutton(MID_FRAME, text=LN.windows_options[2], variable=vAutoinst_option, value=2)
        r3_autoinst.pack(anchor=DI_VAR['w'], ipady=5)

        c1_add = ttk.Checkbutton(MID_FRAME, text=LN.add_import_wifi, variable=vWifi_t, onvalue=1, offvalue=0)
        c1_add.pack(anchor=DI_VAR['w'], ipady=5, pady=30)
        btn_next = ttk.Button(MID_FRAME, text=LN.btn_next, style="Accentbutton", command=lambda: validate_next_page())
        btn_next.pack(anchor=DI_VAR['se'], side=DI_VAR['r'], ipadx=15, padx=10)
        btn_back = ttk.Button(MID_FRAME, text=LN.btn_back, command=lambda: page_1())
        btn_back.pack(anchor=DI_VAR['se'], side=DI_VAR['r'], padx=5)

        # LOGIC
        space_dualboot = fn.gigabyte(distros['size'][vDist.get()] + dualboot_required_space + additional_failsafe_space)
        if COMPATIBILITY_RESULTS['resizable'] < space_dualboot:
            r1_space.pack(padx=20, anchor=DI_VAR['e'], side=DI_VAR['l'])
            r1_autoinst.configure(state='disabled')

        def ask_dualboot_size():
            min_size = dualboot_required_space
            max_size = fn.byte_to_gb(COMPATIBILITY_RESULTS['resizable']) - distros['size'][vDist.get()] - additional_failsafe_space
            float_regex = r'^[0-9]*\.?[0-9]{0,3}$'
            while True:
                result = open_popup(question_type='entry',
                                    title_txt=LN.dualboot_size_question % distros['name'][vDist.get()],
                                    msg_txt=LN.dualboot_size_txt % (min_size, max_size),
                                    regex=float_regex)
                if result == 0:
                    vAutoinst_option.set(-1)
                    break
                try:
                    result = float(result)
                    if min_size <= result <= max_size: return result
                except ValueError: pass

        def validate_next_page(*args):
            if vAutoinst_option.get() == -1: return
            page_autoinst2()

    # page_autoinst2
    def page_autoinst2():
        # ************** Multilingual support *************************************************************************
        def page_name(): page_autoinst2()
        def change_callback(*args): language_handler(current_page=page_name)
        LANG_LIST.bind('<<ComboboxSelected>>', change_callback)
        clear_frame(MID_FRAME)
        # *************************************************************************************************************
        title = ttk.Label(MID_FRAME, wraplength=540, justify=DI_VAR['l'], text=LN.title_autoinst2, font=MEDIUMFONT)
        title.pack(pady=35, anchor=DI_VAR['w'])

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

        btn_next = ttk.Button(MID_FRAME, text=LN.btn_next, style="Accentbutton", command=lambda: validate_next_page())
        btn_next.pack(anchor=DI_VAR['se'], side=DI_VAR['r'], ipadx=15, padx=10)
        btn_back = ttk.Button(MID_FRAME, text=LN.btn_back, command=lambda: page_autoinst1())
        btn_back.pack(anchor=DI_VAR['se'], side=DI_VAR['r'], padx=5)

        def on_lang_click(*args):
            for item in locale_list_fedora.get_children():
                locale_list_fedora.delete(item)
            for locale in langs_and_locales[int(lang_list_fedora.focus())][1]:
                locale_list_fedora.insert(parent='', index='end', iid=locale[2], values=locale[1:2])
        lang_list_fedora.bind('<<TreeviewSelect>>', on_lang_click)

        def validate_next_page(*args):
            global SELECTED_LOCALE
            SELECTED_LOCALE = locale_list_fedora.focus()
            if langtable.parse_locale(SELECTED_LOCALE).language:
                return page_autoinst3()

    def page_autoinst3():
        # ************** Multilingual support *************************************************************************
        def page_name(): page_autoinst3()
        def change_callback(*args): language_handler(current_page=page_name)
        LANG_LIST.bind('<<ComboboxSelected>>', change_callback)
        clear_frame(MID_FRAME)
        # *************************************************************************************************************

        title = ttk.Label(MID_FRAME, wraplength=540, justify=DI_VAR['l'], text=LN.title_autoinst3, font=MEDIUMFONT)
        title.pack(pady=35, anchor=DI_VAR['w'])
        
        chosen_locale_name = langtable.language_name(languageId=SELECTED_LOCALE)
        if IP_LOCALE:
            locale_from_ip = langtable.list_locales(territoryId=IP_LOCALE[0])[0]
            locale_from_ip_name = langtable.language_name(languageId=locale_from_ip)
            if locale_from_ip != SELECTED_LOCALE:
                r1_keymaps_tz = ttk.Radiobutton(MID_FRAME, text=LN.keymap_tz_option % locale_from_ip_name,
                                                variable=vKeymap_timezone_source, value=0, command=lambda: validate_input())
                r1_keymaps_tz.pack(anchor=DI_VAR['w'], ipady=5)

        r2_keymaps_tz = ttk.Radiobutton(MID_FRAME, text=LN.keymap_tz_option % chosen_locale_name,
                                        variable=vKeymap_timezone_source, value=1, command=lambda: validate_input())
        r3_keymaps_tz = ttk.Radiobutton(MID_FRAME, text=LN.keymap_tz_custom, variable=vKeymap_timezone_source,
                                        value=2, command=lambda: validate_input())
        r2_keymaps_tz.pack(anchor=DI_VAR['w'], ipady=5)
        r3_keymaps_tz.pack(anchor=DI_VAR['w'], ipady=5)

        timezone_all = sorted(all_timezones())
        lists_frame = ttk.Frame(MID_FRAME)
        timezone_txt = ttk.Label(lists_frame, wraplength=540, justify=DI_VAR['l'], text=LN.list_timezones, font=VERYSMALLFONT)
        timezone_list = ttk.Combobox(lists_frame, name="timezone", textvariable=vTimezone)
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
        keyboards_txt = ttk.Label(lists_frame, wraplength=540, justify=DI_VAR['l'], text=LN.list_keymaps, font=VERYSMALLFONT)
        keyboard_list = ttk.Combobox(lists_frame, name="keyboard", textvariable=vKeyboard)
        keyboard_list['values'] = tuple(keyboards_all)
        keyboard_list['state'] = 'readonly'

        if IP_LOCALE:
            timezone_list.set(IP_LOCALE[1])
            keyboard_list.set(keyboards_all[0])

        btn_next = ttk.Button(MID_FRAME, text=LN.btn_next, style="Accentbutton", command=lambda: validate_next_page())
        btn_next.pack(anchor=DI_VAR['se'], side=DI_VAR['r'], ipadx=15, padx=10)
        btn_back = ttk.Button(MID_FRAME, text=LN.btn_back, command=lambda: page_autoinst2())
        btn_back.pack(anchor=DI_VAR['se'], side=DI_VAR['r'], padx=5)

        def validate_input(*args):
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
                AUTOINST['keymap'] = langtable.list_keyboards(languageId=SELECTED_LOCALE)[0]
                AUTOINST['timezone'] = langtable.list_timezones(languageId=SELECTED_LOCALE)[0]
            elif vKeymap_timezone_source.get() == 2:
                AUTOINST['keymap'] = vKeyboard.get()
                AUTOINST['timezone'] = vTimezone.get()

            if AUTOINST['keymap'] and AUTOINST['timezone']:
                page_autoinst4()

    def page_autoinst4():
        # ************** Multilingual support *************************************************************************
        def page_name(): page_autoinst4()
        def change_callback(*args): language_handler(current_page=page_name)
        LANG_LIST.bind('<<ComboboxSelected>>', change_callback)
        clear_frame(MID_FRAME)
        # *************************************************************************************************************

        title = ttk.Label(MID_FRAME, wraplength=540, justify=DI_VAR['l'], text=LN.title_autoinst4, font=MEDIUMFONT)
        title.pack(pady=35, anchor=DI_VAR['w'])

        # Regex Syntax *****
        portable_fs_chars = r'a-zA-Z0-9._-'
        _name_base = r'[a-zA-Z0-9._][' + portable_fs_chars + r']{0,30}([' + portable_fs_chars + r']|\$)?'
        username_regex = r'^' + _name_base + '$'
        fullname_regex = r'^[^:]*$'
        # Only allow username and fullname that meet the regex syntax above
        vFullname.trace_add("write", lambda *args: fn.validate_with_regex(vFullname, regex=fullname_regex, mode='fix'))
        vUsername.trace_add("write", lambda *args: fn.validate_with_regex(vUsername, regex=username_regex, mode='fix'))

        entries_frame = ttk.Frame(MID_FRAME)
        fullname_txt = ttk.Label(entries_frame, wraplength=540, justify=DI_VAR['l'], text=LN.entry_fullname, font=VERYSMALLFONT)
        fullname_entry = ttk.Entry(entries_frame, width=40, textvariable=vFullname)
        username_txt = ttk.Label(entries_frame, wraplength=540, justify=DI_VAR['l'], text=LN.entry_username, font=VERYSMALLFONT)
        username_entry = ttk.Entry(entries_frame, width=40, textvariable=vUsername)

        entries_frame.pack(fill='x', padx=20)
        fullname_txt.grid(pady=5, padx=5, column=0, row=0, sticky=DI_VAR['w'])
        fullname_entry.grid(pady=5, padx=5, column=1, row=0)
        username_txt.grid(pady=5, padx=5, column=0, row=1, sticky=DI_VAR['w'])
        username_entry.grid(pady=5, padx=5, column=1, row=1)

        password_reminder = ttk.Label(MID_FRAME, wraplength=540, justify=DI_VAR['l'], text=LN.password_reminder_txt, font=VERYSMALLFONT)
        password_reminder.pack(pady=10, padx=20, anchor=DI_VAR['w'])
        btn_next = ttk.Button(MID_FRAME, text=LN.btn_next, style="Accentbutton", command=lambda: validate_next_page())
        btn_next.pack(anchor=DI_VAR['se'], side=DI_VAR['r'], ipadx=15, padx=10)
        btn_back = ttk.Button(MID_FRAME, text=LN.btn_back, command=lambda: page_autoinst3())
        btn_back.pack(anchor=DI_VAR['se'], side=DI_VAR['r'], padx=5)

        if not vUsername.get():
            username_entry.insert(index=0, string=USERNAME_WINDOWS)
            username_entry.select_range(start=0, end=999)

        def validate_next_page(*args):
            # Username cannot be empty
            is_username_valid = fn.validate_with_regex(vUsername, regex=username_regex, mode='read') not in (False, 'empty')
            is_fullname_valid = fn.validate_with_regex(vFullname, regex=fullname_regex, mode='read')
            if is_username_valid and is_fullname_valid:
                page_verify()

    def page_verify():
        # ************** Multilingual support *************************************************************************
        def page_name(): page_verify()
        def change_callback(*args): language_handler(current_page=page_name)
        LANG_LIST.bind('<<ComboboxSelected>>', change_callback)
        clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set('')
        title = ttk.Label(MID_FRAME, wraplength=540, justify=DI_VAR['l'], text=LN.verify_question, font=MEDIUMFONT)
        title.pack(pady=35, anchor=DI_VAR['w'])
        # Construction user verification text based on user's selections  ++++++++++++++++++++++++++++++++++++++++++++++
        review_sel = 'x  ' + LN.verify_text[0] % distros['name'][vDist.get()] + LN.verify_text[1][vAutoinst_t.get()]
        if vAutoinst_t.get():
            review_sel += LN.verify_text[2][vAutoinst_option.get()]
            review_sel += '\nx  ' + LN.verify_text[3][vAutoinst_option.get()]
            if vAutoinst_option.get() == 1: review_sel = review_sel % fn.get_sys_drive_letter()
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        review_text = tk.Text(MID_FRAME, spacing1=1, height=5, width=100, wrap='word')
        review_text.insert(1.0, review_sel)
        review_text.configure(state='disabled')
        review_text.pack(anchor=DI_VAR['w'], pady=5)
        # additions options (checkboxes)
        c2_add = ttk.Checkbutton(MID_FRAME, text=LN.add_auto_restart, variable=vAutorestart_t, onvalue=1, offvalue=0)
        c2_add.pack(anchor=DI_VAR['w'])
        c3_add = ttk.Checkbutton(MID_FRAME, text=LN.add_torrent, variable=vTorrent_t, onvalue=1, offvalue=0)
        more_options_btn = ttk.Label(MID_FRAME, justify="center", text=LN.more_options, font=VERYSMALLFONT, foreground='#3aa9ff')
        more_options_btn.pack(pady=10, padx=10, anchor=DI_VAR['w'])
        more_options_btn.bind("<Button-1>",
                              lambda x: (more_options_btn.pack_forget(), c3_add.pack(anchor=DI_VAR['w'])))
        btn_next = ttk.Button(MID_FRAME, text=LN.btn_install, style="Accentbutton", command=lambda: page_installing())
        btn_next.pack(anchor=DI_VAR['se'], side=DI_VAR['r'], ipadx=15, padx=10)
        btn_back = ttk.Button(MID_FRAME, text=LN.btn_back, command=lambda: validate_back_page())
        btn_back.pack(anchor=DI_VAR['se'], side=DI_VAR['r'], padx=5)

        def validate_back_page(*args):
            if vAutoinst_t.get(): page_autoinst4()
            else: page_1()

    def page_installing():
        # ************** Multilingual support *************************************************************************
        def page_name(): page_installing()
        def change_callback(*args): language_handler(current_page=page_name)
        LANG_LIST.bind('<<ComboboxSelected>>', change_callback)
        clear_frame(MID_FRAME)
        # *************************************************************************************************************
        vTitleText.set(LN.install_running)
        LANG_LIST.pack_forget()
        # title = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'], text=LN.install_running, font=MEDIUMFONT)
        # title.pack(pady=35, anchor=di_var['w'])
        progressbar_install = ttk.Progressbar(MID_FRAME, orient='horizontal', length=550, mode='determinate')
        progressbar_install.pack(pady=25)
        job_var = tk.StringVar()
        current_job = ttk.Label(MID_FRAME, wraplength=540, justify=DI_VAR['l'], textvariable=job_var, font=SMALLFONT)
        current_job.pack(padx=10, anchor=DI_VAR['w'])

        global INSTALLER_STATUS, MOUNT_ISO_LETTER, TMP_PARTITION_LETTER
        if fn.check_file_if_exists(ISO_PATH) == 'True':
            # checking if files from previous runs are present and if so, ask if user wishes to use them.
            question = open_popup('yes-no', LN.old_download_detected, LN.old_download_detected_text)
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
                    question = open_popup('yes-no', LN.job_checksum_failed, LN.job_checksum_failed_txt)
                    if question: INSTALLER_STATUS = 2.5
                    else:
                        question = open_popup('yes-no', LN.cleanup_question, LN.cleanup_question_txt)
                        if question: fn.remove_folder(DOWNLOAD_PATH)
                        app.destroy()
                else:
                    question = open_popup('abort-retry-continue', LN.job_checksum_mismatch, LN.job_checksum_mismatch_txt % out)
                    if question == 1: pass
                    if question == 2: INSTALLER_STATUS = 2.5
                    if question == 0:
                        question = open_popup('yes-no', LN.cleanup_question, LN.cleanup_question_txt)
                        if question: fn.remove_folder(DOWNLOAD_PATH)
                        else: app.destroy()
            if INSTALLER_STATUS == 2.5:  # step 2: create temporary boot partition
                while GLOBAL_QUEUE.qsize(): GLOBAL_QUEUE.get()  # to empty the queue
                tmp_part_size = fn.gigabyte(distros['size'][vDist.get()])
                Process(target=fn.create_temp_boot_partition, args=(tmp_part_size, GLOBAL_QUEUE,)).start()
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
            if INSTALLER_STATUS == 4:  # step 3: mount iso and copy files to temporary boot partition
                while GLOBAL_QUEUE.qsize(): GLOBAL_QUEUE.get()  # to empty the queue
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
                fn.copy_one_file(grub_cfg_file, TMP_PARTITION_LETTER + ':\\EFI\\BOOT\\grub.cfg')
                Process(target=fn.add_boot_entry, args=(default_efi_file_path, TMP_PARTITION_LETTER, GLOBAL_QUEUE,)).start()
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
                break

        page_restart_required()

    def page_restart_required():
        # ************** Multilingual support *************************************************************************
        def page_name(): page_restart_required()
        def change_callback(*args): language_handler(current_page=page_name)
        LANG_LIST.bind('<<ComboboxSelected>>', change_callback)
        clear_frame(MID_FRAME)
        # *************************************************************************************************************
        LANG_LIST.pack(anchor=DI_VAR['nw'], padx=10, pady=10)

        title = ttk.Label(MID_FRAME, wraplength=540, justify=DI_VAR['l'], text=LN.finished_title, font=MEDIUMFONT)
        title.pack(pady=35, anchor=DI_VAR['w'])

        text_var = tk.StringVar()
        text1 = ttk.Label(MID_FRAME, wraplength=540, justify=DI_VAR['l'], text=LN.finished_text, font=SMALLFONT)
        text1.pack(pady=10, anchor=DI_VAR['w'])
        text2 = ttk.Label(MID_FRAME, wraplength=540, justify="center", textvariable=text_var, font=SMALLFONT)
        text2.pack(pady=10, anchor=DI_VAR['w'])

        button1 = ttk.Button(MID_FRAME, text=LN.btn_restart_now, style="Accentbutton", command=lambda: (fn.restart_windows(), app.destroy()))
        button1.pack(anchor=DI_VAR['se'], side=DI_VAR['r'], ipadx=15, padx=10)
        button2 = ttk.Button(MID_FRAME, text=LN.btn_restart_later, command=lambda: app.destroy())
        button2.pack(anchor=DI_VAR['se'], side=DI_VAR['r'], padx=5)

        if vAutorestart_t.get():
            time_left = 10
            while time_left > 0:
                text_var.set(LN.finished_text_restarting_now % (int(time_left)))
                time_left = time_left - 0.01
                app.after(10, app.update())
            fn.restart_windows()
            app.destroy()

    #if not ctypes.windll.shell32.IsUserAnAdmin():
    #    app.update()
    #    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    #    quit()
    #add_boot_entry(APP_INFO.efi_file_path, 'G', queue1)
    #relabel_volume('C', 'Windows OS')
    #print(get_wifi_profiles())

    # language_handler(new_language='English')

    build_container()
    page_check()
    app.mainloop()


if __name__ == '__main__': main()
