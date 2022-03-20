# from APP_INFO import *
import tkinter as tk
from tkinter import ttk
from multiprocessing import Process, Queue

import APP_INFO
from lang_en import *
from functions import *

# Driver Code
app = tk.Tk()
app.title(SW_NAME)
app.geometry("800x500")
# Style
style = ttk.Style(app)
app.tk.call('source', 'C:/Users/trapp/PycharmProjects/Lnixify/azure dark/azure dark.tcl')
style.theme_use('azure')
style.configure("Accentbutton", foreground='white')
style.configure("Togglebutton", foreground='white')
# app.iconbitmap("yourimage.ico")
app.resizable(False, False)
win_width, win_height = 100, 100

LARGEFONT = ("Ariel", 20)
MEDIUMFONT = ("Ariel", 16)
SMALLFONT = ("Ariel", 12)

# creating a container
container = tk.Frame(app)
container.pack(side="top", fill="both", expand=True)
container.grid_rowconfigure(0, weight=1)
container.grid_columnconfigure(0, weight=1)
# Frames
top_frame = tk.Frame(container, height=100, bg='yellow')
top_frame.pack(fill="x", ipadx=10, ipady=10)
left_frame = tk.Frame(container, width=200, bg='blue')
left_frame.pack(fill="y", side="left", ipadx=10, ipady=10)
middle_frame = tk.Frame(container, bg='cyan', height=800)
middle_frame.pack(fill="both", expand=1, padx=20, pady=20)


def clear_frame():
    for widgets in middle_frame.winfo_children():
        widgets.destroy()


