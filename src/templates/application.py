import multiprocessing
import queue
from tkinter_templates import *
from config.settings import get_config


class Application(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = get_config()
        self.title(config.app.name)  # Set window title to app name
        dpi_factor = get_dpi_scaling_factor()
        self.geometry(str("%sx%s+%s+%s" % (WIDTH, HEIGHT, WIDTH_OFFSET, HEIGHT_OFFSET)))
        self.minsize(MINWIDTH, MINHEIGHT)
        self.maxsize(int(MAXWIDTH * dpi_factor), int(MAXHEIGHT * dpi_factor))
        self.iconbitmap(config.paths.app_icon_path)

        dark_theme(DARK_MODE, self)

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
