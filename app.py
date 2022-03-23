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
#app.tk.call('source', 'azure dark/azure dark.tcl')

style.theme_use('azure')
style.configure("Accentbutton", foreground='white')
style.configure("Togglebutton", foreground='white')
# app.iconbitmap("yourimage.ico")
app.resizable(False, False)
win_width, win_height = 100, 100

LARGEFONT = ("Ariel", 20)
MEDIUMFONT = ("Ariel", 16)
SMALLFONT = ("Ariel", 12)

w_var = "w"
ne_var = "ne"
se_var = "se"
nw_var = "nw"
left_var = "left"
right_var = "right"


def right_to_left_lang(var):
    global w_var, nw_var, ne_var, right_var, left_var, right_var, se_var
    if var:
        if ne_var == "ne":
            w_var = "e"
            ne_var = "nw"
            se_var = "sw"
            nw_var = "ne"
            left_var = "right"
            right_var = "left"
            rebuild_container()

    else:
        if ne_var == "nw":
            w_var = "w"
            ne_var = "ne"
            se_var = "se"
            nw_var = "nw"
            left_var = "left"
            right_var = "right"
            rebuild_container()


queue1 = Queue()
compatibility_results = {}
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


rebuild_container()


def clear_frame():
    for widgets in middle_frame.winfo_children():
        widgets.destroy()


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


