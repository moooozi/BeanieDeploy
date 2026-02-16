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
import contextlib
import ctypes
import inspect
import logging
import pickle
import subprocess
import sys
import threading
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any, Optional, TypeVar, cast

import pywintypes
import win32file
import win32pipe

T = TypeVar("T")

BUFFER_SIZE = 65536


class _PrivilegeManager:
    """Internal singleton for managing the privilege helper process."""

    _instance: Optional["_PrivilegeManager"] = None
    _lock = threading.Lock()

    def __init__(self):
        self.pipe_name: str | None = None
        self.pipe_handle: int | None = None
        self._initialized = False
        self._initializing = False

    @classmethod
    def get_instance(cls) -> "_PrivilegeManager":
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
                    win32pipe.PIPE_TYPE_BYTE
                    | win32pipe.PIPE_READMODE_BYTE
                    | win32pipe.PIPE_WAIT,
                    1,  # Max instances
                    BUFFER_SIZE,
                    BUFFER_SIZE,
                    0,
                    None,  # type: ignore
                )

                if self.pipe_handle == win32file.INVALID_HANDLE_VALUE:
                    msg = "Failed to create named pipe"
                    raise RuntimeError(msg)

                # Get path to executable
                executable = sys.executable

                # Build command line for elevated helper
                args = [*sys.argv, "/PIPE", self.pipe_name]

                command_line = " ".join(f'"{arg}"' for arg in args)

                # Launch elevated helper
                result = ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", executable, command_line, None, 0
                )

                if result <= 32:
                    msg = f"Failed to launch privilege helper (error code: {result})"
                    raise RuntimeError(msg)

                # Wait for helper to connect
                logging.debug(
                    f"Waiting for privilege helper to connect on pipe: {self.pipe_name}"
                )
                win32pipe.ConnectNamedPipe(self.pipe_handle, None)
                logging.debug(
                    f"Privilege helper successfully connected on pipe: {self.pipe_name}"
                )

                # Register cleanup on exit
                atexit.register(self.shutdown)

                self._initialized = True

            finally:
                self._initializing = False

    def _send_command(self, command_data: dict[str, Any]) -> Any:
        """Send command to helper and get response."""
        self._ensure_initialized()

        if self.pipe_handle is None:
            msg = "Privilege manager not initialized"
            raise RuntimeError(msg)

        try:
            data = pickle.dumps(command_data)
            win32file.WriteFile(self.pipe_handle, data)  # type: ignore

            _, response_data = win32file.ReadFile(self.pipe_handle, BUFFER_SIZE)  # type: ignore
            response = pickle.loads(response_data)  # type: ignore

            if isinstance(response, dict) and response.get("type") == "error":
                msg = f"Privilege helper error: {response['error']}"
                raise RuntimeError(msg)

            return response

        except pywintypes.error as e:
            if e.args[0] in (109, 232):
                self._initialized = False
                msg = "Connection to privilege helper lost"
                raise RuntimeError(msg) from e
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
        except Exception:
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
            with contextlib.suppress(Exception):
                win32file.ReadFile(self.pipe_handle, BUFFER_SIZE)  # type: ignore

        except Exception:
            pass
        finally:
            with contextlib.suppress(Exception):
                win32file.CloseHandle(self.pipe_handle)  # type: ignore

            self.pipe_handle = None
            self._initialized = False


# Public API - Simple and clean
class elevated:  # noqa: N801
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
        if "creationflags" in kwargs:
            kwargs["creationflags"] |= subprocess.CREATE_NO_WINDOW
        else:
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        command_data = {
            "type": "subprocess",
            "args": args,
            "kwargs": kwargs,
        }

        response = manager._send_command(command_data)  # noqa: SLF001

        # Reconstruct CompletedProcess
        proc: subprocess.CompletedProcess = subprocess.CompletedProcess(
            args=response["args"],
            returncode=response["returncode"],
            stdout=response.get("stdout"),
            stderr=response.get("stderr"),
        )

        # Handle check flag if it was set
        if kwargs.get("check") and proc.returncode != 0:
            raise subprocess.CalledProcessError(
                proc.returncode, proc.args, proc.stdout, proc.stderr
            )

        return proc

    @staticmethod
    def call(
        target: Callable[..., T], args: tuple = (), kwargs: dict | None = None
    ) -> T:
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
                msg = "Function must be defined in a module"
                raise ValueError(msg)
            module_name = module.__name__
        except (TypeError, OSError) as e:
            msg = f"Cannot get module for function: {e}"
            raise ValueError(msg) from e

        command_data = {
            "type": "function",
            "module_name": module_name,
            "func_name": target.__name__,
            "args": args,
            "kwargs": kwargs,
        }

        response = manager._send_command(command_data)  # noqa: SLF001
        return cast("T", response["result"])


if __name__ == "__main__":
    # Check for elevated helper mode when not in PyInstaller bundle
    if "/PIPE" in sys.argv and not getattr(sys, "frozen", False):
        pipe_index = sys.argv.index("/PIPE")
        if pipe_index + 1 < len(sys.argv):
            pipe_name = sys.argv[pipe_index + 1]

            # Add src directory to path for module imports
            src_dir = Path(__file__).parent.parent
            if str(src_dir) not in sys.path:
                sys.path.insert(0, str(src_dir))

            from .privilege_helper import main

            main(pipe_name)
            raise SystemExit(0)
