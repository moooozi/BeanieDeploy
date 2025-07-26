import pathlib
import pickle
import sys
import tempfile
from services.system import get_admin
from templates.generic_page_layout import GenericPageLayout
from models.page import Page
from pages.page_error import PageError
import tkinter as tk
from compatibility_checks import DoneChecks, CheckType
from async_operations import AsyncOperation
from tkinter_templates import ProgressBar, TextLabel
from core.compatibility_logic import parse_errors


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
        self._active_check = 0
        self._progress = 0.0
        self.done_checks = DoneChecks()
        self._running_check_processes = 0
        self._navigation_completed = False

    def set_done_checks(self, done_checks):
        self.logger.info("Received done checks")
        self.done_checks = done_checks

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
        self.run_checks()

    def run_checks(self):
        self.logger.info("Running checks")
        from compatibility_checks import check_functions

        for check_type in check_functions:
            if self.done_checks.checks[check_type].returncode is not None:
                self.logger.info(f"Check {check_type} already completed, skipping")
                continue
            self.logger.info(f"Running check: {check_type}")
            AsyncOperation().run(
                check_functions[check_type],
                on_complete=lambda output, check_type=check_type: self._handle_check_complete(output, check_type),
            )
            self._running_check_processes += 1

    def _handle_check_complete(self, output, check_type):
        """Callback for when a check completes."""
        self._running_check_processes -= 1
        if output.returncode == -200:
            self.logger.warning(f"Check {check_type} requires admin privileges")
            with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as temp_file:
                pickle.dump(self.done_checks, temp_file)
                temp_file_path = pathlib.Path(temp_file.name).absolute()
            args_string = f'--checks_dumb "{temp_file_path}"'
            self.after(200, lambda: (get_admin(args_string), sys.exit(0)))
        else:
            self.logger.info(f"Check {check_type} completed successfully")
            print(f"🔧 Check {check_type} completed successfully")
            print(f"🔧 Output: {output}")
            self.done_checks.checks[check_type] = output
            self.update_job_var_and_progressbar(check_type)
        
        if self._running_check_processes == 0:
            self.on_checks_complete()

    def update_job_var_and_progressbar(self, current_task: CheckType):
        self.logger.info(f"Updating progress for task: {current_task}")
        if current_task == CheckType.ARCH:
            self._progress += 0.10
            self.job_var.set(self.LN.check_arch)
            self.progressbar_check.set(self._progress)
            self.logger.info(f"Progress: {self._progress * 100}% - Architecture check")
        elif current_task == CheckType.UEFI:
            self._progress += 0.20
            self.job_var.set(self.LN.check_uefi)
            self.progressbar_check.set(self._progress)
            self.logger.info(f"Progress: {self._progress * 100}% - UEFI check")
        elif current_task == CheckType.RAM:
            self._progress += 0.20
            self.job_var.set(self.LN.check_ram)
            self.progressbar_check.set(self._progress)
            self.logger.info(f"Progress: {self._progress * 100}% - RAM check")
        elif current_task == CheckType.SPACE:
            self._progress += 0.20
            self.job_var.set(self.LN.check_space)
            self.progressbar_check.set(self._progress)
            self.logger.info(f"Progress: {self._progress * 100}% - Disk space check")
        elif current_task == CheckType.RESIZABLE:
            self._progress += 0.30
            self.job_var.set(self.LN.check_resizable)
            self.progressbar_check.set(self._progress)
            self.logger.info(f"Progress: {self._progress * 100}% - Resizable partition check")

    def on_checks_complete(self):
        print("🔧 finalize_and_parse_errors called")
        self.logger.info("finalize_and_parse_errors called")
        if self.done_checks:
            print("🔧 Processing done_checks")
            self.logger.info("Processing done_checks")
            print("🔧 Done checks:")
            for check_type, check in self.done_checks.checks.items():
                print(f"🔧 - {check_type.value}: {check}")
            errors = parse_errors(self.done_checks, self.app_config, self.LN)
            if not errors:
                print("🔧 No errors found, proceeding with navigation")
                self.logger.info("No errors found, proceeding with navigation")
                self.state.compatibility.done_checks = self.done_checks
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