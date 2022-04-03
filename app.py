# from APP_INFO import *
import ctypes
import pathlib
import sys
import tkinter as tk
from tkinter import ttk
from multiprocessing import Process, Queue
import APP_INFO
import translations.en as lang
from functions import *

# Driver Code
app = tk.Tk()
app.title(APP_INFO.SW_NAME)
app.geometry("800x500")

# Style
style = ttk.Style(app)
app.tk.call('source', str(pathlib.Path(__file__).parent) + '/azure dark/azure dark.tcl')
# app.tk.call('source', 'azure dark/azure dark.tcl')
style.theme_use('azure')
style.configure("Accentbutton", foreground='white')
style.configure("Togglebutton", foreground='white')
# app.iconbitmap("yourimage.ico")
app.resizable(False, False)
app.option_add('*Font', 'Ariel 11')

LARGEFONT = ("Ariel", 20)
MEDIUMFONT = ("Ariel", 16)
SMALLFONT = ("Ariel", 12)


# Global Variables
sel_vars = [tk.IntVar(app, 1), tk.IntVar(app, 1), tk.IntVar(app, 1), tk.IntVar(app, 1)]
queue1 = Queue()
queue2 = Queue()
queue3 = Queue()
queue4 = Queue()
compatibility_results = {}
compatibility_check_status = 0
installer_status = 0
download_path = get_user_home_dir() + "\\win2linux_tmpdir"
install_media_path = download_path + "\\install_media.iso"
mount_iso_letter = ''
process_compatibility_check = Process(target=compatibility_test, args=(queue1,))

# creating a container
container = tk.Frame(app)
container.pack(side="top", fill="both", expand=True)
# Frames
top_frame = tk.Frame(container, height=100)
left_frame = tk.Frame(container, width=200)
left_frame_img = tk.PhotoImage(file='resources/leftframe.png')
left_frame_label = tk.Label(left_frame, image=left_frame_img)
middle_frame = tk.Frame(container, height=800)



# Multiligual
w_var = "w"
ne_var = "ne"
se_var = "se"
sw_var = "sw"
nw_var = "nw"
left_var = "left"
right_var = "right"


def right_to_left_lang(var):
    global w_var, nw_var, ne_var, right_var, left_var, right_var, se_var, sw_var
    if var:
        if ne_var == "ne":
            w_var = "e"
            ne_var = "nw"
            se_var = "sw"
            sw_var = "se"
            nw_var = "ne"
            left_var = "right"
            right_var = "left"
            rebuild_container()
    else:
        if ne_var == "nw":
            w_var = "w"
            ne_var = "ne"
            se_var = "se"
            sw_var = "sw"
            nw_var = "nw"
            left_var = "left"
            right_var = "right"
            rebuild_container()


lang_available = ["English", "Deutsch", "العربية"]
lang_var = tk.StringVar()
lang_list = ttk.Combobox(top_frame, name="language", textvariable=lang_var)
lang_list['values'] = lang_available
lang_list['state'] = 'readonly'
lang_list.set('English')


def rebuild_container():
    top_frame.pack(fill="x", expand=1)
    left_frame.pack(fill="y", side=left_var)
    left_frame_label.pack()
    middle_frame.pack(fill="both", expand=1, padx=20, pady=20)
    lang_list.pack(anchor=nw_var, padx=10, pady=10)


def change_lang(new_lang_code, pagename):
    global lang
    if new_lang_code == 'English':
        import translations.en as lang
        right_to_left_lang(0)
    if new_lang_code == 'Deutsch':
        import translations.de as lang
        right_to_left_lang(0)
    if new_lang_code == 'العربية':
        import translations.ar as lang
        right_to_left_lang(1)

    pagename()


rebuild_container()


def clear_frame():
    for widgets in middle_frame.winfo_children():
        widgets.destroy()


