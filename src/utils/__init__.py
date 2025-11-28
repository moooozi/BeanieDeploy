"""
Utilities package providing formatting, Windows API access, and localization.

This package contains reusable utility functions organized by purpose:
- formatting: Human-readable text formatting (sizes, speeds, times)
- localization: Translation and language management
- errors: Custom error classes
- logging: Logging configuration
"""

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
]
