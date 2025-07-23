import subprocess
from enum import Enum
from typing import Optional, Callable, List
from PySide6.QtCore import QObject, Signal, QThread

DETACHED_PROCESS_FLAG = 0x00000008


class Status(Enum):
    NOT_STARTED = "Not started"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"


class PySide6AsyncWorker(QThread):
    """
    QThread-based worker for async operations in PySide6.
    
    Much cleaner than the CustomTkinter version because Qt provides:
    - Built-in threading support
    - Proper signal/slot mechanism
    - Better error handling
    - Automatic thread management
    """
    
    # Signals
    finished = Signal(object)  # Emitted when operation completes
    error = Signal(str)  # Emitted on error
    output = Signal(object)  # Emitted for intermediate output
    
    def __init__(
        self,
        function: Optional[Callable] = None,
        cmd: Optional[List[str]] = None,
        args=(),
        kwargs=None,
    ):
        super().__init__()
        self.function = function
        self.cmd = cmd
        self.args = args
        self.kwargs = kwargs or {}
        self.status = Status.NOT_STARTED
        self.result = None

    def run(self):
        """Run the operation in the worker thread."""
        try:
            self.status = Status.RUNNING
            
            if self.function:
                self.result = self.function(*self.args, **self.kwargs)
            elif self.cmd:
                self.result = self._run_command()
            
            self.status = Status.COMPLETED
            self.finished.emit(self.result)
            
        except Exception as e:
            self.status = Status.FAILED
            self.error.emit(str(e))

    def _run_command(self) -> Optional[str]:
        """Run a command and capture output."""
        if not self.cmd:
            return None
            
        try:
            process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=DETACHED_PROCESS_FLAG
            )
            
            output_lines = []
            if process.stdout:
                for line in iter(process.stdout.readline, ''):
                    line = line.strip()
                    if line:
                        output_lines.append(line)
                        self.output.emit(line)  # Emit intermediate output
            
            process.wait()
            return '\n'.join(output_lines)
            
        except Exception as e:
            raise RuntimeError(f"Command execution failed: {str(e)}")


class PySide6AsyncOperations(QObject):
    """
    PySide6 implementation of async operations.
    
    Provides a clean interface for running operations asynchronously
    with proper Qt integration and signal/slot communication.
    """
    
    # Signals
    finished = Signal(object)
    error = Signal(str)
    output = Signal(object)
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.worker: Optional[PySide6AsyncWorker] = None
        self.status = Status.NOT_STARTED

    @classmethod
    def run(
        cls,
        function: Optional[Callable] = None,
        cmd: Optional[List[str]] = None,
        args=(),
        kwargs=None,
        parent: Optional[QObject] = None,
    ) -> 'PySide6AsyncOperations':
        """
        Create and start an async operation.
        
        Args:
            function: Python function to run
            cmd: Command to execute
            args: Arguments for the function
            kwargs: Keyword arguments for the function
            parent: Parent QObject
            
        Returns:
            PySide6AsyncOperations instance
        """
        instance = cls(parent)
        instance.run_async_process(function=function, cmd=cmd, args=args, kwargs=kwargs)
        return instance

    def run_async_process(
        self,
        function: Optional[Callable] = None,
        cmd: Optional[List[str]] = None,
        args=(),
        kwargs=None,
    ):
        """Start an async process."""
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        
        self.worker = PySide6AsyncWorker(function, cmd, args, kwargs)
        
        # Connect signals
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.output.connect(self._on_output)
        
        # Start the worker
        self.worker.start()
        self.status = Status.RUNNING

    def _on_finished(self, result):
        """Handle worker completion."""
        self.status = Status.COMPLETED
        self.finished.emit(result)

    def _on_error(self, error_msg: str):
        """Handle worker error."""
        self.status = Status.FAILED
        self.error.emit(error_msg)

    def _on_output(self, output):
        """Handle intermediate output."""
        self.output.emit(output)

    def is_running(self) -> bool:
        """Check if the operation is currently running."""
        return self.status == Status.RUNNING

    def wait_for_completion(self, timeout_ms: int = 30000) -> bool:
        """
        Wait for the operation to complete.
        
        Args:
            timeout_ms: Timeout in milliseconds
            
        Returns:
            True if completed within timeout, False otherwise
        """
        if self.worker:
            return self.worker.wait(timeout_ms)
        return True

    def stop(self):
        """Stop the current operation."""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            if not self.worker.wait(5000):  # Wait up to 5 seconds
                # In PySide6, there's no kill() method, just terminate
                self.worker.terminate()
            self.status = Status.FAILED


# Utility function for compatibility with existing code
def run_async_operation(
    function: Optional[Callable] = None,
    cmd: Optional[List[str]] = None,
    args=(),
    kwargs=None,
    parent: Optional[QObject] = None,
) -> PySide6AsyncOperations:
    """
    Convenience function to run an async operation.
    
    This provides compatibility with the existing async_operations.py interface.
    """
    return PySide6AsyncOperations.run(
        function=function,
        cmd=cmd,
        args=args,
        kwargs=kwargs,
        parent=parent
    )