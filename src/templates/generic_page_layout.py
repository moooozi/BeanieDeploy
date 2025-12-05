from config.settings import get_config
from tkinter_templates import *


class GenericPageLayout(ctk.CTkContainer):
    def __init__(
        self,
        parent,
        title=None,
        primary_btn_txt=None,
        primary_btn_command=None,
        secondary_btn_txt=None,
        secondary_btn_command=None,
        title_pady=20,
        *args,
        **kwargs,
    ):
        super().__init__(
            parent,
            *args,
            **kwargs,
        )
        self.title = title
        self.primary_btn_txt = primary_btn_txt
        self.primary_btn_command = primary_btn_command
        self.secondary_btn_txt = secondary_btn_txt
        self.secondary_btn_command = secondary_btn_command
        self.title_pady = title_pady
        self.content_frame = ctk.CTkContainer(self)

        if self.title:
            self._title_widget = self.add_page_title(self.title)
        if self.primary_btn_txt or self.secondary_btn_txt:
            self.bottom_frame = ctk.CTkContainer(self, height=34)
            self.bottom_frame.grid(row=2, column=0, sticky="ew")
            self.bottom_frame.grid_propagate(False)
            if self.primary_btn_txt:
                self.add_primary_btn(
                    self.bottom_frame, self.primary_btn_txt, self.primary_btn_command
                )
            if self.secondary_btn_txt:
                self.add_secondary_btn(
                    self.bottom_frame,
                    self.secondary_btn_txt,
                    self.secondary_btn_command,
                )
        self.content_frame.grid(
            row=1, column=0, pady=self.title_pady, padx=(20, 20), sticky="nsew"
        )

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        # Set a specific size for the frame
        self.pack(expand=1, fill="both")

    def add_primary_btn(self, parent, text, command):
        """
        a preset for adding a CustomTkinter button. Used for the likes of "Next" and "Install" buttons
        :return: CustomTkinter button object
        """
        btn_next = ctk.CTkButton(parent, text=text, command=command)
        btn_next.pack(
            anchor=multilingual.get_di_var().se,
            side=multilingual.get_di_var().r,
            ipadx=22,
            padx=0,
        )
        return btn_next

    def add_secondary_btn(self, parent, text, command):
        """
        a preset for adding a CustomTkinter button. Used for the likes of "Back", "Cancel" and "Abort" buttons
        :return: CustomTkinter button object
        """
        btn_back = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            fg_color=colors.btn_background,
            hover_color=colors.btn_background_hover,
            text_color=colors.btn_background_txt,
        )
        btn_back.pack(
            anchor=multilingual.get_di_var().se,
            side=multilingual.get_di_var().r,
            padx=12,
            ipadx=8,
        )
        return btn_back

    def add_page_title(self, text, pady=(40, 5)):
        config = get_config()
        title = ctk.CTkSimpleLabel(
            self,
            wraplength=config.ui.max_width,
            justify=multilingual.get_di_var().l,
            text=text,
            font=FONTS_medium,
        )
        title.grid(
            row=0,
            column=0,
            pady=pady,
            padx=0,
            sticky="",
        )
        return title

    def set_page_title(self, text):
        """Set or update the page title."""
        if hasattr(self, "_title_widget"):
            self._title_widget.configure(text=text)
        else:
            self._title_widget = self.add_page_title(text)
