"""
Formatting utilities for human-readable data representations.
Uses well-maintained libraries (humanize) for proper localization support.
"""
import humanize


def format_bytes(size_bytes: int, binary: bool = False) -> str:
    """
    Format bytes into human-readable string.
    
    Args:
        size_bytes: Size in bytes
        binary: If True, use binary (1024) instead of decimal (1000) units
        
    Returns:
        Human-readable string (e.g., "1.5 GB", "2.3 MiB")
    """
    return humanize.naturalsize(size_bytes, binary=binary)


def format_speed(bytes_per_second: float) -> str:
    """
    Format transfer speed into human-readable string.
    
    Args:
        bytes_per_second: Speed in bytes per second
        
    Returns:
        Human-readable string (e.g., "1.5 MB/s")
    """
    return humanize.naturalsize(bytes_per_second, binary=False) + "/s"


def format_time_delta(seconds: float) -> str:
    """
    Format time duration into human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Human-readable string (e.g., "2 hours", "5 minutes")
    """
    return humanize.naturaldelta(seconds)


def format_eta(seconds: float) -> str:
    """
    Format estimated time remaining.
    
    Args:
        seconds: Seconds remaining
        
    Returns:
        Human-readable ETA string
    """
    if seconds < 0:
        return "calculating..."
    
    return format_time_delta(seconds)
