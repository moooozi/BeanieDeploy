import tkinter.ttk as ttk

import customtkinter as ctk

from core.settings import get_config


class CTkTreeView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        title=None,
        show="tree",
        bulleting=False,
        bullet_char=("⚪",),
        multi_select=False,
        **kwargs,
    ):
        super().__init__(master, fg_color=get_config().ui.colors.element_bg, **kwargs)

        self.bulleting = bulleting
        self.bullet_char = bullet_char
        self.multi_select = multi_select

        if title:
            self.grid_rowconfigure(0, weight=0)  # for title
            self.grid_rowconfigure(1, weight=1)  # for container
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=0)

            self.title_frame = ctk.CTkContainer(self)
            self.title_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=10)
            self.title_frame.grid_columnconfigure(0, weight=0)
            self.title_frame.grid_columnconfigure(1, weight=0)

            self.original_title = title
            self.title_label = ctk.CTkSimpleLabel(
                self.title_frame,
                text=title,
                text_color=get_config().ui.colors.green,
                font=get_config().ui.fonts.smaller,
            )
            self.title_label.grid(row=0, column=0, sticky="w")

            if self.multi_select:
                self.count_label = ctk.CTkSimpleLabel(
                    self.title_frame, text="(0)", font=get_config().ui.fonts.smaller
                )
                self.count_label.grid(row=0, column=1, sticky="w", padx=(5, 0))
        else:
            self.grid_rowconfigure(0, weight=1)
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=0)

            if self.multi_select:
                self.count_label = ctk.CTkSimpleLabel(
                    self, text="(0)", font=get_config().ui.fonts.smaller
                )
                self.count_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)

        # Embed the ttk.Treeview
        self.tree = ttk.Treeview(self, show=show)  # type: ignore
        if self.multi_select:
            self.tree.configure(selectmode="extended")
        else:
            self.tree.configure(selectmode="browse")
        self.tree.grid(row=1, column=0, sticky="nsew")

        # Scrollbar (initially hidden)
        self.scrollbar = ctk.CTkScrollbar(self, command=self.tree.yview)
        self._scrollbar_needs_shown = False
        self.tree.configure(yscrollcommand=self._scrollbar_set)
        self._scrollbar_visible = False
        # Don't grid the scrollbar initially - will be shown only when needed

        # Apply initial theming and scaling
        self._update_appearance()

        # Bind for selection events
        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Configure>", self._on_configure)
        self.tree.bind("<Map>", self._on_map)
        self.tree.bind("<<TreeviewOpen>>", self._on_expand)
        self.tree.bind("<<TreeviewClose>>", self._on_collapse)
        self.selection_callback = None

    def _scrollbar_set(self, first, last):
        """Custom scrollbar set method that tracks if scrolling is needed."""
        # Call the scrollbar's set method
        self.scrollbar.set(first, last)

        # Calculate needs_scrolling based on content height vs visible height
        rowheight = self._apply_widget_scaling(32)
        total_height = self._count_visible_items() * rowheight
        visible_height = self.tree.winfo_height()
        needs_scrolling = total_height > visible_height

        if needs_scrolling and not self._scrollbar_visible:
            # Show scrollbar
            self.scrollbar.grid(row=1, column=1, sticky="ns", padx=(0, 1))
            self._scrollbar_visible = True
        elif not needs_scrolling and self._scrollbar_visible:
            # Hide scrollbar
            self.scrollbar.grid_remove()
            self._scrollbar_visible = False

    def _count_visible_items(self, item=""):
        """Recursively count all visible items in the treeview."""
        count = 0
        for child in self.tree.get_children(item):
            count += 1
            if self.tree.item(child, "open"):
                count += self._count_visible_items(child)
        return count

    def _get_depth(self, item):
        """Get the depth of an item in the tree."""
        depth = 0
        while item:
            item = self.tree.parent(item)
            depth += 1
        return depth

    def _update_appearance(self):
        # Apply CTk theme colors and scaling
        bg_color = self._apply_appearance_mode(self.cget("fg_color"))
        text_color = self._apply_appearance_mode(
            ctk.ThemeManager.theme["CTkLabel"]["text_color"]
        )
        selected_color = self._apply_appearance_mode(
            ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        )

        base_font = ctk.CTkFont(size=14)
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
            background=[("selected", get_config().ui.colors.element_bg_hover[mode])],
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
        if self.bulleting and "text" in kwargs:
            depth = self._get_depth(parent)
            bullet = self.bullet_char[depth % len(self.bullet_char)]
            kwargs["text"] = bullet + " " + kwargs["text"]
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

    def _on_click(self, event):
        if self.multi_select:
            item = self.tree.identify_row(event.y)
            if item:
                current_selection = set(self.tree.selection())
                if item in current_selection:
                    current_selection.remove(item)
                else:
                    current_selection.add(item)
                self.tree.selection_set(list(current_selection))
                self._on_select(event)
            return "break"
        return None

    def _on_select(self, event):
        if self.multi_select:
            selected_count = len(self.tree.selection())
            self.count_label.configure(text=f"({selected_count})")
        if self.selection_callback:
            self.selection_callback(event)
        selected = self.tree.selection()
        if selected:
            self.tree.see(selected[0])

    def _on_expand(self, _event):
        self.update_scrollbar_visibility()

    def _on_collapse(self, _event):
        self.update_scrollbar_visibility()

    def expand_all(self):
        """Expand all items in the treeview."""

        def _expand_recursive(item):
            self.tree.item(item, open=True)
            for child in self.tree.get_children(item):
                _expand_recursive(child)

        for item in self.tree.get_children():
            _expand_recursive(item)
        self.update_scrollbar_visibility()

    def yview(self, *args):
        return self.tree.yview(*args)

    def update_scrollbar_visibility(self):
        """Public method to force scrollbar visibility update."""
        first, last = self.tree.yview()
        self._scrollbar_set(first, last)

    def add_item(self, key, text=""):
        self.insert("", "end", iid=key, text=text)

    def get_selected(self):
        selected = self.selection()
        return selected[0] if selected else None

    def preselect(self, key):
        if key in self.get_children():
            self.selection_set(key)
            self.see(key)
            if self.selection_callback:
                self.selection_callback()

    def clear(self):
        for item in self.get_children():
            self.delete(item)

    def bind_selection(self, callback):
        self.selection_callback = callback
