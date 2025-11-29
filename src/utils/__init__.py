"""
Utilities package providing formatting, Windows API access, and localization.

This package contains reusable utility functions organized by purpose:
- formatting: Human-readable text formatting (sizes, speeds, times)
- localization: Translation and language management
- errors: Custom error classes
- logging: Logging configuration
"""

import contextlib

# Export commonly used utilities for convenient imports
from .formatting import (
    format_bytes,
    format_speed,
    format_time_delta,
    format_eta,
)


from .translation_manager import (
    set_language,
    get_language,
    gettext,
)

from .uuid_utils import PartitionUuid


@contextlib.contextmanager
def com_context():
    """
    Context manager for thread-safe COM operations.
    
    Initializes COM in the current thread and cleans up afterwards.
    Safe for nesting - only initializes once per thread and uninitializes
    when the outermost context exits.
    """
    import pythoncom
    import threading
    
    # Thread-local storage for COM initialization count
    local = threading.local()
    if not hasattr(local, 'com_init_count'):
        local.com_init_count = 0
    
    initialized_here = False
    if local.com_init_count == 0:
        pythoncom.CoInitialize()
        initialized_here = True
    
    local.com_init_count += 1
    
    try:
        yield
    finally:
        local.com_init_count -= 1
        if initialized_here and local.com_init_count == 0:
            pythoncom.CoUninitialize()


__all__ = [
    # Formatting
    'format_bytes',
    'format_speed',
    'format_time_delta',
    'format_eta',
    # Translation
    'set_language',
    'get_language',
    'gettext',
    # COM utilities
    'com_context',
    # UUID utilities
    'PartitionUuid',
]

