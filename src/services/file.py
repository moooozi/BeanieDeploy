"""
File management services.
Handles file operations, hashing, copying, etc.
"""

import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional
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
    with open(file_path, "rb") as f:
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
        os.chmod(filepath, 0o444)  # Read-only
    else:
        os.chmod(filepath, 0o666)  # Read-write


def copy_files(source: str, destination: str) -> None:
    """
    Copy files from source to destination, creating directories as needed.

    Args:
        source: Source directory path
        destination: Destination directory path
    """
    shutil.copytree(source, destination, dirs_exist_ok=True)


def rmdir(location: str) -> Optional[None]:
    """
    Remove a directory and all its contents.

    Args:
        location: Directory path to remove

    Returns:
        None if successful, or result of shutil.rmtree
    """
    if os.path.isdir(location):
        return shutil.rmtree(location)
    return None


def mkdir(location: Path) -> Optional[None]:
    """
    Create a directory if it doesn't exist.

    Args:
        location: Directory path to create

    Returns:
        None if directory exists or was created successfully
    """
    if not location.exists():
        return location.mkdir(parents=True, exist_ok=True)
    return None


def get_file_name_from_url(url: str) -> str:
    """
    Extract filename from a URL.

    Args:
        url: URL to extract filename from

    Returns:
        Filename from the URL
    """
    parsed_url = urlparse(url)
    return os.path.basename(parsed_url.path)


def find_file_by_name(name: str, lookup_dir: str) -> Optional[str]:
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
            return os.path.join(root, name)
    return None


def check_valid_existing_file(file_path: str, file_hash: str) -> Optional[bool]:
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
    if not os.path.isfile(file_path):
        return False

    if get_sha256_hash(file_path).lower() == file_hash.lower():
        return True
    else:
        os.remove(file_path)
        return None
