"""
Type-safe Installation Service.

This replaces the current kwargs-based installation.py with a robust,
maintainable service that uses proper dependency injection and type safety.
"""

import logging
import shutil
from collections.abc import Callable
from pathlib import Path

from config.settings import get_config
from core.state import get_state
from models.downloadable_file import DownloadableFile
from models.installation_context import (
    InstallationContext,
    InstallationResult,
    InstallationStage,
)
from models.partition import PartitioningMethod
from services import config_builders, disk, elevated
from services import file as file_service
from services.download import DownloadProgress, DownloadService
from services.partition import partition_procedure


class HashVerificationError(Exception):
    """Raised when file hash verification fails."""

    def __init__(self, file_path: str, expected: str, actual: str):
        self.file_path = file_path
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Hash mismatch for {file_path}: expected {expected}, got {actual}"
        )


def _create_boot_entry(efi_partition_info) -> int:
    """Create boot entry. Requires elevated privileges."""
    import uuid

    import firmware_variables as fwvars

    if not efi_partition_info:
        msg = "Could not get EFI partition information"
        raise RuntimeError(msg)

    # Find the entry with "Windows Boot Manager" to duplicate
    windows_entry_id = None
    with fwvars.adjust_privileges():
        for entry_id in fwvars.get_boot_order():
            entry = fwvars.get_parsed_boot_entry(entry_id)
            if "windows boot manager" in entry.description.lower():
                windows_entry_id = entry_id
                break
        if windows_entry_id is None:
            msg = "Windows Boot Manager entry not found"
            raise RuntimeError(msg)

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
                    hd_node.partition_guid = efi_partition_info.partition_guid
                    hd_node.partition_number = efi_partition_info.partition_number
                    hd_node.partition_start_lba = efi_partition_info.start_lba
                    hd_node.partition_size_lba = efi_partition_info.size_lba
                    hd_node.partition_signature = uuid.UUID(
                        efi_partition_info.partition_guid
                    ).bytes_le
                    path.set_hard_drive_node(hd_node)

        # Find an unused entry_id for the new entry
        new_entry_id = None
        for i in range(50):
            try:
                fwvars.get_boot_entry(i)
            except OSError as e:
                if hasattr(e, "winerror") and e.winerror == 203:
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
        progress_callback: Callable | None = None,
        download_callback: Callable | None = None,
    ):
        """
        Initialize the installation service.

        Args:
            progress_callback: Called for general progress updates
            download_callback: Called for download-specific progress updates
        """
        self.config = get_config()
        self.state = get_state()
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
            self._update_progress(
                context,
                InstallationStage.INITIALIZING,
                0,
                "Initializing installation...",
            )

            # Prepare work directory
            Path(context.paths.work_dir).mkdir(parents=True, exist_ok=True)

            # Download required files
            download_result = self._download_files(context)
            if not download_result.success:
                return download_result

            # Recalculate partition size if live image installation
            self._update_tmp_partition_size(context)

            # Temporary: Always use RAMDISK for CLEAN_DISK
            if context.kickstart.partitioning.method == PartitioningMethod.CLEAN_DISK:
                context.kickstart.partitioning.method = (
                    PartitioningMethod.CLEAN_DISK_RAMDISK
                )

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

            self._update_progress(
                context,
                InstallationStage.INSTALL_DONE,
                100,
                "Installation completed successfully!",
            )
            return InstallationResult.success_result(boot_result.boot_entry_created)

        except Exception as e:
            error_msg = f"Unexpected error during installation: {e!s}"

            # Cleanup temporary partition if it was created
            cleanup_error = None
            if context.tmp_part_already_created and context.tmp_part:
                try:
                    self._cleanup_failed_installation(context)
                except Exception as cleanup_e:
                    cleanup_error = str(cleanup_e)
                    logging.error(f"Cleanup failed: {cleanup_error}")

            if cleanup_error:
                error_msg += f"\n\nCleanup also failed: {cleanup_error}"

            return InstallationResult.error_result(context.current_stage, error_msg)

    def _download_files(self, context: InstallationContext) -> InstallationResult:
        """Download all required files."""
        try:
            self._update_progress(
                context, InstallationStage.DOWNLOADING, 10, "Starting downloads..."
            )

            for i, file_info in enumerate(context.downloadable_files):
                context.current_file_index = i

                # Create destination directory
                Path(file_info.destination_dir).mkdir(parents=True, exist_ok=True)

                # Check if file already exists with correct hash
                if file_info.full_path.exists() and self._verify_file_hash(file_info):
                    self._download_index += 1
                    continue  # File is already downloaded and verified

                # Download the file
                self._download_single_file(file_info)

                # Verify downloaded file
                if file_info.expected_hash and not self._verify_file_hash(file_info):
                    actual_hash = file_service.get_sha256_hash(str(file_info.full_path))
                    raise HashVerificationError(
                        str(file_info.full_path), file_info.expected_hash, actual_hash
                    )
                self._download_index += 1

            progress = 40  # Downloads complete at 40%
            self._update_progress(
                context,
                InstallationStage.VERIFYING_CHECKSUM,
                progress,
                "All files downloaded and verified",
            )
            return InstallationResult.success_result()

        except HashVerificationError as e:
            return InstallationResult.error_result(
                InstallationStage.VERIFYING_CHECKSUM, str(e)
            )
        except Exception as e:
            return InstallationResult.error_result(
                InstallationStage.DOWNLOADING, f"Download failed: {e!s}"
            )

    def _update_tmp_partition_size(self, context: InstallationContext) -> None:
        """Recalculate partition size for live image installations using accurate content sizes."""
        if not context.is_live_image_installation():
            return

        installer_iso_path = context.get_installer_iso_path()
        live_iso_path = context.get_live_iso_path()
        if not installer_iso_path or not live_iso_path:
            return

        installer_size = disk.get_iso_contents_size(str(installer_iso_path))
        squashfs_size = disk.get_file_size_in_iso(
            str(live_iso_path), "/LiveOS/squashfs.img"
        )
        total_size = installer_size + squashfs_size
        # Add 50MB fixed buffer
        buffer = 50 * 1024 * 1024  # 50MB in bytes
        new_tmp_part_size = total_size + buffer
        context.partition.tmp_part_size = new_tmp_part_size

    def _download_single_file(self, file_info: DownloadableFile) -> None:
        """Download a single file with progress tracking."""

        # Use the new download service
        self.download_service.download_file(
            url=file_info.download_url,
            destination=file_info.destination_dir,
            filename=file_info.file_name,
            expected_hash=file_info.expected_hash,
            progress_callback=self.progress_adapter,
        )

    def progress_adapter(self, progress: DownloadProgress) -> None:
        """Adapt DownloadProgress to download callback format."""
        if self.download_callback:
            self.download_callback(
                self._download_index,
                progress.filename,
                progress.percentage,
                progress.speed_bytes_per_sec,
                progress.eta_seconds,
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
            self._update_progress(
                context,
                InstallationStage.CREATING_TMP_PART,
                50,
                "Creating temporary partition...",
            )

            # Execute partitioning using the partition context
            partitioning_results = elevated.call(
                partition_procedure, kwargs=vars(context.partition)
            )

            # Store the temporary partition information for later use
            context.tmp_part = partitioning_results.tmp_part
            context.tmp_part_already_created = True
            context.partitioning_result = partitioning_results

            # Set partition GUIDs in kickstart for auto-install
            context.kickstart.partitioning.root_guid = (
                partitioning_results.partition_guids.root_guid
            )
            context.kickstart.partitioning.boot_guid = (
                partitioning_results.partition_guids.boot_guid
            )
            context.kickstart.partitioning.sys_drive_uuid = (
                self.state.installation.windows_partition_info.partition_guid
            )
            context.kickstart.partitioning.sys_efi_uuid = (
                self.state.installation.efi_partition_info.partition_guid
            )
            context.kickstart.partitioning.tmp_part_uuid = (
                partitioning_results.tmp_part.partition_info.partition_guid
            )

            self._update_progress(
                context,
                InstallationStage.CREATING_TMP_PART,
                60,
                "Temporary partition created",
            )
            return InstallationResult.success_result()

        except Exception as e:
            return InstallationResult.error_result(
                InstallationStage.CREATING_TMP_PART, f"Partitioning failed: {e!s}"
            )

    def _copy_installation_files(
        self, context: InstallationContext
    ) -> InstallationResult:
        """Copy installation files to temporary partition."""
        try:
            self._update_progress(
                context,
                InstallationStage.COPYING_TO_TMP_PART,
                70,
                "Copying installation files...",
            )

            # Get file paths
            installer_iso_path = context.get_installer_iso_path()
            if not installer_iso_path:
                return InstallationResult.error_result(
                    InstallationStage.COPYING_TO_TMP_PART, "No installer ISO found"
                )

            # Set destination path
            destination = context.tmp_part.mount_path

            # Extract installer ISO contents directly to temp partition
            disk.extract_iso_to_dir(str(installer_iso_path), destination)

            # Handle live image if needed
            if context.is_live_image_installation():
                live_iso_path = context.get_live_iso_path()
                if live_iso_path:
                    # Extract only the LiveOS directory from live ISO directly to destination
                    self._extract_liveos_from_iso(str(live_iso_path), destination)

            # Copy additional files and generate configurations
            self._copy_additional_files(context, destination)
            self._generate_config_files(context, destination)
            self._copy_efi_to_system_partition(destination)

            self._update_progress(
                context,
                InstallationStage.COPYING_TO_TMP_PART,
                85,
                "Files copied successfully",
            )
            return InstallationResult.success_result()

        except Exception as e:
            # Cleanup on failure
            error_msg = f"File copying failed: {e!s}"
            if context.tmp_part_already_created:
                try:
                    self._cleanup_failed_installation(context)
                except Exception as cleanup_e:
                    error_msg += f"\n\nCleanup also failed: {cleanup_e!s}"
            return InstallationResult.error_result(
                InstallationStage.COPYING_TO_TMP_PART, error_msg
            )

    def _extract_liveos_from_iso(self, iso_path: str, target_dir: str) -> None:
        """
        Extract only the LiveOS directory from an ISO file.

        Args:
            iso_path: Path to the ISO file
            target_dir: Directory to extract LiveOS contents to
        """
        disk.extract_iso_to_dir(
            iso_path, target_dir, filter_func=lambda p: p.startswith("/LiveOS/")
        )

    def _copy_additional_files(
        self, context: InstallationContext, destination: str
    ) -> None:
        """Copy additional files like WiFi profiles."""
        destination_path = Path(destination)

        # Copy WiFi profiles if specified
        if (
            context.paths.wifi_profiles_src_dir
            and context.paths.wifi_profiles_dst_dir_name
        ):
            wifi_dst_path = destination_path / context.paths.wifi_profiles_dst_dir_name
            elevated.call(
                shutil.copytree,
                args=(str(context.paths.wifi_profiles_src_dir), str(wifi_dst_path)),
                kwargs={"dirs_exist_ok": True},
            )

        # Copy install-helpers directory to the destination if it exists
        install_helpers_dir = get_config().paths.install_helpers_dir
        if install_helpers_dir.exists():
            install_helpers_dst = destination_path / "install-helpers"
            shutil.copytree(
                str(install_helpers_dir),
                str(install_helpers_dst),
                dirs_exist_ok=True,
            )

    def _generate_config_files(
        self, context: InstallationContext, destination: str
    ) -> None:
        """Generate GRUB and kickstart configuration files."""
        destination_path = Path(destination)

        # Generate GRUB config
        grub_cfg_path = destination_path / context.paths.grub_cfg_relative_path
        grub_cfg_path.parent.mkdir(parents=True, exist_ok=True)

        elevated.call(file_service.set_file_readonly, args=(str(grub_cfg_path), False))

        should_grub_autoinstall = bool(
            context.kickstart.partitioning.method
            and context.kickstart.partitioning.method != PartitioningMethod.CUSTOM
        )
        should_grub_autoinstall_ramdisk = (
            should_grub_autoinstall
            and context.kickstart.partitioning.method == PartitioningMethod.CUSTOM
        )
        grub_cfg_content = config_builders.build_grub_cfg_file(
            context.partition.temp_part_label,
            is_autoinst=bool(
                context.kickstart.partitioning.method
                and context.kickstart.partitioning.method != PartitioningMethod.CUSTOM
            ),
            autoinstall_ramdisk=should_grub_autoinstall_ramdisk,
        )
        grub_cfg_path.write_text(grub_cfg_content)
        elevated.call(file_service.set_file_readonly, args=(str(grub_cfg_path), True))

        # Generate kickstart config if needed
        if (
            context.kickstart.partitioning.method
            and context.kickstart.partitioning.method != PartitioningMethod.CUSTOM
        ):
            # Set live_img_url if installing a live image
            if context.selected_spin.is_live_img:
                context.kickstart.live_img_url = get_config().app.live_img_url

            kickstart_path = (
                destination_path / context.paths.kickstart_cfg_relative_path
            )
            kickstart_content = config_builders.build_autoinstall_ks_file(
                context.kickstart
            )
            kickstart_path.write_text(kickstart_content)

    def _copy_efi_to_system_partition(self, temp_destination: str) -> None:
        """Copy EFI directory to system EFI partition for proper booting."""
        # Get EFI partition volume unique ID
        efi_unique_id = self.state.installation.efi_partition_info.volume_unique_id
        if not efi_unique_id:
            msg = "Could not find system EFI partition"
            raise RuntimeError(msg)

        # Create temp mount path for EFI partition
        efi_mount_path = f"{temp_destination}_efi"
        Path(efi_mount_path).mkdir(parents=True, exist_ok=True)

        try:
            # Mount EFI partition
            elevated.call(
                disk.mount_volume_to_path, args=(efi_unique_id, efi_mount_path)
            )

            # Check if beanie directory already exists
            efi_dst = Path(efi_mount_path) / "EFI" / "beanie"
            if efi_dst.exists():
                msg = f"EFI beanie directory already exists at {efi_dst}, skipping copy"
                logging.info(msg)
                return

            # Copy EFI directory to \EFI\beanie on EFI partition
            efi_src = Path(temp_destination) / "EFI"
            efi_dst.parent.mkdir(parents=True, exist_ok=True)

            elevated.call(
                shutil.copytree,
                args=(str(efi_src), str(efi_dst)),
                kwargs={"dirs_exist_ok": True},
            )

        finally:
            # Unmount EFI partition
            elevated.call(disk.unmount_volume_from_path, args=(efi_mount_path,))
            # Clean up temp mount directory
            shutil.rmtree(efi_mount_path, ignore_errors=True)

    def _create_boot_entry(self, context: InstallationContext) -> InstallationResult:
        """Create boot entry for the installation."""
        try:
            self._update_progress(
                context,
                InstallationStage.ADDING_TMP_BOOT_ENTRY,
                90,
                "Creating boot entry...",
            )
            efi_partition_info = self.state.installation.efi_partition_info
            # Run the entire boot entry creation with elevation
            new_entry_id = elevated.call(_create_boot_entry, args=(efi_partition_info,))

            return InstallationResult.success_result(str(new_entry_id))
        except Exception as e:
            # Cleanup on failure
            error_msg = f"Boot entry creation failed: {e!s}"
            if context.tmp_part_already_created:
                try:
                    self._cleanup_failed_installation(context)
                except Exception as cleanup_e:
                    error_msg += f"\n\nCleanup also failed: {cleanup_e!s}"
            return InstallationResult.error_result(
                InstallationStage.ADDING_TMP_BOOT_ENTRY, error_msg
            )

    def _cleanup_failed_installation(self, context: InstallationContext) -> None:
        """
        Clean up after a failed installation by removing the temporary partition
        and extending the system partition back to its original size.

        Raises:
            Exception: If cleanup fails
        """
        self._update_progress(
            context, InstallationStage.CLEANUP, 0, "Cleaning up failed installation..."
        )

        # Unmount the temporary partition if it's still mounted
        if context.tmp_part and context.tmp_part.mount_path:
            elevated.call(
                disk.unmount_volume_from_path, args=(context.tmp_part.mount_path,)
            )

        # Delete the temporary partition and extend system partition
        # This requires the partitioning information that was stored during creation
        if context.partitioning_result:
            partitioning_info = context.partitioning_result

            # Delete the temporary partition
            elevated.call(
                disk.delete_partition,
                args=(partitioning_info.windows_partition.partition_guid,),
            )

            # Extend the system partition back to original size
            elevated.call(
                disk.resize_partition,
                args=(
                    partitioning_info.windows_partition.partition_guid,
                    partitioning_info.windows_partition.size,
                ),
            )

        self._update_progress(
            context, InstallationStage.CLEANUP, 100, "Cleanup completed"
        )

    def _update_progress(
        self,
        context: InstallationContext,
        stage: InstallationStage,
        percent: float,
        message: str,
    ) -> None:
        """Update progress and notify callback."""
        context.update_progress(stage, percent)

        if self.progress_callback:
            self.progress_callback(stage, percent, message)


# Factory function to create installation service with GUI callbacks
def create_installation_service_for_gui(
    progress_callback: Callable | None = None,
    download_callback: Callable | None = None,
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
        progress_callback=progress_callback, download_callback=download_callback
    )
