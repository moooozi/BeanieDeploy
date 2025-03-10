import pathlib
import pickle
import tempfile
import tkinter_templates as tkt
import globals as GV
import functions as fn
import procedure as prc
from page_manager import Page
import tkinter as tk
from compatibility_checks import (
    check_arch,
    check_uefi,
    check_ram,
    check_space,
    check_resizable,
)


class PageCheck(Page):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.job_var = tk.StringVar(self)
        self.checks = {
            "arch": check_arch,
            "uefi": check_uefi,
            "ram": check_ram,
            "space": check_space,
            "resizable": check_resizable,
        }
        self.current_check = 0
        self.check_names = list(self.checks.keys())

        self.done_checks = GV.DoneChecks()
        self.skip_check = False

    def set_done_checks(self, done_checks):
        self.done_checks = done_checks

    def set_skip_check(self, skip_check):
        self.skip_check = skip_check

    def init_page(self):
        page_frame = tkt.generic_page_layout(self, self.LN.check_running)
        self.progressbar_check = tkt.add_progress_bar(page_frame)
        tkt.add_text_label(page_frame, var=self.job_var, pady=0, padx=10)
        self.update()
        GV.ALL_SPINS = fn.get_json(url=GV.APP_AVAILABLE_SPINS_LIST)
        self.update()
        GV.IP_LOCALE = fn.get_json(url=GV.APP_FEDORA_GEO_IP_URL)
        self.update()
        if self.skip_check:
            self.on_checks_complete()
        else:
            self.run_checks()

    def run_checks(self):
        if self.current_check < len(self.check_names):
            check_name = self.check_names[self.current_check]
            check_function = self.checks[check_name]
            self.after(0, self.run_check, check_name, check_function)
        else:
            self.on_checks_complete()

    def update_job_var_and_progressbar(self, check_name):
        if check_name == "arch":
            self.progressbar_check["value"] = 10
        elif check_name == "uefi":
            self.job_var.set(self.LN.check_uefi)
            self.progressbar_check["value"] = 20
        elif check_name == "ram":
            self.job_var.set(self.LN.check_ram)
            self.progressbar_check["value"] = 30
        elif check_name == "space":
            self.job_var.set(self.LN.check_space)
            self.progressbar_check["value"] = 50
        elif check_name == "resizable":
            self.job_var.set(self.LN.check_resizable)
            self.progressbar_check["value"] = 80

    def run_check(self, check_name, check_function):
        if getattr(self.done_checks, check_name).returncode == -999:
            self.update_job_var_and_progressbar(check_name)
            result = check_function()
            print(
                f"Check {self.current_check + 1}: {result.result}, Return code: {result.returncode}"
            )
            if result.returncode == -200:
                # Store the done_checks object serialized in a file in a temp directory
                with tempfile.NamedTemporaryFile(
                    suffix=".pkl", delete=False
                ) as temp_file:
                    pickle.dump(self.done_checks, temp_file)
                    temp_file_path = pathlib.Path(temp_file.name).absolute()
                args_string = f'--checks_dumb "{temp_file_path}"'
                fn.get_admin(args_string)
            else:
                setattr(self.done_checks, check_name, result)
        self.current_check += 1

        # Schedule the next check
        self.run_checks()

    def on_checks_complete(self):
        if self.done_checks:
            # Handle errors (e.g., display them in the GUI)
            errors = []
            if not self.skip_check:
                if self.done_checks.arch.returncode != 0:
                    errors.append(self.LN.error_arch_9)
                elif self.done_checks.arch.result not in GV.ACCEPTED_ARCHITECTURES:
                    errors.append(self.LN.error_arch_0)
                if self.done_checks.uefi.returncode != 0:
                    errors.append(self.LN.error_uefi_9)
                elif self.done_checks.uefi.result != "uefi":
                    errors.append(self.LN.error_uefi_0)
                if self.done_checks.ram.returncode != 0:
                    errors.append(self.LN.error_totalram_9)
                elif self.done_checks.ram.result < GV.APP_MINIMAL_REQUIRED_RAM:
                    errors.append(self.LN.error_totalram_0)
                if self.done_checks.space.returncode != 0:
                    errors.append(self.LN.error_space_9)
                elif self.done_checks.space.result < GV.APP_MINIMAL_REQUIRED_SPACE:
                    errors.append(self.LN.error_space_0)
                if self.done_checks.resizable.returncode != 0:
                    errors.append(self.LN.error_resizable_9)
                elif self.done_checks.resizable.result < GV.APP_MINIMAL_REQUIRED_SPACE:
                    errors.append(self.LN.error_resizable_0)
            if not errors:
                GV.DONE_CHECKS = self.done_checks
                live_os_installer_index, GV.ACCEPTED_SPINS = prc.parse_spins(
                    GV.ALL_SPINS
                )
                if live_os_installer_index is not None:
                    GV.LIVE_OS_INSTALLER_SPIN = GV.ACCEPTED_SPINS[
                        live_os_installer_index
                    ]
                GV.USERNAME_WINDOWS = fn.get_windows_username()
                self.switch_page("Page1")
            else:
                self.master.pages["PageError"].set_errors(errors)
                self.switch_page("PageError")
        else:
            # All checks passed

            self.switch_page("Page1")
