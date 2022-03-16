import tkinter as tk
from tkinter import ttk
import webbrowser
import subprocess
import powershell

LARGEFONT = ("Ariel", 20)
MEDIUMFONT = ("Ariel", 16)
SMALLFONT = ("Ariel", 14)


class TkinterApp(tk.Tk):

    # __init__ function for class tkinterApp
    def __init__(self, *args, **kwargs):
        # __init__ function for class Tk
        tk.Tk.__init__(self, *args, **kwargs)

        # creating a container
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # initializing frames to an empty array
        self.frames = {}

        # iterating through a tuple consisting
        # of the different page layouts
        for F in (StartPage, PageCheck, Page1, Page2):
            frame = F(container, self)

            # initializing frame of that object from
            # startpage, page1, page2 respectively with
            # for loop
            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)

    # to display the current frame passed as
    # parameter
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()


# first window frame startpage

class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        # label of frame Layout 2
        top_frame = tk.Frame(self, height=100, bg='yellow')
        top_frame.pack(fill="x", ipadx=10, ipady=10)

        left_frame = tk.Frame(self, width=200, bg='blue')
        left_frame.pack(fill="y", side="left", ipadx=10, ipady=10)

        middle_frame = tk.Frame(self, bg='cyan', height=800)
        middle_frame.pack(fill="both", expand=1, padx=20, pady=20)

        def open_url(url):
            webbrowser.open_new_tab(url)

        # Top Frame Content
        #img_app_logo = tk.PhotoImage(file="appLogo.png")
        #btn_app_logo = tk.Label(top_frame, image=img_app_logo, cursor="hand2")
        #url1 = 'https://www.kernel.org/'
        #btn_app_logo.pack(side="left")
        #btn_app_logo.bind("<Button-1>", lambda e: open_url(url1))

        #text_moto = tk.Label(top_frame, text="Free as in Freedom")
        #text_moto.pack(side="left")

        #img_suse = tk.PhotoImage(file="Suse-logo.png")
        #btn_suse = tk.Label(top_frame, image=img_suse, cursor="hand2")
        #url2 = 'https://www.opensuse.org/'
        #btn_suse.pack(side="right")
        #btn_suse.bind("<Button-1>", lambda e: open_url(url2))

        label = ttk.Label(middle_frame, wraplength=win_width,
                          text="Hi, this is Lnixify, the fastest way to deploy GNU/Linux from a Windows machine",
                          font=LARGEFONT)
        label.pack(anchor="w")
        label2 = ttk.Label(middle_frame, wraplength=win_width,
                           text="Click Check to test your system compatibility", font=MEDIUMFONT)
        label2.pack(pady=40, anchor="w")
        button1 = ttk.Button(middle_frame, text="Check ", style="big.TButton",
                             command=lambda: [controller.show_frame(PageCheck), PageCheck.compatibility_test(self)])

        button1.pack(anchor="se", side="right", ipadx=15, padx=10)


