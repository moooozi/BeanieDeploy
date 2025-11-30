import logging
import tkinter as tk

import customtkinter as ctk

from async_operations import AsyncOperation
from config.settings import ConfigManager
from models.check import Check, CheckType, DoneChecks
from models.data_units import DataUnit
from models.page import Page
from multilingual import _
from pages.page_error import PageError
from templates.generic_page_layout import GenericPageLayout
from tkinter_templates import TextLabel


class PageCheck(Page):
    def on_show(self):
        """Called when the page is shown."""
        if self._navigation_completed:
            return
        super().on_show()

    def tkraise(self, aboveThis=None):  # noqa: N803
        """Override tkraise to prevent PageCheck from coming to front after navigation."""
        if hasattr(self, "_navigation_completed") and self._navigation_completed:
            return
        super().tkraise(aboveThis)

    def __init__(self, parent, page_name, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)
        self.job_var = tk.StringVar(self)
        self._active_check = 0
        self._progress = 0.0
        self.done_checks = DoneChecks()
        self._navigation_completed = False

    def set_done_checks(self, done_checks):
        logging.info("Received done checks")
        self.done_checks = done_checks

    def _delayed_navigate_next(self):
        """Navigate to next page with a delay to avoid race conditions."""
        logging.info("_delayed_navigate_next() called")
        self.navigate_next()

    def init_page(self):
        logging.info("PageCheck.init_page() called")

        page_layout = GenericPageLayout(self, _("check.running"))

        page_frame = page_layout.content_frame

        self.progressbar_check = ctk.CTkProgressBar(
            page_frame, orientation="horizontal", mode="determinate"
        )
        self.progressbar_check.pack(pady=(0, 20), fill="both")
        self.progressbar_check.set(0)

        job_label = TextLabel(page_frame, var=self.job_var)
        job_label.pack(pady=0, padx=10)

        self.update()
        logging.info("Starting checks")
        self.run_checks()

    def run_checks(self):
        logging.info("Running checks (sequential)")
        from compatibility_checks import check_functions

        self._pending_check_types = list(check_functions.keys())
        self._check_functions = check_functions
        self._run_next_check()

    def _run_next_check(self) -> None:
        if not self._pending_check_types:
            self.on_checks_complete()
            return
        check_type = self._pending_check_types.pop(0)
        self.update()
        if self.done_checks.checks[check_type].returncode is not None:
            logging.info(f"Check {check_type} already completed, skipping")
            self.update_job_var_and_progressbar(check_type)
            self.after(0, self._run_next_check)
            return
        logging.info(f"Running check: {check_type}")
        AsyncOperation().run(
            self._check_functions[check_type],
            on_complete=lambda output, check_type=check_type: self.after(
                0, self._handle_check_complete, output, check_type
            ),
        )

    def _handle_check_complete(self, output: Check, check_type: CheckType) -> None:
        """Callback for when a check completes."""
        logging.info(f"Check {check_type} completed successfully")
        self.done_checks.checks[check_type] = output
        self.update_job_var_and_progressbar(check_type)
        self.after(0, self._run_next_check)

    def update_job_var_and_progressbar(self, current_task: CheckType):
        logging.info(f"Updating progress for task: {current_task}")
        if current_task == CheckType.ARCH:
            self._progress += 0.10
            self.job_var.set(_("check.arch"))
            self.progressbar_check.set(self._progress)
            logging.info(f"Progress: {self._progress * 100}% - Architecture check")
        elif current_task == CheckType.UEFI:
            self._progress += 0.20
            self.job_var.set(_("check.uefi"))
            self.progressbar_check.set(self._progress)
            logging.info(f"Progress: {self._progress * 100}% - UEFI check")
        elif current_task == CheckType.RAM:
            self._progress += 0.20
            self.job_var.set(_("check.ram"))
            self.progressbar_check.set(self._progress)
            logging.info(f"Progress: {self._progress * 100}% - RAM check")
        elif current_task == CheckType.SPACE:
            self._progress += 0.20
            self.job_var.set(_("check.space"))
            self.progressbar_check.set(self._progress)
            logging.info(f"Progress: {self._progress * 100}% - Disk space check")
        elif current_task == CheckType.RESIZABLE:
            self._progress += 0.30
            self.job_var.set(_("check.resizable"))
            self.progressbar_check.set(self._progress)
            logging.info(
                f"Progress: {self._progress * 100}% - Resizable partition check"
            )

    def on_checks_complete(self):
        """Callback for when all checks are complete."""
        logging.info("finalize_and_parse_errors called")
        if self.done_checks:
            logging.info("Processing done_checks")
            errors = parse_errors(self.done_checks, self.app_config)
            if not errors:
                logging.info("No errors found, proceeding with navigation")
                self.state.compatibility.done_checks = self.done_checks
                logging.info("About to navigate_next()")
                self._navigation_completed = True  # Mark navigation as completed
                self.after(10, self._delayed_navigate_next)
            else:
                msg = f"Found {len(errors)} errors, navigating to error page"
                logging.info(msg)
                from models.page_manager import PageManager

                if self._page_manager is None or not isinstance(
                    self._page_manager, PageManager
                ):
                    msg = "PageManager is not set or is not an instance of PageManager"
                    raise ValueError(msg)
                self._page_manager.configure_page(
                    PageError, lambda page: page.set_errors(errors)
                )
                self.navigate_to(PageError)
        else:
            logging.info("No done_checks, navigating next anyway")
            self.navigate_next()


def parse_errors(done_checks: DoneChecks, app_config: ConfigManager) -> list[str]:
    errors: list[str] = []
    if done_checks.checks[CheckType.ARCH].returncode != 0:
        errors.append(_("error.arch.9"))
    elif (
        done_checks.checks[CheckType.ARCH].result
        not in app_config.ui.accepted_architectures
    ):
        errors.append(_("error.arch.0"))
    if done_checks.checks[CheckType.UEFI].returncode != 0:
        errors.append(_("error.uefi.9"))
    elif done_checks.checks[CheckType.UEFI].result is not True:
        errors.append(_("error.uefi.0"))
    if done_checks.checks[CheckType.RAM].returncode != 0:
        errors.append(_("error.totalram.9"))
    elif done_checks.checks[CheckType.RAM].result < app_config.app.minimal_required_ram:
        errors.append(_("error.totalram.0"))
    if done_checks.checks[CheckType.SPACE].returncode != 0:
        errors.append(_("error.space.9"))
    elif (
        done_checks.checks[CheckType.SPACE].result
        < app_config.app.minimal_required_space
    ):
        errors.append(_("error.space.0"))
    if done_checks.checks[CheckType.RESIZABLE].returncode != 0:
        errors.append(_("error.resizable.9"))
    elif (
        done_checks.checks[CheckType.RESIZABLE].result
        < app_config.app.minimal_required_space
    ):
        errors.append(_("error.resizable.0"))
    if done_checks.checks[CheckType.EFI_SPACE].returncode != 0:
        errors.append(_("error.efi_space.9"))
    elif done_checks.checks[CheckType.EFI_SPACE].result < DataUnit.from_mebibytes(
        app_config.system_requirements.required_efi_space_mb
    ):
        errors.append(_("error.efi_space.0"))
    return errors
