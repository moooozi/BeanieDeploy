MAXWIDTH = 800
MAXHEIGHT = 500
LARGEFONT = ("Ariel", 24)
MEDIUMFONT = ("Ariel Bold", 15)
SMALLFONT = ("Ariel", 12)
VERYSMALLFONT = ("Ariel", 10)
top_background = '#474747'


def clear_frame(frame):
    """removes all elements inside the middle frame, which contains all page-specific content"""
    for widgets in frame.winfo_children():
        widgets.destroy()
