"""
Downloadable File Model - Represents files to be downloaded for installation.
"""

import random
import string
from dataclasses import dataclass, field
from pathlib import Path

from .spin import Spin


@dataclass
class DownloadableFile:
    """Represents a file that needs to be downloaded for installation."""

    file_hint: str  # Purpose: "installer_iso", "live_img_iso", etc.
    download_url: str
    destination_dir: Path
    expected_hash: str
    size_bytes: int
    _file_name: str | None = field(default=None)

    @property
    def file_name(self) -> str:
        """Get the filename, computing it if not set."""
        if self._file_name is not None:
            return self._file_name

        # Compute from URL
        # Remove query parameters first
        url_without_query = self.download_url.split("?")[0]
        url_part = url_without_query.split("/")[-1]
        if url_part:
            self._file_name = self._sanitize_filename(url_part)
        else:
            self._file_name = self._generate_random_filename()

        return self._file_name

    @property
    def full_path(self) -> Path:
        """Get the full path where this file will be saved."""
        return self.destination_dir / self.file_name

    def set_file_name(self, name: str) -> None:
        """Set a custom filename."""
        self._file_name = self._sanitize_filename(name)

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for Windows compatibility by removing forbidden characters.

        Forbidden characters: < > : " | ? * \
        Also removes control characters and trims whitespace.
        """
        if not filename:
            return DownloadableFile._generate_random_filename()

        # Remove control characters (0-31)
        filename = "".join(char for char in filename if ord(char) >= 32)

        # Windows forbidden characters
        forbidden_chars = '<>:"|?*\\'

        # Remove forbidden characters
        for char in forbidden_chars:
            filename = filename.replace(char, "")

        # Trim whitespace
        filename = filename.strip()

        # Ensure not empty after sanitization
        if not filename:
            return DownloadableFile._generate_random_filename()

        return filename

    @staticmethod
    def _generate_random_filename() -> str:
        """Generate a random filename with 5 characters and numbers."""
        # Characters to choose from: letters and digits
        chars = string.ascii_letters + string.digits

        # Generate 5 random characters
        random_part = "".join(random.choice(chars) for _ in range(5))

        return f"file_{random_part}"

    @classmethod
    def from_spin(
        cls,
        spin: Spin,
        file_hint: str,
        destination_dir: Path,
        file_name: str | None = None,
    ) -> "DownloadableFile":
        """Create a DownloadableFile from a Spin object."""
        return cls(
            file_hint=file_hint,
            download_url=spin.dl_link,
            destination_dir=destination_dir,
            expected_hash=spin.hash256,
            size_bytes=spin.size,
            _file_name=file_name,  # If provided, use it; otherwise compute lazily
        )
