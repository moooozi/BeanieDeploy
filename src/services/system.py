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

import tzlocal

from utils import com_context


def is_admin() -> bool:
    """Check if the current process has administrator privileges."""
    return bool(ctypes.windll.shell32.IsUserAnAdmin())


def windows_language_code() -> str:
    """Get the Windows language code (e.g., 'en', 'de', 'fr')."""
    lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
    lang_code = locale.windows_locale[lang_id]
    return lang_code.split("_")[0]


def get_current_windows_locale() -> str | None:
    """Get the current Windows locale."""
    try:
        return locale.getlocale()[0] or None
    except Exception:
        return None


def get_current_windows_timezone() -> str | None:
    """Get the current Windows timezone."""
    try:
        local_tz = tzlocal.get_localzone()
        return local_tz.key
    except Exception:
        return None


def get_current_windows_keyboard() -> str | None:
    """Get the current Windows keyboard layout friendly name."""
    try:
        # Get the first keyboard layout from registry
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Keyboard Layout\Preload")
        try:
            # Get the first layout (usually "1")
            layout_id = winreg.EnumValue(key, 0)[1]
            winreg.CloseKey(key)

            # Now get the friendly name from the Keyboard Layouts registry
            layout_key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                rf"SYSTEM\CurrentControlSet\Control\Keyboard Layouts\{layout_id}",
            )
            friendly_name, _ = winreg.QueryValueEx(layout_key, "Layout Text")
            winreg.CloseKey(layout_key)
            return friendly_name
        except (OSError, FileNotFoundError):
            winreg.CloseKey(key)
            return None
    except (OSError, FileNotFoundError):
        return None


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
