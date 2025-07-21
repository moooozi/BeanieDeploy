"""
Centralized logging configuration for BeanieDeploy.
Replaces random print() statements with proper logging.
"""
import logging
import sys
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green  
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to the log level name
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Set up centralized logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to
        console_output: Whether to output logs to console
        
    Returns:
        Configured logger instance
    """
    
    # Get the root logger for our application
    logger = logging.getLogger("beaniedeploy")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = ColoredFormatter(
        fmt='%(levelname)s | %(message)s'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "beaniedeploy") -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(name)


# Module-level convenience functions
def log_debug(message: str, *args, **kwargs):
    """Log a debug message."""
    get_logger().debug(message, *args, **kwargs)


def log_info(message: str, *args, **kwargs):
    """Log an info message."""
    get_logger().info(message, *args, **kwargs)


def log_warning(message: str, *args, **kwargs):
    """Log a warning message."""
    get_logger().warning(message, *args, **kwargs)


def log_error(message: str, *args, **kwargs):
    """Log an error message."""
    get_logger().error(message, *args, **kwargs)


def log_critical(message: str, *args, **kwargs):
    """Log a critical message."""
    get_logger().critical(message, *args, **kwargs)


def log_exception(message: str, *args, **kwargs):
    """Log an exception with traceback."""
    get_logger().exception(message, *args, **kwargs)
