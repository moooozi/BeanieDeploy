from PySide6.QtWidgets import QVBoxLayout, QLabel, QProgressBar, QMessageBox, QWidget
from PySide6.QtCore import QTimer, Signal
from typing import Optional
import pathlib
import pickle
import tempfile

from models.pyside6_page import PySide6Page, PageValidationResult
from templates.pyside6_generic_page_layout import GenericPageLayout
from pyside6_async_operations import PySide6AsyncOperations
from services.network import get_json
from services.system import get_admin
from services.spin_manager import parse_spins
from compatibility_checks import Checks, DoneChecks, CheckType


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
        self.current_check_operation: Optional[PySide6AsyncOperations] = None

    def set_done_checks(self, done_checks):
        """Set previously completed checks."""
        self.logger.info("Received done checks")
        self.done_checks = done_checks
        done_list = [
            check_type.value
            for check_type, check in self.done_checks.checks.items()
            if check.returncode is not None
        ]
        self.logger.info(f"Done checks: {done_list}")

    def init_page(self):
        """Initialize the page layout and widgets."""
        self.logger.info("Initializing PageCheck (System Compatibility)")
        
        try:
            # Create the main page layout
            page_layout = GenericPageLayout(
                self,
                title=self.LN.check_running,
            )
            
            # Set up the main layout
            main_layout = QVBoxLayout(self)
            main_layout.addWidget(page_layout)
            
            # Create progress bar
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            page_layout.content_layout.addWidget(self.progress_bar)
            
            # Create status label
            self.status_label = QLabel("Initializing checks...")
            self.status_label.setWordWrap(True)
            page_layout.content_layout.addWidget(self.status_label)
            
            # Connect signals
            self.check_progress_updated.connect(self._update_progress)
            self.all_checks_completed.connect(self._on_all_checks_completed)
            
            self.logger.info("PageCheck initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing PageCheck: {e}")
            import traceback
            traceback.print_exc()
            raise

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
        # Start network operations first
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
        
        # Start the compatibility checks
        self._run_next_check()

    def _run_next_check(self):
        """Run the next compatibility check."""
        check_types = list(CheckType)
        
        if self._active_check < len(check_types):
            check_type = check_types[self._active_check]
            self.logger.info(f"Running check {self._active_check + 1}/{len(check_types)}: {check_type}")
            
            # Update progress and status
            progress_percent = int((self._active_check / len(check_types)) * 95)  # Reserve 5% for downloads
            self._update_check_status(check_type, progress_percent)
            
            # Skip if already done
            if self.done_checks.checks[check_type].returncode is not None:
                self.logger.info(f"Check {check_type} already completed, skipping")
                print(f"Check {check_type} already completed, skipping")
                self._active_check += 1
                QTimer.singleShot(1, self._run_next_check)
                return
            
            # Run the check
            check_function = self.checks.check_functions[check_type]
            
            self.current_check_operation = PySide6AsyncOperations(self)
            self.current_check_operation.finished.connect(self._on_check_completed)
            self.current_check_operation.error.connect(self._on_check_error)
            self.current_check_operation.run_async_process(
                function=self._check_wrapper,
                args=[check_type, check_function]
            )
        else:
            self.logger.info("All checks completed")
            self.all_checks_completed.emit()

    def _check_wrapper(self, check_type: CheckType, check_function):
        """Wrapper function for running individual checks."""
        self.logger.info(f"Starting check_wrapper for {check_type}")
        
        try:
            result = check_function()
            self.logger.info(f"Check {check_type}: {result.result}, Return code: {result.returncode}")
            
            if result.returncode == -200:
                # Requires admin privileges
                self.logger.warning(f"Check {check_type} requires admin privileges")
                with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as temp_file:
                    pickle.dump(self.done_checks, temp_file)
                    temp_file_path = pathlib.Path(temp_file.name).absolute()
                args_string = f'--checks_dumb "{temp_file_path}"'
                get_admin(args_string)
                return None  # Will restart with admin privileges
            else:
                self.done_checks.checks[check_type] = result
                return result
                
        except Exception as e:
            self.logger.error(f"Error during check {check_type}: {e}")
            raise

    def _update_check_status(self, check_type: CheckType, progress: int):
        """Update the status display for a specific check."""
        status_messages = {
            CheckType.ARCH: "Checking system architecture...",
            CheckType.UEFI: "Checking UEFI boot mode...",
            CheckType.RAM: "Checking available RAM...",
            CheckType.SPACE: "Checking disk space...",
            CheckType.RESIZABLE: "Checking resizable partitions...",
        }
        
        # Use translated message if available
        message = status_messages.get(check_type, f"Running {check_type.value} check...")
        if hasattr(self.LN, f'check_{check_type.value.lower()}'):
            message = getattr(self.LN, f'check_{check_type.value.lower()}')
        
        self.check_progress_updated.emit(progress, message)

    def _update_progress(self, progress: int, message: str):
        """Update the progress bar and status label."""
        if self.progress_bar:
            self.progress_bar.setValue(progress)
        if self.status_label:
            self.status_label.setText(message)

    def _on_check_completed(self, result):
        """Handle completion of a single check."""
        self._active_check += 1
        QTimer.singleShot(100, self._run_next_check)

    def _on_check_error(self, error_msg: str):
        """Handle error in a check."""
        self.logger.error(f"Check error: {error_msg}")
        self._show_error(f"System check failed: {error_msg}")

    def _on_spins_loaded(self, spins_data):
        """Handle successful loading of spins data."""
        self.logger.info("Spins data loaded successfully")
        
        # Parse the raw spin data into Spin objects (like the original does)
        try:
            _, parsed_spins = parse_spins(spins_data)
            self.state.compatibility.all_spins = parsed_spins
            self.logger.info(f"Parsed {len(parsed_spins)} spins from server data")
        except Exception as e:
            self.logger.error(f"Failed to parse spins data: {e}")
            # Continue anyway, we might have dummy data

    def _on_ip_locale_loaded(self, ip_locale_data):
        """Handle successful loading of IP locale data."""
        self.logger.info("IP locale data loaded successfully")
        self.state.compatibility.ip_locale = ip_locale_data

    def _on_network_error(self, error_msg: str):
        """Handle network errors."""
        self.logger.warning(f"Network error (non-fatal): {error_msg}")
        # Network errors are usually non-fatal, continue with checks

    def _on_all_checks_completed(self):
        """Handle completion of all checks."""
        self.logger.info("All checks completed, finalizing...")
        if self.status_label:
            self.status_label.setText("Finalizing compatibility check...")
        if self.progress_bar:
            self.progress_bar.setValue(95)
        
        # Small delay before finalizing
        QTimer.singleShot(500, self._finalize_and_parse_errors)

    def _finalize_and_parse_errors(self):
        """Finalize checks and navigate to next page or show errors."""
        try:
            self.logger.info("Finalizing checks and parsing errors")
            
            # Process compatibility results
            self._process_compatibility_results()
            
            # Update progress to 100%
            if self.progress_bar:
                self.progress_bar.setValue(100)
            if self.status_label:
                self.status_label.setText("Compatibility check complete!")
            
            # Mark navigation as completed and navigate
            self._navigation_completed = True
            
            # Navigate after a short delay
            QTimer.singleShot(1000, self._safe_navigate_next)
            
        except Exception as e:
            self.logger.error(f"Error finalizing checks: {e}")
            self._show_error(f"Failed to finalize compatibility check: {e}")

    def _process_compatibility_results(self):
        """Process the compatibility check results."""
        self.logger.info("Processing compatibility results...")
        
        if self.done_checks:
            self.logger.info("Processing done_checks")
            errors = []
            
            if not self.skip_check:
                self.logger.info("Running error checks")
                # Check for compatibility errors (same logic as original)
                if self.done_checks.checks[CheckType.ARCH].returncode != 0:
                    errors.append("Architecture check failed")
                elif (
                    self.done_checks.checks[CheckType.ARCH].result
                    not in self.app_config.ui.accepted_architectures
                ):
                    errors.append("Unsupported architecture")
                    
                if self.done_checks.checks[CheckType.UEFI].returncode != 0:
                    errors.append("UEFI check failed")
                elif self.done_checks.checks[CheckType.UEFI].result != "uefi":
                    errors.append("UEFI boot required")
                    
                if self.done_checks.checks[CheckType.RAM].returncode != 0:
                    errors.append("RAM check failed")
                elif (
                    self.done_checks.checks[CheckType.RAM].result
                    < self.app_config.app.minimal_required_ram
                ):
                    errors.append("Insufficient RAM")
                    
                if self.done_checks.checks[CheckType.SPACE].returncode != 0:
                    errors.append("Disk space check failed")
                elif (
                    self.done_checks.checks[CheckType.SPACE].result
                    < self.app_config.app.minimal_required_space
                ):
                    errors.append("Insufficient disk space")
                    
                if self.done_checks.checks[CheckType.RESIZABLE].returncode != 0:
                    errors.append("Resizable partition check failed")
                elif (
                    self.done_checks.checks[CheckType.RESIZABLE].result
                    < self.app_config.app.minimal_required_space
                ):
                    errors.append("No resizable partitions found")
            else:
                self.logger.info("Skipping error checks due to skip_check flag")
            
            if not errors:
                self.logger.info("No errors found, proceeding with spin filtering")
                self.state.compatibility.done_checks = self.done_checks
                
                # Filter spins (like the original does)
                self._filter_accepted_spins()
                
            else:
                self.logger.info(f"Found {len(errors)} errors")
                # Navigate to error page when it's fully implemented
                self._show_error(f"Compatibility errors found: {', '.join(errors)}")
                # TODO: Navigate to error page like original does:
                # from pages.pyside6_page_error import PySide6PageError
                # self.navigate_to(PySide6PageError)
        else:
            # No checks completed, just proceed (like original)
            self.logger.info("No done_checks, proceeding anyway")
            # Navigate next directly
            self.logger.info("About to navigate_next() (no checks done)")
            QTimer.singleShot(10, self._safe_navigate_next)

    def _filter_accepted_spins(self):
        """Filter and set accepted spins (like the original PageCheck does)."""
        if not self.state.compatibility.all_spins:
            self.logger.warning("No spins available to filter")
            return
        
        accepted_spins = []
        live_os_installer_index = None
        
        # Accept all spins for now (the original has more complex filtering)
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
        
        if live_os_installer_index is not None:
            self.state.compatibility.live_os_installer_spin = self.state.compatibility.accepted_spins[
                live_os_installer_index
            ]
        
        self.logger.info(f"Filtered to {len(self.state.compatibility.accepted_spins)} accepted spins")
                
        self.logger.info("About to navigate_next()")
        # Use QTimer to delay navigation slightly (equivalent to self.after(10, ...))
        QTimer.singleShot(10, self._safe_navigate_next)

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

    def _safe_navigate_next(self):
        """Safely navigate to next page, preventing multiple navigation calls."""
        if self._navigation_requested:
            self.logger.info("Navigation already requested, ignoring duplicate call")
            return
        
        self._navigation_requested = True
        self.logger.info("Requesting navigation to next page")
        self.navigate_next()

    def show_validation_error(self, message: str):
        """Show validation error to user."""
        QMessageBox.warning(self, "Validation Error", message)
