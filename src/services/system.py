"""
System-level operations and utilities.
Handles admin privileges, Windows registry, system information, etc.

For privilege escalation, use the new privilege_manager module:
    from services.privilege_manager import run_elevated_cmd, run_elevated_function

For async privileged operations:
    from services.async_privileged_operations import run_elevated_cmd_async
"""

import ctypes
import locale
import winreg

from utils import com_context


def is_admin() -> bool:
    """Check if the current process has administrator privileges."""
    return bool(ctypes.windll.shell32.IsUserAnAdmin())


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


def detect_nvidia() -> bool:
    """
    Detect if NVIDIA graphics card is present in the system.

    Returns:
        True if NVIDIA GPU detected, False otherwise
    """
    try:
        with com_context():
            import win32com.client

            wmi = win32com.client.GetObject("winmgmts:")
            video_controllers = wmi.InstancesOf("Win32_VideoController")
            for controller in video_controllers:
                if "NVIDIA" in str(controller.Name).upper():
                    return True
            return False
    except Exception:
        return False


def app_quit() -> None:
    """Quit the application."""
    raise SystemExit
