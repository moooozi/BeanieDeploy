from templates.generic_page_layout import GenericPageLayout
import tkinter_templates as tkt
import functions as fn
from page_manager import Page
import customtkinter as ctk  # Added import for customtkinter
import time


class PagePlayground(Page):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

    def init_page(self):
        page_layout = GenericPageLayout(
            self,
            "Hello, this is a playground page!",
            secondary_btn_txt=self.LN.btn_quit,
            secondary_btn_command=lambda: fn.app_quit(),
        )
        self.page_frame = page_layout.content_frame

        tkt.add_text_label(self.page_frame, "This is a label", pady=10)

        self.progressbar = ctk.CTkProgressBar(self.page_frame, mode="determinate")
        self.progressbar.pack(pady=10)
        self.progressbar.set(0)
        # add 0.1 to the progressbar each 500ms
        for i in range(101):
            self.progressbar.set(i * 0.01)
            time.sleep(0.5)
            self.update()
