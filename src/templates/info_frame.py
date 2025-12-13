from typing import Any

import vgkit as vgk

import multilingual
from core.settings import get_config


class InfoFrame(vgk.Container):
    def __init__(self, parent, title="", bulleting=True, bullet_char="⚪"):
        super().__init__(parent)
        self.configure(
            width=get_config().ui.width,
            fg_color=get_config().ui.colors.element_bg,
        )
        self.bulleting = bulleting
        self.bullet_char = bullet_char

        # Inner frame for padding
        self.inner_frame = vgk.Frame(self)
        self.inner_frame.pack(fill="both", expand=True, padx=(15, 10), pady=10)

        self.labels: dict[str, vgk.Label] = {}
        if title:
            title_label = vgk.Label(
                self.inner_frame,
                text=title,
                text_color=get_config().ui.colors.green,
                font=get_config().ui.fonts.smaller,
            )
            title_label.pack(anchor=multilingual.get_di_var().w, pady=(3, 5))

    def add_label(self, key: Any, text: str = "") -> None:
        if self.bulleting and text:
            text = self.bullet_char + " " + text
        label = vgk.Label(
            self.inner_frame,
            text=text,
            anchor=multilingual.get_di_var().w,
            justify=multilingual.get_di_var().l,
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
