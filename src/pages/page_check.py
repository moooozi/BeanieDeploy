import pathlib
import pickle
import tempfile
from templates.generic_page_layout import GenericPageLayout
from services.network import get_json
from services.system import get_admin, get_windows_username
from services.spin_manager import parse_spins
from models.page import Page
from pages.page_error import PageError
import tkinter as tk
from compatibility_checks import Checks, DoneChecks, CheckType
from async_operations import AsyncOperations as AO, Status
from tkinter_templates import ProgressBar, TextLabel


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
        print(f"🔧 GUI updated, skip_check = {self.skip_check}")
        
        if self.skip_check:
            import dummy
            
            print("🔧 Skipping checks - using dummy data")
            self.logger.info("Skipping checks - using dummy data")
            # Convert dummy data to proper Spin objects
            _, all_spins = parse_spins(dummy.DUMMY_ALL_SPINS)
            self.state.compatibility.all_spins = all_spins
            self.state.compatibility.ip_locale = dummy.DUMMY_IP_LOCALE
            print("🔧 Set dummy data, calling finalize_and_parse_errors")
            self.logger.info("Set dummy data, calling finalize_and_parse_errors")
            self.finalize_and_parse_errors()
        else:
            print("🔧 Starting real checks")
            self.logger.info("Starting real checks")
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
        self.logger.info("run_checks() called")
        check_types = list(CheckType)
        self.logger.info(f"Total checks to run: {len(check_types)}, Current active check: {self._active_check}")
        
        if self._active_check < len(check_types):
            check_type = check_types[self._active_check]
            self.logger.info(f"Running check {self._active_check + 1}/{len(check_types)}: {check_type}")
            
            check_function = self.checks.check_functions[check_type]
            self.logger.info(f"Got check function for {check_type}: {check_function}")
            
            check_operation = AO()
            self.logger.info(f"Created async operation for {check_type}")
            
            check_operation.run_async_process(
                self.check_wrapper, args=(check_type, check_function, check_operation)
            )
            self.logger.info(f"Started async process for {check_type}")
            
            self.monitor_async_operation(
                check_operation,
                self.run_checks,
            )
            self.logger.info(f"Monitoring async operation for {check_type}")
        else:
            self.logger.info("All checks completed, calling on_checks_complete()")
            self.on_checks_complete()

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
        self.logger.info(f"Starting check_wrapper for {check_type}")
        if self.done_checks.checks[check_type].returncode is None:
            self.logger.info(f"Running check for {check_type}")
            self.update_job_var_and_progressbar(check_type)
            
            try:
                self.logger.info(f"Calling check function for {check_type}")
                result = check_function()
                self.logger.info(f"Check {self._active_check + 1} ({check_type}): {result.result}, Return code: {result.returncode}")
                
                print(f"Check {self._active_check + 1}: {result.result}, Return code: {result.returncode}")
                
                if result.returncode == -200:
                    self.logger.warning(f"Check {check_type} requires admin privileges")
                    with tempfile.NamedTemporaryFile(
                        suffix=".pkl", delete=False
                    ) as temp_file:
                        pickle.dump(self.done_checks, temp_file)
                        temp_file_path = pathlib.Path(temp_file.name).absolute()
                    args_string = f'--checks_dumb "{temp_file_path}"'
                    operation.status = Status.FAILED
                    get_admin(args_string)
                else:
                    self.logger.info(f"Check {check_type} completed successfully")
                    self.done_checks.checks[check_type] = result
            except Exception as e:
                self.logger.error(f"Error during check {check_type}: {e}")
                raise
        else:
            self.logger.info(f"Check {check_type} already completed, skipping")
        
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
            errors = []
            if not self.skip_check:
                print("🔧 Running error checks")
                self.logger.info("Running error checks")
                # ... error checking code stays the same ...
                if self.done_checks.checks[CheckType.ARCH].returncode != 0:
                    errors.append(self.LN.error_arch_9)
                elif (
                    self.done_checks.checks[CheckType.ARCH].result
                    not in self.app_config.ui.accepted_architectures
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
                    < self.app_config.app.minimal_required_ram
                ):
                    errors.append(self.LN.error_totalram_0)
                if self.done_checks.checks[CheckType.SPACE].returncode != 0:
                    errors.append(self.LN.error_space_9)
                elif (
                    self.done_checks.checks[CheckType.SPACE].result
                    < self.app_config.app.minimal_required_space
                ):
                    errors.append(self.LN.error_space_0)
                if self.done_checks.checks[CheckType.RESIZABLE].returncode != 0:
                    errors.append(self.LN.error_resizable_9)
                elif (
                    self.done_checks.checks[CheckType.RESIZABLE].result
                    < self.app_config.app.minimal_required_space
                ):
                    errors.append(self.LN.error_resizable_0)
            else:
                print("🔧 Skipping error checks due to skip_check flag")
                self.logger.info("Skipping error checks due to skip_check flag")
                
            if not errors:
                print("🔧 No errors found, proceeding with navigation")
                self.logger.info("No errors found, proceeding with navigation")
                self.state.compatibility.done_checks = self.done_checks
                print("🔧 About to filter accepted spins")
                # Filter spins (all_spins is already parsed, just need to filter)
                accepted_spins = []
                live_os_installer_index = None
                
                for spin in self.state.compatibility.all_spins:
                    accepted_spins.append(spin)
                
                # Find live OS base index
                for index, spin in enumerate(accepted_spins):
                    if spin.is_base_netinstall:
                        live_os_installer_index = index
                        break
                
                # Filter out live images if no base netinstall found
                if live_os_installer_index is None:
                    self.state.compatibility.accepted_spins = [spin for spin in accepted_spins if not spin.is_live_img]
                else:
                    self.state.compatibility.accepted_spins = accepted_spins
                
                print("🔧 Spin filtering completed")
                if live_os_installer_index is not None:
                    self.state.compatibility.live_os_installer_spin = self.state.compatibility.accepted_spins[
                        live_os_installer_index
                    ]
                print("🔧 About to get windows username")
                self.state.user.windows_username = get_windows_username()
                print("🔧 About to navigate_next()")
                self.logger.info("About to navigate_next()")
                self._navigation_completed = True  # Mark navigation as completed
                # Use after() to delay navigation and avoid race conditions
                self.after(10, self._delayed_navigate_next)
                print("🔧 Scheduled delayed navigation")
            else:
                print(f"🔧 Found {len(errors)} errors, navigating to error page")
                self.logger.info(f"Found {len(errors)} errors, navigating to error page")
                # Set errors on the error page using type-safe method
                from models.page_manager import PageManager
                if self._page_manager is None or not isinstance(self._page_manager, PageManager):
                    raise ValueError("PageManager is not set or is not an instance of PageManager")
                self._page_manager.configure_page(PageError, lambda page: page.set_errors(errors))
                self.navigate_to(PageError)
        else:
            # All checks passed
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
