import pathlib
import pickle
import tempfile
from templates.generic_page_layout import GenericPageLayout
import tkinter_templates as tkt
import globals as GV
import functions as fn
import procedure as prc
from page_manager import Page
import tkinter as tk
from compatibility_checks import Checks, DoneChecks, CheckType
from async_operations import AsyncOperations as AO, Status


class PageCheck(Page):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.job_var = tk.StringVar(self)
        self.checks = Checks()
        self._active_check = 0

        self.done_checks = DoneChecks()
        self.skip_check = False

    def set_done_checks(self, done_checks):
        print("Received done checks")
        self.done_checks = done_checks
        done_list = [
            check_type.value
            for check_type, check in self.done_checks.checks.items()
            if check.returncode is not None
        ]
        print(f"Done checks: {done_list}")

    def set_skip_check(self, skip_check):
        self.skip_check = skip_check

    def init_page(self):
        page_layout = GenericPageLayout(self, self.LN.check_running)

        page_frame = page_layout.content_frame
        self.progressbar_check = tkt.add_progress_bar(page_frame)
        self.progressbar_check.set(0)
        tkt.add_text_label(page_frame, var=self.job_var, pady=0, padx=10)
        self.update()
        if self.skip_check:
            import dummy

            GV.ALL_SPINS = dummy.DUMMY_ALL_SPINS
            GV.IP_LOCALE = dummy.DUMMY_IP_LOCALE
            self.finalize_and_parse_errors()
        else:
            self.spins_promise = AO.run(
                fn.get_json,
                args=[GV.APP_AVAILABLE_SPINS_LIST],
            )
            self.ip_locale_promise = AO.run(
                fn.get_json,
                args=[GV.APP_FEDORA_GEO_IP_URL],
            )
            self.run_checks()

    def run_checks(self):
        check_types = list(CheckType)
        if self._active_check < len(check_types):
            check_type = check_types[self._active_check]
            check_function = self.checks.check_functions[check_type]
            check_operation = AO()
            check_operation.run_async_process(
                self.check_wrapper, args=(check_type, check_function, check_operation)
            )
            self.monitor_async_operation(
                check_operation,
                self.run_checks,
            )
        else:
            self.on_checks_complete()

    def update_job_var_and_progressbar(self, current_task):
        if current_task == CheckType.ARCH:
            self.progressbar_check.set(0.10)
        elif current_task == CheckType.UEFI:
            self.job_var.set(self.LN.check_uefi)
            self.progressbar_check.set(0.20)
        elif current_task == CheckType.RAM:
            self.job_var.set(self.LN.check_ram)
            self.progressbar_check.set(0.30)
        elif current_task == CheckType.SPACE:
            self.job_var.set(self.LN.check_space)
            self.progressbar_check.set(0.50)
        elif current_task == CheckType.RESIZABLE:
            self.job_var.set(self.LN.check_resizable)
            self.progressbar_check.set(0.80)
        elif current_task == "downloads":
            self.job_var.set(self.LN.check_available_downloads)
            self.progressbar_check.set(0.90)

    def check_wrapper(self, check_type, check_function, operation):
        if self.done_checks.checks[check_type].returncode is None:
            self.update_job_var_and_progressbar(check_type)
            result = check_function()
            print(
                f"Check {self._active_check + 1}: {result.result}, Return code: {result.returncode}"
            )
            if result.returncode == -200:
                with tempfile.NamedTemporaryFile(
                    suffix=".pkl", delete=False
                ) as temp_file:
                    pickle.dump(self.done_checks, temp_file)
                    temp_file_path = pathlib.Path(temp_file.name).absolute()
                args_string = f'--checks_dumb "{temp_file_path}"'
                operation.status = Status.FAILED
                fn.get_admin(args_string)

            else:
                self.done_checks.checks[check_type] = result
        self._active_check += 1

    def on_checks_complete(self):
        if self.ip_locale_promise.status == Status.COMPLETED:
            GV.IP_LOCALE = self.ip_locale_promise.output

        if self.spins_promise.status == Status.COMPLETED:
            GV.ALL_SPINS = self.spins_promise.output
            self.finalize_and_parse_errors()
        else:
            self.update_job_var_and_progressbar("downloads")
            self.after(100, self.on_checks_complete)

    def finalize_and_parse_errors(self):
        if self.done_checks:
            errors = []
            if not self.skip_check:
                if self.done_checks.checks[CheckType.ARCH].returncode != 0:
                    errors.append(self.LN.error_arch_9)
                elif (
                    self.done_checks.checks[CheckType.ARCH].result
                    not in GV.ACCEPTED_ARCHITECTURES
                ):
                    errors.append(self.LN.error_arch_0)
                if self.done_checks.checks[CheckType.UEFI].returncode != 0:
                    errors.append(self.LN.error_uefi_9)
                elif self.done_checks.checks[CheckType.UEFI].result != "uefi":
                    errors.append(self.LN.error_uefi_0)
                if self.done_checks.checks[CheckType.RAM].returncode != 0:
                    errors.append(self.LN.error_totalram_9)
                elif (
                    self.done_checks.checks[CheckType.RAM].result
                    < GV.APP_MINIMAL_REQUIRED_RAM
                ):
                    errors.append(self.LN.error_totalram_0)
                if self.done_checks.checks[CheckType.SPACE].returncode != 0:
                    errors.append(self.LN.error_space_9)
                elif (
                    self.done_checks.checks[CheckType.SPACE].result
                    < GV.APP_MINIMAL_REQUIRED_SPACE
                ):
                    errors.append(self.LN.error_space_0)
                if self.done_checks.checks[CheckType.RESIZABLE].returncode != 0:
                    errors.append(self.LN.error_resizable_9)
                elif (
                    self.done_checks.checks[CheckType.RESIZABLE].result
                    < GV.APP_MINIMAL_REQUIRED_SPACE
                ):
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

    def monitor_async_operation(
        self,
        operation: AO,
        callback_function,
        update_intervall=100,
        *args,
        **kwargs,
    ):
        if operation.status == Status.COMPLETED:
            callback_function(*args, **kwargs)
        elif operation.status == Status.FAILED:
            # We exit the program in this case because it will relauch with admin rights
            raise SystemExit
        else:
            self.after(
                update_intervall,
                self.monitor_async_operation,
                operation,
                callback_function,
                update_intervall,
                *args,
                **kwargs,
            )
