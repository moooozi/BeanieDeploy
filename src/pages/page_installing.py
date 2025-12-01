import logging
import threading
import tkinter as tk

import customtkinter as ctk

from models.installation_context import (
    InstallationContext,
    InstallationResult,
    InstallationStage,
)
from models.page import Page
from multilingual import _
from services.installation_service import InstallationService
from templates.generic_page_layout import GenericPageLayout
from tkinter_templates import TextLabel
from utils import format_eta, format_speed


class PageInstalling(Page):
    def __init__(self, parent, page_name, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)
        self.installation_context: InstallationContext = None  # type: ignore
        self.installation_service: InstallationService = None  # type: ignore
        self.install_job_var = tk.StringVar(parent)
        self.current_stage = InstallationStage.INITIALIZING

    def _get_installation_context(self) -> InstallationContext:
        """Infer installation context."""
        if not self.installation_context:
            self.installation_context = InstallationContext.from_application_state(
                self.state
            )
        else:
            logging.info("Using pre-provided installation context")

        return self.installation_context

    def init_page(self):
        """Initialize the installation page with proper error handling."""
        self.update()

        # Create installation context from application state if not already provided
        self.installation_context = self._get_installation_context()
        # Set up GUI
        page_layout = GenericPageLayout(self, _("install.running"))
        page_frame = page_layout.content_frame

        self.progressbar_install = ctk.CTkProgressBar(
            page_frame, orientation="horizontal", mode="determinate"
        )
        self.progressbar_install.pack(pady=(0, 20), fill="both")

        install_label = TextLabel(page_frame, var=self.install_job_var)
        install_label.pack(pady=0, padx=10)

        self.progressbar_install.set(0)
        self.update()

        # Start installation process
        self._start_installation()

    def _start_installation(self) -> None:
        """Start the installation process with proper callbacks."""
        # Create installation service with GUI callbacks
        self.installation_service = InstallationService(
            progress_callback=self._on_progress_update,
            download_callback=self._on_download_progress,
        )

        # Start installation in background
        threading.Thread(target=self._run_installation, daemon=True).start()

    def _run_installation(self) -> None:
        """Run the installation process (called in background thread)."""
        # Type guards to ensure we have valid objects
        if not self.installation_service:
            msg = "Installation service not initialized"
            raise RuntimeError(msg)
        if not self.installation_context:
            msg = "Installation context not initialized"
            raise RuntimeError(msg)

        result = self.installation_service.install(self.installation_context)

        # Schedule GUI update on main thread
        self.after(0, self._on_installation_complete, result)

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
        formatted_speed = format_speed(speed)
        formatted_eta = format_eta(eta) if eta > 0 else "N/A"

        message = (
            f"{_('job.dl.install.media')}\n"
            f"File {index + 1} of {len(self.installation_context.downloadable_files)}\n"
            f"Name: {file_name}\n"
            f"Progress: {percent:.1f}%\n"
            f"Speed: {formatted_speed}\n"
            f"ETA: {formatted_eta}"
        )
        self.install_job_var.set(message)
        real_progress = self._real_progress(index, percent) * 0.80  # 80% for downloads
        self.progressbar_install.set(0.1 + real_progress)
        self.update()

    def _real_progress(self, index: int, percent: float) -> float:
        """Calculate real progress across all files."""
        if not self.installation_context.downloadable_files:
            return 0.0

        total_files = len(self.installation_context.downloadable_files)
        if index >= total_files:
            return 1.0

        downloadable_files_sizes = [
            df.size_bytes for df in self.installation_context.downloadable_files
        ]

        # Sum sizes of all previous files
        if index == 0:
            completed_size = 0
        else:
            completed_size = sum(
                size for size in downloadable_files_sizes[:index] if size
            )
        current_file_size = downloadable_files_sizes[index] or 0
        current_progress = (
            (percent / 100.0) * current_file_size if current_file_size else 0
        )

        total_size = sum(size for size in downloadable_files_sizes if size)
        if total_size == 0:
            return 0.0

        return (completed_size + current_progress) / total_size

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
            logging.info("Installation completed successfully")
            self.progressbar_install.set(1.0)
            self.install_job_var.set("Installation completed successfully!")
            self.update()

            # Navigate to next page after short delay
            self.after(1000, self.navigate_next)
        else:
            logging.error(f"Installation failed: {result.error_message}")
            # Navigate to installation failed page
            from pages.page_install_failed import PageInstallFailed

            failed_page = self.navigate_to(PageInstallFailed)
            if failed_page:
                failed_page.set_error_message(result.error_message)
            # Also raise the error for PyInstaller popup
            msg = f"Installation failed: {result.error_message}"
            raise RuntimeError(msg)

    # Modern methods for new installation system
    def set_installation_context(self, installation_context):
        """Set the installation context for modern type-safe installation."""
        logging.info("Setting installation context for type-safe installation")
        self.installation_context = installation_context
