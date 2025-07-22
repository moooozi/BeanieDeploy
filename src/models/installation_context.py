"""
Installation Context - Type-safe installation data management.

This module provides a robust, type-safe way to manage all installation data
without relying on dictionaries or kwargs passing.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
from enum import Enum

from models.kickstart import Kickstart
from models.partition import Partition
from models.spin import Spin


class InstallationStage(Enum):
    """Installation stages for progress tracking."""
    INITIALIZING = "initializing"
    DOWNLOADING = "downloading" 
    VERIFYING_CHECKSUM = "verifying_checksum"
    CREATING_TMP_PART = "creating_tmp_part"
    COPYING_TO_TMP_PART = "copying_to_tmp_part"
    ADDING_TMP_BOOT_ENTRY = "adding_tmp_boot_entry"
    INSTALL_DONE = "install_done"


@dataclass
class DownloadableFile:
    """Represents a file that needs to be downloaded for installation."""
    file_name: str
    file_hint: str  # Purpose: "installer_iso", "live_img_iso", etc.
    download_url: str
    destination_dir: Path
    expected_hash: str
    size_bytes: int
    
    @property
    def full_path(self) -> Path:
        """Get the full path where this file will be saved."""
        return self.destination_dir / self.file_name
    
    @classmethod
    def from_spin(
        cls,
        spin: Spin,
        file_hint: str,
        destination_dir: Path,
        file_name: Optional[str] = None,
    ) -> "DownloadableFile":
        """Create a DownloadableFile from a Spin object."""
        return cls(
            file_name=file_name or f"{spin.name.replace(' ', '_')}.iso",
            file_hint=file_hint,
            download_url=spin.dl_link,
            destination_dir=destination_dir,
            expected_hash=spin.hash256,
            size_bytes=int(spin.size) if spin.size.isdigit() else 0,
        )


@dataclass
class InstallationPaths:
    """All file paths needed for installation."""
    work_dir: Path
    rpm_source_dir: Optional[Path] = None
    wifi_profiles_src_dir: Optional[Path] = None
    
    # Relative paths within the installation
    grub_cfg_relative_path: str = "boot/grub2/grub.cfg"
    kickstart_cfg_relative_path: str = "ks.cfg"
    efi_file_relative_path: str = "EFI/BOOT/bootx64.efi"
    
    # Destination directory names
    rpm_dst_dir_name: str = "additional_rpms"
    wifi_profiles_dst_dir_name: str = "wifi_profiles"


@dataclass 
class InstallationContext:
    """
    Complete type-safe context for installation process.
    
    This replaces the fragile kwargs/dict approach with a robust,
    type-safe data structure that's easy to validate and maintain.
    """
    # Core configuration
    kickstart: Kickstart
    partition: Partition
    selected_spin: Spin
    live_os_installer_spin: Optional[Spin] = None
    
    # File management
    paths: InstallationPaths = field(default_factory=lambda: InstallationPaths(Path(".")))
    downloadable_files: List[DownloadableFile] = field(default_factory=list)
    
    # Installation state
    current_stage: InstallationStage = InstallationStage.INITIALIZING
    progress_percent: float = 0.0
    current_file_index: int = 0
    tmp_part_letter: Optional[str] = None  # Set during partitioning
    
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
                file_name="install.iso"
            )
            self.downloadable_files.append(installer_file)
            
            live_file = DownloadableFile.from_spin(
                self.selected_spin,
                file_hint="live_img_iso", 
                destination_dir=self.paths.work_dir,
                file_name="live.iso"
            )
            self.downloadable_files.append(live_file)
        else:
            # For regular installs, just the installer ISO
            installer_file = DownloadableFile.from_spin(
                self.selected_spin,
                file_hint="installer_iso",
                destination_dir=self.paths.work_dir,
                file_name="install.iso"
            )
            self.downloadable_files.append(installer_file)
    
    def _calculate_total_size(self) -> None:
        """Calculate total download size."""
        self.total_download_size = sum(file.size_bytes for file in self.downloadable_files)
    
    def get_installer_iso_path(self) -> Optional[Path]:
        """Get the path to the installer ISO."""
        for file in self.downloadable_files:
            if file.file_hint == "installer_iso":
                return file.full_path
        return None
    
    def get_live_iso_path(self) -> Optional[Path]:
        """Get the path to the live ISO."""
        for file in self.downloadable_files:
            if file.file_hint == "live_img_iso":
                return file.full_path
        return None
    
    def is_live_image_installation(self) -> bool:
        """Check if this is a live image installation."""
        return self.selected_spin.is_live_img and self.live_os_installer_spin is not None
    
    def update_progress(self, stage: InstallationStage, percent: Optional[float] = None) -> None:
        """Update installation progress."""
        self.current_stage = stage
        if percent is not None:
            self.progress_percent = percent
    
    def bvalidate(self) -> List[str]:
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
            rpm_source_dir=getattr(config.paths, 'rpm_source_dir', None),
            wifi_profiles_src_dir=getattr(config.paths, 'wifi_profiles_dir', None),
        )
        
        return cls(
            kickstart=state.installation.kickstart,
            partition=state.installation.partition,
            selected_spin=state.installation.selected_spin,
            live_os_installer_spin=state.compatibility.live_os_installer_spin,
            paths=paths,
        )


@dataclass
class InstallationResult:
    """Result of installation process."""
    success: bool
    stage_completed: InstallationStage
    error_message: Optional[str] = None
    boot_entry_created: Optional[str] = None
    
    @classmethod
    def success_result(cls, boot_entry: Optional[str] = None) -> "InstallationResult":
        """Create a successful installation result."""
        return cls(
            success=True,
            stage_completed=InstallationStage.INSTALL_DONE,
            boot_entry_created=boot_entry
        )
    
    @classmethod
    def error_result(cls, stage: InstallationStage, error: str) -> "InstallationResult":
        """Create an error installation result."""
        return cls(
            success=False,
            stage_completed=stage,
            error_message=error
        )
