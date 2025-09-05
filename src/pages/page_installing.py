"""
Modern, type-safe installation page using InstallationContext.

This replaces the fragile kwargs/dict approach with robust type-safe classes.
"""

import pathlib
import pickle
import tempfile
from models.speed_unit import SpeedUnit
from models.installation_context import (
    InstallationContext,
    InstallationStage,
    InstallationResult,
)
from services.installation_service import InstallationService
from templates.generic_page_layout import GenericPageLayout
from services.system import is_admin, get_admin
import tkinter as tk
from models.page import Page
from tkinter_templates import TextLabel
from async_operations import AsyncOperation
import customtkinter as ctk
import pendulum

class PageInstalling(Page):
    """
    Modern installation page using type-safe InstallationContext.

    This replaces the old fragile approach with proper dependency injection
    and type safety.
    """

    def __init__(self, parent, page_name, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)
        self.installation_context: InstallationContext = None # type: ignore
        self.installation_service: InstallationService = None # type: ignore
        self.install_job_var = tk.StringVar(parent)
        self.current_stage = InstallationStage.INITIALIZING


    def _get_installation_context(self) -> InstallationContext:
        """Infer installation context."""
        if not self.installation_context:
            try:
                self.installation_context = InstallationContext.from_application_state(
                    self.state
                )

            except Exception as e:
                print("Failed to create installation context: ", e)
                self.logger.error(f"Failed to create installation context: {e}")
                self._show_error_and_navigate(
                    f"Failed to prepare installation: {str(e)}"
                )
        else:
            self.logger.info("Using pre-provided installation context")

        return self.installation_context

    def init_page(self):
        """Initialize the installation page with proper error handling."""
        self.update()

        # Create installation context from application state if not already provided
        self.installation_context = self._get_installation_context()
        # Set up GUI
        page_layout = GenericPageLayout(self, self.LN.install_running)
        page_frame = page_layout.content_frame

        self.progressbar_install = ctk.CTkProgressBar(
            page_frame, orientation="horizontal", mode="determinate"
        )
        self.progressbar_install.pack(pady=(0, 20), fill="both")

        install_label = TextLabel(page_frame, var=self.install_job_var)
        install_label.pack(pady=0, padx=10)

        self.progressbar_install.set(0)
        self.update()

        # Check for admin privileges
        if not is_admin():
            self._handle_admin_elevation()
            return

        # Start installation process
        self._start_installation()

    def _handle_admin_elevation(self) -> None:
        """Handle elevation to admin privileges."""
        try:
            # Serialize installation context for admin process
            with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as temp_file:
                pickle.dump(self.installation_context, temp_file)
                temp_file_path = pathlib.Path(temp_file.name).absolute()

            args_string = f'--installation_context "{temp_file_path}"'
            get_admin(args_string)

        except Exception as e:
            self.logger.error(f"Failed to elevate to admin: {e}")
            self._show_error_and_navigate(f"Failed to get admin privileges: {str(e)}")

    def _start_installation(self) -> None:
        """Start the installation process with proper callbacks."""
        try:
            # Create installation service with GUI callbacks
            self.installation_service = InstallationService(
                progress_callback=self._on_progress_update,
                download_callback=self._on_download_progress,
            )

            # Start installation in background
            AsyncOperation.run(
                function=self._run_installation,
                use_threading=True,
            )

        except Exception as e:
            self.logger.error(f"Failed to start installation: {e}")
            self._show_error_and_navigate(f"Installation failed to start: {str(e)}")

    def _run_installation(self) -> None:
        """Run the installation process (called in background thread)."""
        try:
            # Type guards to ensure we have valid objects
            if not self.installation_service:
                raise RuntimeError("Installation service not initialized")
            if not self.installation_context:
                raise RuntimeError("Installation context not initialized")

            result = self.installation_service.install(self.installation_context)

            # Schedule GUI update on main thread
            self.after(0, self._on_installation_complete, result)

        except Exception as e:
            self.logger.error(f"Installation failed with exception: {e}")
            error_result = InstallationResult.error_result(
                self.current_stage, f"Installation failed: {str(e)}"
            )
            self.after(0, self._on_installation_complete, error_result)

    def _on_progress_update(
        self, stage: InstallationStage, percent: float, message: str
    ) -> None:
        """Handle general progress updates (called from background thread)."""
        # Schedule GUI update on main thread
        self.after(0, self._update_gui_progress, stage, percent, message)

    def _on_download_progress(
        self, index: int, file_name: str, percent: float, speed: float, eta: float
    ) -> None:
        """Handle download-specific progress updates (called from background thread)."""
        # Schedule GUI update on main thread
        self.after(0, self._update_download_gui, index, file_name, percent, speed, eta)

    def _update_download_gui(
        self, index: int, file_name: str, percent: float, speed: float, eta: float
    ) -> None:
        """Update download-specific GUI (called on main thread)."""
        try:
            formatted_speed = SpeedUnit(speed).to_human_readable()
            formatted_eta = pendulum.duration(seconds=eta).in_words() if eta > 0 else "N/A"

            message = (
                f"{self.LN.job_dl_install_media}\n"
                f"File {index + 1} of {len(self.installation_context.downloadable_files)}\n"
                f"Name: {file_name}\n"
                f"Progress: {percent:.1f}%\n"
                f"Speed: {formatted_speed}\n"
                f"ETA: {formatted_eta}"
            )
            self.install_job_var.set(message)
            real_progress = self._real_progress(index, percent) * 0.80 # 80% for downloads
            self.progressbar_install.set(0.1 + real_progress)
            self.update()

        except Exception as e:
            print(f"Failed to update download GUI: {e}")
            self.logger.warning(f"Failed to update download GUI: {e}")

    def _real_progress(self, index: int, percent: float) -> float:
        """Calculate real progress across all files."""
        if not self.installation_context.downloadable_files:
            print("No downloadable files in installation context.")
            return 0.0

        total_files = len(self.installation_context.downloadable_files)
        if index >= total_files:
            return 1.0

        downloadable_files_sizes = [df.size_bytes for df in self.installation_context.downloadable_files]

        # Sum sizes of all previous files
        if index == 0:
            completed_size = 0
        else:
            completed_size = sum(
                size for size in downloadable_files_sizes[:index] if size
            )
        current_file_size = downloadable_files_sizes[index] or 0
        current_progress = (percent / 100.0) * current_file_size if current_file_size else 0

        total_size = sum(size for size in downloadable_files_sizes if size)
        if total_size == 0:
            return 0.0

        overall_progress = (completed_size + current_progress) / total_size
        return overall_progress

    def _update_gui_progress(
        self, stage: InstallationStage, percent: float, message: str
    ) -> None:
        """Update GUI progress (called on main thread)."""
        self.current_stage = stage
        self.progressbar_install.set(percent / 100.0)
        self.install_job_var.set(message)
        self.update()


    def _on_installation_complete(self, result: InstallationResult) -> None:
        """Handle installation completion (called on main thread)."""
        if result.success:
            self.logger.info("Installation completed successfully")
            self.progressbar_install.set(1.0)
            self.install_job_var.set("Installation completed successfully!")
            self.update()

            # Navigate to next page after short delay
            self.after(1000, self.navigate_next)
        else:
            self.logger.error(f"Installation failed: {result.error_message}")
            self._show_error_and_navigate(
                f"Installation failed: {result.error_message}"
            )

    def _show_error_and_navigate(self, error_message: str) -> None:
        """Show error and navigate to error page."""
        self.logger.error(error_message)
        # TODO: Set error on error page and navigate there
        # For now, just show in the install status
        self.install_job_var.set(f"ERROR: {error_message}")

    # Modern methods for new installation system
    def set_installation_context(self, installation_context):
        """Set the installation context for modern type-safe installation."""
        self.logger.info("Setting installation context for type-safe installation")
        self.installation_context = installation_context
