# from APP_INFO import *
import ctypes
import importlib
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from multiprocessing import Process, Queue
import APP_INFO
from multilingual import language_list, right_to_left_lang
from functions import *

#   DRIVER CODE   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
app = tk.Tk()
app.title(APP_INFO.SW_NAME)
MAXWIDTH = 800
MAXHEIGHT = 500
app.geometry(str("%sx%s" % (MAXWIDTH, MAXHEIGHT)))
current_dir = str(Path(__file__).parent)
# app.iconbitmap("yourimage.ico")
app.resizable(False, False)
app.option_add('*Font', 'Ariel 11')
#   STYLE     /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
style = ttk.Style(app)
app.tk.call('source', current_dir + '/azure dark/azure dark.tcl')
style.theme_use('azure')
style.configure("Accentbutton", foreground='white')
style.configure("Togglebutton", foreground='white')
LARGEFONT = ("Ariel", 20)
MEDIUMFONT = ("Ariel", 16)
SMALLFONT = ("Ariel", 12)
VERYSMALLFONT = ("Ariel", 10)

#   MAIN CONTAINER & FRAMES   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
container = tk.Frame(app)
top_frame = tk.Frame(container, height=90, width=MAXWIDTH)
left_frame = tk.Frame(container, width=200, height=MAXHEIGHT)
left_frame_img = tk.PhotoImage(file='resources/leftframe.png')
left_frame_label = tk.Label(left_frame, image=left_frame_img)
middle_frame = tk.Frame(container, height=700)
#   INITIALIZING GLOBAL VARIABLES /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
sel_vars = (tk.IntVar(app, 0), tk.IntVar(app, 0), tk.IntVar(app, 1), tk.IntVar(app, 0), tk.IntVar(app, 0))
#          ( Install options , Windows Options  , import Wifi?     , auto restart?    , use torrent?
queue1 = Queue()
compatibility_results = {}
compatibility_check_status = 0
installer_status = 0
download_path = get_user_home_dir() + "\\win2linux_tmpdir"
downloaded_iso_name = "install_media.iso"
install_media_path = download_path + "\\" + downloaded_iso_name
mount_iso_letter = ''
#   MULTI-LINGUAL /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
lang_var = tk.StringVar()
lang_list = ttk.Combobox(top_frame, name="language", textvariable=lang_var)
lang_list['values'] = tuple(language_list.keys())
lang_list['state'] = 'readonly'
lang_list.set('English')
lang_current = (None, None)


def rebuild_container():
    """Used to build or rebuild the main frames after language change to a language with different direction
(see function right_to_left_lang)"""
    container.pack(side="top", fill="both", expand=True)
    top_frame.pack(fill="x", expand=1)
    top_frame.pack_propagate(False)
    left_frame.pack(fill="y", side=directions_var['l'])
    left_frame.pack_propagate(False)
    left_frame_label.pack(side='bottom')
    middle_frame.pack(fill="both", expand=1, padx=20, pady=20)
    middle_frame.pack_propagate(False)

    lang_list.pack(anchor=directions_var['nw'], padx=20, pady=20)


def clear_frame():
    """removes all elements inside the middle frame, which contains all page-specific content"""
    for widgets in middle_frame.winfo_children():
        widgets.destroy()


def change_lang(lang):
    """Used to change GUI's display language"""
    global ln, directions_var, lang_current
    lang_new = language_list[lang]
    ln = importlib.import_module('.' + lang_new[0], 'translations')
    if lang_current[1] != lang_new[1]:
        directions_var = right_to_left_lang(lang_new[1])
        rebuild_container()
    lang_current = lang_new


