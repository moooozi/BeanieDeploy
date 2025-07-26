from PySide6.QtWidgets import QVBoxLayout, QLabel, QProgressBar, QMessageBox, QWidget
from PySide6.QtCore import QTimer, Signal
from typing import Optional

from models.pyside6_page import PySide6Page, PageValidationResult
from templates.pyside6_generic_page_layout import GenericPageLayout
from pyside6_async_operations import PySide6AsyncOperations
from services.network import get_json
from services.spin_manager import parse_spins
from compatibility_checks import Checks, DoneChecks, CheckType

from core.check_runner import run_checks
from core.compatibility_logic import parse_errors, filter_spins


class PySide6PageCheck(PySide6Page):
    """
    PySide6 version of PageCheck - System Compatibility Check Page.
    
    Much cleaner than the CustomTkinter version because:
    - Qt's QProgressBar is more robust than custom implementations
    - Better async handling with QThread
    - Built-in status/message display
    - No need for manual GUI updates (Qt handles repainting)
    """
    
    # Signals for async operations
    check_progress_updated = Signal(int, str)  # progress percentage, message
    all_checks_completed = Signal()

    def __init__(self, parent: Optional[QWidget], page_name: str):
        super().__init__(parent, page_name)
        
        # Initialize check system
        self.checks = Checks()
        self.done_checks = DoneChecks()
        self.skip_check = False
        self._active_check = 0
        self._navigation_completed = False
        self._navigation_requested = False  # Guard against multiple navigation calls
        
        # UI components
        self.progress_bar: Optional[QProgressBar] = None
        self.status_label: Optional[QLabel] = None
        
        # Async operations
        self.spins_operation: Optional[PySide6AsyncOperations] = None
        self.ip_locale_operation: Optional[PySide6AsyncOperations] = None

    def set_done_checks(self, done_checks):
        """Set previously completed checks."""
        self.logger.info("Received done checks")
        self.done_checks = done_checks

    def set_skip_check(self, skip_check: bool):
        """Set whether to skip checks and use dummy data."""
        self.skip_check = skip_check

    def init_page(self):
        """Initialize the page layout and widgets."""
        self.logger.info("Initializing PageCheck (System Compatibility)")
        page_layout = GenericPageLayout(self, title=self.LN.check_running)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(page_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        page_layout.content_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Initializing checks...")
        self.status_label.setWordWrap(True)
        page_layout.content_layout.addWidget(self.status_label)

        self.check_progress_updated.connect(self._update_progress)
        self.all_checks_completed.connect(self._on_all_checks_completed)

    def on_show(self):
        """Called when the page is shown - start the checks."""
        if self._navigation_completed:
            self.logger.info("PageCheck.on_show() called but navigation already completed, ignoring")
            return
        self.logger.info("PageCheck.on_show() called - starting checks")
        super().on_show()
        
        # Start checks with a small delay to ensure UI is ready
        QTimer.singleShot(100, self._start_checks)

    def _start_checks(self):
        """Start the checking process."""
        if self.skip_check:
            self._use_dummy_data()
        else:
            self.spins_operation = PySide6AsyncOperations(self)
            self.spins_operation.finished.connect(self._on_spins_loaded)
            self.spins_operation.error.connect(self._on_network_error)
            self.spins_operation.run_async_process(
                function=get_json,
                args=[self.app_config.urls.available_spins_list]
            )

            self.ip_locale_operation = PySide6AsyncOperations(self)
            self.ip_locale_operation.finished.connect(self._on_ip_locale_loaded)
            self.ip_locale_operation.error.connect(self._on_network_error)
            self.ip_locale_operation.run_async_process(
                function=get_json,
                args=[self.app_config.urls.fedora_geo_ip]
            )

            self.run_checks()

    def _use_dummy_data(self):
        import dummy
        self.logger.info("Skipping checks - using dummy data")
        self.status_label.setText("Using dummy data for testing...")
        self.progress_bar.setValue(100)
        _, all_spins = parse_spins(dummy.DUMMY_ALL_SPINS)
        self.state.compatibility.all_spins = all_spins
        self.state.compatibility.ip_locale = dummy.DUMMY_IP_LOCALE
        QTimer.singleShot(500, self.finalize_and_parse_errors)

    def run_checks(self):
        run_checks(
            self.checks,
            self.done_checks,
            self._active_check,
            self.on_checks_complete,
            lambda check_type, check_function, check_operation: self.check_wrapper(check_type, check_function, check_operation),
            self.monitor_async_operation,
            self.logger
        )

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

    def update_job_var_and_progressbar(self, current_task):
        progress_map = {
            CheckType.ARCH: (10, self.LN.check_arch if hasattr(self.LN, 'check_arch') else "Checking architecture..."),
            CheckType.UEFI: (20, self.LN.check_uefi if hasattr(self.LN, 'check_uefi') else "Checking UEFI..."),
            CheckType.RAM: (30, self.LN.check_ram if hasattr(self.LN, 'check_ram') else "Checking RAM..."),
            CheckType.SPACE: (50, self.LN.check_space if hasattr(self.LN, 'check_space') else "Checking disk space..."),
            CheckType.RESIZABLE: (80, self.LN.check_resizable if hasattr(self.LN, 'check_resizable') else "Checking resizable partitions..."),
            "downloads": (90, self.LN.check_available_downloads if hasattr(self.LN, 'check_available_downloads') else "Checking available downloads..."),
        }
        percent, message = progress_map.get(current_task, (0, ""))
        if self.progress_bar:
            self.progress_bar.setValue(percent)
        if self.status_label:
            self.status_label.setText(message)

    def monitor_async_operation(self, operation, callback_function, update_intervall=100, *args, **kwargs):
        if operation.status == operation.Status.COMPLETED:
            callback_function(*args, **kwargs)
        elif operation.status == operation.Status.FAILED:
            raise SystemExit
        else:
            QTimer.singleShot(update_intervall, lambda: self.monitor_async_operation(
                operation, callback_function, update_intervall, *args, **kwargs))

    def on_checks_complete(self):
        if self.ip_locale_operation and self.ip_locale_operation.status == self.ip_locale_operation.status.COMPLETED and self.ip_locale_operation.output:
            if isinstance(self.ip_locale_operation.output, dict):
                self.state.compatibility.ip_locale = self.ip_locale_operation.output
            else:
                self.logger.warning("ip_locale_operation.output is not a dict, skipping assignment")

        if self.spins_operation and self.spins_operation.status == self.spins_operation.status.COMPLETED and self.spins_operation.output:
            _, parsed_spins = parse_spins(self.spins_operation.output)
            self.state.compatibility.all_spins = parsed_spins
            self.finalize_and_parse_errors()
        else:
            self.update_job_var_and_progressbar("downloads")
            QTimer.singleShot(100, self.on_checks_complete)

    def finalize_and_parse_errors(self):
        self.logger.info("finalize_and_parse_errors called")
        if self.done_checks:
            self.logger.info("Processing done_checks")
            errors = parse_errors(self.done_checks, self.app_config, self.LN, self.skip_check)
            if not errors:
                self.logger.info("No errors found, proceeding with navigation")
                self.state.compatibility.done_checks = self.done_checks
                filtered_spins, live_os_installer_index = filter_spins(self.state.compatibility.all_spins)
                self.state.compatibility.accepted_spins = filtered_spins
                if live_os_installer_index is not None:
                    self.state.compatibility.live_os_installer_spin = self.state.compatibility.accepted_spins[live_os_installer_index]
                self._navigation_completed = True
                QTimer.singleShot(10, self._delayed_navigate_next)
            else:
                self.logger.info(f"Found {len(errors)} errors, navigating to error page")
                self._show_error('\n'.join(errors))
                # TODO: Navigate to error page when implemented
        else:
            self.logger.info("No done_checks, navigating next anyway")
            self._delayed_navigate_next()

    def _delayed_navigate_next(self):
        if self._navigation_requested:
            self.logger.info("Navigation already requested, ignoring duplicate call")
            return
        self._navigation_requested = True
        self.logger.info("Requesting navigation to next page")
        self.navigate_next()

    def _on_spins_loaded(self, spins_data):
        _, parsed_spins = parse_spins(spins_data)
        self.state.compatibility.all_spins = parsed_spins

    def _on_ip_locale_loaded(self, ip_locale_data):
        self.state.compatibility.ip_locale = ip_locale_data

    def _on_network_error(self, error_msg: str):
        self.logger.warning(f"Network error (non-fatal): {error_msg}")

    def _show_error(self, message: str):
        """Show error message and navigate to error page."""
        QMessageBox.critical(self, "Compatibility Check Error", message)
        # TODO: Navigate to error page when it's created
        # self.navigate_to_error_page(message)

    def validate_input(self) -> PageValidationResult:
        """Validate that checks are complete."""
        if not self._navigation_completed:
            return PageValidationResult(False, "Compatibility checks are still running.")
        return PageValidationResult(True)

    def show_validation_error(self, message: str):
        """Show validation error to user."""
        QMessageBox.warning(self, "Validation Error", message)
