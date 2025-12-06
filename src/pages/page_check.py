import logging
import threading
import tkinter as tk

import customtkinter as ctk

from config.settings import ConfigManager
from models.check import Check, CheckType, DoneChecks
from models.data_units import DataUnit
from models.page import Page
from multilingual import _


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
        self.total_weight = sum(check_type.weight for check_type in CheckType)

    def init_page(self):
        logging.info("PageCheck.init_page() called")

        self.page_manager.set_title(_("check.running"))
        self.page_manager.set_primary_button(visible=False)
        self.page_manager.set_secondary_button(visible=False)

        page_frame = self
        page_frame.columnconfigure(0, weight=1)

        self.progressbar_check = ctk.CTkProgressBar(
            page_frame, orientation="horizontal", mode="determinate"
        )
        self.progressbar_check.grid(row=0, column=0, pady=(0, 20), sticky="ew")
        self.progressbar_check.set(0)

        job_label = ctk.CTkSimpleLabel(
            page_frame,
            textvariable=self.job_var,
            justify=self._ui.di.l,
            wraplength="self",
            font=self._ui.fonts.small,
            pady=5,
        )
        job_label.grid(row=1, column=0, pady=0, padx=10, sticky="ew")

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
        logging.info(f"Running check: {check_type}")

        def _run_check(check):
            self.update_job_var_and_progressbar(check)
            output = self._check_functions[check_type]()
            self._handle_check_complete(output, check_type)

        threading.Thread(target=_run_check, args=(check_type,), daemon=True).start()

    def _handle_check_complete(self, output: Check, check_type: CheckType) -> None:
        """Callback for when a check completes."""
        self.done_checks.checks[check_type] = output
        self._progress += (check_type.weight / self.total_weight) * 100
        self.progressbar_check.set(self._progress / 100)
        self.after(0, self._run_next_check)

    def update_job_var_and_progressbar(self, check: CheckType):
        self.job_var.set(_(f"check.{check.value}"))  # noqa: INT001
        logging.info(f"Progress: {self._progress}%")

    def on_checks_complete(self):
        """Callback for when all checks are complete."""
        if self.done_checks:
            logging.info("Processing done_checks")
            errors = parse_errors(self.done_checks, self.app_config)
            if not errors:
                logging.info("No errors found, proceeding with navigation")
                self.state.compatibility.done_checks = self.done_checks
                self._navigation_completed = True  # Mark navigation as completed
                self.after(10, self.navigate_next)
            else:
                msg = f"Found {len(errors)} errors, navigating to error page"
                logging.info(msg)
                self.state.set_error_messages(errors, "compatibility")
        else:
            logging.info("No done_checks, navigating next anyway")
            self.navigate_next()


def parse_errors(done_checks: DoneChecks, app_config: ConfigManager) -> list[str]:
    errors: list[str] = []
    if done_checks.checks[CheckType.ARCH].returncode != 0:
        errors.append(_("error.arch.1"))
    elif (
        done_checks.checks[CheckType.ARCH].result
        not in app_config.ui.accepted_architectures
    ):
        errors.append(_("error.arch.0"))
    if done_checks.checks[CheckType.UEFI].returncode != 0:
        errors.append(_("error.uefi.1"))
    elif done_checks.checks[CheckType.UEFI].result is not True:
        errors.append(_("error.uefi.0"))
    if done_checks.checks[CheckType.RAM].returncode != 0:
        errors.append(_("error.totalram.1"))
    elif done_checks.checks[CheckType.RAM].result < app_config.app.minimal_required_ram:
        errors.append(_("error.totalram.0"))
    if done_checks.checks[CheckType.SPACE].returncode != 0:
        errors.append(_("error.space.1"))
    elif (
        done_checks.checks[CheckType.SPACE].result
        < app_config.app.minimal_required_space
    ):
        errors.append(_("error.space.0"))
    if done_checks.checks[CheckType.RESIZABLE].returncode != 0:
        errors.append(_("error.resizable.1"))
    elif (
        done_checks.checks[CheckType.RESIZABLE].result
        < app_config.app.minimal_required_space
    ):
        errors.append(_("error.resizable.0"))
    if done_checks.checks[CheckType.EFI_SPACE].returncode != 0:
        errors.append(_("error.efi_space.1"))
    elif done_checks.checks[CheckType.EFI_SPACE].result < DataUnit.from_mebibytes(
        app_config.system_requirements.required_efi_space_mb
    ):
        errors.append(_("error.efi_space.0"))
    return errors