def reload_page(lang, current_page):
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
        title = ttk.Label(middle_frame, wraplength=540, justify=directions_var['l'], text=ln.ln_check_running, font=MEDIUMFONT)
        progressbar_check = ttk.Progressbar(middle_frame, orient='horizontal', length=500, mode='indeterminate')

        title.pack(pady=35, anchor=directions_var['w'])
        progressbar_check.pack(expand=True)
        progressbar_check.start(10)
        # Request admin if not available
        if not ctypes.windll.shell32.IsUserAnAdmin():
            app.update()
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            quit()
        global compatibility_results, compatibility_check_status
        #compatibility_results = {'uefi': 0, 'ram': 0, 'space': 0, 'resizable': 0, 'bitlocker': 0}
        compatibility_results = {'uefi': 1, 'ram': 1, 'space': 2, 'resizable': 1, 'bitlocker': 1}
        if not compatibility_results:
            if not compatibility_check_status:
                Process(target=compatibility_test,
                        args=(APP_INFO.required_installer_space, APP_INFO.required_ram, queue1,)).start()
                compatibility_check_status = 1
            if compatibility_check_status == 1:
                while not queue1.qsize():
                    app.after(10, app.update())
                compatibility_results = queue1.get()
                compatibility_check_status = 2

        btn_quit = ttk.Button(middle_frame, text=ln.ln_btn_quit, command=lambda: app.destroy())

        if compatibility_results['uefi'] == 1 and compatibility_results['ram'] == 1 and compatibility_results[
            'space'] in (1, 2) and compatibility_results['resizable'] == 1 and compatibility_results['bitlocker'] == 1:
            page_1(compatibility_results['space'])
        else:
            title.pack_forget()
            progressbar_check.pack_forget()
            title = ttk.Label(middle_frame, wraplength=540, justify=directions_var['l'], text=ln.ln_error_title,
                              font=MEDIUMFONT)
            errors = []
            if compatibility_results['uefi'] == 0:
                errors.append(ln.ln_error_uefi_0)
            if compatibility_results['uefi'] == 9:
                errors.append(ln.ln_error_uefi_9)
            if compatibility_results['ram'] == 0:
                errors.append(ln.ln_error_totalram_0)
            if compatibility_results['ram'] == 9:
                errors.append(ln.ln_error_totalram_9)
            if compatibility_results['space'] == 0:
                errors.append(ln.ln_error_space_0)
            if compatibility_results['space'] == 9:
                errors.append(ln.ln_error_space_9)
            if compatibility_results['resizable'] == 0:
                errors.append(ln.ln_error_resizable_0)
            if compatibility_results['resizable'] == 9:
                errors.append(ln.ln_error_resizable_9)
            if compatibility_results['bitlocker'] == 0:
                errors.append(ln.ln_error_bitlocker_0)
            if compatibility_results['bitlocker'] == 9:
                errors.append(ln.ln_error_bitlocker_9)

            errors_text_label = ttk.Label(middle_frame, wraplength=540, justify=directions_var['l'],
                                          text=ln.ln_error_list + '\n',
                                          font=SMALLFONT)
            errors_listed = 'x  ' + ("\nx  ".join(errors))
            errors_text = tk.Text(middle_frame, spacing1=6, height=6)
            errors_text.insert(1.0, errors_listed)
            errors_text.configure(state='disabled')

            title.pack(pady=35, anchor=directions_var['nw'])
            errors_text_label.pack(padx=10, anchor=directions_var['w'])
            errors_text.pack(padx=10, pady=5, anchor=directions_var['w'])
            btn_quit.pack(anchor=directions_var['se'], side=directions_var['r'], ipadx=15, padx=10)

    # page_1
    def page_1(space_check_results):
        # ************** Multilingual support *************************************************************************
        def page_name(): page_1(space_check_results)
        def change_callback(*args): reload_page(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()
        # *************************************************************************************************************

        global sel_vars

        title = ttk.Label(middle_frame, wraplength=540, justify=directions_var['l'], text=ln.ln_install_question, font=MEDIUMFONT)
        btn_next = ttk.Button(middle_frame, text=ln.ln_btn_next, style="Accentbutton",
                             command=lambda: page_2(space_check_results))

        r1_install = ttk.Radiobutton(middle_frame, text=ln.ln_install_options[0], variable=sel_vars[0], value=0)
        r2_install = ttk.Radiobutton(middle_frame, text=ln.ln_install_options[1], variable=sel_vars[0], value=1)
        r3_install = ttk.Radiobutton(middle_frame, text=ln.ln_install_options[2], variable=sel_vars[0], value=2)

        title.pack(pady=35, anchor=directions_var['w'])
        r1_install.pack(anchor=directions_var['w'], ipady=5)
        r2_install.pack(anchor=directions_var['w'], ipady=5)
        r3_install.pack(anchor=directions_var['w'], ipady=5)
        btn_next.pack(anchor=directions_var['se'], side=directions_var['r'], ipadx=15, padx=10)

    # page_2
    def page_2(space_check_results):
        # ************** Multilingual support *************************************************************************
        def page_name(): page_2(space_check_results)
        def change_callback(*args): reload_page(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()
        # *************************************************************************************************************

        title = ttk.Label(middle_frame, wraplength=540, justify=directions_var['l'], text=ln.ln_windows_question, font=MEDIUMFONT)

        btn_next = ttk.Button(middle_frame, text=ln.ln_btn_next, style="Accentbutton",
                             command=lambda: page_verify(space_check_results))

        btn_back = ttk.Button(middle_frame, text=ln.ln_btn_back,
                             command=lambda: page_1(space_check_results))
        global sel_vars
        if space_check_results == 2:
            r1_windows = ttk.Radiobutton(middle_frame, text=ln.ln_windows_options[0], variable=sel_vars[1], value=0)
        else:
            r1_windows = ttk.Radiobutton(middle_frame, text=ln.ln_windows_option1_disabled, state='disabled')
        r2_windows = ttk.Radiobutton(middle_frame, text=ln.ln_windows_options[1], variable=sel_vars[1], value=1)
        r3_windows = ttk.Radiobutton(middle_frame, text=ln.ln_windows_options[2], variable=sel_vars[1], value=2)
        r4_windows = ttk.Radiobutton(middle_frame, text=ln.ln_windows_options[3], variable=sel_vars[1], value=3)

        title.pack(pady=35, anchor=directions_var['w'])
        r1_windows.pack(anchor=directions_var['w'], ipady=5)
        r2_windows.pack(anchor=directions_var['w'], ipady=5)
        r3_windows.pack(anchor=directions_var['w'], ipady=5)
        r4_windows.pack(anchor=directions_var['w'], ipady=5)
        btn_next.pack(anchor=directions_var['se'], side=directions_var['r'], ipadx=15, padx=10)
        btn_back.pack(anchor=directions_var['se'], side=directions_var['r'], padx=5)

    def page_verify(space_check_results):
        # ************** Multilingual support *************************************************************************
        def page_name(): page_verify(space_check_results)
        def change_callback(*args): reload_page(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()
        # *************************************************************************************************************

        global sel_vars
        title = ttk.Label(middle_frame, wraplength=540, justify=directions_var['l'], text=ln.ln_verify_question, font=MEDIUMFONT)
        btn_next = ttk.Button(middle_frame, text=ln.ln_btn_start, style="Accentbutton",
                             command=lambda: page_installing())
        btn_back = ttk.Button(middle_frame, text=ln.ln_btn_back,
                             command=lambda: page_2(space_check_results))

        review_sel = 'x  ' + ln.ln_install_options[sel_vars[0].get()] + '\nx  ' + ln.ln_windows_options[sel_vars[1].get()]
        review_text = tk.Text(middle_frame, spacing1=1,height=6)
        review_text.insert(1.0, review_sel)
        review_text.configure(state='disabled')

        c1_import_wifi = ttk.Checkbutton(middle_frame, text=ln.ln_addition_import_wifi, variable=sel_vars[2],
                                         onvalue=1, offvalue=0)
        c2_auto_restart = ttk.Checkbutton(middle_frame, text=ln.ln_addition_auto_restart, variable=sel_vars[3],
                                          onvalue=1, offvalue=0)
        c3_torrent = ttk.Checkbutton(middle_frame, text=ln.ln_advanced_torrent, variable=sel_vars[4],
                                          onvalue=1, offvalue=0)
        advanced_btn = ttk.Label(middle_frame, wraplength=540, justify="center",
                                 text=ln.ln_show_advanced, font=VERYSMALLFONT,foreground='#3aa9ff')

        def show_advanced(event):
            advanced_btn.pack_forget()
            c3_torrent.pack(anchor=directions_var['w'])
        advanced_btn.bind("<Button-1>", show_advanced)
        title.pack(pady=35, anchor=directions_var['w'])
        review_text.pack(anchor=directions_var['w'], pady=5)
        c1_import_wifi.pack(anchor=directions_var['w'])
        c2_auto_restart.pack(anchor=directions_var['w'])
        advanced_btn.pack(pady=10, padx=10, anchor=directions_var['w'])
        btn_next.pack(anchor=directions_var['se'], side=directions_var['r'], ipadx=15, padx=10)
        btn_back.pack(anchor=directions_var['se'], side=directions_var['r'], padx=5)

    def page_installing():
        # ************** Multilingual support *************************************************************************
        def page_name(): page_installing()
        def change_callback(*args): reload_page(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()
        # *************************************************************************************************************

        lang_list.pack_forget()
        title = ttk.Label(middle_frame, wraplength=540, justify=directions_var['l'], text=ln.ln_install_running, font=MEDIUMFONT)
        progressbar_install = ttk.Progressbar(middle_frame, orient='horizontal', length=500, mode='determinate')
        job_var = tk.StringVar()
        current_job = ttk.Label(middle_frame, wraplength=540, justify=directions_var['l'], textvariable=job_var, font=SMALLFONT)

        title.pack(pady=25, anchor=directions_var['w'])
        progressbar_install.pack(expand=True)
        current_job.pack(pady=5, anchor=directions_var['w'])

        global installer_status, mount_iso_letter, tmp_part_letter
        if check_file_if_exists(install_media_path) == 'True':
            question = messagebox.askyesno(ln.ln_old_download_detected, ln.ln_old_download_detected_text)
            if question:
                installer_status = 2
            else:
                cleanup_remove_folder(download_path)
        if not installer_status:
            while queue1.qsize(): queue1.get()  # to empty the queue
            progressbar_install['value'] = 0
            job_var.set(ln.ln_job_starting_download)
            app.update()
            create_dir(download_path)
            aria2_location = current_dir + '\\resources\\aria2c.exe'
            if sel_vars[4].get():
                args = (aria2_location, APP_INFO.url_torrent, download_path, 1, queue1,)
                # if torrent is selected
            else:
                args = (aria2_location, APP_INFO.url_direct_dl, download_path, 0, queue1,)
                # if torrent is not selected (direct download)
            Process(target=download_with_aria2, args=args).start()
            installer_status = 1



        if installer_status == 1:
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
            rename_file(download_path, '*.iso', downloaded_iso_name)
            installer_status = 2

        if installer_status == 2:
            while queue1.qsize(): queue1.get()  # to empty the queue
            Process(target=create_temp_boot_partition, args=(APP_INFO.required_installer_space, queue1,)).start()
            job_var.set(ln.ln_job_creating_tmp_part)
            progressbar_install['value'] = 90
            installer_status = 3

        if installer_status == 3:
            while not queue1.qsize():
                app.after(200, app.update())
            tmp_part_result = queue1.get()
            if tmp_part_result[0] == 1:
                tmp_part_letter = tmp_part_result[1]
                installer_status = 4
        if installer_status == 4:
            while queue1.qsize(): queue1.get()  # to empty the queue
            mount_iso_letter = mount_iso(install_media_path)
            source_files = mount_iso_letter + ':\\'
            destination_files = tmp_part_letter + ':\\'
            Process(target=copy_files, args=(source_files, destination_files, queue1,)).start()
            job_var.set(ln.ln_job_copying_to_tmp_part)
            progressbar_install['value'] = 94
            installer_status = 5
        if installer_status == 5:
            while not queue1.qsize():
                app.after(200, app.update())
            if queue1.get() == 1:
                installer_status = 6
        if installer_status == 6:
            while queue1.qsize(): queue1.get()  # to empty the queue
            job_var.set(ln.ln_job_adding_tmp_boot_entry)
            progressbar_install['value'] = 99
            Process(target=add_boot_entry, args=(APP_INFO.efi_file_path, tmp_part_letter, queue1,)).start()
            installer_status = 7
        if installer_status == 7:
            while not queue1.qsize():
                app.after(200, app.update())
            if queue1.get() == 1:
                installer_status = 8
        if installer_status == 8:
            cleanup_remove_folder(download_path)
            installer_status = 9
        if installer_status == 9:
            page_installer_installed()

    def page_installer_installed():
        # ************** Multilingual support *************************************************************************
        def page_name(): page_installer_installed()
        def change_callback(*args): reload_page(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()
        # *************************************************************************************************************

        lang_list.pack(anchor=directions_var['nw'], padx=10, pady=10)
        title = ttk.Label(middle_frame, wraplength=540, justify=directions_var['l'], text=ln.ln_finished_title, font=MEDIUMFONT)
        button1 = ttk.Button(middle_frame, text=ln.ln_btn_restart_now, style="Accentbutton",
                             command= lambda: [restart_windows(), app.destroy()])
        button2 = ttk.Button(middle_frame, text=ln.ln_btn_restart_later, command=lambda: app.destroy())
        text_var = tk.StringVar()
        text1 = ttk.Label(middle_frame, wraplength=540, justify=directions_var['l'], text=ln.ln_finished_text, font=SMALLFONT)
        text2 = ttk.Label(middle_frame, wraplength=540, justify="center", textvariable=text_var, font=SMALLFONT)

        title.pack(pady=35, anchor=directions_var['w'])
        text1.pack(pady=10, anchor=directions_var['w'])
        text2.pack(pady=10, anchor=directions_var['w'])
        button1.pack(anchor=directions_var['se'], side=directions_var['r'], ipadx=15, padx=10)
        button2.pack(anchor=directions_var['se'], side=directions_var['r'], padx=5)

        if sel_vars[3].get():
            time_left = 10
            while time_left:
                text_var.set(ln.ln_finished_text_restarting_now % (int(time_left)))
                time_left = time_left - 0.01
                app.after(10, app.update())
            restart_windows()
            app.destroy()

    change_lang('English')
    rebuild_container()
    page_check()
    #print(rename_file(download_path, '*.iso', downloaded_iso_name))
    app.mainloop()


if __name__ == '__main__': main()
