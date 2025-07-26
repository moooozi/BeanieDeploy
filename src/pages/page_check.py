from templates.generic_page_layout import GenericPageLayout
from services.network import get_json
from services.spin_manager import parse_spins
from models.page import Page
from pages.page_error import PageError
import tkinter as tk
from compatibility_checks import Checks, DoneChecks, CheckType
from async_operations import AsyncOperations as AO, Status
from tkinter_templates import ProgressBar, TextLabel
from core.compatibility_logic import parse_errors, filter_spins


class PageCheck(Page):
    def on_show(self):
        """Called when the page is shown."""
        if self._navigation_completed:
            print("🔧 PageCheck.on_show() called but navigation already completed, ignoring")
            return
        print("🔧 PageCheck.on_show() called")
        super().on_show()

    def tkraise(self, aboveThis=None):
        """Override tkraise to prevent PageCheck from coming to front after navigation."""
        if hasattr(self, '_navigation_completed') and self._navigation_completed:
            print("🔧 PageCheck.tkraise() called but navigation already completed, ignoring")
            return
        print("🔧 PageCheck.tkraise() called")
        super().tkraise(aboveThis)

    def __init__(self, parent, page_name, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)
        self.job_var = tk.StringVar(self)
        self.checks = Checks()
        self._active_check = 0

        self.done_checks = DoneChecks()
        self.skip_check = False
        self._navigation_completed = False

    def set_done_checks(self, done_checks):
        self.logger.info("Received done checks")
        self.done_checks = done_checks
        done_list = [
            check_type.value
            for check_type, check in self.done_checks.checks.items()
            if check.returncode is not None
        ]
        self.logger.info(f"Done checks: {done_list}")

    def set_skip_check(self, skip_check):
        self.skip_check = skip_check

    def _delayed_navigate_next(self):
        """Navigate to next page with a delay to avoid race conditions."""
        print("🔧 _delayed_navigate_next() called")
        self.logger.info("_delayed_navigate_next() called")
        self.navigate_next()
        print("🔧 navigate_next() completed")

    def init_page(self):
        print("🔧 PageCheck.init_page() called")
        self.logger.info("PageCheck.init_page() called")
        
        page_layout = GenericPageLayout(self, self.LN.check_running)
        print("🔧 GenericPageLayout created")

        page_frame = page_layout.content_frame
        
        self.progressbar_check = ProgressBar(page_frame)
        self.progressbar_check.pack(pady=(0, 20), fill="both")
        self.progressbar_check.set(0)
        
        job_label = TextLabel(page_frame, var=self.job_var)
        job_label.pack(pady=0, padx=10)
        print("🔧 GUI elements created")
        
        self.update()        
        print("🔧 Starting checks")
        self.logger.info("Starting checks")
        self.spins_promise = AO.run(
            get_json,
            args=[self.app_config.urls.available_spins_list],
        )
        self.ip_locale_promise = AO.run(
            get_json,
            args=[self.app_config.urls.fedora_geo_ip],
        )
        self.run_checks()

    def run_checks(self):
        from core.check_runner import run_checks
        run_checks(
            self.checks,
            self.done_checks,
            self._active_check,
            self.on_checks_complete,
            lambda check_type, check_function, check_operation: self.check_wrapper(check_type, check_function, check_operation),
            self.monitor_async_operation,
            self.logger
        )

    def update_job_var_and_progressbar(self, current_task):
        self.logger.info(f"Updating progress for task: {current_task}")
        if current_task == CheckType.ARCH:
            self.job_var.set(self.LN.check_arch if hasattr(self.LN, 'check_arch') else "Checking architecture...")
            self.progressbar_check.set(0.10)
            self.logger.info("Progress: 10% - Architecture check")
        elif current_task == CheckType.UEFI:
            self.job_var.set(self.LN.check_uefi if hasattr(self.LN, 'check_uefi') else "Checking UEFI...")
            self.progressbar_check.set(0.20)
            self.logger.info("Progress: 20% - UEFI check")
        elif current_task == CheckType.RAM:
            self.job_var.set(self.LN.check_ram if hasattr(self.LN, 'check_ram') else "Checking RAM...")
            self.progressbar_check.set(0.30)
            self.logger.info("Progress: 30% - RAM check")
        elif current_task == CheckType.SPACE:
            self.job_var.set(self.LN.check_space if hasattr(self.LN, 'check_space') else "Checking disk space...")
            self.progressbar_check.set(0.50)
            self.logger.info("Progress: 50% - Disk space check")
        elif current_task == CheckType.RESIZABLE:
            self.job_var.set(self.LN.check_resizable if hasattr(self.LN, 'check_resizable') else "Checking resizable partitions...")
            self.progressbar_check.set(0.80)
            self.logger.info("Progress: 80% - Resizable partition check")
        elif current_task == "downloads":
            self.job_var.set(self.LN.check_available_downloads if hasattr(self.LN, 'check_available_downloads') else "Checking available downloads...")
            self.progressbar_check.set(0.90)
            self.logger.info("Progress: 90% - Available downloads check")
        self.update()  # Force GUI update

    def check_wrapper(self, check_type, check_function, operation):
        from core.check_runner import check_wrapper
        check_wrapper(
            check_type,
            check_function,
            operation,
            self.done_checks,
            self.LN,
            self.app_config,
            self.logger,
            self.update_job_var_and_progressbar
        )
        self._active_check += 1
        self.logger.info(f"Moving to next check, active_check now: {self._active_check}")

    def on_checks_complete(self):
        if self.ip_locale_promise.status == Status.COMPLETED and self.ip_locale_promise.output:
            self.state.compatibility.ip_locale = self.ip_locale_promise.output

        if self.spins_promise.status == Status.COMPLETED and self.spins_promise.output:
            # Parse the raw spin data into Spin objects
            _, parsed_spins = parse_spins(self.spins_promise.output)
            self.state.compatibility.all_spins = parsed_spins
            self.finalize_and_parse_errors()
        else:
            self.update_job_var_and_progressbar("downloads")
            self.after(100, self.on_checks_complete)

    def finalize_and_parse_errors(self):
        print("🔧 finalize_and_parse_errors called")
        self.logger.info("finalize_and_parse_errors called")
        if self.done_checks:
            print("🔧 Processing done_checks")
            self.logger.info("Processing done_checks")
            errors = parse_errors(self.done_checks, self.app_config, self.LN, self.skip_check)
            if not errors:
                print("🔧 No errors found, proceeding with navigation")
                self.logger.info("No errors found, proceeding with navigation")
                self.state.compatibility.done_checks = self.done_checks
                print("🔧 About to filter accepted spins")
                filtered_spins, live_os_installer_index = filter_spins(self.state.compatibility.all_spins)
                self.state.compatibility.accepted_spins = filtered_spins
                print("🔧 Spin filtering completed")
                if live_os_installer_index is not None:
                    self.state.compatibility.live_os_installer_spin = self.state.compatibility.accepted_spins[live_os_installer_index]
                print("🔧 About to navigate_next()")
                self.logger.info("About to navigate_next()")
                self._navigation_completed = True  # Mark navigation as completed
                self.after(10, self._delayed_navigate_next)
                print("🔧 Scheduled delayed navigation")
            else:
                print(f"🔧 Found {len(errors)} errors, navigating to error page")
                self.logger.info(f"Found {len(errors)} errors, navigating to error page")
                from models.page_manager import PageManager
                if self._page_manager is None or not isinstance(self._page_manager, PageManager):
                    raise ValueError("PageManager is not set or is not an instance of PageManager")
                self._page_manager.configure_page(PageError, lambda page: page.set_errors(errors))
                self.navigate_to(PageError)
        else:
            print("🔧 No done_checks, navigating next anyway")
            self.logger.info("No done_checks, navigating next anyway")
            self.navigate_next()

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
