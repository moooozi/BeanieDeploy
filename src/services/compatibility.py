"""
System compatibility checking service.
Extracted from the UI layer for better separation of concerns.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional
import subprocess

from config.settings import ConfigManager
from utils.logging import get_logger
from utils.errors import handle_exception
from utils.system import is_admin


logger = get_logger(__name__)


class CheckType(Enum):
    """Types of system compatibility checks."""
    ARCH = "arch"
    UEFI = "uefi"
    RAM = "ram"
    SPACE = "space"
    RESIZABLE = "resizable"


@dataclass
class CheckResult:
    """Result of a compatibility check."""
    check_type: CheckType
    success: bool
    value: Any
    error_message: Optional[str] = None
    raw_output: Optional[str] = None


class CompatibilityChecker:
    """Service for checking system compatibility."""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
    
    @handle_exception
    def check_architecture(self) -> CheckResult:
        """Check system architecture."""
        self.logger.info("Checking system architecture")
        
        try:
            result = subprocess.run(
                ["powershell.exe", "$env:PROCESSOR_ARCHITECTURE"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                timeout=10
            )
            
            arch = result.stdout.strip().lower()
            success = arch in self.config.ui.accepted_architectures
            
            self.logger.info(f"System architecture: {arch}, supported: {success}")
            
            return CheckResult(
                check_type=CheckType.ARCH,
                success=success,
                value=arch,
                raw_output=result.stdout
            )
            
        except Exception as e:
            error_msg = f"Failed to check architecture: {e}"
            self.logger.error(error_msg)
            return CheckResult(
                check_type=CheckType.ARCH,
                success=False,
                value=None,
                error_message=error_msg
            )
    
    @handle_exception
    def check_uefi(self) -> CheckResult:
        """Check if system uses UEFI firmware."""
        self.logger.info("Checking firmware type")
        
        try:
            result = subprocess.run(
                ["powershell.exe", "$env:firmware_type"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                timeout=10
            )
            
            firmware_type = result.stdout.strip().lower()
            success = firmware_type == "uefi"
            
            self.logger.info(f"Firmware type: {firmware_type}, UEFI: {success}")
            
            return CheckResult(
                check_type=CheckType.UEFI,
                success=success,
                value=firmware_type,
                raw_output=result.stdout
            )
            
        except Exception as e:
            error_msg = f"Failed to check firmware type: {e}"
            self.logger.error(error_msg)
            return CheckResult(
                check_type=CheckType.UEFI,
                success=False,
                value=None,
                error_message=error_msg
            )
    
    @handle_exception
    def check_ram(self) -> CheckResult:
        """Check system RAM."""
        self.logger.info("Checking RAM size")
        
        try:
            result = subprocess.run(
                [
                    "powershell.exe",
                    "(Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property capacity -Sum).sum"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                timeout=15
            )
            
            ram_bytes = int(result.stdout.strip())
            success = ram_bytes >= self.config.app.minimal_required_ram.bytes
            
            self.logger.info(f"System RAM: {ram_bytes} bytes, sufficient: {success}")
            
            return CheckResult(
                check_type=CheckType.RAM,
                success=success,
                value=ram_bytes,
                raw_output=result.stdout
            )
            
        except Exception as e:
            error_msg = f"Failed to check RAM: {e}"
            self.logger.error(error_msg)
            return CheckResult(
                check_type=CheckType.RAM,
                success=False,
                value=None,
                error_message=error_msg
            )
    
    @handle_exception
    def check_disk_space(self) -> CheckResult:
        """Check available disk space."""
        self.logger.info("Checking available disk space")
        
        try:
            result = subprocess.run(
                [
                    "powershell.exe",
                    "(Get-Volume | Where DriveLetter -eq $env:SystemDrive.Substring(0, 1)).SizeRemaining"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                timeout=15
            )
            
            available_bytes = int(result.stdout.strip())
            success = available_bytes >= self.config.app.minimal_required_space.bytes
            
            self.logger.info(f"Available space: {available_bytes} bytes, sufficient: {success}")
            
            return CheckResult(
                check_type=CheckType.SPACE,
                success=success,
                value=available_bytes,
                raw_output=result.stdout
            )
            
        except Exception as e:
            error_msg = f"Failed to check disk space: {e}"
            self.logger.error(error_msg)
            return CheckResult(
                check_type=CheckType.SPACE,
                success=False,
                value=None,
                error_message=error_msg
            )
    
    @handle_exception
    def check_resizable_space(self) -> CheckResult:
        """Check if disk can be resized for dual boot."""
        self.logger.info("Checking disk resize capability")
        
        if not is_admin():
            error_msg = "Administrator privileges required to check disk resize capability"
            self.logger.warning(error_msg)
            return CheckResult(
                check_type=CheckType.RESIZABLE,
                success=False,
                value=None,
                error_message=error_msg
            )
        
        try:
            result = subprocess.run(
                [
                    "powershell.exe",
                    "((Get-Volume | Where DriveLetter -eq $env:SystemDrive.Substring(0, 1)).Size - (Get-PartitionSupportedSize -DriveLetter $env:SystemDrive.Substring(0, 1)).SizeMin)"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                timeout=20
            )
            
            resizable_bytes = int(result.stdout.strip())
            success = resizable_bytes >= self.config.app.minimal_required_space.bytes
            
            self.logger.info(f"Resizable space: {resizable_bytes} bytes, sufficient: {success}")
            
            return CheckResult(
                check_type=CheckType.RESIZABLE,
                success=success,
                value=resizable_bytes,
                raw_output=result.stdout
            )
            
        except Exception as e:
            error_msg = f"Failed to check disk resize capability: {e}"
            self.logger.error(error_msg)
            return CheckResult(
                check_type=CheckType.RESIZABLE,
                success=False,
                value=None,
                error_message=error_msg
            )
    
    def run_all_checks(self) -> Dict[CheckType, CheckResult]:
        """Run all compatibility checks."""
        self.logger.info("Running all compatibility checks")
        
        checks = {
            CheckType.ARCH: self.check_architecture,
            CheckType.UEFI: self.check_uefi,
            CheckType.RAM: self.check_ram,
            CheckType.SPACE: self.check_disk_space,
            CheckType.RESIZABLE: self.check_resizable_space,
        }
        
        results = {}
        for check_type, check_func in checks.items():
            try:
                results[check_type] = check_func()
            except Exception as e:
                self.logger.error(f"Unexpected error in {check_type.value} check: {e}")
                results[check_type] = CheckResult(
                    check_type=check_type,
                    success=False,
                    value=None,
                    error_message=str(e)
                )
        
        # Log summary
        passed = sum(1 for result in results.values() if result.success)
        total = len(results)
        self.logger.info(f"Compatibility checks completed: {passed}/{total} passed")
        
        return results
    
    def get_error_messages(self, results: Dict[CheckType, CheckResult]) -> list[str]:
        """Get user-friendly error messages for failed checks."""
        errors = []
        
        for check_type, result in results.items():
            if not result.success:
                if check_type == CheckType.ARCH:
                    if result.error_message:
                        errors.append("Could not determine system architecture")
                    else:
                        errors.append(f"Unsupported architecture: {result.value}")
                
                elif check_type == CheckType.UEFI:
                    if result.error_message:
                        errors.append("Could not determine firmware type")
                    else:
                        errors.append("UEFI firmware required (Legacy BIOS not supported)")
                
                elif check_type == CheckType.RAM:
                    if result.error_message:
                        errors.append("Could not determine system RAM")
                    else:
                        required_gb = self.config.app.minimal_required_ram.gigabytes
                        errors.append(f"Insufficient RAM (minimum {required_gb}GB required)")
                
                elif check_type == CheckType.SPACE:
                    if result.error_message:
                        errors.append("Could not determine available disk space")
                    else:
                        required_gb = self.config.app.minimal_required_space.gigabytes
                        errors.append(f"Insufficient disk space (minimum {required_gb}GB required)")
                
                elif check_type == CheckType.RESIZABLE:
                    if result.error_message:
                        errors.append("Could not determine disk resize capability")
                    else:
                        required_gb = self.config.app.minimal_required_space.gigabytes
                        errors.append(f"Cannot resize disk for dual boot (need {required_gb}GB)")
        
        return errors
