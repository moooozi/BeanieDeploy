"""
Colored logging for BeanieDeploy.
"""

import logging
from pathlib import Path

import coloredlogs

# Automatically install colored logging for all standard logging calls
coloredlogs.install(
    level="DEBUG",  # Show all levels including debug
    fmt="%(levelname)s | %(message)s",
    level_styles={
        "debug": {"color": "cyan"},
        "info": {"color": "green"},
        "warning": {"color": "yellow"},
        "error": {"color": "red"},
        "critical": {"color": "magenta", "bold": True},
    },
    field_styles={
        "levelname": {"bold": True},
    },
)


def _setup_file_logging(log_file: Path):
    """Set up file logging with detailed format."""
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | %(name)s | %(levelname)s | "
            "%(filename)s:%(lineno)d | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logging.getLogger().addHandler(file_handler)


def setup_file_logging(log_file: Path):
    """Set up file logging. Call this once at startup."""
    _setup_file_logging(log_file)
