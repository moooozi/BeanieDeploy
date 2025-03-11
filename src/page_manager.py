from abc import ABC, abstractmethod
import customtkinter as ctk
import multilingual


class PageManager(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.pages = {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def add_page(self, page_name, page_class, *args, **kwargs):
        page = page_class(self, *args, switch_page=self.show_page, **kwargs)
        self.pages[page_name] = page
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(0, weight=1)
        page.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def _show_page(self, page_name):
        print(f"Switching to {page_name}")
        page: Page = self.pages[page_name]
        if not page._initiated:
            print(f"Initializing page: {page_name}")
            page.init_page()
            page._initiated = True
        else:
            print(f"Page {page_name} already initialized")
        page.on_show()

    def show_page(self, page_name):
        self.after(10, lambda: self._show_page(page_name))
        self.after(10, lambda: self.pages[page_name].tkraise())


class Page(ctk.CTkFrame, ABC):
    LN = multilingual.get_lang()
    DI_VAR = multilingual.get_di_var()

    def __init__(self, parent, switch_page, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.switch_page = switch_page
        self._initiated = False

    @abstractmethod
    def init_page(self):
        """Initialize the page layout and widgets."""
        pass

    def on_show(self):
        """Called when the page is shown."""
        pass
