"""
Centralized error handling and custom exceptions for BeanieDeploy.
Replaces the chaotic exception handling with proper error management.
"""
from typing import Optional, Any
from dataclasses import dataclass


class BeanieDeployError(Exception):
    """Base exception for all BeanieDeploy errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[dict] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class ConfigurationError(BeanieDeployError):
    """Raised when there's a configuration problem."""
    pass


class SystemRequirementError(BeanieDeployError):
    """Raised when system requirements are not met."""
    pass


class PrivilegeError(BeanieDeployError):
    """Raised when admin privileges are required but not available."""
    pass


class NetworkError(BeanieDeployError):
    """Raised when network operations fail."""
    pass


class FileSystemError(BeanieDeployError):
    """Raised when file system operations fail."""
    pass


class InstallationError(BeanieDeployError):
    """Raised when installation process fails."""
    pass


class ValidationError(BeanieDeployError):
    """Raised when input validation fails."""
    pass


@dataclass
class ErrorInfo:
    """Structured error information."""
    
    error_type: str
    message: str
    error_code: Optional[str] = None
    details: Optional[dict] = None
    suggestion: Optional[str] = None
    recoverable: bool = True


class ErrorHandler:
    """Centralized error handling and reporting."""
    
    def __init__(self):
        self.error_callbacks = []
    
    def add_error_callback(self, callback):
        """Add a callback to be notified of errors."""
        self.error_callbacks.append(callback)
    
    def handle_error(self, error: Exception, context: str = "") -> ErrorInfo:
        """
        Handle an error and convert it to structured information.
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
            
        Returns:
            Structured error information
        """
        if isinstance(error, BeanieDeployError):
            error_info = ErrorInfo(
                error_type=error.__class__.__name__,
                message=str(error),
                error_code=error.error_code,
                details=error.details,
                recoverable=self._is_recoverable(error)
            )
        else:
            error_info = ErrorInfo(
                error_type=error.__class__.__name__,
                message=str(error),
                details={"context": context} if context else None,
                recoverable=False
            )
        
        # Add helpful suggestions
        error_info.suggestion = self._get_suggestion(error_info)
        
        # Notify callbacks
        for callback in self.error_callbacks:
            try:
                callback(error_info)
            except Exception:
                # Don't let error handling callbacks crash the app
                pass
        
        return error_info
    
    def _is_recoverable(self, error: BeanieDeployError) -> bool:
        """Determine if an error is recoverable."""
        non_recoverable_types = (ConfigurationError, SystemRequirementError)
        return not isinstance(error, non_recoverable_types)
    
    def _get_suggestion(self, error_info: ErrorInfo) -> Optional[str]:
        """Get a helpful suggestion for resolving the error."""
        suggestions = {
            "PrivilegeError": "Try running the application as administrator.",
            "NetworkError": "Check your internet connection and try again.",
            "FileSystemError": "Ensure you have sufficient disk space and permissions.",
            "SystemRequirementError": "Verify your system meets the minimum requirements.",
            "ValidationError": "Please check your input and try again.",
        }
        return suggestions.get(error_info.error_type)


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_exception(func):
    """Decorator for automatic exception handling."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_info = get_error_handler().handle_error(e, func.__name__)
            # Re-raise as BeanieDeployError if it wasn't already
            if not isinstance(e, BeanieDeployError):
                raise BeanieDeployError(
                    f"Error in {func.__name__}: {str(e)}",
                    details=error_info.details
                ) from e
            raise
    return wrapper
