"""
Download service for handling file downloads and network operations.
Uses a custom Rust-based downloader for better performance and native SSL support.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requers


@dataclass
class DownloadProgress:
    """Progress information for downloads."""

    filename: str
    downloaded_bytes: int
    total_bytes: int
    speed_bytes_per_sec: float
    eta_seconds: float
    percentage: float


def download_file(
    url: str,
    destination: Path,
    filename: str | None = None,
    expected_hash: str | None = None,
    progress_callback: Callable[[DownloadProgress], None] | None = None,
) -> Path:
    """
    Download a file with progress tracking and verification.

    Args:
        url: URL to download from
        destination: Directory to save to
        filename: Optional custom filename
        expected_hash: Optional SHA256 hash for verification
        progress_callback: Optional callback for progress updates

    Returns:
        Path to downloaded file

    Raises:
        NetworkError: If download fails
    """
    if not filename:
        filename = url.split("/")[-1]

    filepath = destination / filename
    destination.mkdir(parents=True, exist_ok=True)

    logging.info(f"Starting download: {url} -> {filepath}")

    try:
        # Use Rust downloader - now returns a handle for progress monitoring
        download_handle = requers.download_file(
            url,
            str(filepath),
            True,  # resume
        )

        # Monitor progress
        while not download_handle.is_finished():
            if progress_callback:
                progress_info = download_handle.get_progress()
                downloaded = progress_info.get("downloaded", 0)
                total = progress_info.get("total", 0)
                speed = progress_info.get("speed", 0.0)
                eta = progress_info.get("eta", 0.0)

                percentage = (downloaded / total) * 100 if total and total > 0 else 0.0

                progress = DownloadProgress(
                    filename=filename,
                    downloaded_bytes=downloaded,
                    total_bytes=total,
                    speed_bytes_per_sec=speed,
                    eta_seconds=eta,
                    percentage=percentage,
                )

                progress_callback(progress)

            # Small delay to avoid busy waiting
            import time

            time.sleep(0.2)

        # Check if download was successful
        if not download_handle.is_successful():
            filepath.unlink()
            msg = f"Download failed for {filename}"
            raise RuntimeError(msg)

        # Verify hash if provided
        if expected_hash and not _verify_file_hash(filepath, expected_hash):
            filepath.unlink()  # Remove corrupted file
            msg = f"Hash verification failed for {filename}"
            raise ValueError(msg)
        logging.info(
            f"Successfully downloaded {filename} ({filepath.stat().st_size} bytes)"
        )
        return filepath

    except Exception as e:
        # Clean up partial download
        if filepath.exists():
            filepath.unlink()
        msg = f"Failed to download {url}: {e}"
        raise RuntimeError(msg) from e


def _verify_file_hash(filepath: Path, expected_hash: str) -> bool:
    """Verify file SHA256 hash."""
    try:
        calculated_hash = requers.hash_file(str(filepath)).lower()
        expected_hash = expected_hash.lower()

        logging.debug(
            f"Hash verification: calculated={calculated_hash}, expected={expected_hash}"
        )
        return calculated_hash == expected_hash

    except Exception as e:
        logging.error(f"Hash verification failed: {e}")
        return False


def fetch_json(url: str) -> Any:
    """
    Fetch and parse JSON from a URL using the Rust downloader.

    Args:
        url: URL to fetch JSON from

    Returns:
        Parsed JSON data
    """
    try:
        logging.info(f"Fetching JSON from: {url}")
        headers = {"User-Agent": "BeanieDeploy/1.0"}
        response = requers.get(url, headers=headers, timeout=30.0)
        response.raise_for_status()

        data = response.json()
        logging.debug(f"Successfully fetched JSON data from {url}")
        return data
    except Exception as e:
        msg = f"Failed to fetch JSON from {url}"
        raise RuntimeError(msg) from e
