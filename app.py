import tkinter as tk
from tkinter import ttk
import webbrowser
import subprocess
import powershell
import concurrent.futures

LARGEFONT = ("Ariel", 20)
MEDIUMFONT = ("Ariel", 16)
SMALLFONT = ("Ariel", 12)


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
        for F in (PageCheck, PageError, Page1, Page2):
            frame = F(container, self)

            # initializing frame of that object from
            # startpage, page1, page2 respectively with
            # for loop
            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(PageCheck)

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

        # def start_test():
        #    p1 = controller.show_frame(PageCheck)
        #    p2 = PageCheck.compatibility_test(self)
        #    p1.start()
        #    p2.start()
        # Top Frame Content
        # img_app_logo = tk.PhotoImage(file="appLogo.png")
        # btn_app_logo = tk.Label(top_frame, image=img_app_logo, cursor="hand2")
        # url1 = 'https://www.kernel.org/'
        # btn_app_logo.pack(side="left")
        # btn_app_logo.bind("<Button-1>", lambda e: open_url(url1))

        # text_moto = tk.Label(top_frame, text="Free as in Freedom")
        # text_moto.pack(side="left")

        # img_suse = tk.PhotoImage(file="Suse-logo.png")
        # btn_suse = tk.Label(top_frame, image=img_suse, cursor="hand2")
        # url2 = 'https://www.opensuse.org/'
        # btn_suse.pack(side="right")
        # btn_suse.bind("<Button-1>", lambda e: open_url(url2))

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
        label3 = ttk.Label(middle_frame, text="Compatibility Check Passed!", font=MEDIUMFONT)
        label4 = ttk.Label(middle_frame, text="Compatibility Check Failed!", font=MEDIUMFONT)

        pb_hD = ttk.Progressbar(middle_frame, orient='horizontal', length=500, mode='indeterminate')

        label2.pack(pady=40, anchor="w")
        pb_hD.pack(expand=True)

        pb_hD.start(10)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self.compatibility_test)
            compatibility_results = future.result()
        button1 = ttk.Button(middle_frame, text="Next",
                             command=lambda: controller.show_frame(Page1))

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
            label4.pack(pady=40, anchor="nw")
            errors = []

            if compatibility_results['result_uefi_check'] == 0:
                errors.append('Your system does not support (or is not using) UEFI boot.')
            if compatibility_results['result_uefi_check'] == 9:
                errors.append("UEFI boot support could not be verified.")
            if compatibility_results['result_totalram_check'] == 0:
                errors.append("Your system does not have sufficient RAM capacity.")
            if compatibility_results['result_totalram_check'] == 9:
                errors.append("Failed to check available RAM capacity.")
            if compatibility_results['result_space_check'] == 0:
                errors.append("Not enough disk space on your system drive.")
            if compatibility_results['result_space_check'] == 9:
                errors.append("Failed to check available disk space on your system drive.")
            if compatibility_results['result_resizable_check'] == 9:
                errors.append("Failed to check system drive resizability.")
            if compatibility_results['result_resizable_check'] == 0:
                errors.append("Not enough shrink room on system drive.")

            label5 = ttk.Label(middle_frame, text=("\n".join(errors)), font=SMALLFONT)
            label5.pack(padx=10, anchor="w")
            button2.pack(anchor="se", side="right", ipadx=15, padx=10)

    def compatibility_test(self):

        print('hey')
        required_space_min = 900 * 1024 * 1024
        required_space_dualboot = required_space_min + 70 * 1024 * 1024 * 1024
        required_ram = 4

        def check_uefi():
            return subprocess.run([r'powershell.exe', r'$env:firmware_type'], stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, shell=True)

        def check_totalram():
            return subprocess.run([r'powershell.exe',
                                   r'(Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property capacity -Sum).sum /1gb'],
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

        def check_space():
            return subprocess.run([r'powershell.exe',
                                   r'(Get-Volume | Where DriveLetter -eq $env:SystemDrive.Substring(0, 1)).SizeRemaining'],
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

        def check_resizable():
            return subprocess.run([r'powershell.exe',
                                   r'((Get-Volume | Where DriveLetter -eq $env:SystemDrive.Substring(0, 1)).Size - (Get-PartitionSupportedSize -DriveLetter $env:SystemDrive.Substring(0, 1)).SizeMin)'],
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

        totalram = int(check_totalram().stdout)
        result_resizable_check = 0
        if check_totalram().returncode != 0:
            result_totalram_check = 9
        elif totalram >= required_ram:
            result_totalram_check = 1
        else:
            result_totalram_check = 0
        if check_uefi().returncode != 0:
            result_uefi_check = 9
        elif b'uefi' in check_uefi().stdout.lower():
            result_uefi_check = 1
        else:
            result_uefi_check = 0

        if check_space().returncode != 0:
            result_space_check = 9

        space_available = int(str(check_space().stdout)[2:-5])

        if space_available > required_space_dualboot:
            result_space_check = 2
        elif space_available > required_space_min:
            result_space_check = 1
        else:
            result_space_check = 0

        if result_space_check in (1, 2):
            if check_resizable().returncode != 0:
                result_resizable_check = 9
            elif int(str(check_resizable().stdout)[2:-5]) > required_space_min:
                result_resizable_check = 1
            else:
                result_resizable_check = 0
        else:
            result_resizable_check = 8
        check_results = {'result_uefi_check': result_uefi_check,
                         'result_totalram_check': result_totalram_check,
                         'result_space_check': result_space_check,
                         'result_resizable_check': result_resizable_check}
        return check_results


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


class PageError(tk.Frame):

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
        label2 = ttk.Label(middle_frame, text="Could not complete compatibility test", font=MEDIUMFONT)
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
