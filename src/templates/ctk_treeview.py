import tkinter.ttk as ttk

import customtkinter as ctk

import multilingual
from tkinter_templates import MINWIDTH, FONTS_smaller, colors


class CTkTreeView(ctk.CTkFrame):
    def __init__(self, master, title=None, show="tree", **kwargs):
        super().__init__(master, **kwargs)
        self.configure(width=MINWIDTH, fg_color=colors.element_bg)
        # Inner frame for padding

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

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
        container.grid_columnconfigure(1, weight=0)

        # Embed the ttk.Treeview
        self.tree = ttk.Treeview(container, show=show)  # type: ignore
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbar (initially hidden)
        self.scrollbar = ctk.CTkScrollbar(container, command=self.tree.yview)
        self._scrollbar_needs_shown = False
        self.tree.configure(yscrollcommand=self._scrollbar_set)
        self._scrollbar_visible = False
        # Don't grid the scrollbar initially - will be shown only when needed

        # Apply initial theming and scaling
        self._update_appearance()

        # Bind for selection events
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Configure>", self._on_configure)
        self.tree.bind("<Map>", self._on_map)
        self.selection_callback = None

    def _scrollbar_set(self, first, last):
        """Custom scrollbar set method that tracks if scrolling is needed."""
        # Call the scrollbar's set method
        self.scrollbar.set(first, last)

        # Calculate needs_scrolling based on content height vs visible height
        rowheight = self._apply_widget_scaling(32)
        total_height = len(self.get_children()) * rowheight
        visible_height = self.tree.winfo_height()
        needs_scrolling = total_height > visible_height

        if needs_scrolling and not self._scrollbar_visible:
            # Show scrollbar
            self.scrollbar.grid(row=0, column=1, sticky="ns")
            self._scrollbar_visible = True
        elif not needs_scrolling and self._scrollbar_visible:
            # Hide scrollbar
            self.scrollbar.grid_remove()
            self._scrollbar_visible = False

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
        if hasattr(self, "tree"):
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

    def see(self, item=None):
        if item is None:
            # get selected item
            item = self.selection()[0]
            if not item:
                return
        self.tree.see(item)

    def bind(self, sequence=None, command=None, add=None):
        # Override to prevent binding issues; use tree.bind for Treeview-specific events
        treeview_events = [
            "<<TreeviewSelect>>",
            "<<TreeviewOpen>>",
            "<<TreeviewClose>>",
        ]
        if sequence in treeview_events:
            if add is not None:
                self.tree.bind(sequence, command, add=add)
            else:
                self.tree.bind(sequence, command)
        else:
            if add is not None:
                super().bind(sequence, command, add=add)
            else:
                super().bind(sequence, command)

    def _on_configure(self, _event):
        self.update_scrollbar_visibility()

    def _on_map(self, _event):
        self.update_scrollbar_visibility()

    def _on_select(self, event):
        if self.selection_callback:
            self.selection_callback(event)
        selected = self.tree.selection()
        if selected:
            self.tree.see(selected[0])

    def expand_all(self):
        """Expand all items in the treeview."""

        def _expand_recursive(item):
            self.tree.item(item, open=True)
            for child in self.tree.get_children(item):
                _expand_recursive(child)

        for item in self.tree.get_children():
            _expand_recursive(item)

    def yview(self, *args):
        return self.tree.yview(*args)

    def update_scrollbar_visibility(self):
        """Public method to force scrollbar visibility update."""
        self._scrollbar_set(0, 1)
