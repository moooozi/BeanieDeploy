"""
Download service for handling file downloads and network operations.
Uses requests library for better reliability and features.
"""

import hashlib
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from config.settings import ConfigManager


@dataclass
class DownloadProgress:
    """Progress information for downloads."""

    filename: str
    downloaded_bytes: int
    total_bytes: int
    speed_bytes_per_sec: float
    eta_seconds: float
    percentage: float


class DownloadService:
    """Service for handling downloads and network operations."""

    def __init__(self, config: ConfigManager):
        self.config = config

    def download_file(
        self,
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
            start_time = time.time()
            last_progress_time = start_time

            # Start the download with requests
            headers = {"User-Agent": "BeanieDeploy/1.0"}
            with requests.get(
                url, headers=headers, stream=True, timeout=30
            ) as response:
                response.raise_for_status()

                total_size = int(response.headers.get("Content-Length", 0))
                downloaded_size = 0

                with filepath.open("wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:  # Filter out keep-alive chunks
                            f.write(chunk)
                            downloaded_size += len(chunk)

                            # Update progress
                            current_time = time.time()
                            if (
                                progress_callback
                                and (current_time - last_progress_time) > 0.5
                            ):  # Update every 0.5s
                                elapsed = current_time - start_time
                                speed = downloaded_size / elapsed if elapsed > 0 else 0
                                eta = (
                                    (total_size - downloaded_size) / speed
                                    if speed > 0
                                    else 0
                                )
                                percentage = (
                                    (downloaded_size / total_size) * 100
                                    if total_size > 0
                                    else 0
                                )

                                progress = DownloadProgress(
                                    filename=filename,
                                    downloaded_bytes=downloaded_size,
                                    total_bytes=total_size,
                                    speed_bytes_per_sec=speed,
                                    eta_seconds=eta,
                                    percentage=percentage,
                                )

                                progress_callback(progress)
                                last_progress_time = current_time

            # Verify hash if provided
            if expected_hash and not self._verify_file_hash(filepath, expected_hash):
                filepath.unlink()  # Remove corrupted file
                msg = f"Hash verification failed for {filename}"
                raise ValueError(msg)

            logging.info(
                f"Successfully downloaded {filename} ({downloaded_size} bytes)"
            )
            return filepath

        except Exception as e:
            # Clean up partial download
            if filepath.exists():
                filepath.unlink()
            msg = f"Failed to download {url}: {e}"
            raise RuntimeError(msg) from e

    def _verify_file_hash(self, filepath: Path, expected_hash: str) -> bool:
        """Verify file SHA256 hash."""
        try:
            sha256_hash = hashlib.sha256()
            with filepath.open("rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)

            calculated_hash = sha256_hash.hexdigest().lower()
            expected_hash = expected_hash.lower()

            logging.debug(
                f"Hash verification: calculated={calculated_hash}, expected={expected_hash}"
            )
            return calculated_hash == expected_hash

        except Exception as e:
            logging.error(f"Hash verification failed: {e}")
            return False

    def fetch_json(self, url: str) -> dict[str, Any]:
        """
        Fetch and parse JSON from a URL using requests.

        Args:
            url: URL to fetch JSON from

        Returns:
            Parsed JSON data
        """
        try:
            logging.info(f"Fetching JSON from: {url}")
            headers = {"User-Agent": "BeanieDeploy/1.0"}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            logging.debug(f"Successfully fetched JSON data from {url}")
            return data
        except Exception as e:
            msg = f"Failed to fetch JSON from {url}"
            raise RuntimeError(msg) from e

    def fetch_available_spins(self) -> dict[str, Any]:
        """Fetch available Fedora spins from the remote API."""
        logging.info("Fetching available Fedora spins")
        return self.fetch_json(self.config.urls.available_spins_list)

    def fetch_geo_location(self) -> dict[str, Any]:
        """Fetch user's geo location for mirror selection."""
        logging.info("Fetching geo location for mirror selection")
        try:
            return self.fetch_json(self.config.urls.fedora_geo_ip)
        except Exception as e:
            logging.warning(f"Failed to fetch geo location: {e}")
            return {}  # Return empty dict as fallback
