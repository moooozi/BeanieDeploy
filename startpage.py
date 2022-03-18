from APP_INFO import *

import tkinter as tk
from tkinter import ttk
from functions import *
import concurrent.futures
from lang_en import *

# Driver Code
app = tk.Tk()
app.title(SW_NAME)
app.geometry("800x500")
# app.iconbitmap("yourimage.ico")
app.resizable(False, False)
app.tk.call('tk', 'scaling', 2.0)
win_width, win_height = 550, 400

LARGEFONT = ("Ariel", 20)
MEDIUMFONT = ("Ariel", 16)
SMALLFONT = ("Ariel", 12)

# creating a container
container = tk.Frame(app)
container.pack(side="top", fill="both", expand=True)
container.grid_rowconfigure(0, weight=1)
container.grid_columnconfigure(0, weight=1)

# initializing frames to an empty array
frames = {}
pages = ['page_check', 'page_error', 'page_1', 'page_2']
# iterating through a tuple consisting of the different page layouts
for page in pages:
    frame = tk.Frame(container)
    # initializing frame of that object respectively with for loop
    frames[page] = frame
    frame.grid(row=0, column=0, sticky="nsew")


def show_frame(cont):
    global frame
    frame = frames[cont]
    frame.tkraise()


show_frame("page_check")


# page_check
def page_check():
    page_name = "page_check"
    top_frame = tk.Frame(frames[page_name], height=100, bg='yellow')
    top_frame.pack(fill="x", ipadx=10, ipady=10)

    left_frame = tk.Frame(frames[page_name], width=200, bg='blue')
    left_frame.pack(fill="y", side="left", ipadx=10, ipady=10)

    middle_frame = tk.Frame(frames[page_name], bg='cyan', height=800)
    middle_frame.pack(fill="both", expand=1, padx=20, pady=20)

    label2 = ttk.Label(middle_frame, text="Checking System requirements. please wait...", font=MEDIUMFONT)
    label3 = ttk.Label(middle_frame, text="Compatibility Check Passed!", font=MEDIUMFONT)

    pb_hD = ttk.Progressbar(middle_frame, orient='horizontal', length=500, mode='indeterminate')

    label2.pack(pady=40, anchor="w")
    pb_hD.pack(expand=True)

    pb_hD.start(10)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(compatibility_test)
        compatibility_results = future.result()
    button1 = ttk.Button(middle_frame, text="Next",
                         command=lambda: show_frame("page_1"))

    button2 = ttk.Button(middle_frame, text="Quit",
                         command=lambda: app.destroy())

    print(compatibility_results)
    if compatibility_results['result_uefi_check'] == 1 and compatibility_results['result_totalram_check'] == 1 and \
            compatibility_results['result_space_check'] in (1, 2):
        label2.pack_forget()
        pb_hD.pack_forget()
        label3.pack(pady=40, anchor="nw")
        button1.pack(anchor="se", side="right", ipadx=15, padx=10)
        button2.pack(anchor="se", side="right", ipadx=15, padx=10)
    else:

        label2.pack_forget()
        pb_hD.pack_forget()
        label4 = ttk.Label(middle_frame, text=error_title, font=MEDIUMFONT)
        errors = []
        if compatibility_results['result_uefi_check'] == 0:
            errors.append(error_uefi_0)
        if compatibility_results['result_uefi_check'] == 9:
            errors.append(error_uefi_9)
        if compatibility_results['result_totalram_check'] == 0:
            errors.append(error_totalram_0)
        if compatibility_results['result_totalram_check'] == 9:
            errors.append(error_totalram_9)
        if compatibility_results['result_space_check'] == 0:
            errors.append(error_space_0)
        if compatibility_results['result_space_check'] == 9:
            errors.append(error_space_9)
        if compatibility_results['result_resizable_check'] == 9:
            errors.append(error_resizable_0)
        if compatibility_results['result_resizable_check'] == 0:
            errors.append(error_resizable_9)

        label5 = ttk.Label(middle_frame, text=("\n".join(errors)), font=SMALLFONT)

        label4.pack(pady=40, anchor="nw")
        label5.pack(padx=10, anchor="w")
        button2.pack(anchor="se", side="right", ipadx=15, padx=10)


