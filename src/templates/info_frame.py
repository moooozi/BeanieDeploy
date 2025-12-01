from typing import Any

from tkinter_templates import *


class InfoFrame(ctk.CTkFrame):
    def __init__(self, parent, title=""):
        super().__init__(parent)
        self.configure(
            width=MINWIDTH,
            fg_color=colors.element_bg,
        )
        # Inner frame for padding
        self.inner_frame = ctk.CTkFrame(self, fg_color=colors.element_bg)
        self.inner_frame.pack(fill="both", expand=True, padx=(15, 10), pady=10)

        self.labels: dict[str, ctk.CTkLabel] = {}
        if title:
            title_label = TextLabel(
                self.inner_frame,
                text=title,
                text_color=colors.green,
                font=FONTS_smaller,
            )
            title_label.pack(anchor=multilingual.get_di_var().w, pady=(0, 5))

    def add_label(self, key: Any, text: str = "") -> None:
        label = ctk.CTkLabel(
            self.inner_frame, text=text, anchor=multilingual.get_di_var().w
        )
        label.pack(fill="x", pady=1)
        self.labels[key] = label

    def update_label(self, key: Any, text: str) -> None:
        if key in self.labels:
            self.labels[key].configure(text=text)
        else:
            msg = f"Label with key '{key}' does not exist."
            raise KeyError(msg)

    def flush_labels(self) -> None:
        for label in self.labels.values():
            label.pack_forget()
        self.labels.clear()
