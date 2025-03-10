import tkinter_templates as tkt
import globals as GV
import functions as fn
from page_manager import Page
import customtkinter as ctk  # Added import for customtkinter


class PageError(Page):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.errors = []

    def init_page(self):
        self.page_frame = tkt.generic_page_layout(
            self,
            self.LN.error_title % GV.APP_SW_NAME,
            secondary_btn_txt=self.LN.btn_quit,
            secondary_btn_command=lambda: fn.app_quit(),
        )

        tkt.add_text_label(self.page_frame, self.LN.error_list, pady=10)

        self.info_frame_raster = tkt.InfoFrameRaster(self.page_frame)
        self.info_frame_raster.pack(fill="x", pady=5, padx=10)

    def set_errors(self, errors):
        self.errors = errors
        self.info_frame_raster.flush_labels()  # Clear existing labels

        for i, error in enumerate(self.errors):
            self.info_frame_raster.add_label(f"error_{i}", error)
