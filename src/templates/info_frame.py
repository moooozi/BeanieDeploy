from tkinter_templates import *


class InfoFrame(ctk.CTkFrame):
    def __init__(self, parent, title=""):
        super().__init__(parent)
        self.labels = {}
        if title:
            title_label = TextLabel(
                self,
                text=title,
                foreground=color_green,
                font=FONTS_smaller,
            )
            title_label.pack(anchor=multilingual.get_di_var().w, pady=5, padx=4)

    def add_label(self, key, text=""):
        label = ctk.CTkLabel(self, text=text, anchor=multilingual.get_di_var().w)
        label.pack(fill="x", pady=2, padx=10)
        self.labels[key] = label

    def update_label(self, key, text):
        if key in self.labels:
            self.labels[key].configure(text=text)
        else:
            raise KeyError(f"Label with key '{key}' does not exist.")

    def flush_labels(self):
        for label in self.labels.values():
            label.pack_forget()
        self.labels.clear()
