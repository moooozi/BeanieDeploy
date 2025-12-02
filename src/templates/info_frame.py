from typing import Any

from tkinter_templates import *


class InfoFrame(ctk.CTkFrame):
    def __init__(self, parent, title="", bulleting=True, bullet_char="⚪"):
        super().__init__(parent)
        self.configure(
            width=MINWIDTH,
            fg_color=colors.element_bg,
        )
        self.bulleting = bulleting
        self.bullet_char = bullet_char

        # Inner frame for padding
        self.inner_frame = ctk.CTkContainer(self, bg_color=colors.element_bg)
        self.inner_frame.pack(fill="both", expand=True, padx=(15, 10), pady=10)

        self.labels: dict[str, ctk.CTkSimpleLabel] = {}
        if title:
            title_label = ctk.CTkSimpleLabel(
                self.inner_frame,
                text=title,
                text_color=colors.green,
                font=FONTS_smaller,
            )
            title_label.pack(anchor=multilingual.get_di_var().w, pady=(3, 5))

    def add_label(self, key: Any, text: str = "") -> None:
        if self.bulleting:
            text = self.bullet_char + " " + text
        label = ctk.CTkSimpleLabel(
            self.inner_frame, text=text, anchor=multilingual.get_di_var().w
        )
        label.pack(fill="x", pady=4)
        self.labels[key] = label

    def update_label(self, key: Any, text: str) -> None:
        if key in self.labels:
            if self.bulleting:
                text = self.bullet_char + " " + text
            self.labels[key].configure(text=text)
        else:
            msg = f"Label with key '{key}' does not exist."
            raise KeyError(msg)

    def flush_labels(self) -> None:
        for label in self.labels.values():
            label.pack_forget()
        self.labels.clear()
