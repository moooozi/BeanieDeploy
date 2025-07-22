"""
Utility functions for formatting, validation, and other common operations.
"""
import json
import re
from typing import Union, Optional


def format_speed(speed: float) -> str:
    """
    Format speed in bytes/second to human-readable format.
    
    Args:
        speed: Speed in bytes per second
        
    Returns:
        Formatted speed string
    """
    speed_bits = speed * 8  # Convert bytes to bits
    if speed_bits < 1024:
        return f"{speed_bits:.2f} bit/s"
    elif speed_bits < 1024 * 1024:
        return f"{speed_bits / 1024:.2f} Kbit/s"
    else:
        return f"{speed_bits / (1024 * 1024):.2f} Mbit/s"


def format_size(size: float) -> str:
    """
    Format file size in bytes to human-readable format.
    
    Args:
        size: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size < 1024:
        return f"{size:.2f} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"


def format_eta(eta_in_seconds: Union[float, str]) -> str:
    """
    Format estimated time remaining in human-readable format.
    
    Args:
        eta_in_seconds: ETA in seconds or "N/A"
        
    Returns:
        Formatted ETA string
    """
    if eta_in_seconds == "N/A":
        return str(eta_in_seconds)
    
    eta_seconds = float(eta_in_seconds)
    hours, remainder = divmod(eta_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{int(hours)} {{ln_hour}} {int(minutes):02} {{ln_minute}} {int(seconds):02} {{ln_second}} {{ln_left}}"
    elif minutes > 0:
        return f"{int(minutes)} {{ln_minute}} {int(seconds):02} {{ln_second}} {{ln_left}}"
    else:
        return f"{int(seconds)} {{ln_second}} {{ln_left}}"


def validate_with_regex(var: str, regex: str, mode: str = "read") -> Optional[bool]:
    """
    Validate a string against a regex pattern.
    
    Args:
        var: String to validate
        regex: Regular expression pattern
        mode: "read" for validation only, "fix" to attempt correction
        
    Returns:
        True if valid, False if invalid, None if string becomes empty after fixing
    """
    regex_compiled = re.compile(regex)
    
    while var != "":
        if re.match(regex_compiled, var):
            return True
        elif mode == "read":
            return False
        elif mode == "fix":
            var = var[:-1]
    
    # String is empty now
    return None


def enqueue_output(out, queue) -> None:
    """
    Read output from a stream and put it into a queue.
    Used for asynchronous process communication.
    
    Args:
        out: Output stream to read from
        queue: Queue to put output into
    """
    for line in iter(out.readline, b""):
        try:
            parsed_line = json.loads(line)
        except json.JSONDecodeError:
            parsed_line = line
        queue.put(parsed_line)
    out.close()
