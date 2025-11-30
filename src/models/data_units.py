"""
Modern data unit wrapper using humanize library.
Provides a thin compatibility layer over humanize for byte size handling.
"""

import humanize


class DataUnit:
    """
    Modern byte size wrapper using humanize library.
    All formatting is delegated to humanize - zero manual implementation.
    """

    # Constants for backward compatibility only
    BYTE = 1
    KILOBYTE = 1000
    MEGABYTE = 1_000_000
    GIGABYTE = 1_000_000_000
    KIBIBYTE = 1024
    MEBIBYTE = 1_048_576
    GIBIBYTE = 1_073_741_824

    def __init__(self, bytes_value):
        """Initialize with byte value."""
        if bytes_value < 0:
            msg = "Data size cannot be negative"
            raise ValueError(msg)
        self.bytes_value = int(bytes_value)

    @classmethod
    def from_string(cls, data_str):
        """Parse humanize-generated string back to bytes (basic implementation)."""
        # This is for parsing ISO-like formats: "1.5 GB", "500 MB", etc.
        parts = data_str.strip().split()
        if not parts:
            msg = f"Invalid data string: '{data_str}'"
            raise ValueError(msg)

        if len(parts) == 1:
            # Just a number, assume bytes
            return cls(float(parts[0]))

        value = float(parts[0])
        unit = parts[1].upper()

        # Mapping for common units
        multipliers = {
            "B": 1,
            "BYTES": 1,
            "BYTE": 1,
            "KB": 1000,
            "KIB": 1024,
            "MB": 1_000_000,
            "MIB": 1_048_576,
            "GB": 1_000_000_000,
            "GIB": 1_073_741_824,
            "TB": 1_000_000_000_000,
            "TIB": 1_099_511_627_776,
        }

        multiplier = multipliers.get(unit)
        if multiplier is None:
            msg = f"Unknown unit: '{unit}'"
            raise ValueError(msg)

        return cls(int(value * multiplier))

    @classmethod
    def from_bytes(cls, bytes_val):
        """Create from byte value."""
        return cls(bytes_val)

    @classmethod
    def from_kilobytes(cls, kb):
        """Create from kilobytes."""
        return cls(int(kb * 1000))

    @classmethod
    def from_megabytes(cls, mb):
        """Create from megabytes."""
        return cls(int(mb * 1_000_000))

    @classmethod
    def from_gigabytes(cls, gb):
        """Create from gigabytes."""
        return cls(int(gb * 1_000_000_000))

    @classmethod
    def from_kibibytes(cls, kib):
        """Create from kibibytes."""
        return cls(int(kib * 1024))

    @classmethod
    def from_mebibytes(cls, mib):
        """Create from mebibytes."""
        return cls(int(mib * 1_048_576))

    @classmethod
    def from_gibibytes(cls, gib):
        """Create from gibibytes."""
        return cls(int(gib * 1_073_741_824))

    def to_kilobytes(self, round_decimals=2):
        """Convert to kilobytes (1000-based)."""
        return round(self.bytes_value / 1000, round_decimals)

    def to_megabytes(self, round_decimals=2):
        """Convert to megabytes (1000-based)."""
        return round(self.bytes_value / 1_000_000, round_decimals)

    def to_gigabytes(self, round_decimals=2):
        """Convert to gigabytes (1000-based)."""
        return round(self.bytes_value / 1_000_000_000, round_decimals)

    def to_kibibytes(self, round_decimals=2):
        """Convert to kibibytes (1024-based)."""
        return round(self.bytes_value / 1024, round_decimals)

    def to_mebibytes(self, round_decimals=2):
        """Convert to mebibytes (1024-based)."""
        return round(self.bytes_value / 1_048_576, round_decimals)

    def to_gibibytes(self, round_decimals=2):
        """Convert to gibibytes (1024-based)."""
        return round(self.bytes_value / 1_073_741_824, round_decimals)

    def to_human_readable(self, binary=False):
        """
        Format using humanize library.

        Args:
            binary: Use binary units (KiB, MiB) instead of decimal (KB, MB)

        Returns:
            Human-readable string via humanize
        """
        return humanize.naturalsize(self.bytes_value, binary=binary)

    def to_bytes(self):
        """Get raw byte value."""
        return self.bytes_value

    @property
    def bytes(self):
        """Property for accessing bytes value."""
        return self.bytes_value

    @property
    def kilobytes(self):
        """Property for accessing kilobytes value."""
        return self.to_kilobytes()

    @property
    def megabytes(self):
        """Property for accessing megabytes value."""
        return self.to_megabytes()

    @property
    def gigabytes(self):
        """Property for accessing gigabytes value."""
        return self.to_gigabytes()

    def __int__(self):
        return int(self.bytes_value)

    def __float__(self):
        return float(self.bytes_value)

    def __repr__(self):
        return f"DataUnit({self.bytes_value} bytes)"

    def __str__(self):
        return str(int(self.bytes_value))

    def __add__(self, other):
        if isinstance(other, DataUnit):
            return DataUnit(self.bytes_value + other.bytes_value)
        if isinstance(other, (int, float)):
            return DataUnit(self.bytes_value + other)
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, DataUnit):
            return DataUnit(self.bytes_value - other.bytes_value)
        if isinstance(other, (int, float)):
            return DataUnit(self.bytes_value - other)
        return NotImplemented

    def __rsub__(self, other):
        if isinstance(other, (int, float)):
            return DataUnit(other - self.bytes_value)
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return DataUnit(self.bytes_value * other)
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return DataUnit(self.bytes_value / other)
        return NotImplemented

    def __rtruediv__(self, other):
        if isinstance(other, (int, float)):
            return DataUnit(other / self.bytes_value)
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, DataUnit):
            return self.bytes_value == other.bytes_value
        if isinstance(other, (int, float)):
            return self.bytes_value == other
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, DataUnit):
            return self.bytes_value < other.bytes_value
        if isinstance(other, (int, float)):
            return self.bytes_value < other
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, DataUnit):
            return self.bytes_value <= other.bytes_value
        if isinstance(other, (int, float)):
            return self.bytes_value <= other
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, DataUnit):
            return self.bytes_value > other.bytes_value
        if isinstance(other, (int, float)):
            return self.bytes_value > other
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, DataUnit):
            return self.bytes_value >= other.bytes_value
        if isinstance(other, (int, float)):
            return self.bytes_value >= other
        return NotImplemented

    def __round__(self, ndigits=None):
        return DataUnit(round(self.bytes_value, ndigits))
