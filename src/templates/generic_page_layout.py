import customtkinter as ctk

from config.settings import get_config


class GenericPageLayout:
    def __init__(
        self,
        container,
        title=None,
        primary_btn_txt=None,
        primary_btn_command=None,
        secondary_btn_txt=None,
        secondary_btn_command=None,
        title_pady=20,
    ):
        self.container = container
        self.title = title
        self.primary_btn_txt = primary_btn_txt
        self.primary_btn_command = primary_btn_command
        self.secondary_btn_txt = secondary_btn_txt
        self.secondary_btn_command = secondary_btn_command
        self.title_pady = title_pady
        self.content_frame = ctk.CTkContainer(self.container)
        self._ui = get_config().ui

        if self.title:
            self._title_widget = self.add_page_title(self.title)
        if self.primary_btn_txt or self.secondary_btn_txt:
            if self.primary_btn_txt:
                self.add_primary_btn(
                    self.container, self.primary_btn_txt, self.primary_btn_command
                )
            if self.secondary_btn_txt:
                self.add_secondary_btn(
                    self.container,
                    self.secondary_btn_txt,
                    self.secondary_btn_command,
                )
        self.content_frame.grid(
            row=1,
            column=0,
            columnspan=3,
            pady=self.title_pady,
            padx=self._ui.margin_side,
            sticky="nsew",
        )

        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(1, weight=1)
        self.container.grid_rowconfigure(2, weight=0)

    def add_primary_btn(self, parent, text, command):
        """
        a preset for adding a CustomTkinter button. Used for the likes of "Next" and "Install" buttons
        :return: CustomTkinter button object
        """
        btn_next = ctk.CTkButton(parent, text=text, command=command, corner_radius=20)
        btn_next.grid(
            row=2,
            column=2,
            ipadx=15,
            padx=(0, self._ui.margin_side),
            pady=(0, self._ui.margin_bottom),
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
            fg_color=self._ui.colors.btn_background,
            hover_color=self._ui.colors.btn_background_hover,
            text_color=self._ui.colors.btn_background_txt,
            corner_radius=20,
        )
        btn_back.grid(row=2, column=1, padx=12, pady=(0, self._ui.margin_bottom))
        return btn_back

    def add_page_title(self, text, pady=(40, 5)):
        title = ctk.CTkSimpleLabel(
            self.container, text=text, font=self._ui.fonts.medium, wraplength="self"
        )
        title.grid(
            row=0,
            column=0,
            columnspan=3,
            pady=pady,
            padx=0,
            sticky="ew",
        )
        return title

    def set_page_title(self, text):
        """Set or update the page title."""
        if hasattr(self, "_title_widget"):
            self._title_widget.configure(text=text)
        else:
            self._title_widget = self.add_page_title(text)
