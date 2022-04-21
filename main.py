# from APP_INFO import *
import ctypes
import importlib
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk
from multiprocessing import Process, Queue
from APP_INFO import *
from multilingual import language_list, right_to_left_lang
from functions import *
from translations.en import *

#   DRIVER CODE   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
app = tk.Tk()
app.title(SW_NAME)
MAXWIDTH = 800
MAXHEIGHT = 500
app.geometry(str("%sx%s" % (MAXWIDTH, MAXHEIGHT)))
current_dir = str(Path(__file__).parent)
# app.iconbitmap("yourimage.ico")
app.resizable(False, False)
app.option_add('*Font', 'Ariel 11')
#   STYLE     /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
style = ttk.Style(app)
app.tk.call('source', current_dir + '/theme/azure-dark.tcl')
style.theme_use('azure')
style.configure("Accentbutton", foreground='white')
style.configure("Togglebutton", foreground='white')
LARGEFONT = ("Ariel", 24)
MEDIUMFONT = ("Ariel Bold", 15)
SMALLFONT = ("Ariel", 12)
VERYSMALLFONT = ("Ariel", 10)

#   MAIN CONTAINER & FRAMES   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
container = tk.Frame(app)
top_bg = '#474747'
top_frame = tk.Frame(container, height=100, width=MAXWIDTH, background=top_bg)
main_title_text = tk.StringVar()
top_main_title = ttk.Label(top_frame, justify='center', textvariable=main_title_text, font=LARGEFONT, background=top_bg)
left_frame = tk.Frame(container, width=200, height=MAXHEIGHT)
left_frame_img = tk.PhotoImage(file='resources/leftframe.png')
left_frame_label = tk.Label(left_frame, image=left_frame_img)
middle_frame = tk.Frame(container, height=700)
#   INITIALIZING GLOBAL VARIABLES /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /

# Tkinter variables, the '_t' suffix means Toggle
vDist = tk.IntVar(app, -2)
vAutoinst_t = tk.IntVar(app, 1)
vAutoinst_option = tk.IntVar(app, -1)
vWifi_t = tk.IntVar(app, 1)
vAutorestart_t = tk.IntVar(app, 0)
vTorrent_t = tk.IntVar(app, 0)

queue1 = Queue()
compatibility_results = {}
compatibility_check_status = 0
installer_status = 0
download_path = ''
install_iso_name = ''
install_iso_path = ''
mount_iso_letter = ''
grub_config_dir = current_dir + '\\resources\\grub_conf\\'
#   MULTI-LINGUAL /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
lang_var = tk.StringVar()
lang_list = ttk.Combobox(top_frame, name="language", textvariable=lang_var, background=top_bg)
lang_list['values'] = tuple(language_list.keys())
lang_list['state'] = 'readonly'
lang_list.set('English')
lang_current = (None, None)


def build_container():
    """Used to build or rebuild the main frames after language change to a language with different direction
(see function right_to_left_lang)"""
    container.pack(side="top", fill="both", expand=True)
    top_frame.pack(fill="x", expand=1)
    top_frame.pack_propagate(False)
    lang_list.pack(anchor=di_var['w'], side='left', padx=30)
    top_main_title.pack(anchor='center',side='left', padx=15)
    left_frame.pack(fill="y", side=di_var['l'])
    left_frame.pack_propagate(False)
    left_frame_label.pack(side='bottom')
    middle_frame.pack(fill="both", expand=1, padx=15, pady=20)
    middle_frame.pack_propagate(False)


def clear_frame():
    """removes all elements inside the middle frame, which contains all page-specific content"""
    for widgets in middle_frame.winfo_children():
        widgets.destroy()


def change_lang(lang):
    """Used to change GUI's display language"""
    global di_var, lang_current
    lang_new = language_list[lang]
    importlib.import_module('.' + lang_new[0], 'translations')
    if lang_current[1] != lang_new[1]:
        di_var = right_to_left_lang(lang_new[1])
        build_container()
    lang_current = lang_new


def reload_page(lang, current_page):
    """reloads the page after changing GUI's display language"""
    change_lang(lang)
    current_page()


