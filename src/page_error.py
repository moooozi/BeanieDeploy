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

        self.error_labels = []  # List to store error labels

        self.info_frame = ctk.CTkFrame(self.page_frame)
        self.info_frame.pack(fill="both", expand=True, pady=5, padx=10)

        # Configure grid weights for the parent container and page_frame
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.page_frame.grid_columnconfigure(0, weight=1)
        self.page_frame.grid_rowconfigure(0, weight=1)

    def set_errors(self, errors):
        self.errors = errors
        for label in self.error_labels:
            label.destroy()  # Remove existing labels

        self.error_labels = []  # Clear the list

        for error in self.errors:
            error_label = ctk.CTkLabel(self.info_frame, text=error, anchor="w")
            error_label.pack(fill="x", pady=2)
            self.error_labels.append(error_label)
