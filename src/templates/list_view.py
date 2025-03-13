from tkinter_templates import *


class ListView(ctk.CTkFrame):
    def __init__(self, parent, title="", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.labels = {}
        self.selected_label = None
        self.original_colors_text = {}
        self.original_colors_fg = {}
        self.selection_callback = None

        self.canvas = ctk.CTkCanvas(
            self,
            background=self.cget("fg_color")[1],
            highlightthickness=0,
            confine=True,
        )
        self.scrollbar = ctk.CTkScrollbar(self, command=self.canvas.yview)
        self.scrollable_frame = ctk.CTkFrame(
            self.canvas,
        )

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # Configure the grid layout to make the scrollable frame expand
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_rowconfigure(0, weight=1)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        if title:
            textlabel = add_text_label(
                self.scrollable_frame,
                title,
                anchor=multilingual.get_di_var().w,
                pady=5,
                padx=4,
                foreground=color_green,
                font=FONTS_smaller,
                pack=False,
            )
            textlabel.grid(sticky=multilingual.get_di_var().w, pady=5, padx=10)

    def add_item(self, key, text=""):
        label = ctk.CTkLabel(
            self.scrollable_frame,
            text=text,
            anchor=multilingual.get_di_var().w,
            cursor="hand2",
        )
        label.grid(sticky="ew", pady=2, padx=10)
        self.labels[key] = label
        self.original_colors_text[key] = label.cget("text_color")
        self.original_colors_fg[key] = label.cget("fg_color")

        label.bind("<Button-1>", lambda e, k=key: self.on_click(k))
        label.bind("<Enter>", lambda e, l=label: self.on_hover(l))
        label.bind("<Leave>", lambda e, l=label: self.on_leave(l, key))

    def on_click(self, key):
        if self.selected_label:
            self.selected_label.configure(
                text_color=self.original_colors_text[self.get_selected()]
            )
        self.selected_label = self.labels[key]
        self.selected_label.configure(text_color=("blue", "lightblue"))
        if self.selection_callback:
            self.selection_callback()

    def on_hover(self, label):
        if label != self.selected_label:
            label.configure(fg_color=("lightgray", "grey"))

    def on_leave(self, label, key):
        if label != self.selected_label:
            label.configure(fg_color=self.original_colors_fg[key])

    def get_selected(self):
        return next(
            (k for k, v in self.labels.items() if v == self.selected_label), None
        )

    def clear(self):
        for label in self.labels.values():
            label.grid_forget()
        self.labels.clear()
        self.selected_label = None
        self.original_colors_text.clear()
        self.original_colors_fg.clear()

    def bind_selection(self, callback):
        self.selection_callback = callback

    def set_selection(self, key):
        if key in self.labels:
            self.on_click(key)
            self.canvas.yview_moveto(
                self.labels[key].winfo_y() / self.scrollable_frame.winfo_height()
            )
