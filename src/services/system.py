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


def get_windows_ui_locale() -> str:
    """Get the Windows UI locale (e.g., 'en_US', 'de_DE', 'fr_FR')."""
    lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
    return locale.windows_locale[lang_id]


def get_current_windows_timezone() -> str | None:
    """Get the current Windows timezone using Windows registry."""
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\TimeZoneInformation",
        )
        tz_name, _ = winreg.QueryValueEx(key, "TimeZoneKeyName")
        winreg.CloseKey(key)
        return tz_name
    except Exception:
        return None


def get_current_windows_timezone_iana() -> str | None:
    """Get the current Windows timezone in IANA format using tzlocal."""
    try:
        from tzlocal import get_localzone

        return get_localzone().key
    except Exception:
        return None


def get_windows_timezone_from_iana(iana_timezone: str) -> str | None:
    """Get the Windows timezone name from an IANA timezone string."""
    try:
        from tzlocal.windows_tz import tz_win

        return tz_win.get(iana_timezone)
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
