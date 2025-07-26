from tkinter_templates import *
from tkinter import ttk
import customtkinter as ctk

class ListView(ctk.CTkFrame):
    def __init__(self, parent, title="", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.selection_callback = None
        self._configure_binding = None
        self._last_scaling_params = None

        if title:
            textlabel = ctk.CTkLabel(
                self,
                text=title,
                text_color=color_green,
                font=FONTS_smaller,
            )
            textlabel.pack(anchor=multilingual.get_di_var().w, pady=5, padx=10)

        # Container frame for tree and scrollbar
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(container, show="tree")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree_scrollbar = ctk.CTkScrollbar(container, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scrollbar.set)
        self.tree_scrollbar.grid(row=0, column=1, sticky="ns")

        self._update_scaling() # DPI Awareness
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Bind to root window <Configure> event for live DPI awareness workaround
        root = self.winfo_toplevel()
        self._configure_binding = root.bind('<Configure>', lambda e: self._update_scaling(), add='+')

    def destroy(self):
        # Unbind the <Configure> event
        root = self.winfo_toplevel()
        if self._configure_binding is not None:
            root.unbind('<Configure>', self._configure_binding)
            self._configure_binding = None
        super().destroy()

    def _update_scaling(self, *args, **kwargs):
        # Apply CustomTkinter theme colors and large font to Treeview
        bg_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        text_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        selected_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])

        base_font = ctk.CTkFont(size=16)
        scaled_font = self._apply_font_scaling(base_font)
        if isinstance(scaled_font, tuple):
            font_tuple = scaled_font
        else:
            font_tuple = (scaled_font.cget("family"), scaled_font.cget("size"))
        rowheight = self._apply_widget_scaling(32)

        scaling_params = (bg_color, text_color, selected_color, font_tuple, rowheight)
        if hasattr(self, '_last_scaling_params') and self._last_scaling_params == scaling_params:
            return  # No change, skip update
        self._last_scaling_params = scaling_params

        style = ttk.Style()
        style.theme_use('default')
        style.configure("Custom.Treeview", 
                        background=bg_color, 
                        foreground=text_color, 
                        fieldbackground=bg_color, 
                        borderwidth=0,
                        font=font_tuple,
                        rowheight=rowheight)
        style.map('Custom.Treeview', 
                  background=[('selected', bg_color)], 
                  foreground=[('selected', selected_color)])
        self.tree.configure(style="Custom.Treeview")

    def add_item(self, key, text=""):
        self.tree.insert("", "end", iid=key, text=text)

    def on_click(self, key):
        self.tree.selection_set(key)
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

    def _on_select(self, event):
        if self.selection_callback:
            self.selection_callback()
