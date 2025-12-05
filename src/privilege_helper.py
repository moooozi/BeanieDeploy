"""
Privilege Helper - Runs as administrator and executes commands via Named Pipe.

This script is launched with elevated privileges and listens for commands on a Named Pipe.
It can execute both PowerShell commands and Python functions, then returns the results.
"""

import contextlib
import pickle
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any

import pywintypes
import win32file

# Add src directory to path for module imports
src_dir = Path(__file__).parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

BUFFER_SIZE = 65536


def execute_command(command_data: dict[str, Any]) -> Any:
    """
    Execute a command (subprocess or function) and return results.

    Args:
        command_data: Dictionary with type and parameters

    Returns:
        Serializable result
    """
    try:
        cmd_type = command_data.get("type")

        if cmd_type == "subprocess":
            # Execute subprocess.run with provided arguments
            args = command_data.get("args")
            kwargs = command_data.get("kwargs", {})

            if not args:
                msg = "args is required"
                raise ValueError(msg)

            proc = subprocess.run(args, **kwargs)  # type: ignore

            return {
                "type": "subprocess",
                "args": proc.args,
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }

        if cmd_type == "function":
            # Execute a Python function by importing its module
            module_name = command_data.get("module_name")
            func_name = command_data.get("func_name")
            args = command_data.get("args", ())
            kwargs = command_data.get("kwargs", {})

            if not module_name or not func_name:
                msg = "module_name and func_name are required"
                raise ValueError(msg)

            import importlib

            module = importlib.import_module(module_name)
            func = getattr(module, func_name)
            result = func(*args, **kwargs)

            return {
                "type": "function",
                "result": result,
            }

        if cmd_type == "ping":
            return {"type": "ping", "message": "pong"}

        msg = f"Unknown command type: {cmd_type}"
        raise ValueError(msg)

    except Exception as e:
        return {
            "type": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


def main(pipe_name: str):
    """Main loop - listen on Named Pipe and execute commands."""

    full_pipe_name = rf"\\.\pipe\{pipe_name}"
    pipe_handle = None

    try:
        # Connect to the existing pipe created by the client
        pipe_handle = win32file.CreateFile(
            full_pipe_name,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None,
        )

        # Main command loop
        while True:
            try:
                # Read command from pipe
                _, data = win32file.ReadFile(pipe_handle, BUFFER_SIZE)  # type: ignore

                if not data:
                    break

                # Deserialize command
                command_data = pickle.loads(data)  # type: ignore

                # Check for shutdown command
                if command_data.get("type") == "shutdown":
                    response = {"success": True, "message": "Shutting down"}
                    response_data = pickle.dumps(response)
                    win32file.WriteFile(pipe_handle, response_data)  # type: ignore
                    break

                # Execute command
                response = execute_command(command_data)

                # Send response back
                response_data = pickle.dumps(response)
                win32file.WriteFile(pipe_handle, response_data)  # type: ignore

            except pywintypes.error as e:
                # Pipe error - likely disconnected
                if e.args[0] in (109, 232):  # ERROR_BROKEN_PIPE, ERROR_NO_DATA
                    break
                raise

    except Exception:
        traceback.print_exc()
        raise SystemExit(1) from None
    finally:
        if pipe_handle is not None:
            with contextlib.suppress(Exception):
                win32file.CloseHandle(pipe_handle)  # type: ignore
