"""
Integration helpers for the new installation system.

This provides utilities to migrate from the old kwargs/dict approach
to the new type-safe InstallationContext system.
"""
from typing import Dict, Any, List
from pathlib import Path

from models.installation_context import (
    InstallationContext,
    DownloadableFile
)
from services.network import get_file_name_from_url


"""
Integration helpers for the new installation system.

This provides utilities to migrate from the old kwargs/dict approach
to the new type-safe InstallationContext system.
"""
from typing import Dict, Any, List
from pathlib import Path

from models.installation_context import (
    InstallationContext,
    DownloadableFile,
    InstallationPaths
)
from services.network import get_file_name_from_url


class InstallationMigration:
    """
    Utilities to migrate from old installation system to new type-safe approach.
    
    This class helps convert the existing application state and kwargs
    into the new InstallationContext format.
    """
    
    @staticmethod
    def convert_legacy_installer_args(
        installer_args_dict: Dict[str, Any],
        app_config: Any,
        logger: Any
    ) -> InstallationContext:
        """
        Convert legacy installer args dictionary to InstallationContext.
        
        Args:
            installer_args_dict: The old-style installer arguments
            app_config: Application configuration object
            logger: Logger instance
            
        Returns:
            A properly populated InstallationContext
            
        Raises:
            ValueError: If required data is missing or invalid
        """
        try:
            # Extract download files
            downloadable_files: List[DownloadableFile] = []
            if "dl_files" in installer_args_dict and installer_args_dict["dl_files"]:
                for dl_file in installer_args_dict["dl_files"]:
                    if hasattr(dl_file, '__dict__'):
                        # Convert DownloadFile dataclass to DownloadableFile
                        downloadable_files.append(DownloadableFile(
                            file_name=dl_file.file_name or get_file_name_from_url(dl_file.dl_link),
                            file_hint=getattr(dl_file, 'file_hint', ''),
                            download_url=dl_file.dl_link,
                            destination_dir=Path(dl_file.dst_dir or app_config.paths.work_dir),
                            expected_hash=dl_file.hash256.strip().lower() if dl_file.hash256 else "",
                            size_bytes=dl_file.size or 0
                        ))
                    else:
                        # Handle dictionary format
                        downloadable_files.append(DownloadableFile(
                            file_name=dl_file.get('file_name', '') or get_file_name_from_url(dl_file['dl_link']),
                            file_hint=dl_file.get('file_hint', ''),
                            download_url=dl_file['dl_link'],
                            destination_dir=Path(dl_file.get('dst_dir', app_config.paths.work_dir)),
                            expected_hash=dl_file.get('hash256', '').strip().lower(),
                            size_bytes=dl_file.get('size', 0)
                        ))
            
            # Create installation paths
            paths = InstallationPaths(
                work_dir=Path(installer_args_dict.get('work_dir', app_config.paths.work_dir)),
                rpm_source_dir=Path(installer_args_dict['rpm_source_dir']) if installer_args_dict.get('rpm_source_dir') else None,
                wifi_profiles_src_dir=Path(installer_args_dict['wifi_profiles_src_dir']) if installer_args_dict.get('wifi_profiles_src_dir') else None,
                grub_cfg_relative_path=installer_args_dict.get('grub_cfg_relative_path', 'boot/grub2/grub.cfg'),
                kickstart_cfg_relative_path=installer_args_dict.get('kickstart_cfg_relative_path', 'ks.cfg'),
                efi_file_relative_path=installer_args_dict.get('efi_file_relative_path', 'EFI/BOOT/bootx64.efi'),
                rpm_dst_dir_name=installer_args_dict.get('rpm_dst_dir_name', 'additional_rpms'),
                wifi_profiles_dst_dir_name=installer_args_dict.get('wifi_profiles_dst_dir_name', 'wifi_profiles')
            )
            
            # For legacy conversion, we need to create dummy objects
            # This is a simplified version - in practice you'd extract from actual state
            logger.warning("Legacy installer args conversion - creating minimal context")
            
            # Create minimal dummy objects (would normally extract from ks_kwargs/part_kwargs)
            from models.kickstart import Kickstart
            from models.partition import Partition
            from models.spin import Spin
            
            dummy_kickstart = Kickstart()
            dummy_partition = Partition()
            dummy_spin = Spin(
                name="legacy_spin",
                size="0",
                hash256="",
                dl_link=""
            )
            
            return InstallationContext(
                kickstart=dummy_kickstart,
                partition=dummy_partition,
                selected_spin=dummy_spin,
                live_os_installer_spin=None,
                paths=paths,
                downloadable_files=downloadable_files
            )
            
        except Exception as e:
            logger.error(f"Failed to convert legacy installer args: {e}")
            raise ValueError(f"Could not convert legacy installer arguments: {str(e)}")

    @staticmethod
    def convert_from_application_state(state: Any, app_config: Any, logger: Any) -> InstallationContext:
        """
        Convert application state directly to InstallationContext.
        
        This is the preferred method for new code.
        
        Args:
            state: Application state object
            app_config: Application configuration
            logger: Logger instance
            
        Returns:
            A properly populated InstallationContext
        """
        try:
            # Build download files list from selected spin
            downloadable_files: List[DownloadableFile] = []
            
            if state.installation.selected_spin:
                if state.installation.selected_spin.is_live_img:
                    # For live images, we need both installer and live images
                    if state.compatibility.live_os_installer_spin:
                        installer_img = DownloadableFile(
                            file_name="install.iso",
                            file_hint="installer_iso",
                            download_url=state.compatibility.live_os_installer_spin.dl_link,
                            destination_dir=Path(app_config.paths.work_dir),
                            expected_hash=state.compatibility.live_os_installer_spin.hash256.strip().lower() if state.compatibility.live_os_installer_spin.hash256 else "",
                            size_bytes=int(state.compatibility.live_os_installer_spin.size) if state.compatibility.live_os_installer_spin.size.isdigit() else 0
                        )
                        downloadable_files.append(installer_img)
                    
                    live_img = DownloadableFile(
                        file_name="live.iso",
                        file_hint="live_img_iso",
                        download_url=state.installation.selected_spin.dl_link,
                        destination_dir=Path(app_config.paths.work_dir),
                        expected_hash=state.installation.selected_spin.hash256.strip().lower() if state.installation.selected_spin.hash256 else "",
                        size_bytes=int(state.installation.selected_spin.size) if state.installation.selected_spin.size.isdigit() else 0
                    )
                    downloadable_files.append(live_img)
                else:
                    # For non-live images
                    installer_img = DownloadableFile(
                        file_name="install.iso",
                        file_hint="installer_iso",
                        download_url=state.installation.selected_spin.dl_link,
                        destination_dir=Path(app_config.paths.work_dir),
                        expected_hash=state.installation.selected_spin.hash256.strip().lower() if state.installation.selected_spin.hash256 else "",
                        size_bytes=int(state.installation.selected_spin.size) if state.installation.selected_spin.size.isdigit() else 0
                    )
                    downloadable_files.append(installer_img)
            
            # Build installation paths
            paths = InstallationPaths(
                work_dir=Path(app_config.paths.work_dir),
                rpm_source_dir=Path(app_config.paths.rpm_source_dir) if hasattr(app_config.paths, 'rpm_source_dir') else None,
                wifi_profiles_src_dir=Path(app_config.paths.wifi_profiles_dir) if hasattr(app_config.paths, 'wifi_profiles_dir') else None,
                grub_cfg_relative_path="boot/grub2/grub.cfg",
                kickstart_cfg_relative_path="ks.cfg",
                efi_file_relative_path=getattr(app_config.app, 'default_efi_file_path', 'EFI/BOOT/bootx64.efi') if hasattr(app_config.app, 'default_efi_file_path') else "EFI/BOOT/bootx64.efi",
                rpm_dst_dir_name="additional_rpms",
                wifi_profiles_dst_dir_name="wifi_profiles"
            )
            
            return InstallationContext(
                kickstart=state.installation.kickstart,
                partition=state.installation.partition,
                selected_spin=state.installation.selected_spin,
                live_os_installer_spin=getattr(state.compatibility, 'live_os_installer_spin', None) if hasattr(state, 'compatibility') else None,
                paths=paths,
                downloadable_files=downloadable_files
            )
            
        except Exception as e:
            logger.error(f"Failed to convert application state: {e}")
            raise ValueError(f"Could not convert application state: {str(e)}")
