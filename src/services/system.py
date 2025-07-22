"""
System-level operations and utilities.
Handles admin privileges, Windows registry, system information, etc.
"""
import ctypes
import os
import subprocess
import winreg
from typing import Union
from pathlib import Path
import locale


def is_admin() -> bool:
    """Check if the current process has administrator privileges."""
    return bool(ctypes.windll.shell32.IsUserAnAdmin())


def get_admin(args: str = "") -> None:
    """
    Elevate to administrator privileges.
    
    Args:
        args: Additional command line arguments to pass when restarting with admin privileges
        
    Raises:
        SystemExit: Always raises SystemExit after attempting to restart with admin privileges
    """
    from sys import executable, argv
    
    # Check if running in PyInstaller bundle
    is_pyinstaller_bundle = getattr(__import__('sys'), 'frozen', False) and hasattr(__import__('sys'), '_MEIPASS')
    
    if is_pyinstaller_bundle:
        # In PyInstaller bundle: exclude argv[0] since executable is the bundled .exe
        existing_args = " ".join(argv[1:]) if len(argv) > 1 else ""
    else:
        # In dev mode: include argv[0] since executable is python.exe and we need the script path
        existing_args = " ".join(argv)
    
    args_combined = existing_args + (" " + args if args else "")
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, args_combined, None, 1)
    raise SystemExit


def get_windows_username() -> str:
    """Get the current Windows username."""
    return os.getlogin()


def windows_language_code() -> str:
    """Get the Windows language code (e.g., 'en', 'de', 'fr')."""
    lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
    lang_code = locale.windows_locale[lang_id]
    return lang_code.split("_")[0]


def quit_and_restart_windows() -> None:
    """Initiate a Windows restart and quit the application."""
    ctypes.windll.advapi32.InitiateSystemShutdownW(None, "Restarting...", 0, True, True)
    raise SystemExit


def set_windows_time_to_utc() -> bool:
    """
    Configure Windows to use UTC time instead of local time.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        key = winreg.CreateKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\TimeZoneInformation",
        )
        winreg.SetValueEx(key, "RealTimeIsUniversal", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def cleanup_on_reboot(dir_to_delete: Union[str, Path]) -> None:
    """
    Schedule a directory to be deleted on next reboot.
    
    Args:
        dir_to_delete: Path to directory that should be deleted on reboot
    """
    dir_path = str(dir_to_delete).replace("/", "\\")
    cmd = f'CMD /C rmdir /s /q "{dir_path}"'

    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
        0,
        winreg.KEY_SET_VALUE,
    ) as key:
        winreg.SetValueEx(key, "BeanyDeploy Cleanup", 0, winreg.REG_SZ, cmd)


def run_powershell_script(script: str) -> str:
    """
    Execute a PowerShell script and return the output.
    
    Args:
        script: PowerShell script to execute
        
    Returns:
        Script output as string
    """
    result = subprocess.run(
        [r"powershell.exe", "-ExecutionPolicy", "Unrestricted", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    return result.stdout


def detect_nvidia() -> bool:
    """
    Detect if NVIDIA graphics card is present in the system.
    
    Returns:
        True if NVIDIA GPU detected, False otherwise
    """
    result = subprocess.run(
        [r"powershell.exe", "Get-WmiObject Win32_VideoController"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    return "NVIDIA" in result.stdout


def app_quit() -> None:
    """Quit the application."""
    raise SystemExit
