"""
Services package containing business logic and system operations.

This package contains service modules for:
- disk: Disk and partition management
- system: System-level operations (admin, registry, etc.)
- download: File downloading with progress tracking
- installation_service: Main installation orchestration
- network: Wi-Fi profile management
- file: File operations and validation
"""

# Export commonly used service functions
from .system import is_admin
from .privilege_manager import elevated

__all__ = [
    'is_admin',
    'elevated',
]
