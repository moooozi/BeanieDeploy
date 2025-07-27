"""
Type-safe Installation Service.

This replaces the current kwargs-based installation.py with a robust,
maintainable service that uses proper dependency injection and type safety.
"""
from pathlib import Path
from typing import Optional, Protocol

from config.settings import get_config
from models.installation_context import (
    InstallationContext, 
    InstallationResult, 
    InstallationStage,
    DownloadableFile
)
from services import disk, boot, config_builders
from services import file as file_service
from services.download import DownloadService, DownloadProgress
from services.partition import partition_procedure


class ProgressCallback(Protocol):
    """Protocol for progress update callbacks."""
    def __call__(self, stage: InstallationStage, percent: float, message: str) -> None:
        """Called when installation progress updates."""
        ...


class DownloadProgressCallback(Protocol):
    """Protocol for download progress callbacks."""
    def __call__(self, file_name: str, percent: float, speed: float, eta: float) -> None:
        """Called when download progress updates."""
        ...


class HashVerificationError(Exception):
    """Raised when file hash verification fails."""
    def __init__(self, file_path: str, expected: str, actual: str):
        self.file_path = file_path
        self.expected = expected
        self.actual = actual
        super().__init__(f"Hash mismatch for {file_path}: expected {expected}, got {actual}")


