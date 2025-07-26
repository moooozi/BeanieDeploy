import ctypes
import ctypes.wintypes as wintypes
import os
import sys

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
advapi32 = ctypes.WinDLL('advapi32', use_last_error=True)
user32 = ctypes.WinDLL('user32', use_last_error=True)

SE_PRIVILEGE_ENABLED = 0x00000002
TOKEN_QUERY = 0x0008
TOKEN_ADJUST_PRIVILEGES = 0x0020


# Privilege adjustment helpers
class LUID(ctypes.Structure):
    _fields_ = [("LowPart", wintypes.DWORD), ("HighPart", wintypes.LONG)]

class TOKEN_PRIVILEGES(ctypes.Structure):
    _fields_ = [
        ("PrivilegeCount", wintypes.DWORD),
        ("Luid", LUID),
        ("Attributes", wintypes.DWORD)
    ]

# Set argtypes/restype for OpenProcessToken
advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
advapi32.OpenProcessToken.restype = wintypes.BOOL

# Set argtypes/restype for LookupPrivilegeValueW
advapi32.LookupPrivilegeValueW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.POINTER(LUID)]
advapi32.LookupPrivilegeValueW.restype = wintypes.BOOL

# Set argtypes/restype for AdjustTokenPrivileges
advapi32.AdjustTokenPrivileges.argtypes = [
    wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(TOKEN_PRIVILEGES),
    wintypes.DWORD, ctypes.c_void_p, ctypes.c_void_p
]
advapi32.AdjustTokenPrivileges.restype = wintypes.BOOL

def obtain_privileges(privilege):
    hToken = wintypes.HANDLE()
    if not advapi32.OpenProcessToken(kernel32.GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, ctypes.byref(hToken)):
        raise OSError("OpenProcessToken failed")
    luid = LUID()
    if not advapi32.LookupPrivilegeValueW(None, privilege, ctypes.byref(luid)):
        raise OSError("LookupPrivilegeValue failed")
    tp = TOKEN_PRIVILEGES(1, luid, SE_PRIVILEGE_ENABLED)
    if not advapi32.AdjustTokenPrivileges(hToken, False, ctypes.byref(tp), 0, None, None):
        raise OSError("AdjustTokenPrivileges failed")
    
def obtain_system_privileges():
    obtain_privileges("SeSystemEnvironmentPrivilege")
    obtain_privileges("SeShutdownPrivilege")

def _setup_sys_path():
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))


def obtain_all_privileges() -> None:
    _setup_sys_path()
    from services.system import get_admin
    get_admin()
    obtain_system_privileges()
    print("System privileges obtained successfully.")




if __name__ == "__main__":
    _setup_sys_path()
    from services.system import get_admin, is_admin
    if not is_admin():
        print("Elevating to admin privileges...")
        get_admin()
    if is_admin():
        print("Running with admin privileges")
    else:
        raise PermissionError("Admin privileges not obtained")
    try:
        obtain_system_privileges()
        print("System privileges obtained successfully.")
    except Exception as e:
        print(f"Error: {e}")
    
    input("Press Enter to exit...")