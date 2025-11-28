"""
Models package containing data classes and business logic models.

This package contains type-safe data models for:
- Installation context and options
- Language and localization
- Page management and navigation
- Partition and system information
- Distribution (spin) definitions
"""

# Export main models for convenient imports
# Note: Page is not imported here to avoid circular imports with config.settings
from .installation_context import InstallationContext, InstallationStage
from .direction import Direction
from .data_units import DataUnit
from .spin import Spin

__all__ = [
    'InstallationContext',
    'InstallationStage',
    'Direction',
    'DataUnit',
    'Spin',
]