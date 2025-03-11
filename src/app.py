from page_manager import PageManager
from page_autoinst2 import PageAutoinst2
from page_check import PageCheck
from page_error import PageError
from page_install_method import PageInstallMethod
from page_installing import PageInstalling
from page_1 import Page1
from page_autoinst_addition_1 import PageAutoinstAddition1
from page_autoinst_addition_2 import PageAutoinstAddition2
from page_autoinst_addition_3 import PageAutoinstAddition3
from page_playground import PagePlayground
from page_verify import PageVerify
import tkinter_templates as tkt


class MainApp(tkt.Application):
    def __init__(
        self,
        skip_check=False,
        done_checks=None,
        install_args=None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.page_manager = PageManager(self)
        self.page_manager.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.page_manager.add_page("PageError", PageError)
        self.page_manager.add_page("PageCheck", PageCheck)
        self.page_manager.add_page("Page1", Page1)
        self.page_manager.add_page("PageInstallMethod", PageInstallMethod)
        self.page_manager.add_page("PageAutoinstAddition1", PageAutoinstAddition1)
        self.page_manager.add_page("PageAutoinstAddition2", PageAutoinstAddition2)
        self.page_manager.add_page("PageAutoinstAddition3", PageAutoinstAddition3)
        self.page_manager.add_page("PageAutoinst2", PageAutoinst2)
        self.page_manager.add_page("PageVerify", PageVerify)
        self.page_manager.add_page("PageInstalling", PageInstalling)
        self.page_manager.add_page("PagePlayground", PagePlayground)

        playground = False

        if playground:
            return self.page_manager.show_page("PagePlayground")
        if install_args:
            self.page_manager.pages["PageInstalling"].set_installer_args(install_args)
            return self.page_manager.show_page("PageInstalling")
        if skip_check:
            self.page_manager.pages["PageCheck"].set_skip_check(skip_check)
        if done_checks:
            self.page_manager.pages["PageCheck"].set_done_checks(done_checks)
        return self.page_manager.show_page("PageCheck")
