class SpeedUnit:
    BIT = 1
    KILOBIT = 1000
    MEGABIT = 1000 * 1000
    GIGABIT = 1000 * 1000 * 1000
    KIBIBIT = 1024
    MEBIBIT = 1024 * 1024
    GIBIBIT = 1024 * 1024 * 1024
    BYTE = 8
    KILOBYTE = 1000 * BYTE
    MEGABYTE = 1000 * KILOBYTE
    GIGABYTE = 1000 * MEGABYTE
    KIBIBYTE = 1024 * BYTE
    MEBIBYTE = 1024 * KIBIBYTE
    GIBIBYTE = 1024 * MEBIBYTE

    def __init__(self, bits_per_second):
        if bits_per_second < 0:
            raise ValueError("Speed cannot be negative")
        self.bits_per_second = bits_per_second

    @classmethod
    def from_string(cls, speed_str):
        units = {
            "bps": cls.BIT,
            "Kbps": cls.KILOBIT,
            "Mbps": cls.MEGABIT,
            "Gbps": cls.GIGABIT,
            "Kibps": cls.KIBIBIT,
            "Mibps": cls.MEBIBIT,
            "Gibps": cls.GIBIBIT,
            "Bps": cls.BYTE,
            "KBps": cls.KILOBYTE,
            "MBps": cls.MEGABYTE,
            "GBps": cls.GIGABYTE,
            "KiBps": cls.KIBIBYTE,
            "MiBps": cls.MEBIBYTE,
            "GiBps": cls.GIBIBYTE,
        }
        value, unit = speed_str.split()
        return cls(float(value) * units[unit])

    @classmethod
    def from_bits(cls, bits):
        return cls(bits)

    @classmethod
    def from_kilobits(cls, kilobits):
        return cls(kilobits * cls.KILOBIT)

    @classmethod
    def from_megabits(cls, megabits):
        return cls(megabits * cls.MEGABIT)

    @classmethod
    def from_gigabits(cls, gigabits):
        return cls(gigabits * cls.GIGABIT)

    @classmethod
    def from_bytes(cls, bytes):
        return cls(bytes * cls.BYTE)

    @classmethod
    def from_kilobytes(cls, kilobytes):
        return cls(kilobytes * cls.KILOBYTE)

    @classmethod
    def from_megabytes(cls, megabytes):
        return cls(megabytes * cls.MEGABYTE)

    @classmethod
    def from_gigabytes(cls, gigabytes):
        return cls(gigabytes * cls.GIGABYTE)

    def to_kilobits(self, round_decimals=2):
        return round(self.bits_per_second / self.KILOBIT, round_decimals)

    def to_megabits(self, round_decimals=2):
        return round(self.bits_per_second / self.MEGABIT, round_decimals)

    def to_gigabits(self, round_decimals=2):
        return round(self.bits_per_second / self.GIGABIT, round_decimals)

    def to_kibibits(self, round_decimals=2):
        return round(self.bits_per_second / self.KIBIBIT, round_decimals)

    def to_mebibits(self, round_decimals=2):
        return round(self.bits_per_second / self.MEBIBIT, round_decimals)

    def to_gibibits(self, round_decimals=2):
        return round(self.bits_per_second / self.GIBIBIT, round_decimals)

    def to_kilobytes(self, round_decimals=2):
        return round(self.bits_per_second / self.KILOBYTE, round_decimals)

    def to_megabytes(self, round_decimals=2):
        return round(self.bits_per_second / self.MEGABYTE, round_decimals)

    def to_gigabytes(self, round_decimals=2):
        return round(self.bits_per_second / self.GIGABYTE, round_decimals)

    def to_kibibytes(self, round_decimals=2):
        return round(self.bits_per_second / self.KIBIBYTE, round_decimals)

    def to_mebibytes(self, round_decimals=2):
        return round(self.bits_per_second / self.MEBIBYTE, round_decimals)

    def to_gibibytes(self, round_decimals=2):
        return round(self.bits_per_second / self.GIBIBYTE, round_decimals)

    def to_human_readable(self):
        if self.bits_per_second < self.KILOBIT:
            return f"{self.bits_per_second} bps"
        elif self.bits_per_second < self.MEGABIT:
            return f"{self.to_kilobits()} Kbps"
        elif self.bits_per_second < self.GIGABIT:
            return f"{self.to_megabits()} Mbps"
        return f"{self.to_gigabits()} Gbps"

    def to_bits(self):
        return self.bits_per_second

    def __int__(self):
        return int(self.bits_per_second)

    def __float__(self):
        return float(self.bits_per_second)

    def __repr__(self):
        return f"SpeedUnit({self.bits_per_second} bps)"

    def __str__(self):
        return str(int(self.bits_per_second))

    def __add__(self, other):
        if isinstance(other, SpeedUnit):
            return SpeedUnit(self.bits_per_second + other.bits_per_second)
        elif isinstance(other, (int, float)):
            return SpeedUnit(self.bits_per_second + other)
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, SpeedUnit):
            return SpeedUnit(self.bits_per_second - other.bits_per_second)
        elif isinstance(other, (int, float)):
            return SpeedUnit(self.bits_per_second - other)
        return NotImplemented

    def __rsub__(self, other):
        if isinstance(other, (int, float)):
            return SpeedUnit(other - self.bits_per_second)
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return SpeedUnit(self.bits_per_second * other)
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return SpeedUnit(self.bits_per_second / other)
        return NotImplemented

    def __rtruediv__(self, other):
        if isinstance(other, (int, float)):
            return SpeedUnit(other / self.bits_per_second)
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, SpeedUnit):
            return self.bits_per_second == other.bits_per_second
        elif isinstance(other, (int, float)):
            return self.bits_per_second == other
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, SpeedUnit):
            return self.bits_per_second < other.bits_per_second
        elif isinstance(other, (int, float)):
            return self.bits_per_second < other
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, SpeedUnit):
            return self.bits_per_second <= other.bits_per_second
        elif isinstance(other, (int, float)):
            return self.bits_per_second <= other
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, SpeedUnit):
            return self.bits_per_second > other.bits_per_second
        elif isinstance(other, (int, float)):
            return self.bits_per_second > other
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, SpeedUnit):
            return self.bits_per_second >= other.bits_per_second
        elif isinstance(other, (int, float)):
            return self.bits_per_second >= other
        return NotImplemented

    def __round__(self, ndigits=None):
        return SpeedUnit(round(self.bits_per_second, ndigits))
