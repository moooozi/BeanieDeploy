"""
Utility functions for BeanieDeploy.
Refactored to use proper configuration instead of globals.
"""
import os
import shutil
import subprocess
import ctypes
from pathlib import Path
from typing import Dict, Any
import webbrowser

from config.settings import ConfigManager
from utils.logging import get_logger
from utils.errors import BeanieDeployError, NetworkError, FileSystemError, handle_exception


logger = get_logger(__name__)


def open_url(url: str) -> None:
    """Open URL in default web browser."""
    webbrowser.open_new_tab(url)


def get_windows_username() -> str:
    """Get the current Windows username."""
    return os.getlogin()


def set_file_readonly(filepath: Path, is_readonly: bool) -> None:
    """Set file readonly status."""
    try:
        if is_readonly:
            os.chmod(filepath, 0o444)  # Read-only
        else:
            os.chmod(filepath, 0o666)  # Read-write
    except OSError as e:
        raise FileSystemError(f"Failed to set file permissions for {filepath}") from e


def format_speed(speed: float) -> str:
    """Format download speed in human-readable format."""
    speed_bits = speed * 8  # Convert bytes to bits
    if speed_bits < 1024:
        return f"{speed_bits:.2f} bit/s"
    elif speed_bits < 1024 * 1024:
        return f"{speed_bits / 1024:.2f} Kbit/s"
    else:
        return f"{speed_bits / (1024 * 1024):.2f} Mbit/s"


def format_size(size: float) -> str:
    """Format file size in human-readable format."""
    if size < 1024:
        return f"{size:.2f} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"


def format_eta(eta_in_seconds) -> str:
    """Format estimated time remaining."""
    if eta_in_seconds == "N/A":
        return str(eta_in_seconds)
    
    hours, remainder = divmod(eta_in_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{int(hours)} hour {int(minutes):02} minute {int(seconds):02} second left"
    elif minutes > 0:
        return f"{int(minutes)} minute {int(seconds):02} second left"
    else:
        return f"{int(seconds)} second left"


@handle_exception
def get_json(url: str) -> Dict[str, Any]:
    """
    Fetch and parse JSON from a URL using requests.
    
    Args:
        url: URL to fetch JSON from
        
    Returns:
        Parsed JSON data
        
    Raises:
        NetworkError: If the request fails
    """
    try:
        # Use requests for better reliability
        import requests
        logger.info(f"Fetching JSON from: {url}")
        headers = {'User-Agent': 'BeanieDeploy/1.0'}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        logger.debug(f"Successfully fetched JSON data from {url}")
        return data
    except Exception as e:
        raise NetworkError(f"Failed to fetch JSON from {url}") from e


def windows_language_code() -> str:
    """Get Windows language code."""
    try:
        result = subprocess.run(
            ["powershell.exe", "$((Get-UICulture).Name)"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            timeout=10
        )
        return result.stdout.strip() if result.returncode == 0 else "en-US"
    except Exception:
        logger.warning("Failed to get Windows language code, defaulting to en-US")
        return "en-US"


def is_admin() -> bool:
    """Check if the current process has administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def get_admin(args_string: str = "") -> None:
    """
    Request administrator privileges and restart the application.
    
    Args:
        args_string: Additional command line arguments
    """
    try:
        import sys
        script_path = sys.argv[0]
        args = " ".join(sys.argv[1:])
        if args_string:
            args += f" {args_string}"
        
        logger.info("Requesting administrator privileges")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script_path}" {args}', None, 1
        )
        sys.exit()
    except Exception as e:
        raise BeanieDeployError("Failed to request administrator privileges") from e


def cleanup_on_reboot(script_dir: Path) -> None:
    """
    Set up cleanup operations to run on next reboot.
    
    Args:
        script_dir: Directory containing the script
    """
    try:
        # This function would set up Windows registry entries for cleanup
        # Implementation depends on specific cleanup requirements
        logger.info("Setting up cleanup operations for next reboot")
        # TODO: Implement actual cleanup logic
    except Exception as e:
        logger.warning(f"Failed to set up cleanup operations: {e}")


def app_quit() -> None:
    """Clean application exit."""
    logger.info("Application shutting down")
    # Any cleanup operations can be added here
    import sys
    sys.exit(0)


# Boot manager functions (using configuration)
def add_boot_entry(config: ConfigManager, entry_id: str, name: str, path: str) -> subprocess.CompletedProcess:
    """Add a boot entry using bootmgr helper."""
    cmd = [
        str(config.paths.bootmgr_helper_relative),
        "-c", f"Boot{entry_id}", name, path
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


def remove_boot_entry(config: ConfigManager, entry_id: str) -> subprocess.CompletedProcess:
    """Remove a boot entry using bootmgr helper."""
    cmd = [
        str(config.paths.bootmgr_helper_relative),
        "-N", f"{entry_id}"
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


def create_boot_entry(config: ConfigManager) -> subprocess.CompletedProcess:
    """Create a new boot entry."""
    cmd = [str(config.paths.bootmgr_helper_relative), "-c"]
    return subprocess.run(cmd, capture_output=True, text=True)


def backup_boot_entries(config: ConfigManager) -> subprocess.CompletedProcess:
    """Backup boot entries."""
    cmd = [str(config.paths.bootmgr_helper_relative), "-B"]
    return subprocess.run(cmd, capture_output=True, text=True)


# Legacy compatibility functions (to be removed after migration)
def mkdir(path: str) -> None:
    """Create directory (legacy function)."""
    Path(path).mkdir(parents=True, exist_ok=True)


def rmdir(path: str) -> None:
    """Remove directory (legacy function)."""
    shutil.rmtree(path, ignore_errors=True)
