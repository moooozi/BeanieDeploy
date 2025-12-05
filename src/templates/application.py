import customtkinter as ctk

from config.settings import get_config


class Application(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = get_config()
        self.title(config.app.name)  # Set window title to app name
        self.geometry(str(f"{config.ui.width}x{config.ui.height}"))
        # self.minsize(MINWIDTH, MINHEIGHT)
        # self.maxsize(MAXWIDTH, MAXHEIGHT)
        self.iconbitmap(config.paths.app_icon_path)
        self.configure(fg_color=config.ui.colors.background)