# page_check
def main():
    def page_check():
        page_name = "page_check"

        label2 = ttk.Label(middle_frame, text=lang_check_running, font=MEDIUMFONT)
        progressbar_check = ttk.Progressbar(middle_frame, orient='horizontal', length=500, mode='indeterminate')

        label2.pack(pady=40, anchor="w")
        progressbar_check.pack(expand=True)

        progressbar_check.start(10)
        queue1 = Queue()

        p1 = Process(target=compatibility_test, args=(queue1,))
        p1.start()
        while queue1.empty():
            app.update()
        compatibility_results = queue1.get()

        button2 = ttk.Button(middle_frame, text=lang_btn_quit,
                             command=lambda: app.destroy())

        print(compatibility_results)
        if compatibility_results['result_uefi_check'] == 1 and compatibility_results['result_totalram_check'] == 1 and \
                compatibility_results['result_space_check'] in (1, 2):
            page_1(compatibility_results['result_space_check'])
        else:

            label2.pack_forget()
            progressbar_check.pack_forget()
            label4 = ttk.Label(middle_frame, text=lang_error_title, font=MEDIUMFONT)
            errors = []
            if compatibility_results['result_uefi_check'] == 0:
                errors.append(lang_error_uefi_0)
            if compatibility_results['result_uefi_check'] == 9:
                errors.append(lang_error_uefi_9)
            if compatibility_results['result_totalram_check'] == 0:
                errors.append(lang_error_totalram_0)
            if compatibility_results['result_totalram_check'] == 9:
                errors.append(lang_error_totalram_9)
            if compatibility_results['result_space_check'] == 0:
                errors.append(lang_error_space_0)
            if compatibility_results['result_space_check'] == 9:
                errors.append(lang_error_space_9)
            if compatibility_results['result_resizable_check'] == 9:
                errors.append(lang_error_resizable_0)
            if compatibility_results['result_resizable_check'] == 0:
                errors.append(lang_error_resizable_9)

            label5 = ttk.Label(middle_frame, text=("\n".join(errors)), font=SMALLFONT)

            label4.pack(pady=40, anchor="nw")
            label5.pack(padx=10, anchor="w")
            button2.pack(anchor="se", side="right", ipadx=15, padx=10)

    # page_1
    def page_1(space_check_results):
        page_name = "page_1"
        clear_frame()

        label2 = ttk.Label(middle_frame, text=lang_install_question, font=MEDIUMFONT)
        label2.pack(pady=40, anchor="w")
        button1 = ttk.Button(middle_frame, text=lang_btn_next, style="Accentbutton",
                             command=lambda: page_2(space_check_results, var1))
        # putting the button in its place by
        # using grid
        var1 = tk.IntVar(app, 1)
        var1.set(1)

        r1_install = ttk.Radiobutton(middle_frame, text=lang_install_options[1], variable=var1, value=1)
        r1_install.pack(anchor="w", ipady=5)
        r2_install = ttk.Radiobutton(middle_frame, text=lang_install_options[2], variable=var1, value=2)
        r2_install.pack(anchor="w", ipady=5)
        r3_install = ttk.Radiobutton(middle_frame, text=lang_install_options[3], variable=var1, value=3)
        r3_install.pack(anchor="w", ipady=5)

        button1.pack(anchor="se", side="right", ipadx=15, padx=10)

    # page_2
    def page_2(space_check_results, selection1):
        page_name = "page_2"
        clear_frame()
        label2 = ttk.Label(middle_frame, text=lang_windows_question, font=MEDIUMFONT)
        label2.pack(pady=40, anchor="w")

        button1 = ttk.Button(middle_frame, text=lang_btn_next, style="Accentbutton",
                             command=lambda: page_1(space_check_results))

        button2 = ttk.Button(middle_frame, text="Back",
                             command=lambda: page_verify(space_check_results, selection1, var2))

        var2 = tk.IntVar(app, 1)
        if space_check_results == 2:
            r1_windows = ttk.Radiobutton(middle_frame, text=lang_windows_options[1], variable=var2, value=1)
        else:
            r1_windows = ttk.Radiobutton(middle_frame, text=lang_windows_option1_disabled, state='disabled')
        r2_windows = ttk.Radiobutton(middle_frame, text=lang_windows_options[2], variable=var2, value=2)
        r3_windows = ttk.Radiobutton(middle_frame, text=lang_windows_options[3], variable=var2, value=3)
        r4_windows = ttk.Radiobutton(middle_frame, text=lang_windows_options[4], variable=var2, value=3)

        r1_windows.pack(anchor="w", ipady=5)
        r2_windows.pack(anchor="w", ipady=5)
        r3_windows.pack(anchor="w", ipady=5)
        r4_windows.pack(anchor="w", ipady=5)

        button1.pack(anchor="se", side="right", ipadx=15, padx=10)
        button2.pack(anchor="se", side="right", padx=5)

    def page_verify(space_check_results, selection1, selection2):
        page_name = "page_2"
        clear_frame()
        label2 = ttk.Label(middle_frame, text=lang_verify_question, font=MEDIUMFONT)
        label2.pack(pady=40, anchor="w")

        button1 = ttk.Button(middle_frame, text=lang_btn_start, style="Accentbutton",
                             command=lambda: page_installing(selection1, selection2))

        button2 = ttk.Button(middle_frame, text="Back",
                             command=lambda: page_1(space_check_results))

        review_text1 = 'x  ' + lang_install_options[selection1] + '\n' + 'x  ' + lang_windows_options[selection2]
        review_text = ttk.Label(middle_frame, text=review_text1)

        review_text.pack(anchor='w', padx=5)

        button1.pack(anchor="se", side="right", ipadx=15, padx=10)
        button2.pack(anchor="se", side="right", padx=5)

    def page_installing(selection1, selection2):
        page_name = "page_installing"
        clear_frame()
        queue2 = Queue()
        label2 = ttk.Label(middle_frame, text=lang_install_running, font=MEDIUMFONT)
        progressbar_install = ttk.Progressbar(middle_frame, orient='horizontal', length=500, mode='determinate')
        current_job_title = "Starting download"
        current_job = ttk.Label(middle_frame, text=current_job_title, font=MEDIUMFONT)

        label2.pack(pady=40, anchor="w")
        progressbar_install.pack(expand=True)
        current_job.pack(pady=40, anchor="w")

        download_path = get_user_home_dir() + '\win2linux_tmpdir'
        install_media_path = download_path + "\install_media.iso"
        p2 = Process(target=download_file, args=(APP_INFO.iso_url, install_media_path))
        p2.start()
        while queue2.qsize() == 0:
            app.update_idletasks()
        # Wait 2 sec
        app.after(2000, app.update_idletasks())
        job_id = queue2.get()
        download_size = get_download_size(job_id)

        def retrack(jobid, totalsize):
            downloaded = track(jobid)
            percent = (downloaded * 100)/totalsize
            progressbar_install['value'] = percent*0.85
            app.update()
            if downloaded < totalsize:
                app.after(1000, retrack(jobid, totalsize))

        retrack(job_id, download_size)
        finish_downloaded(job_id)

    page_check()
    app.mainloop()


if __name__ == '__main__':
    main()
