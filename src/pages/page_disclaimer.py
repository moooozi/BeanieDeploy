import tkinter as tk

import vgkit as vgk

from models.page import Page, PageValidationResult
from multilingual import _


class PageDisclaimer(Page):
    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)

    def init_page(self):
        self.page_manager.set_title(_("disclaimer.title"))
        self.page_manager.set_primary_button(
            _("btn.run_compatibility_check"), state="disabled"
        )

        self.columnconfigure(0, weight=1)

        # Disclaimer text
        disclaimer_text = _("disclaimer.text")

        info_frame = vgk.Container(
            self,
            fg_color=self._ui.colors.element_bg,
        )
        info_label = vgk.Label(
            info_frame,
            text=disclaimer_text,
            justify=self._ui.di.l,
            font=self._ui.fonts.smaller,
            wraplength="self",
        )
        info_label.pack(
            fill="x",
            expand=True,
            padx=10,
        )
        info_frame.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=8)

        self.accept_disclaimer_var = tk.BooleanVar(value=False)
        checkbox = vgk.CheckBox(
            self,
            text=_("checkbox.accept.disclaimer"),
            variable=self.accept_disclaimer_var,
            onvalue=True,
            offvalue=False,
            command=self._on_checkbox_change,
        )
        checkbox.grid(row=1, column=0, sticky="w", pady=20)
        self.grid_rowconfigure(1, weight=1)

    def _on_checkbox_change(self):
        """Enable or disable the primary button based on checkbox state."""
        state = "normal" if self.accept_disclaimer_var.get() else "disabled"
        self.page_manager.set_primary_button(state=state)

    def validate_input(self) -> PageValidationResult:
        """Validate that the disclaimer has been accepted."""
        if not self.accept_disclaimer_var.get():
            return PageValidationResult(False, _("checkbox.accept.disclaimer"))
        return PageValidationResult(True)

    def on_next(self):
        """Destroy the disclaimer page when proceeding."""
        self.destroy()