class InstallationService:
    """
    Type-safe installation service.
    
    This service handles the complete installation process using a robust
    InstallationContext instead of fragile kwargs/dict passing.
    """
    
    def __init__(
        self, 
        progress_callback: Optional[ProgressCallback] = None,
        download_callback: Optional[DownloadProgressCallback] = None
    ):
        """
        Initialize the installation service.
        
        Args:
            progress_callback: Called for general progress updates
            download_callback: Called for download-specific progress updates
        """
        self.config = get_config()
        self.progress_callback = progress_callback
        self.download_callback = download_callback
        self.download_service = DownloadService(self.config)
        
    def install(self, context: InstallationContext) -> InstallationResult:
        """
        Execute the complete installation process.
        
        Args:
            context: Type-safe installation context with all needed data
            
        Returns:
            InstallationResult indicating success/failure and details
        """
        try:
            self._update_progress(context, InstallationStage.INITIALIZING, 0, "Initializing installation...")
            
            # Prepare work directory
            file_service.mkdir(context.paths.work_dir)
            
            # Download required files
            download_result = self._download_files(context)
            if not download_result.success:
                return download_result
            
            # Execute partitioning
            partition_result = self._setup_partitioning(context)
            if not partition_result.success:
                return partition_result
                
            # Copy installation files
            copy_result = self._copy_installation_files(context)
            if not copy_result.success:
                return copy_result
            
            # Create boot entry
            boot_result = self._create_boot_entry(context)
            if not boot_result.success:
                return boot_result
            
            self._update_progress(context, InstallationStage.INSTALL_DONE, 100, "Installation completed successfully!")
            return InstallationResult.success_result(boot_result.boot_entry_created)
            
        except Exception as e:
            error_msg = f"Unexpected error during installation: {str(e)}"
            return InstallationResult.error_result(context.current_stage, error_msg)
    
    def _download_files(self, context: InstallationContext) -> InstallationResult:
        """Download all required files."""
        try:
            self._update_progress(context, InstallationStage.DOWNLOADING, 10, "Starting downloads...")
            
            for i, file_info in enumerate(context.downloadable_files):
                context.current_file_index = i
                
                # Create destination directory
                file_service.mkdir(file_info.destination_dir)
                
                # Check if file already exists with correct hash
                if file_info.full_path.exists():
                    if self._verify_file_hash(file_info):
                        continue  # File is already downloaded and verified
                
                # Download the file
                self._download_single_file(file_info, context)
                
                # Verify downloaded file
                if file_info.expected_hash and not self._verify_file_hash(file_info):
                    actual_hash = file_service.get_sha256_hash(str(file_info.full_path))
                    raise HashVerificationError(
                        str(file_info.full_path), 
                        file_info.expected_hash, 
                        actual_hash
                    )
            
            progress = 40  # Downloads complete at 40%
            self._update_progress(context, InstallationStage.VERIFYING_CHECKSUM, progress, "All files downloaded and verified")
            return InstallationResult.success_result()
            
        except HashVerificationError as e:
            return InstallationResult.error_result(InstallationStage.VERIFYING_CHECKSUM, str(e))
        except Exception as e:
            return InstallationResult.error_result(InstallationStage.DOWNLOADING, f"Download failed: {str(e)}")
    
    def _download_single_file(self, file_info: DownloadableFile, context: InstallationContext) -> None:
        """Download a single file with progress tracking."""
        def progress_adapter(progress: DownloadProgress) -> None:
            """Adapt DownloadProgress to download callback format."""
            if self.download_callback:
                self.download_callback(
                    progress.filename,
                    progress.percentage,
                    progress.speed_bytes_per_sec,
                    progress.eta_seconds
                )
        
        # Use the new download service
        self.download_service.download_file(
            url=file_info.download_url,
            destination=file_info.destination_dir,
            filename=file_info.file_name,
            expected_hash=file_info.expected_hash,
            progress_callback=progress_adapter
        )
    
    def _verify_file_hash(self, file_info: DownloadableFile) -> bool:
        """Verify file hash matches expected value."""
        if not file_info.expected_hash:
            return True  # No hash to verify
            
        if not file_info.full_path.exists():
            return False
            
        actual_hash = file_service.get_sha256_hash(str(file_info.full_path))
        return actual_hash.lower().strip() == file_info.expected_hash.lower().strip()
    
    def _setup_partitioning(self, context: InstallationContext) -> InstallationResult:
        """Set up partitioning for installation."""
        try:
            self._update_progress(context, InstallationStage.CREATING_TMP_PART, 50, "Creating temporary partition...")
            
            # Execute partitioning using the partition context
            partitioning_results = partition_procedure(**vars(context.partition))
            
            # Store the temporary partition letter for later use
            context.tmp_part_letter = partitioning_results.tmp_part_letter
            
            self._update_progress(context, InstallationStage.CREATING_TMP_PART, 60, "Temporary partition created")
            return InstallationResult.success_result()
            
        except Exception as e:
            return InstallationResult.error_result(
                InstallationStage.CREATING_TMP_PART, 
                f"Partitioning failed: {str(e)}"
            )
    
    def _copy_installation_files(self, context: InstallationContext) -> InstallationResult:
        """Copy installation files to temporary partition."""
        try:
            self._update_progress(context, InstallationStage.COPYING_TO_TMP_PART, 70, "Copying installation files...")
            
            # Get file paths
            installer_iso_path = context.get_installer_iso_path()
            if not installer_iso_path:
                return InstallationResult.error_result(
                    InstallationStage.COPYING_TO_TMP_PART,
                    "No installer ISO found"
                )
            
            # Mount installer ISO
            installer_mount_letter = disk.mount_iso(str(installer_iso_path))
            source_files = f"{installer_mount_letter}:\\"
            destination = f"{context.tmp_part_letter}:\\"
            
            try:
                # Copy installer files
                file_service.copy_files(source=source_files, destination=destination)
                
                # Handle live image if needed
                if context.is_live_image_installation():
                    live_iso_path = context.get_live_iso_path()
                    if live_iso_path:
                        live_image_mount_letter = disk.mount_iso(str(live_iso_path))
                        try:
                            # Copy live image files as needed
                            live_image_source = f"{live_image_mount_letter}:\\LiveOS\\"
                            destination = f"{context.tmp_part_letter}:\\LiveOS\\"
                            file_service.copy_files(source=live_image_source, destination=destination)
                        finally:
                            disk.unmount_iso(str(live_iso_path))
                
                # Copy additional files
                self._copy_additional_files(context, destination)
                
                # Generate configuration files
                self._generate_config_files(context, destination)
                
            finally:
                # Always unmount the installer ISO
                disk.unmount_iso(str(installer_iso_path))
                # Remove temporary drive letter if it exists
                if context.tmp_part_letter:
                    disk.remove_drive_letter(context.tmp_part_letter)
            
            self._update_progress(context, InstallationStage.COPYING_TO_TMP_PART, 85, "Files copied successfully")
            return InstallationResult.success_result()
            
        except Exception as e:
            return InstallationResult.error_result(
                InstallationStage.COPYING_TO_TMP_PART,
                f"File copying failed: {str(e)}"
            )
    
    def _copy_additional_files(self, context: InstallationContext, destination: str) -> None:
        """Copy additional files like RPMs and WiFi profiles."""
        destination_path = Path(destination)
        
        # Copy RPM files if specified
        if context.paths.rpm_source_dir and context.paths.rpm_dst_dir_name:
            rpm_dst_path = destination_path / context.paths.rpm_dst_dir_name
            file_service.mkdir(rpm_dst_path)
            file_service.copy_files(
                source=str(context.paths.rpm_source_dir), 
                destination=str(rpm_dst_path)
            )
        
        # Copy WiFi profiles if specified
        if context.paths.wifi_profiles_src_dir and context.paths.wifi_profiles_dst_dir_name:
            wifi_dst_path = destination_path / context.paths.wifi_profiles_dst_dir_name
            file_service.copy_files(
                source=str(context.paths.wifi_profiles_src_dir),
                destination=str(wifi_dst_path)
            )
    
    def _generate_config_files(self, context: InstallationContext, destination: str) -> None:
        """Generate GRUB and kickstart configuration files."""
        destination_path = Path(destination)
        
        # Generate GRUB config
        grub_cfg_path = destination_path / context.paths.grub_cfg_relative_path
        grub_cfg_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_service.set_file_readonly(str(grub_cfg_path), False)
        grub_cfg_content = config_builders.build_grub_cfg_file(
            context.partition.temp_part_label,
            is_autoinst=bool(context.kickstart.partition_method != "custom")
        )
        grub_cfg_path.write_text(grub_cfg_content)
        file_service.set_file_readonly(str(grub_cfg_path), True)
        
        # Generate kickstart config if needed
        if context.kickstart.partition_method != "custom":
            kickstart_path = destination_path / context.paths.kickstart_cfg_relative_path
            kickstart_content = config_builders.build_autoinstall_ks_file(**vars(context.kickstart))
            kickstart_path.write_text(kickstart_content)
    
    def _create_boot_entry(self, context: InstallationContext) -> InstallationResult:
        """Create boot entry for the installation."""
        try:
            self._update_progress(context, InstallationStage.ADDING_TMP_BOOT_ENTRY, 90, "Creating boot entry...")
            
            # Get current boot information
            boot_entries = boot.get_boot_entries()
            
            # Find Windows boot entry to duplicate
            windows_entry = None
            for entry in boot_entries:
                if "windows" in entry["description"].lower():
                    windows_entry = entry["entry_id"].replace("Boot", "")
                    break
            
            if not windows_entry:
                return InstallationResult.error_result(
                    InstallationStage.ADDING_TMP_BOOT_ENTRY,
                    "Could not find Windows boot entry to duplicate"
                )
            
            # Create new boot entry
            new_boot_entry = boot.create_boot_entry(
                self.config.app.name,
                context.paths.efi_file_relative_path,
                windows_entry,
            )
            
            # Set it as next boot option
            boot.set_bootnext(new_boot_entry)
            
            return InstallationResult.success_result(new_boot_entry)
            
        except Exception as e:
            return InstallationResult.error_result(
                InstallationStage.ADDING_TMP_BOOT_ENTRY,
                f"Boot entry creation failed: {str(e)}"
            )
    
    def _update_progress(
        self, 
        context: InstallationContext, 
        stage: InstallationStage, 
        percent: float, 
        message: str
    ) -> None:
        """Update progress and notify callback."""
        context.update_progress(stage, percent)
        
        if self.progress_callback:
            self.progress_callback(stage, percent, message)


# Factory function to create installation service with GUI callbacks
def create_installation_service_for_gui(
    progress_callback: Optional[ProgressCallback] = None,
    download_callback: Optional[DownloadProgressCallback] = None
) -> InstallationService:
    """
    Factory function to create an installation service configured for GUI use.
    
    Args:
        progress_callback: Called for general progress updates
        download_callback: Called for download-specific progress updates
        
    Returns:
        Configured InstallationService instance
    """
    return InstallationService(
        progress_callback=progress_callback,
        download_callback=download_callback
    )