# page_check
def main():
    def page_check():
        page_name = "page_check"

        def page_name(): page_check()

        def change_callback(*args): change_lang(lang_var.get(), page_name)

        lang_list.bind('<<ComboboxSelected>>', change_callback)

        clear_frame()

        label2 = ttk.Label(middle_frame, wraplength=540,  justify=left_var, text=lang.ln_check_running, font=MEDIUMFONT)
        progressbar_check = ttk.Progressbar(middle_frame, orient='horizontal', length=500, mode='indeterminate')

        label2.pack(pady=40, anchor=w_var)
        progressbar_check.pack(expand=True)

        progressbar_check.start(10)
        if not ctypes.windll.shell32.IsUserAnAdmin():
            app.update()
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            quit()
        global compatibility_results
        # compatibility_results = {'result_uefi_check': 0,'result_totalram_check': 0,'result_space_check': 0,'result_resizable_check': 0,'result_bitlocker_check': 0}
        if not compatibility_results:
            if not process_compatibility_check.is_alive():
                process_compatibility_check.start()
            while queue1.empty():
                app.update()
            compatibility_results = queue1.get()

        button2 = ttk.Button(middle_frame, text=lang.ln_btn_quit,
                             command=lambda: app.destroy())

        if compatibility_results['result_uefi_check'] == 1 and compatibility_results[
            'result_totalram_check'] == 1 and compatibility_results[
            'result_space_check'] in (1, 2) and compatibility_results[
            'result_resizable_check'] == 1 and compatibility_results[
            'result_bitlocker_check'] == 1:
            page_1(compatibility_results['result_space_check'])
        else:

            label2.pack_forget()
            progressbar_check.pack_forget()
            label4 = ttk.Label(middle_frame, wraplength=540,  justify=left_var,  text=lang.ln_error_title, font=MEDIUMFONT)
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
            if compatibility_results['result_resizable_check'] == 9:
                errors.append(lang.ln_error_resizable_0)
            if compatibility_results['result_resizable_check'] == 0:
                errors.append(lang.ln_error_resizable_9)
            if compatibility_results['result_bitlocker_check'] == 9:
                errors.append(lang.ln_error_bitlocker_0)
            if compatibility_results['result_bitlocker_check'] == 0:
                errors.append(lang.ln_error_bitlocker_9)

            label5 = ttk.Label(middle_frame, wraplength=540,  justify=left_var, text=lang.ln_error_list + "\n\n- " + ("\n- ".join(errors)),
                               font=SMALLFONT)

            label4.pack(pady=40, anchor=nw_var)
            label5.pack(padx=10, anchor=w_var)
            button2.pack(anchor=se_var, side=right_var, ipadx=15, padx=10)

    # page_1
    def page_1(space_check_results):
        def page_name(): page_1(space_check_results)

        clear_frame()

        def change_callback(*args): change_lang(lang_var.get(), page_name)

        lang_list.bind('<<ComboboxSelected>>', change_callback)

        label2 = ttk.Label(middle_frame, wraplength=540,  justify=left_var, text=lang.ln_install_question, font=MEDIUMFONT)
        label2.pack(pady=40, anchor=w_var)
        button1 = ttk.Button(middle_frame, text=lang.ln_btn_next, style="Accentbutton",
                             command=lambda: page_2(space_check_results, var1))

        # putting the button in its place by
        # using grid
        var1 = tk.IntVar(app, 1)
        var1.set(1)

        r1_install = ttk.Radiobutton(middle_frame, text=lang.ln_install_options[1], variable=var1, value=1)
        r1_install.pack(anchor=w_var, ipady=5)
        r2_install = ttk.Radiobutton(middle_frame, text=lang.ln_install_options[2], variable=var1, value=2)
        r2_install.pack(anchor=w_var, ipady=5)
        r3_install = ttk.Radiobutton(middle_frame, text=lang.ln_install_options[3], variable=var1, value=3)
        r3_install.pack(anchor=w_var, ipady=5)

        button1.pack(anchor=se_var, side=right_var, ipadx=15, padx=10)
        lang_list.pack(anchor=ne_var, side=right_var)

    # page_2
    def page_2(space_check_results, selection1):
        def page_name():
            page_2(space_check_results, selection1)

        clear_frame()

        def change_callback(*args):
            change_lang(lang_var.get(), page_name)

        lang_list.bind('<<ComboboxSelected>>', change_callback)

        label2 = ttk.Label(middle_frame, wraplength=540,  justify=left_var, text=lang.ln_windows_question, font=MEDIUMFONT)
        label2.pack(pady=40, anchor=w_var)

        button1 = ttk.Button(middle_frame, text=lang.ln_btn_next, style="Accentbutton",
                             command=lambda: page_verify(space_check_results, selection1, var2))

        button2 = ttk.Button(middle_frame, text=lang.ln_btn_back,
                             command=lambda: page_1(space_check_results))

        var2 = tk.IntVar(app, 1)
        if space_check_results == 2:
            r1_windows = ttk.Radiobutton(middle_frame, text=lang.ln_windows_options[1], variable=var2, value=1)
        else:
            r1_windows = ttk.Radiobutton(middle_frame, text=lang.ln_windows_option1_disabled, state='disabled')
        r2_windows = ttk.Radiobutton(middle_frame, text=lang.ln_windows_options[2], variable=var2, value=2)
        r3_windows = ttk.Radiobutton(middle_frame, text=lang.ln_windows_options[3], variable=var2, value=3)
        r4_windows = ttk.Radiobutton(middle_frame, text=lang.ln_windows_options[4], variable=var2, value=4)

        r1_windows.pack(anchor=w_var, ipady=5)
        r2_windows.pack(anchor=w_var, ipady=5)
        r3_windows.pack(anchor=w_var, ipady=5)
        r4_windows.pack(anchor=w_var, ipady=5)

        button1.pack(anchor=se_var, side=right_var, ipadx=15, padx=10)
        button2.pack(anchor=se_var, side=right_var, padx=5)

    def page_verify(space_check_results, selection1, selection2):
        def page_name(): page_verify(space_check_results, selection1, selection2)

        clear_frame()

        def change_callback(*args): change_lang(lang_var.get(), page_name)

        lang_list.bind('<<ComboboxSelected>>', change_callback)

        label2 = ttk.Label(middle_frame, wraplength=540,  justify=left_var, text=lang.ln_verify_question, font=MEDIUMFONT)
        label2.pack(pady=40, anchor=w_var)

        button1 = ttk.Button(middle_frame, text=lang.ln_btn_start, style="Accentbutton",
                             command=lambda: page_installing(selection1, selection2))

        button2 = ttk.Button(middle_frame, text=lang.ln_btn_back,
                             command=lambda: page_1(space_check_results))

        review_text1 = 'x  ' + lang.ln_install_options[selection1] + '\n' + 'x  ' + lang.ln_windows_options[
            selection2]
        review_text = ttk.Label(middle_frame, wraplength=540,  justify=left_var, text=review_text1)

        review_text.pack(anchor='w', padx=5)

        button1.pack(anchor=se_var, side=right_var, ipadx=15, padx=10)
        button2.pack(anchor=se_var, side=right_var, padx=5)

    def page_installing(selection1, selection2):
        page_name = "page_installing"
        clear_frame()
        queue2 = Queue()
        label2 = ttk.Label(middle_frame, wraplength=540,  justify=left_var, text=lang.ln_install_running, font=MEDIUMFONT)
        progressbar_install = ttk.Progressbar(middle_frame, orient='horizontal', length=500, mode='determinate')
        current_job_title = "Starting download"
        current_job = ttk.Label(middle_frame, wraplength=540,  justify=left_var, text=current_job_title, font=MEDIUMFONT)

        label2.pack(pady=40, anchor=w_var)
        progressbar_install.pack(expand=True)
        current_job.pack(pady=40, anchor=w_var)

        download_path = get_user_home_dir() + '\win2linux_tmpdir'
        install_media_path = download_path + "\install_media.iso"
        p2 = Process(target=download_file, args=(APP_INFO.iso_url, install_media_path))
        p2.start()
        while queue2.qsize() == 0:
            app.update_idletasks()
        # Wait 2 sec
        app.after(2000, app.update())
        job_id = queue2.get()
        download_size = get_download_size(job_id)

        def retrack(jobid, totalsize):
            downloaded = get_total_download_size(jobid)
            percent = (downloaded * 100) / totalsize
            progressbar_install['value'] = percent * 0.85
            app.update()
            if downloaded < totalsize:
                app.after(1000, retrack(jobid, totalsize))

        retrack(job_id, download_size)
        finish_downloaded(job_id)

    print(lang.ln_install_text)
    #page_check()
    app.mainloop()


if __name__ == '__main__':
    main()
