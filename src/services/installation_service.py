"""
Type-safe Installation Service.

This replaces the current kwargs-based installation.py with a robust,
maintainable service that uses proper dependency injection and type safety.
"""
import os
from pathlib import Path
import shutil
from typing import Callable, Optional

from config.settings import get_config
from models.installation_context import (
    InstallationContext, 
    InstallationResult, 
    InstallationStage,
    DownloadableFile
)
from services import disk, config_builders, elevated
from services import file as file_service
from services.download import DownloadService, DownloadProgress
from services.partition import partition_procedure, get_system_efi_drive_uuid
from services.disk import get_partition_info_by_guid

class HashVerificationError(Exception):
    """Raised when file hash verification fails."""
    def __init__(self, file_path: str, expected: str, actual: str):
        self.file_path = file_path
        self.expected = expected
        self.actual = actual
        super().__init__(f"Hash mismatch for {file_path}: expected {expected}, got {actual}")


def _create_boot_entry_elevated(tmp_part) -> int:
    """Create boot entry with elevated privileges."""
    import firmware_variables as fwvars
    import uuid

    # Get EFI partition details
    efi_guid = elevated.call(get_system_efi_drive_uuid)
    if not efi_guid:
        raise RuntimeError("Could not find system EFI partition")
    
    efi_part_info = elevated.call(get_partition_info_by_guid, args=(efi_guid,))
    if not efi_part_info:
        raise RuntimeError("Could not get EFI partition information")

    # Find the entry with "Windows Boot Manager" to duplicate
    windows_entry_id = None
    with fwvars.adjust_privileges():
        for entry_id in fwvars.get_boot_order():
            entry = fwvars.get_parsed_boot_entry(entry_id)
            if "windows boot manager" in entry.description.lower():
                windows_entry_id = entry_id
                break
        if windows_entry_id is None:
            raise RuntimeError("Windows Boot Manager entry not found")

        # Duplicate the entry
        new_entry = fwvars.get_parsed_boot_entry(windows_entry_id)
        new_entry.description = "Beanie Installer"
        new_entry.optional_data = b""

        # Edit the duplicate entry to point to our EFI file on EFI partition
        for path in new_entry.file_path_list.paths:
            if path.is_file_path():
                path.set_file_path("\\EFI\\beanie\\BOOT\\BOOTX64.EFI")
            elif path.is_hard_drive():
                hd_node = path.get_hard_drive_node()
                if hd_node:
                    # Set to EFI partition instead of temp partition
                    hd_node.partition_guid = efi_guid.lower()
                    hd_node.partition_number = efi_part_info['partition_number']
                    hd_node.partition_start_lba = efi_part_info['start_lba']
                    hd_node.partition_size_lba = efi_part_info['size_lba']
                    hd_node.partition_signature = uuid.UUID(efi_guid).bytes_le
                    path.set_hard_drive_node(hd_node)

        # Find an unused entry_id for the new entry
        new_entry_id = None
        for i in range(50):
            try:
                fwvars.get_boot_entry(i)
            except OSError as e:
                if hasattr(e, 'winerror') and e.winerror == 203:
                    new_entry_id = i
                    break
                # else: skip unknown errors
        if new_entry_id is None:
            new_entry_id = 16  # fallback

        fwvars.set_parsed_boot_entry(new_entry_id, new_entry)

        # Set the new entry as BootNext
        fwvars.set_boot_next(new_entry_id)
    
    return new_entry_id


