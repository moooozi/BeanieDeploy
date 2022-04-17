# from APP_INFO import *
import ctypes
import importlib
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from multiprocessing import Process, Queue
from APP_INFO import *
from multilingual import language_list, right_to_left_lang
from functions import *

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
MEDIUMFONT = ("Ariel", 15)
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
tk_vars = (tk.IntVar(app, 0), tk.IntVar(app, 0), tk.IntVar(app, 1), tk.IntVar(app, 0), tk.IntVar(app, 0), tk.IntVar(app, 1))
#          ( Install options , Windows Options  , import Wifi?     , auto restart?    , use torrent?, auto install    )
queue1 = Queue()
compatibility_results = {}
compatibility_check_status = 0
installer_status = 0
download_path = ''
install_iso_name = ''
install_iso_path = ''
mount_iso_letter = ''
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
    middle_frame.pack(fill="both", expand=1, padx=20, pady=20)
    middle_frame.pack_propagate(False)



def clear_frame():
    """removes all elements inside the middle frame, which contains all page-specific content"""
    for widgets in middle_frame.winfo_children():
        widgets.destroy()


def change_lang(lang):
    """Used to change GUI's display language"""
    global ln, di_var, lang_current
    lang_new = language_list[lang]
    ln = importlib.import_module('.' + lang_new[0], 'translations')
    if lang_current[1] != lang_new[1]:
        di_var = right_to_left_lang(lang_new[1])
        build_container()
    lang_current = lang_new


def reload_page(lang, current_page):
    """reloads the page after changing GUI's display language"""
    change_lang(lang)
    current_page()


