"""
File management services.
Handles file operations, hashing, copying, etc.
"""

import hashlib
import os
from pathlib import Path
from urllib.parse import urlparse


def get_sha256_hash(file_path: str) -> str:
    """
    Calculate SHA256 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        SHA256 hash as hexadecimal string
    """
    sha256 = hashlib.sha256()
    with Path(file_path).open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def set_file_readonly(filepath: str, is_readonly: bool) -> None:
    """
    Set or remove read-only attribute on a file.

    Args:
        filepath: Path to the file
        is_readonly: True to make read-only, False to make writable
    """
    if is_readonly:
        Path(filepath).chmod(0o444)  # Read-only
    else:
        Path(filepath).chmod(0o666)  # Read-write


def get_file_name_from_url(url: str) -> str:
    """
    Extract filename from a URL.

    Args:
        url: URL to extract filename from

    Returns:
        Filename from the URL
    """
    parsed_url = urlparse(url)
    return Path(parsed_url.path).name


def find_file_by_name(name: str, lookup_dir: str) -> str | None:
    """
    Find a file by name in a directory tree.

    Args:
        name: Filename to search for
        lookup_dir: Directory to search in

    Returns:
        Full path to the file if found, None otherwise
    """
    for root, _, files in os.walk(lookup_dir):
        if name in files:
            return str(Path(root) / name)
    return None


def check_valid_existing_file(file_path: str, file_hash: str) -> bool | None:
    """
    Check if a file exists and has the correct hash.

    Args:
        file_path: Path to the file to check
        file_hash: Expected SHA256 hash

    Returns:
        True if file exists and hash matches,
        False if file doesn't exist,
        None if file exists but hash doesn't match (file is removed)
    """
    if not Path(file_path).is_file():
        return False

    if get_sha256_hash(file_path).lower() == file_hash.lower():
        return True
    Path(file_path).unlink()
    return None