# page_check
def main():
    def page_check():
        def page_name(): page_check()
        def change_callback(*args): change_lang(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()

        label2 = ttk.Label(middle_frame, wraplength=540, justify=left_var, text=lang.ln_check_running, font=MEDIUMFONT)
        progressbar_check = ttk.Progressbar(middle_frame, orient='horizontal', length=500, mode='indeterminate')

        label2.pack(pady=40, anchor=w_var)
        progressbar_check.pack(expand=True)
        progressbar_check.start(10)
        # Request admin if not available
        if not ctypes.windll.shell32.IsUserAnAdmin():
            app.update()
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            quit()
        global compatibility_results, compatibility_check_status
        #compatibility_results = {'result_uefi_check': 0, 'result_totalram_check': 0, 'result_space_check': 0, 'result_resizable_check': 0, 'result_bitlocker_check': 0}
        compatibility_results = {'result_uefi_check': 1, 'result_totalram_check': 1, 'result_space_check': 2, 'result_resizable_check': 1, 'result_bitlocker_check': 1}
        if not compatibility_results:
            if not compatibility_check_status:
                process_compatibility_check.start()
                compatibility_check_status = 1
            if compatibility_check_status == 1:
                while queue1.empty():
                    app.after(10, app.update())
                compatibility_results = queue1.get()
                compatibility_check_status = 2

        button2 = ttk.Button(middle_frame, text=lang.ln_btn_quit, command=lambda: app.destroy())

        if compatibility_results['result_uefi_check'] == 1 and compatibility_results[
            'result_totalram_check'] == 1 and compatibility_results[
            'result_space_check'] in (1, 2) and compatibility_results[
            'result_resizable_check'] == 1 and compatibility_results[
            'result_bitlocker_check'] == 1:
            page_1(compatibility_results['result_space_check'])
        else:

            label2.pack_forget()
            progressbar_check.pack_forget()
            title = ttk.Label(middle_frame, wraplength=540, justify=left_var, text=lang.ln_error_title,
                               font=MEDIUMFONT)
            errors = []
            if compatibility_results['result_uefi_check'] == 0:
                errors.append(lang.ln_error_uefi_0)
            if compatibility_results['result_uefi_check'] == 9:
                errors.append(lang.ln_error_uefi_9)
            if compatibility_results['result_totalram_check'] == 0:
                errors.append(lang.ln_error_totalram_0)
            if compatibility_results['result_totalram_check'] == 9:
                errors.append(lang.ln_error_totalram_9)
            if compatibility_results['result_space_check'] == 0:
                errors.append(lang.ln_error_space_0)
            if compatibility_results['result_space_check'] == 9:
                errors.append(lang.ln_error_space_9)
            if compatibility_results['result_resizable_check'] == 0:
                errors.append(lang.ln_error_resizable_0)
            if compatibility_results['result_resizable_check'] == 9:
                errors.append(lang.ln_error_resizable_9)
            if compatibility_results['result_bitlocker_check'] == 0:
                errors.append(lang.ln_error_bitlocker_0)
            if compatibility_results['result_bitlocker_check'] == 9:
                errors.append(lang.ln_error_bitlocker_9)

            label5 = ttk.Label(middle_frame, wraplength=540, justify=left_var,
                               text=lang.ln_error_list + "\n\n- " + ("\n- ".join(errors)),
                               font=SMALLFONT)
            title.pack(pady=40, anchor=nw_var)
            label5.pack(padx=10, anchor=w_var)
            button2.pack(anchor=se_var, side=right_var, ipadx=15, padx=10)

    # page_1
    def page_1(space_check_results):
        def page_name(): page_1(space_check_results)
        def change_callback(*args): change_lang(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()
        global sel_vars

        title = ttk.Label(middle_frame, wraplength=540, justify=left_var, text=lang.ln_install_question, font=MEDIUMFONT)
        button1 = ttk.Button(middle_frame, text=lang.ln_btn_next, style="Accentbutton",
                             command=lambda: page_2(space_check_results))

        r1_install = ttk.Radiobutton(middle_frame, text=lang.ln_install_options[1], variable=sel_vars[0], value=1)
        r2_install = ttk.Radiobutton(middle_frame, text=lang.ln_install_options[2], variable=sel_vars[0], value=2)
        r3_install = ttk.Radiobutton(middle_frame, text=lang.ln_install_options[3], variable=sel_vars[0], value=3)

        title.pack(pady=40, anchor=w_var)
        r1_install.pack(anchor=w_var, ipady=5)
        r2_install.pack(anchor=w_var, ipady=5)
        r3_install.pack(anchor=w_var, ipady=5)
        button1.pack(anchor=se_var, side=right_var, ipadx=15, padx=10)

    # page_2
    def page_2(space_check_results):
        def page_name(): page_2(space_check_results)
        def change_callback(*args): change_lang(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()

        title = ttk.Label(middle_frame, wraplength=540, justify=left_var, text=lang.ln_windows_question,
                           font=MEDIUMFONT)

        button1 = ttk.Button(middle_frame, text=lang.ln_btn_next, style="Accentbutton",
                             command=lambda: page_verify(space_check_results))

        button2 = ttk.Button(middle_frame, text=lang.ln_btn_back,
                             command=lambda: page_1(space_check_results))
        global sel_vars
        if space_check_results == 2:
            r1_windows = ttk.Radiobutton(middle_frame, text=lang.ln_windows_options[1], variable=sel_vars[1], value=1)
        else:
            r1_windows = ttk.Radiobutton(middle_frame, text=lang.ln_windows_option1_disabled, state='disabled')
        r2_windows = ttk.Radiobutton(middle_frame, text=lang.ln_windows_options[2], variable=sel_vars[1], value=2)
        r3_windows = ttk.Radiobutton(middle_frame, text=lang.ln_windows_options[3], variable=sel_vars[1], value=3)
        r4_windows = ttk.Radiobutton(middle_frame, text=lang.ln_windows_options[4], variable=sel_vars[1], value=4)

        title.pack(pady=40, anchor=w_var)
        r1_windows.pack(anchor=w_var, ipady=5)
        r2_windows.pack(anchor=w_var, ipady=5)
        r3_windows.pack(anchor=w_var, ipady=5)
        r4_windows.pack(anchor=w_var, ipady=5)
        button1.pack(anchor=se_var, side=right_var, ipadx=15, padx=10)
        button2.pack(anchor=se_var, side=right_var, padx=5)

    def page_verify(space_check_results):
        def page_name(): page_verify(space_check_results)
        def change_callback(*args): change_lang(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()

        global sel_vars
        title = ttk.Label(middle_frame, wraplength=540, justify=left_var, text=lang.ln_verify_question, font=MEDIUMFONT)
        button1 = ttk.Button(middle_frame, text=lang.ln_btn_start, style="Accentbutton",
                             command=lambda: page_installing())
        button2 = ttk.Button(middle_frame, text=lang.ln_btn_back,
                             command=lambda: page_2(space_check_results))

        review_sel = 'x  ' + lang.ln_install_options[sel_vars[0].get()] + '\nx  ' + lang.ln_windows_options[sel_vars[1].get()]
        review_text = tk.Text(middle_frame, spacing1=1,height=6)
        review_text.insert(1.0, review_sel)
        review_text.configure(state='disabled')

        c1_import_wifi = ttk.Checkbutton(middle_frame, text=lang.ln_addition_import_wifi, variable=sel_vars[2],
                                         onvalue=1, offvalue=0)
        c2_auto_restart = ttk.Checkbutton(middle_frame, text=lang.ln_addition_auto_restart, variable=sel_vars[3],
                                          onvalue=1, offvalue=0)

        title.pack(pady=40, anchor=w_var)
        review_text.pack(anchor=w_var, pady=5)
        c1_import_wifi.pack(anchor=w_var)
        c2_auto_restart.pack(anchor=w_var)
        button1.pack(anchor=se_var, side=right_var, ipadx=15, padx=10)
        button2.pack(anchor=se_var, side=right_var, padx=5)

    def page_installing():
        def page_name(): page_installing()
        def change_callback(*args): change_lang(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()

        lang_list.pack_forget()
        title = ttk.Label(middle_frame, wraplength=540, justify=left_var, text=lang.ln_install_running, font=MEDIUMFONT)
        progressbar_install = ttk.Progressbar(middle_frame, orient='horizontal', length=500, mode='determinate')
        job_var = tk.StringVar()
        current_job = ttk.Label(middle_frame, wraplength=540, justify=left_var, textvariable=job_var, font=SMALLFONT)

        title.pack(pady=40, anchor=w_var)
        progressbar_install.pack(expand=True)
        current_job.pack(pady=5, anchor=w_var)

        global installer_status, process_dl_install_media, process_create_tmp_partition, mount_iso_letter, \
               process_copy_to_part, tmp_part_letter, process_make_boot, job_id
        if not installer_status:
            if queue2.qsize(): queue2.get()  # to empty the queue
            progressbar_install['value'] = 0
            job_var.set(lang.ln_job_starting_download)
            app.update()
            create_dir(download_path)
            process_dl_install_media = Process(target=download_file, args=(APP_INFO.iso_url, install_media_path, queue2,))
            process_dl_install_media.start()
            while not queue2.qsize():
                app.after(100, app.update())
            job_id = queue2.get()
            installer_status = 1

        if installer_status == 1:
            dl_status = track_download(job_id)
            while dl_status[0] != dl_status[1]:
                dl_status = track_download(job_id)
                percent = (int(dl_status[1]) * 100) / int(dl_status[0])
                progressbar_install['value'] = percent * 0.92
                job_var.set(lang.ln_job_downloading_install_media + r'(%' + str(round(percent, 1)) + ')')
                app.after(500, app.update())
            finish_download(job_id)
            installer_status = 2

        if installer_status == 2:
            if queue3.qsize(): queue3.get()  # to empty the queue
            process_create_tmp_partition = Process(target=create_temp_boot_partition,args=(APP_INFO.required_shrink_space, queue3,))
            process_create_tmp_partition.start()
            job_var.set(lang.ln_job_creating_tmp_part)
            progressbar_install['value'] = 92
            installer_status = 3

        if installer_status == 3:
            while process_create_tmp_partition.is_alive():
                app.after(1000, app.update())
            tmp_part_result = queue3.get()
            if tmp_part_result[0] == 1:
                tmp_part_letter = tmp_part_result[1]
                installer_status = 4
        if installer_status == 4:
            mount_iso_letter = mount_iso(download_path)
            source_files = mount_iso_letter + ':\\'
            destination_files = tmp_part_letter + ':\\'
            process_copy_to_part = Process(target=copy_files, args=(source_files, destination_files,))
            process_copy_to_part.start()
            job_var.set(lang.ln_job_copying_to_tmp_part)
            progressbar_install['value'] = 94
            installer_status = 5

        if installer_status == 5:
            while process_copy_to_part.is_alive():
                app.after(1000, app.update())
            installer_status = 6
        if installer_status == 6:
            job_var.set(lang.ln_job_adding_tmp_boot_entry)
            progressbar_install['value'] = 99
            process_make_boot = Process(target=add_boot_entry, args=(APP_INFO.efi_file_path, tmp_part_letter,))
            process_make_boot.start()
            installer_status = 7
        if installer_status == 7:
            while process_make_boot.is_alive():
                app.after(1000, app.update())
            installer_status = 8
        if installer_status == 8:
            cleanup_after_install(download_path)
            installer_status = 9
        if installer_status == 9:
            page_ready_to_install()

    def page_ready_to_install():
        def page_name(): page_ready_to_install()
        def change_callback(*args): change_lang(lang_var.get(), page_name)
        lang_list.bind('<<ComboboxSelected>>', change_callback)
        clear_frame()
        lang_list.pack(anchor=nw_var, padx=10, pady=10)
        title = ttk.Label(middle_frame, wraplength=540, justify=left_var, text=lang.ln_finished_title, font=MEDIUMFONT)
        button1 = ttk.Button(middle_frame, text=lang.ln_btn_restart_now, style="Accentbutton",
                             command= lambda: [restart_windows(), app.destroy()])
        button2 = ttk.Button(middle_frame, text=lang.ln_btn_restart_later, command=lambda: app.destroy())
        text_var = tk.StringVar()
        text1 = ttk.Label(middle_frame, wraplength=540, justify=left_var, text=lang.ln_finished_text, font=SMALLFONT)
        text2 = ttk.Label(middle_frame, wraplength=540, justify="center", textvariable=text_var, font=SMALLFONT)

        title.pack(pady=40, anchor=w_var)
        text1.pack(pady=40, anchor=w_var)
        text2.pack(pady=40, anchor=w_var)
        button1.pack(anchor=se_var, side=right_var, ipadx=15, padx=10)
        button2.pack(anchor=se_var, side=right_var, padx=5)

        if sel_vars[3].get():
            time_left = 1000
            while True:
                if time_left:
                    text_var.set(lang.ln_finished_text_restarting_now % (int(time_left/100)))
                    time_left = time_left - 1
                    app.after(10, app.update())
                else:
                    restart_windows()
                    done = 1
                    break
            if done:
                app.destroy()

    print(get_user_home_dir())
    print(install_media_path)
    page_check()
    app.mainloop()


if __name__ == '__main__':
    main()
