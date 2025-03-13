class DataUnit:
    BYTE = 1
    KILOBYTE = 1024
    MEGABYTE = 1024 * 1024
    GIGABYTE = 1024 * 1024 * 1024

    def __init__(self, bytes_value):
        self.bytes_value = bytes_value

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

    def to_kilobytes(self, round_decimals=2):
        return round(self.bytes_value / self.KILOBYTE, round_decimals)

    def to_megabytes(self, round_decimals=2):
        return round(self.bytes_value / self.MEGABYTE, round_decimals)

    def to_gigabytes(self, round_decimals=2):
        return round(self.bytes_value / self.GIGABYTE, round_decimals)

    def to_bytes(self):
        return self.bytes_value

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