def open_popup(question_type, title_txt, msg_txt):
    """
Pops up window to get input from user and freezes the main GUI while waiting for response
    :param question_type: can be a 'yes-no','cancel-confirm', 'abort-retry-continue', and 'entry' for text input
    :param title_txt: the title for the popup in big font
    :param msg_txt: the smaller text beneath the title
    :return:
    """
    pop = tk.Toplevel(app)
    pop_var = tk.IntVar()
    x = app.winfo_x()
    y = app.winfo_y()
    pop.geometry("600x300")
    pop.geometry("+%d+%d" % (x+125, y+125))
    pop.overrideredirect(True)
    pop.focus_set()
    pop.grab_set()
    border_frame = tk.Frame(pop, highlightbackground="gray", highlightthickness=1)
    border_frame.pack(expand=1, fill='both', pady=5, padx=5)
    pop_frame = tk.Frame(border_frame)
    pop_frame.pack(expand=1, fill='both', pady=5, padx=10)
    btn_danger_txt = None
    btn_true_txt = None
    btn_false_txt = None
    #ttk.Label(pop_frame, text="Hello World!", font=('Mistral 18 bold')).pack()
    title = ttk.Label(pop_frame, wraplength=600, font=('Mistral 18 bold'), justify=di_var['l'], text=title_txt)
    title.pack(pady=20, anchor=di_var['w'])
    if len(msg_txt) > 120: msg_font = VERYSMALLFONT
    else: msg_font = SMALLFONT
    msg = ttk.Label(pop_frame, wraplength=600, justify=di_var['l'], text=msg_txt, font=msg_font)
    msg.pack(pady=10, anchor=di_var['w'])

    if question_type == 'cancel-confirm':
        btn_true_txt = ln_btn_confirm
        btn_false_txt = ln_btn_cancel
    elif question_type == 'abort-retry-continue':
        btn_true_txt = ln_btn_dl_again
        btn_false_txt = ln_btn_abort
        btn_danger_txt = ln_btn_continue_anyways
    elif question_type == 'yes-no':
        btn_true_txt = ln_btn_yes
        btn_false_txt = ln_btn_no
    elif question_type == 'entry':
        btn_true_txt = ln_btn_confirm
        btn_false_txt = ln_btn_cancel
        entry_var = tk.StringVar()
        entry = ttk.Entry(pop_frame, width=8, textvariable=entry_var)
        entry.pack(pady=10, anchor=di_var['w'])

    btn_true = ttk.Button(pop_frame, text=btn_true_txt, style="Accentbutton", command=lambda: validate_pop_input(1))
    btn_true.pack(anchor=di_var['se'], side=di_var['r'], ipadx=15, padx=10)
    btn_false = ttk.Button(pop_frame, text=btn_false_txt, command=lambda: validate_pop_input(0))
    btn_false.pack(anchor=di_var['se'], side=di_var['r'], padx=5)
    btn_danger = ttk.Button(pop_frame, text=btn_danger_txt, style="Dangerbutton", command=lambda: validate_pop_input(2))
    more_options_btn = ttk.Label(pop_frame, justify="center", text=ln_more_options, font=VERYSMALLFONT, foreground='#3aa9ff')
    more_options_btn.bind("<Button-1>",
                          lambda xy: (more_options_btn.pack_forget(), btn_danger.pack(anchor=di_var['se'], side=di_var['r'], padx=5)))
    if btn_danger_txt is not None: more_options_btn.pack(anchor=di_var['se'], side=di_var['r'], padx=5, pady=8)

    def validate_pop_input(inputted):
        pop_var.set(inputted)
        pop.destroy()
    pop.wait_window()
    if question_type == 'entry' and pop_var.get() == 1: return entry_var.get()
    return pop_var.get()


