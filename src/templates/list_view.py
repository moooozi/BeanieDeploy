from tkinter_templates import *

from .ctk_treeview import CTkTreeView


class ListView(CTkTreeView):
    def __init__(self, parent, *args, title="", **kwargs):
        super().__init__(parent, *args, title=title, **kwargs)
        self.selection_callback = None

        self.bind("<<TreeviewSelect>>", self._on_select)

    def destroy(self):
        super().destroy()

    def add_item(self, key, text=""):
        self.insert("", "end", iid=key, text=text)

    def preselect(self, key):
        self.selection_set(key)
        self.see(key)
        if self.selection_callback:
            self.selection_callback()

    def get_selected(self):
        selected = self.selection()
        return selected[0] if selected else None

    def clear(self):
        for item in self.get_children():
            self.delete(item)

    def bind_selection(self, callback):
        self.selection_callback = callback

    def set_selection(self, key):
        if key in self.get_children():
            self.selection_set(key)
            self.see(key)
