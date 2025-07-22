class DataUnit:
    BYTE = 1
    KILOBYTE = 1000
    MEGABYTE = 1000 * KILOBYTE
    GIGABYTE = 1000 * MEGABYTE
    KIBIBYTE = 1024
    MEBIBYTE = 1024 * KIBIBYTE
    GIBIBYTE = 1024 * MEBIBYTE

    def __init__(self, bytes_value):
        if bytes_value < 0:
            raise ValueError("Data size cannot be negative")
        self.bytes_value = bytes_value

    @classmethod
    def from_string(cls, data_str):
        units = {
            "B": cls.BYTE,
            "KB": cls.KILOBYTE,
            "MB": cls.MEGABYTE,
            "GB": cls.GIGABYTE,
            "KiB": cls.KIBIBYTE,
            "MiB": cls.MEBIBYTE,
            "GiB": cls.GIBIBYTE,
        }
        value, unit = data_str.split()
        return cls(float(value) * units[unit])

    @classmethod
    def from_bytes(cls, bytes):
        return cls(bytes)

    @classmethod
    def from_kilobytes(cls, kilobytes):
        return cls(kilobytes * cls.KILOBYTE)

    @classmethod
    def from_megabytes(cls, megabytes):
        return cls(megabytes * cls.MEGABYTE)

    @classmethod
    def from_gigabytes(cls, gigabytes):
        return cls(gigabytes * cls.GIGABYTE)

    @classmethod
    def from_kibibytes(cls, kibibytes):
        return cls(kibibytes * cls.KIBIBYTE)

    @classmethod
    def from_mebibytes(cls, mebibytes):
        return cls(mebibytes * cls.MEBIBYTE)

    @classmethod
    def from_gibibytes(cls, gibibytes):
        return cls(gibibytes * cls.GIBIBYTE)

    def to_kilobytes(self, round_decimals=2):
        return round(self.bytes_value / self.KILOBYTE, round_decimals)

    def to_megabytes(self, round_decimals=2):
        return round(self.bytes_value / self.MEGABYTE, round_decimals)

    def to_gigabytes(self, round_decimals=2):
        return round(self.bytes_value / self.GIGABYTE, round_decimals)

    def to_kibibytes(self, round_decimals=2):
        return round(self.bytes_value / self.KIBIBYTE, round_decimals)

    def to_mebibytes(self, round_decimals=2):
        return round(self.bytes_value / self.MEBIBYTE, round_decimals)

    def to_gibibytes(self, round_decimals=2):
        return round(self.bytes_value / self.GIBIBYTE, round_decimals)

    def to_human_readable(self):
        if self.bytes_value < self.KILOBYTE:
            return f"{self.bytes_value} B"
        elif self.bytes_value < self.MEGABYTE:
            return f"{self.to_kilobytes()} KB"
        elif self.bytes_value < self.GIGABYTE:
            return f"{self.to_megabytes()} MB"
        return f"{self.to_gigabytes()} GB"

    def to_bytes(self):
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
        elif isinstance(other, (int, float)):
            return DataUnit(self.bytes_value + other)
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, DataUnit):
            return DataUnit(self.bytes_value - other.bytes_value)
        elif isinstance(other, (int, float)):
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
        elif isinstance(other, (int, float)):
            return self.bytes_value == other
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, DataUnit):
            return self.bytes_value < other.bytes_value
        elif isinstance(other, (int, float)):
            return self.bytes_value < other
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, DataUnit):
            return self.bytes_value <= other.bytes_value
        elif isinstance(other, (int, float)):
            return self.bytes_value <= other
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, DataUnit):
            return self.bytes_value > other.bytes_value
        elif isinstance(other, (int, float)):
            return self.bytes_value > other
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, DataUnit):
            return self.bytes_value >= other.bytes_value
        elif isinstance(other, (int, float)):
            return self.bytes_value >= other
        return NotImplemented

    def __round__(self, ndigits=None):
        return DataUnit(round(self.bytes_value, ndigits))
