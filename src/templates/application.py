import multiprocessing
import queue

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

    def wait_and_handle_queue_output(
        self,
        output_queue: multiprocessing.Queue,
        callback,
        frequency=100,
        retry_count=0,
    ):
        try:
            while not output_queue.empty():
                output = output_queue.get_nowait()
                callback(output)
        except queue.Empty:
            if retry_count:
                self.after(
                    frequency,
                    self.wait_and_handle_queue_output,
                    output_queue,
                    callback,
                    frequency,
                    retry_count - 1,
                )
