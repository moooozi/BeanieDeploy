import customtkinter as ctk

from tkinter_templates import *

from .ctk_treeview import CTkTreeView


class ListView(ctk.CTkFrame):
    def __init__(self, parent, title="", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.selection_callback = None

        if title:
            textlabel = ctk.CTkSimpleLabel(
                self,
                text=title,
                text_color=colors.green,
                font=FONTS_smaller,
            )
            textlabel.pack(anchor=multilingual.get_di_var().w, pady=10, padx=15)

        # Container frame for tree and scrollbar
        self.configure(fg_color=colors.element_bg)
        container = ctk.CTkContainer(self, bg_color=colors.element_bg)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.tree = CTkTreeView(container, show="tree")
        self.tree.configure(fg_color=colors.element_bg)
        self.tree.grid(row=0, column=0, sticky="nsew")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def destroy(self):
        super().destroy()

    def add_item(self, key, text=""):
        self.tree.insert("", "end", iid=key, text=text)

    def preselect(self, key):
        self.tree.selection_set(key)
        self.tree.see(key)
        if self.selection_callback:
            self.selection_callback()

    def get_selected(self):
        selected = self.tree.selection()
        return selected[0] if selected else None

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def bind_selection(self, callback):
        self.selection_callback = callback

    def set_selection(self, key):
        if key in self.tree.get_children():
            self.tree.selection_set(key)
            self.tree.see(key)

    def _on_select(self, _event):
        if self.selection_callback:
            self.selection_callback()
