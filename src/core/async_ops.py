"""
Modern async operations management.
Replaces the chaotic queue-based system with proper async/await patterns.
"""
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass
from enum import Enum

from utils.logging import get_logger
from utils.errors import BeanieDeployError


class OperationStatus(Enum):
    """Status of async operations."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OperationResult:
    """Result of an async operation."""
    status: OperationStatus
    result: Any = None
    error: Optional[Exception] = None
    duration: float = 0.0


class AsyncOperationManager:
    """
    Modern async operation manager to replace the old AsyncOperations class.
    Uses proper async/await patterns and thread pools.
    """
    
    def __init__(self, max_workers: int = 4):
        self.logger = get_logger(__name__)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.operations: Dict[str, Future] = {}
        self._operation_counter = 0
    
    def submit_operation(
        self,
        func: Callable,
        *args,
        operation_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Submit an operation to run asynchronously.
        
        Args:
            func: Function to execute
            *args: Arguments for the function
            operation_id: Optional custom operation ID
            **kwargs: Keyword arguments for the function
            
        Returns:
            Operation ID for tracking
        """
        if operation_id is None:
            self._operation_counter += 1
            operation_id = f"op_{self._operation_counter}"
        
        self.logger.debug(f"Submitting operation {operation_id}: {func.__name__}")
        
        future = self.executor.submit(func, *args, **kwargs)
        self.operations[operation_id] = future
        
        return operation_id
    
    def get_operation_status(self, operation_id: str) -> OperationStatus:
        """Get the status of an operation."""
        if operation_id not in self.operations:
            return OperationStatus.FAILED
        
        future = self.operations[operation_id]
        
        if future.cancelled():
            return OperationStatus.CANCELLED
        elif future.done():
            if future.exception():
                return OperationStatus.FAILED
            else:
                return OperationStatus.COMPLETED
        else:
            return OperationStatus.RUNNING
    
    def get_operation_result(self, operation_id: str, timeout: Optional[float] = None) -> OperationResult:
        """
        Get the result of an operation.
        
        Args:
            operation_id: ID of the operation
            timeout: Maximum time to wait for completion
            
        Returns:
            Operation result
        """
        if operation_id not in self.operations:
            return OperationResult(
                status=OperationStatus.FAILED,
                error=BeanieDeployError(f"Operation {operation_id} not found")
            )
        
        future = self.operations[operation_id]
        
        try:
            result = future.result(timeout=timeout)
            return OperationResult(
                status=OperationStatus.COMPLETED,
                result=result
            )
        except TimeoutError:
            return OperationResult(
                status=OperationStatus.RUNNING
            )
        except Exception as e:
            return OperationResult(
                status=OperationStatus.FAILED,
                error=e
            )
    
    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel an operation."""
        if operation_id not in self.operations:
            return False
        
        future = self.operations[operation_id]
        return future.cancel()
    
    def wait_for_operation(self, operation_id: str, timeout: Optional[float] = None) -> OperationResult:
        """Wait for an operation to complete."""
        return self.get_operation_result(operation_id, timeout)
    
    def cleanup_completed_operations(self) -> None:
        """Remove completed operations from tracking."""
        completed_ops = [
            op_id for op_id, future in self.operations.items()
            if future.done()
        ]
        
        for op_id in completed_ops:
            del self.operations[op_id]
    
    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the operation manager."""
        self.executor.shutdown(wait=wait)


class ProgressTracker:
    """Track progress of long-running operations."""
    
    def __init__(self):
        self.progress = 0.0
        self.message = ""
        self.callbacks = []
    
    def update(self, progress: float, message: str = "") -> None:
        """Update progress and notify callbacks."""
        self.progress = max(0.0, min(100.0, progress))
        self.message = message
        
        for callback in self.callbacks:
            try:
                callback(self.progress, self.message)
            except Exception:
                # Don't let callback errors stop progress updates
                pass
    
    def add_callback(self, callback: Callable[[float, str], None]) -> None:
        """Add a progress callback."""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[float, str], None]) -> None:
        """Remove a progress callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)


# Global instance
_async_manager: Optional[AsyncOperationManager] = None


def get_async_manager() -> AsyncOperationManager:
    """Get the global async operation manager."""
    global _async_manager
    if _async_manager is None:
        _async_manager = AsyncOperationManager()
    return _async_manager


def set_async_manager(manager: AsyncOperationManager) -> None:
    """Set the global async operation manager (for testing)."""
    global _async_manager
    _async_manager = manager


# Convenience functions
def submit_async(func: Callable, *args, **kwargs) -> str:
    """Submit an async operation."""
    return get_async_manager().submit_operation(func, *args, **kwargs)


def wait_for_result(operation_id: str, timeout: Optional[float] = None) -> OperationResult:
    """Wait for an operation result."""
    return get_async_manager().wait_for_operation(operation_id, timeout)