def main():
    def page_check():
        """The page on which is decided whether the app can run on the device or not"""
        # ************** Multilingual support *************************************************************************
        def page_name(): page_check()
        def change_callback(*args): reload_page(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()
        # *************************************************************************************************************
        title = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'], text=ln.ln_check_running, font=MEDIUMFONT)
        progressbar_check = ttk.Progressbar(middle_frame, orient='horizontal', length=540, mode='indeterminate')
        job_var = tk.StringVar()
        current_job = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'], textvariable=job_var, font=SMALLFONT)

        title.pack(pady=35, anchor=di_var['w'])
        progressbar_check.pack(pady=25)
        progressbar_check.start(10)
        current_job.pack(padx=10, anchor=di_var['w'])
        # Request elevation (admin) if not running as admin
        if not ctypes.windll.shell32.IsUserAnAdmin():
            app.update()
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            quit()
        global compatibility_results, compatibility_check_status
        # compatibility_results = {'uefi': 0, 'ram': 0, 'space': 0, 'resizable': 0, 'bitlocker': 0}
        # compatibility_results = {'uefi': 1, 'ram': 1, 'space': 2, 'resizable': 1, 'bitlocker': 1}
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
                    elif queue_out == 'uefi': job_var.set(ln.ln_check_uefi)
                    elif queue_out == 'ram': job_var.set(ln.ln_check_ram)
                    elif queue_out == 'space': job_var.set(ln.ln_check_space)
                    elif queue_out == 'resizable': job_var.set(ln.ln_check_resizable)
                    elif queue_out == 'bitlocker': job_var.set(ln.ln_check_bitlocker)
                    else:
                        compatibility_results = queue_out
                        compatibility_check_status = 2
                        break

        btn_quit = ttk.Button(middle_frame, text=ln.ln_btn_quit, command=lambda: app.destroy())
        if compatibility_results['uefi'] == 1 \
                and compatibility_results['arch'] == 1 \
                and compatibility_results['ram'] >= required_ram \
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
            title = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'], text=ln.ln_error_title,
                              font=MEDIUMFONT)
            errors = []
            if compatibility_results['arch'] == 0:
                errors.append(ln.ln_error_arch_0)
            if compatibility_results['arch'] == -1:
                errors.append(ln.ln_error_arch_9)
            if compatibility_results['uefi'] == 0:
                errors.append(ln.ln_error_uefi_0)
            if compatibility_results['uefi'] == -1:
                errors.append(ln.ln_error_uefi_9)
            if compatibility_results['ram'] <= required_ram:
                errors.append(ln.ln_error_totalram_0)
            if compatibility_results['ram'] == -1:
                errors.append(ln.ln_error_totalram_9)
            if compatibility_results['space'] <= gigabyte(minimal_required_space):
                errors.append(ln.ln_error_space_0)
            if compatibility_results['space'] == -1:
                errors.append(ln.ln_error_space_9)
            if compatibility_results['resizable'] <= gigabyte(minimal_required_space):
                errors.append(ln.ln_error_resizable_0)
            if compatibility_results['resizable'] == -1:
                errors.append(ln.ln_error_resizable_9)
            if compatibility_results['bitlocker'] == 0:
                errors.append(ln.ln_error_bitlocker_0)
            if compatibility_results['bitlocker'] == -1:
                errors.append(ln.ln_error_bitlocker_9)

            errors_text_label = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'],
                                          text=ln.ln_error_list + '\n',
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

        global tk_vars

        main_title_text.set('Welcome to Lnixify')
        title = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'], text=ln.ln_install_question, font=MEDIUMFONT)
        btn_next = ttk.Button(middle_frame, text=ln.ln_btn_next, style="Accentbutton",
                              command=lambda: validate_next_page())
        c1_autoinst = ttk.Checkbutton(middle_frame, text=ln.ln_install_auto, variable=tk_vars[5], onvalue=1, offvalue=0)

        title.pack(pady=35, anchor=di_var['w'])
        for index, distro in enumerate(distros):
            txt = ''
            if distro[6]: txt += ln.ln_adv + ': '
            txt += distro[0] + ' %s (%s)' % (distro[1], distro[2])
            if distro[5]:
                txt += ' (%s)' % ln.ln_recommended
                tk_vars[0].set(index)
            if compatibility_results['resizable'] < gigabyte(distro[3]):
                temp_frame = ttk.Frame(middle_frame)
                temp_frame.pack(fill="x")
                ttk.Radiobutton(temp_frame, text=txt, state='disabled').pack(anchor=di_var['w'], side=di_var['l'])
                ttk.Label(temp_frame, wraplength=540, justify="center", text=ln.ln_warn_space,
                          font=VERYSMALLFONT, foreground='#ff4a4a').pack(padx=50, anchor=di_var['e'], side=di_var['r'])
                if distro[5]: tk_vars[0].set(-1)
            else:
                ttk.Radiobutton(middle_frame, text=txt, variable=tk_vars[0], value=index,
                                command=lambda: validate_input()).pack(anchor=di_var['w'], ipady=2)

        c1_autoinst.pack(anchor=di_var['w'], pady=40)
        btn_next.pack(anchor=di_var['se'], side=di_var['r'], ipadx=15, padx=10)

        def validate_input(*args):
            selected = tk_vars[0].get()
            if distros[selected][4]:
                c1_autoinst['state'] = 'enabled'
            else:
                c1_autoinst['state'] = 'disabled'
                tk_vars[5].set(0)
            if distros[selected][6]:
                question = messagebox.askyesno(ln.ln_adv_confirm, ln.ln_adv_confirm_text)
                if not question:
                    tk_vars[0].set(0)
                    c1_autoinst['state'] = 'enabled'
                    tk_vars[5].set(1)

        def validate_next_page(*args):
            if tk_vars[0].get() == -1: return
            if tk_vars[5].get(): return page_2()
            return page_verify()

    # page_2
    def page_2():
        # ************** Multilingual support *************************************************************************
        def page_name(): page_2()
        def change_callback(*args): reload_page(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()
        # *************************************************************************************************************
        global tk_vars

        selected_distro = tk_vars[0].get()
        main_title_text.set(ln.ln_install_auto)
        title = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'],
                          text=ln.ln_windows_question % distros[selected_distro][0], font=MEDIUMFONT)

        btn_next = ttk.Button(middle_frame, text=ln.ln_btn_next, style="Accentbutton",
                              command=lambda: validate_next_page())
        btn_back = ttk.Button(middle_frame, text=ln.ln_btn_back,
                              command=lambda: page_1())

        r2_windows = ttk.Radiobutton(middle_frame, text=ln.ln_windows_options[1] % distros[selected_distro][0], variable=tk_vars[1], value=1)
        r3_windows = ttk.Radiobutton(middle_frame, text=ln.ln_windows_options[2] % distros[selected_distro][0], variable=tk_vars[1], value=2)


        title.pack(pady=35, anchor=di_var['w'])
        if compatibility_results['space'] < gigabyte(distros[selected_distro][3] + gigabyte(dualboot_required_space)):
            temp_frame = ttk.Frame(middle_frame)
            temp_frame.pack(fill="x")
            ttk.Radiobutton(temp_frame, text=ln.ln_windows_options[0] % distros[selected_distro][0],
                            state='disabled').pack(anchor=di_var['w'], side=di_var['l'], ipady=5)
            ttk.Label(temp_frame, wraplength=540, justify="center", text=ln.ln_warn_space,
                      font=VERYSMALLFONT, foreground='#ff4a4a').pack(padx=20, anchor=di_var['e'], side=di_var['l'])
            tk_vars[1].set(-1)

        else:
            ttk.Radiobutton(middle_frame, text=ln.ln_windows_options[0] % distros[selected_distro][0],
                            variable=tk_vars[1], value=0).pack(anchor=di_var['w'], ipady=5)
        r2_windows.pack(anchor=di_var['w'], ipady=5)
        r3_windows.pack(anchor=di_var['w'], ipady=5)
        btn_next.pack(anchor=di_var['se'], side=di_var['r'], ipadx=15, padx=10)
        btn_back.pack(anchor=di_var['se'], side=di_var['r'], padx=5)



        def validate_next_page(*args):
            if tk_vars[1].get() == -1: return
            return page_verify()


    def page_verify():
        # ************** Multilingual support *************************************************************************
        def page_name(): page_verify()
        def change_callback(*args): reload_page(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()
        # *************************************************************************************************************
        global tk_vars

        main_title_text.set('')
        title = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'], text=ln.ln_verify_question, font=MEDIUMFONT)
        btn_next = ttk.Button(middle_frame, text=ln.ln_btn_start, style="Accentbutton",
                              command=lambda: page_installing())
        btn_back = ttk.Button(middle_frame, text=ln.ln_btn_back,
                              command=lambda: page_2())

        review_sel = 'x  ' + ln.ln_install_options[tk_vars[0].get()] + '\nx  ' + ln.ln_windows_options[tk_vars[1].get()]
        review_text = tk.Text(middle_frame, spacing1=1, height=6, state='disabled')
        review_text.insert(1.0, review_sel)
        # additions options (checkboxes)
        c1_add = ttk.Checkbutton(middle_frame, text=ln.ln_add_import_wifi, variable=tk_vars[2], onvalue=1, offvalue=0)
        c2_add = ttk.Checkbutton(middle_frame, text=ln.ln_add_auto_restart, variable=tk_vars[3], onvalue=1, offvalue=0)
        c3_add = ttk.Checkbutton(middle_frame, text=ln.ln_adv_torrent, variable=tk_vars[4], onvalue=1, offvalue=0)
        more_settings_btn = ttk.Label(middle_frame, wraplength=540, justify="center", text=ln.ln_more_settings,
                                      font=VERYSMALLFONT, foreground='#3aa9ff')

        def show_more_settings(*args):
            more_settings_btn.pack_forget()
            c3_add.pack(anchor=di_var['w'])
        more_settings_btn.bind("<Button-1>", show_more_settings)
        title.pack(pady=35, anchor=di_var['w'])
        review_text.pack(anchor=di_var['w'], pady=5)
        c1_add.pack(anchor=di_var['w'])
        c2_add.pack(anchor=di_var['w'])
        more_settings_btn.pack(pady=10, padx=10, anchor=di_var['w'])
        btn_next.pack(anchor=di_var['se'], side=di_var['r'], ipadx=15, padx=10)
        btn_back.pack(anchor=di_var['se'], side=di_var['r'], padx=5)

    def page_installing():
        # ************** Multilingual support *************************************************************************
        def page_name(): page_installing()
        def change_callback(*args): reload_page(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()
        # *************************************************************************************************************

        lang_list.pack_forget()
        title = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'], text=ln.ln_install_running, font=MEDIUMFONT)
        progressbar_install = ttk.Progressbar(middle_frame, orient='horizontal', length=540, mode='determinate')
        job_var = tk.StringVar()
        current_job = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'], textvariable=job_var, font=SMALLFONT)

        title.pack(pady=35, anchor=di_var['w'])
        progressbar_install.pack(pady=25)
        current_job.pack(padx=10, anchor=di_var['w'])

        global installer_status, mount_iso_letter, tmp_part_letter
        if check_file_if_exists(install_iso_path) == 'True':
            # checking if files from previous runs are present and if so, ask if user wishes to use them.
            question = messagebox.askyesno(ln.ln_old_download_detected, ln.ln_old_download_detected_text)
            if question:
                installer_status = 2
            else:
                cleanup_remove_folder(download_path)
        if not installer_status:  # first step, start the download
            while queue1.qsize(): queue1.get()  # to empty the queue
            progressbar_install['value'] = 0
            job_var.set(ln.ln_job_starting_download)
            app.update()
            create_dir(download_path)
            aria2_location = current_dir + '\\resources\\aria2c.exe'
            if tk_vars[4].get():
                # if torrent is selected
                args = (aria2_location, distros[tk_vars[0].get()][9], download_path, 1, queue1,)
            else:
                # if torrent is not selected (direct download)
                args = (aria2_location, distros[tk_vars[0].get()][8], download_path, 0, queue1,)
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
                txt = ln.ln_job_dl_install_media + '\n%s\n%s%s/s, %s%s' % (dl_status['size'], ln.ln_dl_speed,
                                                                           dl_status['speed'], ln.ln_dl_timeleft,
                                                                           dl_status['eta'])
                job_var.set(txt)
                app.after(100, app.update())
            move_files_to_dir(download_path, download_path)
            rename_file(download_path, '*.iso', install_iso_name)
            installer_status = 2

        if installer_status == 2:  # step 2: create temporary boot partition
            while queue1.qsize(): queue1.get()  # to empty the queue
            Process(target=create_temp_boot_partition, args=(distros[distros[tk_vars[0].get()][3]], queue1,)).start()
            job_var.set(ln.ln_job_creating_tmp_part)
            progressbar_install['value'] = 90
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
            job_var.set(ln.ln_job_copying_to_tmp_part)
            progressbar_install['value'] = 94
            installer_status = 5
        if installer_status == 5:  # while copying files is ongoing...
            while not queue1.qsize():
                app.after(200, app.update())
            if queue1.get() == 1:
                installer_status = 6
        if installer_status == 6:  # step 4: adding boot entry
            while queue1.qsize(): queue1.get()  # to empty the queue
            job_var.set(ln.ln_job_adding_tmp_boot_entry)
            progressbar_install['value'] = 98
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
            page_installer_installed()

    def page_installer_installed():
        # ************** Multilingual support *************************************************************************
        def page_name(): page_installer_installed()
        def change_callback(*args): reload_page(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()
        # *************************************************************************************************************

        lang_list.pack(anchor=di_var['nw'], padx=10, pady=10)
        title = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'], text=ln.ln_finished_title, font=MEDIUMFONT)
        button1 = ttk.Button(middle_frame, text=ln.ln_btn_restart_now, style="Accentbutton",
                             command= lambda: [restart_windows(), app.destroy()])
        button2 = ttk.Button(middle_frame, text=ln.ln_btn_restart_later, command=lambda: app.destroy())
        text_var = tk.StringVar()
        text1 = ttk.Label(middle_frame, wraplength=540, justify=di_var['l'], text=ln.ln_finished_text, font=SMALLFONT)
        text2 = ttk.Label(middle_frame, wraplength=540, justify="center", textvariable=text_var, font=SMALLFONT)

        title.pack(pady=35, anchor=di_var['w'])
        text1.pack(pady=10, anchor=di_var['w'])
        text2.pack(pady=10, anchor=di_var['w'])
        button1.pack(anchor=di_var['se'], side=di_var['r'], ipadx=15, padx=10)
        button2.pack(anchor=di_var['se'], side=di_var['r'], padx=5)

        if tk_vars[3].get():
            time_left = 10
            while time_left:
                text_var.set(ln.ln_finished_text_restarting_now % (int(time_left)))
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
    build_container()
    page_check()
    app.mainloop()


if __name__ == '__main__': main()
