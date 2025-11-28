"""
Privilege Manager - Simplified API for elevated operations.

Provides two simple interfaces:
1. elevated.run() - Same API as subprocess.run()
2. elevated.call() - Same API as threading.Thread/multiprocessing.Process

Usage:
    # Subprocess with elevation
    from services import elevated
    proc = elevated.run(["powershell.exe", "-Command", "Get-Process"], 
                        capture_output=True, text=True)
    
    # Function with elevation
    result = elevated.call(target=my_function, args=(1, 2), kwargs={'key': 'value'})
"""
import atexit
import ctypes
import inspect
import pickle
import subprocess
import sys
import threading
import uuid
import win32file
import win32pipe
import pywintypes
from typing import Any, Callable, Dict, Optional, Tuple

BUFFER_SIZE = 65536


class _PrivilegeManager:
    """Internal singleton for managing the privilege helper process."""
    
    _instance: Optional['_PrivilegeManager'] = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.pipe_name: Optional[str] = None
        self.pipe_handle: Optional[int] = None
        self._initialized = False
        self._initializing = False
        
    @classmethod
    def get_instance(cls) -> '_PrivilegeManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _ensure_initialized(self):
        """Ensure the privilege helper is running and connected."""
        if self._initialized:
            return
            
        with self._lock:
            if self._initialized:
                return
                
            if self._initializing:
                # Another thread is initializing, wait for it
                while self._initializing:
                    pass
                return
            
            self._initializing = True
            
            try:
                # Generate unique pipe name
                self.pipe_name = f"BeanieDeploy_Privilege_{uuid.uuid4().hex}"
                full_pipe_name = rf"\\.\pipe\{self.pipe_name}"
                
                # Create the named pipe
                self.pipe_handle = win32pipe.CreateNamedPipe(
                    full_pipe_name,
                    win32pipe.PIPE_ACCESS_DUPLEX,
                    win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
                    1,  # Max instances
                    BUFFER_SIZE,
                    BUFFER_SIZE,
                    0,
                    None,  # type: ignore
                )
                
                if self.pipe_handle == win32file.INVALID_HANDLE_VALUE:
                    raise RuntimeError("Failed to create named pipe")
                
                # Get path to executable
                executable = sys.executable
                
                # Launch elevated helper (embedded in main exe)
                result = ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",
                    executable,
                    f'/PIPE {self.pipe_name}',
                    None,
                    0,  # SW_HIDE
                )
                
                if result <= 32:
                    raise RuntimeError(f"Failed to launch privilege helper (error code: {result})")
                
                # Wait for helper to connect
                win32pipe.ConnectNamedPipe(self.pipe_handle, None)
                
                # Register cleanup on exit
                atexit.register(self.shutdown)
                
                self._initialized = True
                
            finally:
                self._initializing = False
    
    def _send_command(self, command_data: Dict[str, Any]) -> Any:
        """Send command to helper and get response."""
        self._ensure_initialized()
        
        if self.pipe_handle is None:
            raise RuntimeError("Privilege manager not initialized")
        
        try:
            data = pickle.dumps(command_data)
            win32file.WriteFile(self.pipe_handle, data)  # type: ignore
            
            _, response_data = win32file.ReadFile(self.pipe_handle, BUFFER_SIZE)  # type: ignore
            response = pickle.loads(response_data)  # type: ignore
            
            if isinstance(response, dict) and response.get("type") == "error":
                raise RuntimeError(f"Privilege helper error: {response['error']}")
            
            return response
            
        except pywintypes.error as e:
            if e.args[0] in (109, 232):
                self._initialized = False
                raise RuntimeError("Connection to privilege helper lost")
            raise
    
    def ping(self) -> bool:
        """
        Check if the privilege helper is alive and responsive.
        
        Returns:
            True if helper responds, False otherwise
        """
        try:
            response = self._send_command({"type": "ping"})
            return isinstance(response, dict) and response.get("type") == "ping"
        except:
            return False
    
    def shutdown(self):
        """Shutdown the privilege helper and close the pipe."""
        if not self._initialized or self.pipe_handle is None:
            return
            
        try:
            # Send shutdown command
            shutdown_data = {"type": "shutdown"}
            data = pickle.dumps(shutdown_data)
            win32file.WriteFile(self.pipe_handle, data)  # type: ignore
            
            # Read acknowledgment
            try:
                win32file.ReadFile(self.pipe_handle, BUFFER_SIZE)  # type: ignore
            except:
                pass
                
        except:
            pass
        finally:
            try:
                win32file.CloseHandle(self.pipe_handle)  # type: ignore
            except:
                pass
            
            self.pipe_handle = None
            self._initialized = False


# Public API - Simple and clean
class elevated:
    """Namespace for elevated operations. Use elevated.run() or elevated.call()."""
    
    @staticmethod
    def run(args, **kwargs) -> subprocess.CompletedProcess:
        """
        Run a subprocess with elevated privileges. API identical to subprocess.run().
        
        Args:
            args: Command to execute
            **kwargs: All subprocess.run() arguments supported
            
        Returns:
            subprocess.CompletedProcess object
            
        Example:
            proc = elevated.run(["powershell.exe", "-Command", "Get-Process"],
                               capture_output=True, text=True)
        """
        # Let subprocess.run handle all the argument parsing/validation
        # We just intercept and forward to the helper
        manager = _PrivilegeManager.get_instance()
        
        # Add CREATE_NO_WINDOW flag
        if 'creationflags' in kwargs:
            kwargs['creationflags'] |= subprocess.CREATE_NO_WINDOW
        else:
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        
        command_data = {
            "type": "subprocess",
            "args": args,
            "kwargs": kwargs,
        }
        
        response = manager._send_command(command_data)
        
        # Reconstruct CompletedProcess
        proc = subprocess.CompletedProcess(
            args=response["args"],
            returncode=response["returncode"],
            stdout=response.get("stdout"),
            stderr=response.get("stderr"),
        )
        
        # Handle check flag if it was set
        if kwargs.get('check') and proc.returncode != 0:
            raise subprocess.CalledProcessError(
                proc.returncode, proc.args, proc.stdout, proc.stderr
            )
        
        return proc
    
    @staticmethod
    def call(target: Callable, args: Tuple = (), kwargs: Optional[Dict] = None) -> Any:
        """
        Call a function with elevated privileges. API similar to threading.Thread.
        
        Args:
            target: Function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            
        Returns:
            Function's return value
            
        Example:
            def get_disk_info():
                import subprocess
                return subprocess.check_output(["diskpart", "..."])
            
            result = elevated.call(target=get_disk_info)
        """
        if kwargs is None:
            kwargs = {}
        
        manager = _PrivilegeManager.get_instance()
        
        # Get module and function names
        try:
            module = inspect.getmodule(target)
            if module is None:
                raise ValueError("Function must be defined in a module")
            module_name = module.__name__
        except (TypeError, OSError) as e:
            raise ValueError(f"Cannot get module for function: {e}")
        
        command_data = {
            "type": "function",
            "module_name": module_name,
            "func_name": target.__name__,
            "args": args,
            "kwargs": kwargs,
        }
        
        response = manager._send_command(command_data)
        return response["result"]