class PageCheck(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        top_frame = tk.Frame(self, height=100, bg='yellow')
        top_frame.pack(fill="x", ipadx=10, ipady=10)

        left_frame = tk.Frame(self, width=200, bg='blue')
        left_frame.pack(fill="y", side="left", ipadx=10, ipady=10)

        middle_frame = tk.Frame(self, bg='cyan', height=800)
        middle_frame.pack(fill="both", expand=1, padx=20, pady=20)

        label2 = ttk.Label(middle_frame, text="Checking System requirements. please wait...", font=MEDIUMFONT)
        label2.pack(pady=40, anchor="w")

    def compatibility_test(self, controller):

        print('hey')
        space_required_min = 900 * 1024 * 1024
        space_required_dualboot = space_required_min + 70 * 1024 * 1024 * 1024

        check_uefi = subprocess.run(
            [r'powershell.exe', r'$env:firmware_type'],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

        check_space = subprocess.run(
            [r'powershell.exe', r'(Get-Volume | Where DriveLetter -eq $env:SystemDrive.Substring(0, 1)).SizeRemaining'],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

        #check_resizable = subprocess.run(
        #    [r'powershell.exe', r'(Get-PartitionSupportedSize -DriveLetter $env:SystemDrive.Substring(0, 1)).SizeMax'],
        #    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

        check_totalram = subprocess.run(
            [r'powershell.exe', r'(Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property capacity -Sum).sum /1gb'],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

        required_ram = 4
        totalram = int(check_totalram.stdout)

        if check_totalram.returncode != 0:
            result_totalram_check = 9
        elif totalram >= required_ram:
            result_totalram_check = 1
        else:
            result_totalram_check = 0
        if check_uefi.returncode != 0:
            result_uefi_check = 9
        elif b'uefi' in check_uefi.stdout.lower():
            result_uefi_check = 1
        else:
            result_uefi_check = 0

        if check_space.returncode != 0:
            result_space_check = 9
        if int(check_space.stdout) > space_required_dualboot:
            result_space_check = 2
        elif int(check_space.stdout) > space_required_min:
            result_space_check = 1
        else:
            result_space_check = 0

        #if check_resizable.returncode != 0: print("not complete  ")
        # print(check_resizable.stdout)
        # if 900000000> check_resizable: pass

        def error_codes(uefi_return, totalram_return, ):
            pass

        if result_uefi_check == 1 and result_totalram_check == 1 and result_space_check == (1 | 2):
            controller.show_frame(Page2)
        else:



class Page1(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        top_frame = tk.Frame(self, height=100, bg='yellow')
        top_frame.pack(fill="x", ipadx=10, ipady=10)

        left_frame = tk.Frame(self, width=200, bg='blue')
        left_frame.pack(fill="y", side="left", ipadx=10, ipady=10)

        middle_frame = tk.Frame(self, bg='cyan', height=800)
        middle_frame.pack(fill="both", expand=1, padx=20, pady=20)

        # button1 = ttk.Button(self, text="StartPage",
        #                     command=lambda: controller.show_frame(StartPage))
        # button1.pack()

        # button to show frame 2 with text
        # layout2
        # label = ttk.Label(middle_frame, text="First, help me help you", font=LARGEFONT)
        # label.pack(anchor="w")
        label2 = ttk.Label(middle_frame, text="Which option describes you the best?", font=MEDIUMFONT)
        label2.pack(pady=40, anchor="w")
        button1 = ttk.Button(middle_frame, text="Next", style="big.TButton",
                             command=lambda: controller.show_frame(Page2))

        # putting the button in its place by
        # using grid

        var = tk.StringVar(self, "1")

        # Dictionary to create multiple buttons
        values = {"Quick Install with KDE Desktop (Choose this if your new to Linux)": "1",
                  "Quick Install with GNOME Desktop": "2",
                  "Advanced: Let me configure my applets later": "3"}

        # Loop is used to create multiple Radiobuttons
        # rather than creating each button separately
        for (text, value) in values.items():
            ttk.Radiobutton(middle_frame, text=text, variable=var,
                            value=value).pack(anchor="w", ipady=5)
        var.set("1")

        button1.pack(anchor="se", side="right", ipadx=15, padx=10)


# third window frame page2
class Page2(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        top_frame = tk.Frame(self, height=100, bg='yellow')
        top_frame.pack(fill="x", ipadx=10, ipady=10)

        left_frame = tk.Frame(self, width=200, bg='blue')
        left_frame.pack(fill="y", side="left", ipadx=10, ipady=10)

        middle_frame = tk.Frame(self, bg='cyan', height=800)
        middle_frame.pack(fill="both", expand=1, padx=20, pady=20)

        label2 = ttk.Label(middle_frame, text="Got it, what do you want me to do with Windows?", font=MEDIUMFONT)
        label2.pack(pady=40, anchor="w")

        button1 = ttk.Button(middle_frame, text="Next",
                             command=lambda: controller.show_frame(Page1))

        button2 = ttk.Button(middle_frame, text="Back",
                             command=lambda: controller.show_frame(Page1))

        var = tk.StringVar(self, "1")

        # Dictionary to create multiple buttons
        values = {"Remove Windows & migrate my Library (Music, Photos, Videos) to Linux": "1",
                  "Nuke Windows & all data(!) and start fresh with Linux": "2",
                  "Do nothing and let me partition later (Dual boot possible)": "3"}

        # Loop is used to create multiple Radiobuttons
        # rather than creating each button separately
        for (text, value) in values.items():
            ttk.Radiobutton(middle_frame, text=text, variable=var,
                            value=value).pack(anchor="w", ipady=5)

        button1.pack(anchor="se", side="right", ipadx=15, padx=10)
        button2.pack(anchor="se", side="right", padx=5)


win_width, win_height = 550, 400

# Driver Code
app = TkinterApp()
app.title("Lnixify")
app.geometry("800x500")
# app.wm_minsize(700, 400)
# app.wm_maxsize(1200, 800)
# app.iconbitmap("yourimage.ico")
app.resizable(False, False)
app.tk.call('tk', 'scaling', 2.0)
app.mainloop()
