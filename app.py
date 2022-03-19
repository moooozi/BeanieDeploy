from APP_INFO import *
import tkinter as tk
from tkinter import ttk
from multiprocessing import Process
from lang_en import *
from functions import *

# Driver Code
app = tk.Tk()
app.title(SW_NAME)
app.geometry("800x500")
# app.iconbitmap("yourimage.ico")
app.resizable(False, False)
app.tk.call('tk', 'scaling', 1.5)
win_width, win_height = 550, 400

LARGEFONT = ("Ariel", 20)
MEDIUMFONT = ("Ariel", 16)
SMALLFONT = ("Ariel", 12)

# creating a container
container = tk.Frame(app)
container.pack(side="top", fill="both", expand=True)
container.grid_rowconfigure(0, weight=1)
container.grid_columnconfigure(0, weight=1)

top_frame = tk.Frame(container, height=100, bg='yellow')
top_frame.pack(fill="x", ipadx=10, ipady=10)
left_frame = tk.Frame(container, width=200, bg='blue')
left_frame.pack(fill="y", side="left", ipadx=10, ipady=10)
middle_frame = tk.Frame(container, bg='cyan', height=800)
middle_frame.pack(fill="both", expand=1, padx=20, pady=20)


def clear_frame():
    for widgets in middle_frame.winfo_children():
        widgets.destroy()


selections = {}


# page_check
def main():
    def page_check():
        page_name = "page_check"

        label2 = ttk.Label(middle_frame, text="Checking System requirements. please wait...", font=MEDIUMFONT)
        label3 = ttk.Label(middle_frame, text="Compatibility Check Passed!", font=MEDIUMFONT)

        proggresbar_check = ttk.Progressbar(middle_frame, orient='horizontal', length=500, mode='indeterminate')

        label2.pack(pady=40, anchor="w")
        proggresbar_check.pack(expand=True)

        proggresbar_check.start(10)
        queue1 = Queue()

        p1 = Process(target=compatibility_test, args=(queue1,))
        p1.start()
        while queue1.empty():
            app.update()
        compatibility_results = queue1.get()
        button1 = ttk.Button(middle_frame, text="Next",
                             command=lambda: page_1())

        button2 = ttk.Button(middle_frame, text="Quit",
                             command=lambda: app.destroy())

        print(compatibility_results)
        if compatibility_results['result_uefi_check'] == 1 and compatibility_results['result_totalram_check'] == 1 and \
                compatibility_results['result_space_check'] in (1, 2):
            page_1()
        else:

            label2.pack_forget()
            proggresbar_check.pack_forget()
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
    def page_1():
        page_name = "page_1"
        clear_frame()

        label2 = ttk.Label(middle_frame, text=lang_install_question, font=MEDIUMFONT)
        label2.pack(pady=40, anchor="w")
        button1 = ttk.Button(middle_frame, text="Next",
                             command=lambda: page_2())
        # putting the button in its place by
        # using grid
        var1 = tk.IntVar(app, 1)
        # Dictionary to create multiple buttons
        values = {lang_install_option1: 1,
                  lang_install_option2: 2,
                  lang_install_option3: 3}

        # Loop is used to create multiple Radiobuttons
        # rather than creating each button separately
        var1.set(1)
        for (text, value) in values.items():
            ttk.Radiobutton(middle_frame, text=text, variable=var1,
                            value=value).pack(anchor="w", ipady=5)

        button1.pack(anchor="se", side="right", ipadx=15, padx=10)

    # page_2
    def page_2():
        page_name = "page_2"
        clear_frame()
        label2 = ttk.Label(middle_frame, text=lang_windows_question, font=MEDIUMFONT)
        label2.pack(pady=40, anchor="w")

        button1 = ttk.Button(middle_frame, text="Next",
                             command=lambda: page_1())

        button2 = ttk.Button(middle_frame, text="Back",
                             command=lambda: page_1())

        var2 = tk.IntVar(app, 1)

        # Dictionary to create multiple buttons

        values = {lang_windows_option1: 1,
                  lang_windows_option2: 2,
                  lang_windows_option3: 3}

        # Loop is used to create multiple Radiobuttons
        # rather than creating each button separately
        for (text, value) in values.items():
            ttk.Radiobutton(middle_frame, text=text, variable=var2,
                            value=value).pack(anchor="w", ipady=5)

        button1.pack(anchor="se", side="right", ipadx=15, padx=10)
        button2.pack(anchor="se", side="right", padx=5)

    page_check()
    app.mainloop()


if __name__ == '__main__':
    main()
