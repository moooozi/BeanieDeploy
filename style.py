from sys import executable, argv
from pathlib import Path
from ctypes import windll

MAXWIDTH = 800
MAXHEIGHT = 500
LARGEFONT = ("Ariel", 24)
MEDIUMFONT = ("Ariel Bold", 15)
SMALLFONT = ("Ariel", 12)
VERYSMALLFONT = ("Ariel", 10)
top_background = '#474747'
CURRENT_DIR = str(Path(__file__).parent.absolute())


def clear_frame(frame):
    """removes all elements inside the middle frame, which contains all page-specific content"""
    for widgets in frame.winfo_children():
        widgets.destroy()


def get_admin():
    if not windll.shell32.IsUserAnAdmin():
        windll.shell32.ShellExecuteW(None, "runas", executable, " ".join(argv), None, 1)
        quit()