# page_error
def page_error():
    page_name = "page_error"

    top_frame = tk.Frame(frames[page_name], height=100, bg='yellow')
    top_frame.pack(fill="x", ipadx=10, ipady=10)

    left_frame = tk.Frame(frames[page_name], width=200, bg='blue')
    left_frame.pack(fill="y", side="left", ipadx=10, ipady=10)

    middle_frame = tk.Frame(frames[page_name], bg='cyan', height=800)
    middle_frame.pack(fill="both", expand=1, padx=20, pady=20)

    # button1 = ttk.Button(frames[page_name], text="StartPage",
    #                     command=lambda: controller.show_frame(StartPage))
    # button1.pack()

    # button to show frame 2 with text
    # layout2
    # label = ttk.Label(middle_frame, text="First, help me help you", font=LARGEFONT)
    # label.pack(anchor="w")
    label2 = ttk.Label(middle_frame, text="Could not complete compatibility test", font=MEDIUMFONT)
    label2.pack(pady=40, anchor="w")
    button1 = ttk.Button(middle_frame, text="Next", style="big.TButton",
                         command=lambda: show_frame("page_2"))

    button1.pack(anchor="se", side="right", ipadx=15, padx=10)


# page_1
def page_1():
    page_name = "page_1"

    top_frame = tk.Frame(frames[page_name], height=100, bg='yellow')
    top_frame.pack(fill="x", ipadx=10, ipady=10)

    left_frame = tk.Frame(frames[page_name], width=200, bg='blue')
    left_frame.pack(fill="y", side="left", ipadx=10, ipady=10)

    middle_frame = tk.Frame(frames[page_name], bg='cyan', height=800)
    middle_frame.pack(fill="both", expand=1, padx=20, pady=20)

    label2 = ttk.Label(middle_frame, text="Which option describes you the best?", font=MEDIUMFONT)
    label2.pack(pady=40, anchor="w")
    button1 = ttk.Button(middle_frame, text="Next", style="big.TButton",
                         command=lambda: show_frame("page_2"))
    # putting the button in its place by
    # using grid
    var1 = tk.IntVar(1)
    # Dictionary to create multiple buttons
    values = {install_option1: 1,
              install_option2: 2,
              install_option3: 3}

    # Loop is used to create multiple Radiobuttons
    # rather than creating each button separately
    for (text, value) in values.items():
        ttk.Radiobutton(middle_frame, text=text, variable=var1,
                        value=value).pack(anchor="w", ipady=5)
    var1.set(1)

    button1.pack(anchor="se", side="right", ipadx=15, padx=10)


# page_2
def page_2():
    page_name = "page_2"

    top_frame = tk.Frame(frames[page_name], height=100, bg='yellow')
    top_frame.pack(fill="x", ipadx=10, ipady=10)

    left_frame = tk.Frame(frames[page_name], width=200, bg='blue')
    left_frame.pack(fill="y", side="left", ipadx=10, ipady=10)

    middle_frame = tk.Frame(frames[page_name], bg='cyan', height=800)
    middle_frame.pack(fill="both", expand=1, padx=20, pady=20)

    label2 = ttk.Label(middle_frame, text="Got it, what do you want me to do with Windows?", font=MEDIUMFONT)
    label2.pack(pady=40, anchor="w")

    button1 = ttk.Button(middle_frame, text="Next",
                         command=lambda: show_frame("page_1"))

    button2 = ttk.Button(middle_frame, text="Back",
                         command=lambda: show_frame("page_1"))

    var2 = tk.IntVar(1)

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


app.mainloop()
