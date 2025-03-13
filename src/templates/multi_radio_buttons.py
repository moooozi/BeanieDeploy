from tkinter_templates import *


class MultiRadioButtons(ctk.CTkFrame):
    def __init__(self, parent, items: dict, var, validate_func=None, *args, **kwargs):
        super().__init__(
            parent,
            bg_color="transparent",
            fg_color="transparent",
            *args,
            **kwargs,
        )
        self.var = var
        self.validate_func = validate_func
        self.items = items
        self.radio_buttons = {}
        self.advanced_frame = ctk.CTkFrame(
            self, bg_color="transparent", fg_color="transparent"
        )
        self.show_advanced_label = ctk.CTkLabel(
            self,
            text="Show advanced options",
            font=FONTS_smaller,
            text_color=color_blue,
            cursor="hand2",
        )
        self._create_widgets()

        if self.var.get() in self.items:
            print("var is in items and its value is", self.var.get())
            if self.items[self.var.get()].get("advanced", False):
                print("var is advanced")
                self.after(2000, self.show_advanced_options())

    def _create_widgets(self):
        if any(self.items[item].get("advanced", False) for item in self.items):
            self.show_advanced_label.grid(
                ipady=5, row=len(self.items) + 1, column=0, sticky="w"
            )
            self.show_advanced_label.bind(
                "<Button-1>", lambda e: self.show_advanced_options()
            )

        for index, item in enumerate(self.items.keys()):
            target_frame = (
                self.advanced_frame if self.items[item].get("advanced", False) else self
            )
            button = self._add_radio_btn(
                target_frame,
                self.items[item]["name"],
                self.var,
                item,
                command=lambda: self.validate_func(),
            )
            button.grid(ipady=5, row=index, column=0, sticky="nwe")
            self.radio_buttons[item] = button
            if "error" in self.items[item] and self.items[item]["error"]:
                button.configure(state="disabled")
                ctk.CTkLabel(
                    target_frame,
                    justify="center",
                    text=self.items[item]["error"],
                    font=FONTS_smaller,
                    text_color=color_red,
                ).grid(ipadx=5, row=index, column=1, sticky=multilingual.get_di_var().w)
                if self.var.get() == item:
                    self.var.set("")
            elif "description" in self.items[item] and self.items[item]["description"]:
                ctk.CTkLabel(
                    target_frame,
                    justify="center",
                    text=self.items[item]["description"],
                    font=FONTS_tiny,
                    text_color=color_blue,
                ).grid(ipadx=5, row=index, column=1, sticky=multilingual.get_di_var().w)
        self.grid_columnconfigure(0, weight=1)
        self.advanced_frame.grid_columnconfigure(0, weight=1)

    def show_advanced_options(self):
        self.advanced_frame.grid(row=len(self.items), column=0, sticky="w")
        self.show_advanced_label.grid_remove()

    def _add_radio_btn(self, parent, text, var, value, command=None):
        radio = ctk.CTkRadioButton(
            parent,
            text=text,
            variable=var,
            value=value,
        )
        if command:
            radio.configure(command=command)
        return radio
