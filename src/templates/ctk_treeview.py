import tkinter.ttk as ttk

import customtkinter as ctk

from tkinter_templates import colors


class CTkTreeView(ctk.CTkFrame):
    def __init__(self, master, show="tree", **kwargs):
        super().__init__(master, **kwargs)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        # Embed the ttk.Treeview
        self.tree = ttk.Treeview(self, show=show)  # type: ignore
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbar
        self.scrollbar = ctk.CTkScrollbar(self, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # Apply initial theming and scaling
        self._update_appearance()

        # Bind for selection events (customize as needed)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.selection_callback = None

    def _update_appearance(self):
        # Apply CTk theme colors and scaling
        bg_color = self._apply_appearance_mode(self.cget("fg_color"))
        text_color = self._apply_appearance_mode(
            ctk.ThemeManager.theme["CTkLabel"]["text_color"]
        )
        selected_color = self._apply_appearance_mode(
            ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        )

        base_font = ctk.CTkFont(size=16)
        scaled_font = self._apply_font_scaling(base_font)
        font_tuple = (
            scaled_font
            if isinstance(scaled_font, tuple)
            else (scaled_font.cget("family"), scaled_font.cget("size"))
        )
        rowheight = self._apply_widget_scaling(32)

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "CTk.Treeview",
            background=bg_color,
            foreground=text_color,
            fieldbackground=bg_color,
            borderwidth=0,
            font=font_tuple,
            rowheight=rowheight,
        )
        mode = int(self._get_appearance_mode() == "dark")
        style.map(
            "CTk.Treeview",
            background=[("selected", colors.element_bg_hover[mode])],
            foreground=[("selected", selected_color)],
        )
        self.tree.configure(style="CTk.Treeview")

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)
        if not no_color_updates:
            self._update_appearance()

    # Proxy methods to make it behave like ttk.Treeview
    def insert(self, parent, index, iid=None, **kwargs):
        return self.tree.insert(parent, index, iid=iid, **kwargs)

    def delete(self, *items):
        self.tree.delete(*items)

    def get_children(self, item=""):
        return self.tree.get_children(item)

    def selection(self):
        return self.tree.selection()

    def selection_set(self, *items):
        self.tree.selection_set(*items)

    def see(self, item):
        self.tree.see(item)

    def bind(self, sequence=None, command=None, add=None):
        # Override to prevent binding issues; use tree.bind for Treeview-specific events
        if sequence == "<<TreeviewSelect>>":
            if add is not None:
                self.tree.bind(sequence, command, add=add)
            else:
                self.tree.bind(sequence, command)
        else:
            if add is not None:
                super().bind(sequence, command, add=add)
            else:
                super().bind(sequence, command)

    def _on_select(self, event):
        if self.selection_callback:
            self.selection_callback(event)
        selected = self.tree.selection()
        if selected:
            self.tree.see(selected[0])

    def configure(self, require_redraw=False, **kwargs):
        if "yscrollcommand" in kwargs:
            self.tree.configure(yscrollcommand=kwargs.pop("yscrollcommand"))
        super().configure(require_redraw=require_redraw, **kwargs)

    def yview(self, *args):
        return self.tree.yview(*args)
