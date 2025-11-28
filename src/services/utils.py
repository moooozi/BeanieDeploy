"""
Utility functions for validation and other common operations.
Formatting functions have been moved to utils.formatting module.
"""
import json
import re
from typing import Optional

# Re-export formatting functions from the new location for backward compatibility
from utils.formatting import format_speed, format_bytes as format_size, format_eta  # type: ignore


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
