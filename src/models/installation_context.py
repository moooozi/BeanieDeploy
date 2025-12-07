"""
Installation Context - Type-safe installation data management.

This module provides a robust, type-safe way to manage all installation data
without relying on dictionaries or kwargs passing.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from services.partition import PartitioningResult, TemporaryPartition

from .downloadable_file import DownloadableFile
from .kickstart import KickstartConfig
from .partition import Partition
from .spin import Spin


class InstallationStage(Enum):
    """Installation stages for progress tracking."""

    INITIALIZING = "initializing"
    DOWNLOADING = "downloading"
    VERIFYING_CHECKSUM = "verifying_checksum"
    CREATING_TMP_PART = "creating_tmp_part"
    COPYING_TO_TMP_PART = "copying_to_tmp_part"
    ADDING_TMP_BOOT_ENTRY = "adding_tmp_boot_entry"
    CLEANUP = "cleanup"
    INSTALL_DONE = "install_done"


@dataclass
class InstallationPaths:
    """All file paths needed for installation."""

    work_dir: Path
    wifi_profiles_src_dir: Path | None = None

    # Relative paths within the installation
    grub_cfg_relative_path: str = "boot/grub2/grub.cfg"
    kickstart_cfg_relative_path: str = "ks.cfg"
    efi_file_relative_path: str = "EFI/BOOT/bootx64.efi"

    # Destination directory names
    wifi_profiles_dst_dir_name: str = "wifi_profiles"


@dataclass
class InstallationContext:
    """
    Complete type-safe context for installation process.

    This replaces the fragile kwargs/dict approach with a robust,
    type-safe data structure that's easy to validate and maintain.
    """

    # Core configuration
    kickstart: KickstartConfig
    partition: Partition
    tmp_part: TemporaryPartition
    selected_spin: Spin
    live_os_installer_spin: Spin | None = None

    # File management
    paths: InstallationPaths = field(default_factory=lambda: InstallationPaths(Path()))
    downloadable_files: list[DownloadableFile] = field(default_factory=list)

    # Installation state
    current_stage: InstallationStage = InstallationStage.INITIALIZING
    progress_percent: float = 0.0
    current_file_index: int = 0
    tmp_part_already_created: bool = False
    partitioning_result: PartitioningResult | None = None

    # Progress tracking
    total_download_size: int = 0
    downloaded_size: int = 0

    def __post_init__(self):
        """Initialize the context after creation."""
        self._prepare_download_files()
        self._calculate_total_size()

    def _prepare_download_files(self) -> None:
        """Prepare the list of files that need to be downloaded."""
        self.downloadable_files.clear()

        if self.selected_spin.is_live_img and self.live_os_installer_spin:
            # For live images, we need both installer and live ISO
            installer_file = DownloadableFile.from_spin(
                self.live_os_installer_spin,
                file_hint="installer_iso",
                destination_dir=self.paths.work_dir,
            )
            self.downloadable_files.append(installer_file)

            live_file = DownloadableFile.from_spin(
                self.selected_spin,
                file_hint="live_img_iso",
                destination_dir=self.paths.work_dir,
            )
            self.downloadable_files.append(live_file)
        else:
            # For regular installs, just the installer ISO
            installer_file = DownloadableFile.from_spin(
                self.selected_spin,
                file_hint="installer_iso",
                destination_dir=self.paths.work_dir,
            )
            self.downloadable_files.append(installer_file)

    def _calculate_total_size(self) -> None:
        """Calculate total download size."""
        self.total_download_size = sum(
            file.size_bytes for file in self.downloadable_files
        )

    def get_installer_iso_path(self) -> Path | None:
        """Get the path to the installer ISO."""
        for file in self.downloadable_files:
            if file.file_hint == "installer_iso":
                return file.full_path
        return None

    def get_live_iso_path(self) -> Path | None:
        """Get the path to the live ISO."""
        for file in self.downloadable_files:
            if file.file_hint == "live_img_iso":
                return file.full_path
        return None

    def is_live_image_installation(self) -> bool:
        """Check if this is a live image installation."""
        return (
            self.selected_spin.is_live_img and self.live_os_installer_spin is not None
        )

    def update_progress(
        self, stage: InstallationStage, percent: float | None = None
    ) -> None:
        """Update installation progress."""
        self.current_stage = stage
        if percent is not None:
            self.progress_percent = percent

    def validate(self) -> list[str]:
        """
        Validate the installation context.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not self.selected_spin:
            errors.append("No spin selected for installation")

        if not self.kickstart:
            errors.append("No kickstart configuration provided")

        if not self.partition:
            errors.append("No partition configuration provided")

        if not self.paths.work_dir:
            errors.append("No work directory specified")

        if not self.downloadable_files:
            errors.append("No files to download")

        # Validate file URLs and paths
        for file in self.downloadable_files:
            if not file.download_url:
                errors.append(f"No download URL for file: {file.file_name}")
            if not file.destination_dir:
                errors.append(f"No destination directory for file: {file.file_name}")

        return errors

    @classmethod
    def from_application_state(cls, state) -> "InstallationContext":
        """
        Create InstallationContext from the application state.

        This method replaces the current fragile kwargs approach.
        """
        from config.settings import get_config

        config = get_config()

        # Create paths configuration
        paths = InstallationPaths(
            work_dir=config.paths.work_dir,
            wifi_profiles_src_dir=getattr(config.paths, "wifi_profiles_dir", None),
        )

        # Sync partitioning method from install_options to kickstart if not set
        kickstart = state.installation.kickstart
        if (
            kickstart
            and not kickstart.partitioning.method
            and state.installation.install_options
        ):
            kickstart.partitioning.method = (
                state.installation.install_options.partition_method
            )

        # Sync ostree_args from selected_spin to kickstart if spin has ostree_args
        if (
            kickstart
            and state.installation.selected_spin
            and state.installation.selected_spin.ostree_args
        ):
            kickstart.ostree_args = state.installation.selected_spin.ostree_args

        return cls(
            kickstart=kickstart,
            partition=state.installation.partition,
            selected_spin=state.installation.selected_spin,
            live_os_installer_spin=state.compatibility.live_os_installer_spin,
            paths=paths,
            tmp_part=state.installation.tmp_part,
        )


@dataclass
class InstallationResult:
    """Result of installation process."""

    success: bool
    stage_completed: InstallationStage
    error_message: str | None = None
    boot_entry_created: str | None = None

    @classmethod
    def success_result(cls, boot_entry: str | None = None) -> "InstallationResult":
        """Create a successful installation result."""
        return cls(
            success=True,
            stage_completed=InstallationStage.INSTALL_DONE,
            boot_entry_created=boot_entry,
        )

    @classmethod
    def error_result(cls, stage: InstallationStage, error: str) -> "InstallationResult":
        """Create an error installation result."""
        return cls(success=False, stage_completed=stage, error_message=error)
