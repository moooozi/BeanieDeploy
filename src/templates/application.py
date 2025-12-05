from config.settings import get_config
from tkinter_templates import *


class Application(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = get_config()
        self.title(config.app.name)  # Set window title to app name
        self.geometry(str(f"{WIDTH}x{HEIGHT}"))
        # self.minsize(MINWIDTH, MINHEIGHT)
        # self.maxsize(MAXWIDTH, MAXHEIGHT)
        self.iconbitmap(config.paths.app_icon_path)
        self.configure(fg_color=colors.background)