def main():
    def page_check():
        """The page on which is decided whether the app can run on the device or not"""
        # ************** Multilingual support *************************************************************************
        def page_name(): page_check()
        def change_callback(*args): reload_page(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()
        # *************************************************************************************************************
        title = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'], text=ln_check_running, font=MEDIUMFONT)
        title.pack(pady=35, anchor=di_var['w'])
        progressbar_check = ttk.Progressbar(middle_frame, orient='horizontal', length=550, mode='indeterminate')
        progressbar_check.pack(pady=25)
        progressbar_check.start(10)
        job_var = tk.StringVar()
        current_job = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'], textvariable=job_var, font=SMALLFONT)
        current_job.pack(padx=10, anchor=di_var['w'])
        # Request elevation (admin) if not running as admin
        if not ctypes.windll.shell32.IsUserAnAdmin():
            app.update()
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            quit()
        global compatibility_results, compatibility_check_status
        compatibility_results = {'uefi': 1, 'ram': 34359738368, 'space': 134064279552, 'resizable': 5853276160, 'bitlocker': 1, 'arch': 1}
        if not compatibility_results:
            if not compatibility_check_status:
                Process(target=compatibility_test,
                        args=(minimal_required_space, queue1,)).start()
                compatibility_check_status = 1
            if compatibility_check_status == 1:
                while True:
                    while not queue1.qsize(): app.after(10, app.update())
                    queue_out = queue1.get()
                    if queue_out == 'arch': pass
                    elif queue_out == 'uefi': job_var.set(ln_check_uefi)
                    elif queue_out == 'ram': job_var.set(ln_check_ram)
                    elif queue_out == 'space': job_var.set(ln_check_space)
                    elif queue_out == 'resizable': job_var.set(ln_check_resizable)
                    elif queue_out == 'bitlocker': job_var.set(ln_check_bitlocker)
                    else:
                        compatibility_results = queue_out
                        compatibility_check_status = 2
                        break
        btn_quit = ttk.Button(middle_frame, text=ln_btn_quit, command=lambda: app.destroy())
        if compatibility_results['uefi'] == 1 \
                and compatibility_results['arch'] == 1 \
                and compatibility_results['ram'] >= gigabyte(minimal_required_ram) \
                and compatibility_results['space'] >= gigabyte(minimal_required_space) \
                and compatibility_results['resizable'] >= gigabyte(minimal_required_space) \
                and compatibility_results['bitlocker'] == 1:

            global download_path, install_iso_name, install_iso_path
            download_path = get_user_home_dir() + "\\win2linux_tmpdir"
            install_iso_name = 'install_media.iso'
            install_iso_path = download_path + "\\" + install_iso_name
            page_1()
        else:
            title.pack_forget()
            progressbar_check.pack_forget()
            title = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'], text=ln_error_title,
                              font=MEDIUMFONT)
            errors = []
            if compatibility_results['arch'] == 0:
                errors.append(ln_error_arch_0)
            if compatibility_results['arch'] == -1:
                errors.append(ln_error_arch_9)
            if compatibility_results['uefi'] == 0:
                errors.append(ln_error_uefi_0)
            if compatibility_results['uefi'] == -1:
                errors.append(ln_error_uefi_9)
            if compatibility_results['ram'] < gigabyte(minimal_required_ram):
                errors.append(ln_error_totalram_0)
            if compatibility_results['ram'] == -1:
                errors.append(ln_error_totalram_9)
            if compatibility_results['space'] < gigabyte(minimal_required_space):
                errors.append(ln_error_space_0)
            if compatibility_results['space'] == -1:
                errors.append(ln_error_space_9)
            if compatibility_results['resizable'] < gigabyte(minimal_required_space):
                errors.append(ln_error_resizable_0)
            if compatibility_results['resizable'] == -1:
                errors.append(ln_error_resizable_9)
            if compatibility_results['bitlocker'] == 0:
                errors.append(ln_error_bitlocker_0)
            if compatibility_results['bitlocker'] == -1:
                errors.append(ln_error_bitlocker_9)

            errors_text_label = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'],
                                          text=ln_error_list + '\n',
                                          font=SMALLFONT)
            errors_listed = 'x  ' + ("\nx  ".join(errors))
            errors_text = tk.Text(middle_frame, spacing1=6, height=6)
            errors_text.insert(1.0, errors_listed)
            errors_text.configure(state='disabled')

            title.pack(pady=35, anchor=di_var['nw'])
            errors_text_label.pack(padx=10, anchor=di_var['w'])
            errors_text.pack(padx=10, pady=5, anchor=di_var['w'])
            btn_quit.pack(anchor=di_var['se'], side=di_var['r'], ipadx=15, padx=10)

    # page_1
    def page_1():
        # ************** Multilingual support *************************************************************************
        def page_name(): page_1()
        def change_callback(*args): reload_page(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()
        # *************************************************************************************************************
        main_title_text.set('Welcome to Lnixify')
        title = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'], text=ln_install_question, font=MEDIUMFONT)
        title.pack(pady=35, anchor=di_var['w'])

        for index, distro in enumerate(distros['name']):
            txt = ''  # Generating Text for each list member of installable flavors/distros
            if distros['advanced'][index]: txt += ln_adv + ': '
            txt += distro + ' %s' % distros['version'][index]
            if distros['de'][index]: txt += ' (%s)' % distros['de'][index]
            if distros['netinstall'][index]: txt += ' (%s)' % ln_net_install
            if distros['recommended'][index]:
                if vDist.get() == -2: vDist.set(index)  # If unset, set it to the default value
                if distros['auto-installable'][index]: vAutoinst_t.set(1)
                txt += ' (%s)' % ln_recommended

            temp_frame = ttk.Frame(middle_frame)
            temp_frame.pack(fill="x", pady=5)
            radio = ttk.Radiobutton(temp_frame, text=txt, variable=vDist, value=index, command=lambda: validate_input())
            radio.pack(anchor=di_var['w'], side=di_var['l'])
            if distros['netinstall'][index]: dl_size_txt = ln_init_download % distros['size'][index]
            else: dl_size_txt = ln_total_download % distros['size'][index]
            ttk.Label(temp_frame, wraplength=540, justify="center", text=dl_size_txt,
                      font=VERYSMALLFONT, foreground='#3aa9ff').pack(padx=5, anchor=di_var['e'], side=di_var['r'])
            if compatibility_results['resizable'] < gigabyte(distros['size'][index]):
                radio.configure(state='disabled')
                ttk.Label(temp_frame, wraplength=540, justify="center", text=ln_warn_space,
                          font=VERYSMALLFONT, foreground='#ff4a4a').pack(padx=5, anchor=di_var['e'], side=di_var['r'])
                if distros['recommended'][index]:
                    vDist.set(-1)

        c1_autoinst = ttk.Checkbutton(middle_frame, text=ln_install_auto, variable=vAutoinst_t, onvalue=1, offvalue=0)
        c1_autoinst.pack(anchor=di_var['w'], pady=40)
        btn_next = ttk.Button(middle_frame, text=ln_btn_next, style="Accentbutton", command=lambda: validate_next_page())
        btn_next.pack(anchor=di_var['se'], side=di_var['r'], ipadx=15, padx=10)

        def validate_input(*args):
            if distros['advanced'][vDist.get()]:
                question = open_popup('cancel-confirm', ln_adv_confirm, ln_adv_confirm_text)
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
            if vAutoinst_t.get(): return page_2()
            return page_verify()

    # page_2
    def page_2():
        # ************** Multilingual support *************************************************************************
        def page_name(): page_2()
        def change_callback(*args): reload_page(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()
        # *************************************************************************************************************
        main_title_text.set(ln_install_auto)
        title = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'],
                          text=ln_windows_question % distros['name'][vDist.get()], font=MEDIUMFONT)
        title.pack(pady=35, anchor=di_var['w'])

        r1_frame = ttk.Frame(middle_frame)
        r1_frame.pack(fill="x")
        r1_autoinst = ttk.Radiobutton(r1_frame, text=ln_windows_options[0], variable=vAutoinst_option, value=0,
                                      command=lambda:ask_dualboot_size())
        r1_autoinst.pack(anchor=di_var['w'], side=di_var['l'], ipady=5)
        r1_space = ttk.Label(r1_frame, wraplength=540, justify="center", text=ln_warn_space, font=VERYSMALLFONT,
                             foreground='#ff4a4a')
        r2_autoinst = ttk.Radiobutton(middle_frame, text=ln_windows_options[1], variable=vAutoinst_option, value=1)
        r2_autoinst.pack(anchor=di_var['w'], ipady=5)
        r3_autoinst = ttk.Radiobutton(middle_frame, text=ln_windows_options[2], variable=vAutoinst_option, value=2)
        r3_autoinst.pack(anchor=di_var['w'], ipady=5)

        btn_next = ttk.Button(middle_frame, text=ln_btn_next, style="Accentbutton", command=lambda: validate_next_page())
        btn_next.pack(anchor=di_var['se'], side=di_var['r'], ipadx=15, padx=10)
        btn_back = ttk.Button(middle_frame, text=ln_btn_back, command=lambda: page_1())
        btn_back.pack(anchor=di_var['se'], side=di_var['r'], padx=5)

        if compatibility_results['space'] < gigabyte(distros['size'][vDist.get()] + dualboot_required_space):
            vAutoinst_option.set(-1)
            r1_space.pack(padx=20, anchor=di_var['e'], side=di_var['l'])
            r1_autoinst.configure(state='disabled')

        def ask_dualboot_size():
            min_size = dualboot_required_space
            max_size = byte_to_gb(compatibility_results['resizable']) - distros['size'][vDist.get()] - 0.5
            while True:
                result = open_popup('entry', ln_dualboot_size_question % distros['name'][vDist.get()],
                                    ln_dualboot_size_txt % (min_size, max_size))
                if result == 0:
                    vAutoinst_option.set(-1)
                    break
                try:
                    result = float(result)
                    if min_size <= result <= max_size: return result
                except ValueError: pass

        def validate_next_page(*args):
            if vAutoinst_option.get() == -1: return
            page_verify()

    def page_verify():
        # ************** Multilingual support *************************************************************************
        def page_name(): page_verify()
        def change_callback(*args): reload_page(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()
        # *************************************************************************************************************
        main_title_text.set('')
        title = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'], text=ln_verify_question, font=MEDIUMFONT)
        title.pack(pady=35, anchor=di_var['w'])
        # Construction user verification text based on user's selections  ++++++++++++++++++++++++++++++++++++++++++++++
        review_sel = 'x  ' + ln_verify_text[0] % distros['name'][vDist.get()] + ln_verify_text[1][vAutoinst_t.get()]
        if vAutoinst_t.get():
            review_sel += ln_verify_text[2][vAutoinst_option.get()]
            review_sel += '\nx  ' + ln_verify_text[3][vAutoinst_option.get()]
            if vAutoinst_option.get() == 1: review_sel = review_sel % get_sys_drive_letter()
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        review_text = tk.Text(middle_frame, spacing1=1, height=5, width=100, wrap='word')
        review_text.insert(1.0, review_sel)
        review_text.configure(state='disabled')
        review_text.pack(anchor=di_var['w'], pady=5)
        # additions options (checkboxes)
        c1_add = ttk.Checkbutton(middle_frame, text=ln_add_import_wifi, variable=vWifi_t, onvalue=1, offvalue=0)
        c1_add.pack(anchor=di_var['w'])
        c2_add = ttk.Checkbutton(middle_frame, text=ln_add_auto_restart, variable=vAutorestart_t, onvalue=1, offvalue=0)
        c2_add.pack(anchor=di_var['w'])
        c3_add = ttk.Checkbutton(middle_frame, text=ln_add_torrent, variable=vTorrent_t, onvalue=1, offvalue=0)
        more_options_btn = ttk.Label(middle_frame, justify="center", text=ln_more_options, font=VERYSMALLFONT, foreground='#3aa9ff')
        more_options_btn.pack(pady=10, padx=10, anchor=di_var['w'])
        more_options_btn.bind("<Button-1>",
                               lambda x: (more_options_btn.pack_forget(), c3_add.pack(anchor=di_var['w'])))
        btn_next = ttk.Button(middle_frame, text=ln_btn_install, style="Accentbutton", command=lambda: page_installing())
        btn_next.pack(anchor=di_var['se'], side=di_var['r'], ipadx=15, padx=10)
        btn_back = ttk.Button(middle_frame, text=ln_btn_back, command=lambda: validate_back_page())
        btn_back.pack(anchor=di_var['se'], side=di_var['r'], padx=5)

        def validate_back_page(*args):
            if vAutoinst_t.get(): page_2()
            else: page_1()

    def page_installing():
        # ************** Multilingual support *************************************************************************
        def page_name(): page_installing()
        def change_callback(*args): reload_page(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()
        # *************************************************************************************************************
        main_title_text.set('ln_install_running')
        lang_list.pack_forget()
        # title = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'], text=ln_install_running, font=MEDIUMFONT)
        # title.pack(pady=35, anchor=di_var['w'])
        progressbar_install = ttk.Progressbar(middle_frame, orient='horizontal', length=550, mode='determinate')
        progressbar_install.pack(pady=25)
        job_var = tk.StringVar()
        current_job = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'], textvariable=job_var, font=SMALLFONT)
        current_job.pack(padx=10, anchor=di_var['w'])

        global installer_status, mount_iso_letter, tmp_part_letter
        if check_file_if_exists(install_iso_path) == 'True':
            # checking if files from previous runs are present and if so, ask if user wishes to use them.
            question = open_popup('yes-no', ln_old_download_detected, ln_old_download_detected_text)
            if question:
                installer_status = 2
            else:
                cleanup_remove_folder(download_path)

        while True:
            if not installer_status:  # first step, start the download
                while queue1.qsize(): queue1.get()  # to empty the queue
                progressbar_install['value'] = 0
                job_var.set(ln_job_starting_download)
                app.update()
                create_dir(download_path)
                aria2_location = current_dir + '\\resources\\aria2c.exe'
                if vTorrent_t.get() and distros['torrent'][vDist.get()]:
                    # if torrent is selected and a torrent link is available
                    args = (aria2_location, distros['torrent'][vDist.get()], download_path, 1, queue1,)
                else:
                    # if torrent is not selected or not available (direct download)
                    args = (aria2_location, distros['dl_link'][vDist.get()], download_path, 0, queue1,)
                Process(target=download_with_aria2, args=args).start()
                installer_status = 1

            if installer_status == 1:  # While downloading, track download stats...
                while True:
                    while not queue1.qsize(): app.after(100, app.update())
                    while queue1.qsize() != 1: queue1.get()
                    dl_status = queue1.get()
                    if dl_status == 'OK':
                        installer_status = 3
                        break
                    progressbar_install['value'] = dl_status['%'] * 0.90
                    txt = ln_job_dl_install_media + '\n%s\n%s%s/s, %s%s' % (dl_status['size'], ln_dl_speed,
                                                                            dl_status['speed'], ln_dl_timeleft,
                                                                            dl_status['eta'])
                    job_var.set(txt)
                    app.after(100, app.update())
                move_files_to_dir(download_path, download_path)
                rename_file(download_path, '*.iso', install_iso_name)
                installer_status = 2

            if installer_status == 2:  # step 2: create temporary boot partition
                while queue1.qsize(): queue1.get()  # to empty the queue
                Process(target=check_hash, args=(install_iso_path, distros['hash256'][vDist.get()], queue1,)).start()
                job_var.set(ln_job_checksum)
                progressbar_install['value'] = 90
                while not queue1.qsize(): app.after(50, app.update())
                out = queue1.get()
                if out == 1: installer_status = 2.5
                elif out == -1:
                    question = open_popup('yes-no', ln_job_checksum_failed, ln_job_checksum_failed_txt)
                    if question: installer_status = 2.5
                    else:
                        question = open_popup('yes-no', ln_cleanup_question, ln_cleanup_question_txt)
                        if question: cleanup_remove_folder(download_path)
                        app.destroy()
                else:
                    question = open_popup('abort-retry-continue', ln_job_checksum_mismatch, ln_job_checksum_mismatch_txt % out)
                    if question == 1: pass
                    if question == 2: installer_status = 2.5
                    if question == 0:
                        question = open_popup('yes-no', ln_cleanup_question, ln_cleanup_question_txt)
                        if question: cleanup_remove_folder(download_path)
                        app.destroy()
            if installer_status == 2.5:  # step 2: create temporary boot partition
                while queue1.qsize(): queue1.get()  # to empty the queue
                tmp_part_size = gigabyte(distros['size'][vDist.get()])
                Process(target=create_temp_boot_partition, args=(tmp_part_size, queue1,)).start()
                job_var.set(ln_job_creating_tmp_part)
                progressbar_install['value'] = 92
                installer_status = 3

            if installer_status == 3:  # while creating partition is ongoing...
                while not queue1.qsize():
                    app.after(200, app.update())
                tmp_part_result = queue1.get()
                if tmp_part_result[0] == 1:
                    tmp_part_letter = tmp_part_result[1]
                    installer_status = 4
            if installer_status == 4:  # step 3: mount iso and copy files to temporary boot partition
                while queue1.qsize(): queue1.get()  # to empty the queue
                mount_iso_letter = mount_iso(install_iso_path)
                source_files = mount_iso_letter + ':\\'
                destination_files = tmp_part_letter + ':\\'
                Process(target=copy_files, args=(source_files, destination_files, queue1,)).start()
                job_var.set(ln_job_copying_to_tmp_part)
                progressbar_install['value'] = 94
                installer_status = 5
            if installer_status == 5:  # while copying files is ongoing...
                while not queue1.qsize():
                    app.after(200, app.update())
                if queue1.get() == 1:
                    installer_status = 6
            if installer_status == 6:  # step 4: adding boot entry
                while queue1.qsize(): queue1.get()  # to empty the queue
                job_var.set(ln_job_adding_tmp_boot_entry)
                progressbar_install['value'] = 98
                if vAutoinst_t.get(): grub_cfg_file = grub_config_dir + 'grub_autoinst.cfg'
                else: grub_cfg_file = grub_config_dir + 'grub_default.cfg'
                copy_one_file(grub_cfg_file, tmp_part_letter + ':\\EFI\\BOOT\\grub.cfg')
                Process(target=add_boot_entry, args=(default_efi_file_path, tmp_part_letter, queue1,)).start()
                installer_status = 7
            if installer_status == 7:  # while adding boot entry is ongoing...
                while not queue1.qsize():
                    app.after(200, app.update())
                if queue1.get() == 1:
                    installer_status = 8
            if installer_status == 8:  # step 5: clean up iso and other downloaded files since install is complete
                unmount_iso(install_iso_path)
                cleanup_remove_folder(download_path)
                installer_status = 9
            if installer_status == 9:  # step 6: redirect to next page
                break

        page_installer_installed()

    def page_installer_installed():
        # ************** Multilingual support *************************************************************************
        def page_name(): page_installer_installed()
        def change_callback(*args): reload_page(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()
        # *************************************************************************************************************
        lang_list.pack(anchor=di_var['nw'], padx=10, pady=10)

        title = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'], text=ln_finished_title, font=MEDIUMFONT)
        title.pack(pady=35, anchor=di_var['w'])

        text_var = tk.StringVar()
        text1 = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'], text=ln_finished_text, font=SMALLFONT)
        text1.pack(pady=10, anchor=di_var['w'])
        text2 = ttk.Label(middle_frame, wraplength=540, justify="center", textvariable=text_var, font=SMALLFONT)
        text2.pack(pady=10, anchor=di_var['w'])

        button1 = ttk.Button(middle_frame, text=ln_btn_restart_now, style="Accentbutton", command=lambda: (restart_windows(), app.destroy()))
        button1.pack(anchor=di_var['se'], side=di_var['r'], ipadx=15, padx=10)
        button2 = ttk.Button(middle_frame, text=ln_btn_restart_later, command=lambda: app.destroy())
        button2.pack(anchor=di_var['se'], side=di_var['r'], padx=5)

        if vAutorestart_t.get():
            time_left = 10
            while time_left > 0:
                text_var.set(ln_finished_text_restarting_now % (int(time_left)))
                time_left = time_left - 0.01
                app.after(10, app.update())
            restart_windows()
            app.destroy()

    #if not ctypes.windll.shell32.IsUserAnAdmin():
    #    app.update()
    #    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    #    quit()
    #add_boot_entry(APP_INFO.efi_file_path, 'G', queue1)
    #relabel_volume('C', 'Windows OS')
    #print(get_wifi_profiles())

    change_lang('English')
    #open_popup('2','2','1')
    page_check()

    app.mainloop()


if __name__ == '__main__': main()