class InstallationService:
    """
    Type-safe installation service.
    
    This service handles the complete installation process using a robust
    InstallationContext instead of fragile kwargs/dict passing.
    """
    
    def __init__(
        self, 
        progress_callback: Optional[Callable] = None,
        download_callback: Optional[Callable] = None,
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
        self._download_index: int = 0

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
            os.makedirs(context.paths.work_dir, exist_ok=True)

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
            
            # Cleanup temporary partition if it was created
            if context.tmp_part_already_created and context.tmp_part:
                self._cleanup_failed_installation(context)
            
            return InstallationResult.error_result(context.current_stage, error_msg)
    
    def _download_files(self, context: InstallationContext) -> InstallationResult:
        """Download all required files."""
        try:
            self._update_progress(context, InstallationStage.DOWNLOADING, 10, "Starting downloads...")
            
            for i, file_info in enumerate(context.downloadable_files):
                context.current_file_index = i
                
                # Create destination directory
                os.makedirs(file_info.destination_dir, exist_ok=True)

                # Check if file already exists with correct hash
                if file_info.full_path.exists():
                    if self._verify_file_hash(file_info):
                        self._download_index += 1
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
                self._download_index += 1
            
            progress = 40  # Downloads complete at 40%
            self._update_progress(context, InstallationStage.VERIFYING_CHECKSUM, progress, "All files downloaded and verified")
            return InstallationResult.success_result()
            
        except HashVerificationError as e:
            return InstallationResult.error_result(InstallationStage.VERIFYING_CHECKSUM, str(e))
        except Exception as e:
            return InstallationResult.error_result(InstallationStage.DOWNLOADING, f"Download failed: {str(e)}")
    
    def _download_single_file(self, file_info: DownloadableFile, context: InstallationContext) -> None:
        """Download a single file with progress tracking."""
        
        # Use the new download service
        self.download_service.download_file(
            url=file_info.download_url,
            destination=file_info.destination_dir,
            filename=file_info.file_name,
            expected_hash=file_info.expected_hash,
            progress_callback=self.progress_adapter
        )

    def progress_adapter(self, progress: DownloadProgress) -> None:
        """Adapt DownloadProgress to download callback format."""
        if self.download_callback:
            self.download_callback(
                self._download_index,
                progress.filename,
                progress.percentage,
                progress.speed_bytes_per_sec,
                progress.eta_seconds
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
            partitioning_results = elevated.call(partition_procedure, kwargs=vars(context.partition))
            
            # Store the temporary partition information for later use
            context.tmp_part = partitioning_results.tmp_part
            context.tmp_part_already_created = True
            context.partitioning_result = partitioning_results

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
            installer_mount_letter = elevated.call(disk.mount_iso, args=(str(installer_iso_path),))
            source_files = f"{installer_mount_letter}:\\"
            destination = context.tmp_part.mount_path
            
            try:
                # Copy installer files
                elevated.call(shutil.copytree, args=(source_files, destination), kwargs={'dirs_exist_ok': True})
                
                # Handle live image if needed
                if context.is_live_image_installation():
                    live_iso_path = context.get_live_iso_path()
                    if live_iso_path:
                        live_image_mount_letter = elevated.call(disk.mount_iso, args=(str(live_iso_path),))
                        try:
                            # Copy live image files as needed
                            live_image_source = f"{live_image_mount_letter}:\\LiveOS\\"
                            live_destination = f"{context.tmp_part.mount_path}\\LiveOS"
                            elevated.call(shutil.copytree, args=(live_image_source, live_destination), kwargs={'dirs_exist_ok': True})
                        finally:
                            elevated.call(disk.unmount_iso, args=(str(live_iso_path),))
                
                # Copy additional files
                self._copy_additional_files(context, destination)
                
                # Generate configuration files
                self._generate_config_files(context, destination)
                
                # Copy EFI directory to system EFI partition
                self._copy_efi_to_system_partition(context, destination)
                
            finally:
                # Always unmount the installer ISO
                elevated.call(disk.unmount_iso, args=(str(installer_iso_path),))
                # Unmount temporary partition from path
                elevated.call(disk.unmount_volume_from_path, args=(context.tmp_part.mount_path,))
            
            self._update_progress(context, InstallationStage.COPYING_TO_TMP_PART, 85, "Files copied successfully")
            return InstallationResult.success_result()
            
        except Exception as e:
            # Cleanup on failure
            if context.tmp_part_already_created:
                self._cleanup_failed_installation(context)
            return InstallationResult.error_result(
                InstallationStage.COPYING_TO_TMP_PART,
                f"File copying failed: {str(e)}"
            )
    
    def _copy_additional_files(self, context: InstallationContext, destination: str) -> None:
        """Copy additional files like WiFi profiles."""
        destination_path = Path(destination)
        
        # Copy WiFi profiles if specified
        if context.paths.wifi_profiles_src_dir and context.paths.wifi_profiles_dst_dir_name:
            wifi_dst_path = destination_path / context.paths.wifi_profiles_dst_dir_name
            elevated.call(shutil.copytree, args=(str(context.paths.wifi_profiles_src_dir), str(wifi_dst_path)), kwargs={'dirs_exist_ok': True})
    
    def _generate_config_files(self, context: InstallationContext, destination: str) -> None:
        """Generate GRUB and kickstart configuration files."""
        destination_path = Path(destination)
        
        # Generate GRUB config
        grub_cfg_path = destination_path / context.paths.grub_cfg_relative_path
        grub_cfg_path.parent.mkdir(parents=True, exist_ok=True)
        
        elevated.call(file_service.set_file_readonly, args=(str(grub_cfg_path), False))
        grub_cfg_content = config_builders.build_grub_cfg_file(
            context.partition.temp_part_label,
            is_autoinst=bool(context.kickstart.partition_method != "custom")
        )
        grub_cfg_path.write_text(grub_cfg_content)
        elevated.call(file_service.set_file_readonly, args=(str(grub_cfg_path), True))
        
        # Generate kickstart config if needed
        if context.kickstart.partition_method != "custom":
            kickstart_path = destination_path / context.paths.kickstart_cfg_relative_path
            kickstart_content = config_builders.build_autoinstall_ks_file(**vars(context.kickstart))
            kickstart_path.write_text(kickstart_content)
    
    def _copy_efi_to_system_partition(self, context: InstallationContext, temp_destination: str) -> None:
        """Copy EFI directory to system EFI partition for proper booting."""
        # Get EFI partition GUID
        efi_guid = elevated.call(get_system_efi_drive_uuid)
        if not efi_guid:
            raise RuntimeError("Could not find system EFI partition")
        
        # Normalize GUID format
        if not efi_guid.startswith("\\\\?\\Volume{"):
            efi_guid = f"\\\\?\\Volume{{{efi_guid}}}"
        
        # Create temp mount path for EFI partition
        efi_mount_path = f"{temp_destination}_efi"
        os.makedirs(efi_mount_path, exist_ok=True)
        
        try:
            # Mount EFI partition
            elevated.call(disk.mount_volume_to_path, args=(efi_guid, efi_mount_path))
            
            # Check if beanie directory already exists
            efi_dst = Path(efi_mount_path) / "EFI" / "beanie"
            if efi_dst.exists():
                print(f"Beanie EFI directory already exists at {efi_dst}, skipping copy")
                return
            
            # Copy EFI directory to \EFI\beanie on EFI partition
            efi_src = Path(temp_destination) / "EFI"
            efi_dst.parent.mkdir(parents=True, exist_ok=True)
            
            elevated.call(shutil.copytree, args=(str(efi_src), str(efi_dst)), kwargs={'dirs_exist_ok': True})
            
        finally:
            # Unmount EFI partition
            elevated.call(disk.unmount_volume_from_path, args=(efi_mount_path,))
            # Clean up temp mount directory
            shutil.rmtree(efi_mount_path, ignore_errors=True)
    
    def _create_boot_entry(self, context: InstallationContext) -> InstallationResult:
        """Create boot entry for the installation."""
        try:
            self._update_progress(context, InstallationStage.ADDING_TMP_BOOT_ENTRY, 90, "Creating boot entry...")
            
            # Run the entire boot entry creation with elevation
            new_entry_id = elevated.call(_create_boot_entry_elevated, args=(context.tmp_part,))
            
            return InstallationResult.success_result(str(new_entry_id))
        except Exception as e:
            # Cleanup on failure
            if context.tmp_part_already_created:
                self._cleanup_failed_installation(context)
            return InstallationResult.error_result(
                InstallationStage.ADDING_TMP_BOOT_ENTRY,
                f"Boot entry creation failed: {str(e)}"
            )

    def _cleanup_failed_installation(self, context: InstallationContext) -> None:
        """
        Clean up after a failed installation by removing the temporary partition
        and extending the system partition back to its original size.
        """
        try:
            self._update_progress(context, InstallationStage.CLEANUP, 0, "Cleaning up failed installation...")
            
            # Unmount the temporary partition if it's still mounted
            if context.tmp_part and context.tmp_part.mount_path:
                try:
                    elevated.call(disk.unmount_volume_from_path, args=(context.tmp_part.mount_path,))
                except Exception:
                    pass  # Ignore errors during cleanup
            
            # Delete the temporary partition and extend system partition
            # This requires the partitioning information that was stored during creation
            if context.partitioning_result:
                partitioning_info = context.partitioning_result
                
                # Delete the temporary partition
                try:
                    elevated.call(
                        self._delete_partition, 
                        args=(partitioning_info.sys_disk_number, context.tmp_part.partition_number)
                    )
                except Exception:
                    pass  # Continue with extension even if deletion fails
                
                # Extend the system partition
                try:
                    original_sys_size = disk.get_drive_size_after_resize(
                        partitioning_info.sys_drive_letter, 
                        partitioning_info.shrink_space
                    )
                    disk.resize_partition(partitioning_info.sys_drive_letter, original_sys_size)
                except Exception:
                    pass  # Continue even if extension fails
            
            self._update_progress(context, InstallationStage.CLEANUP, 100, "Cleanup completed")
            
        except Exception as e:
            # Don't let cleanup errors prevent the error from being reported
            print(f"Warning: Cleanup failed: {e}")

    def _delete_partition(self, disk_number: int, partition_number: int) -> None:
        """
        Delete a partition by its number on the specified disk.
        
        Args:
            disk_number: Disk number containing the partition
            partition_number: Partition number to delete
        """
        import subprocess
        script = f"Remove-Partition -DiskNumber {disk_number} -PartitionNumber {partition_number} -Confirm:$false"
        subprocess.run(
            [r"powershell.exe", "-Command", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
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
    progress_callback: Optional[Callable] = None,
    download_callback: Optional[Callable] = None
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
