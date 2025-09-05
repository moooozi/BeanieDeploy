import pendulum

class TimeLeft:
    """
    Replacement for the custom TimeLeft class using pendulum.Duration.
    Supports arithmetic and human-readable formatting.
    """
    def __init__(self, seconds):
        if seconds < 0:
            raise ValueError("Time cannot be negative")
        self.duration = pendulum.duration(seconds=seconds)

    @classmethod
    def from_seconds(cls, seconds):
        return cls(seconds)

    @classmethod
    def from_minutes(cls, minutes):
        return cls(minutes * 60)

    @classmethod
    def from_hours(cls, hours):
        return cls(hours * 3600)

    @classmethod
    def from_days(cls, days):
        return cls(days * 86400)

    def to_human_readable(self, locale="en"):
        # pendulum's in_words() supports locale
        return self.duration.in_words(locale=locale)

    def __int__(self):
        return int(self.duration.total_seconds())

    def __float__(self):
        return float(self.duration.total_seconds())

    def __repr__(self):
        return f"TimeLeft({self.duration.total_seconds()} seconds)"

    def __str__(self):
        return self.to_human_readable()

    def __add__(self, other):
        if isinstance(other, TimeLeft):
            return TimeLeft(self.duration.total_seconds() + other.duration.total_seconds())
        elif isinstance(other, (int, float)):
            return TimeLeft(self.duration.total_seconds() + other)
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, TimeLeft):
            return TimeLeft(self.duration.total_seconds() - other.duration.total_seconds())
        elif isinstance(other, (int, float)):
            return TimeLeft(self.duration.total_seconds() - other)
        return NotImplemented

    def __rsub__(self, other):
        if isinstance(other, (int, float)):
            return TimeLeft(other - self.duration.total_seconds())
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return TimeLeft(self.duration.total_seconds() * other)
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return TimeLeft(self.duration.total_seconds() / other)
        return NotImplemented

    def __rtruediv__(self, other):
        if isinstance(other, (int, float)):
            return TimeLeft(other / self.duration.total_seconds())
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, TimeLeft):
            return self.duration.total_seconds() == other.duration.total_seconds()
        elif isinstance(other, (int, float)):
            return self.duration.total_seconds() == other
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, TimeLeft):
            return self.duration.total_seconds() < other.duration.total_seconds()
        elif isinstance(other, (int, float)):
            return self.duration.total_seconds() < other
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, TimeLeft):
            return self.duration.total_seconds() <= other.duration.total_seconds()
        elif isinstance(other, (int, float)):
            return self.duration.total_seconds() <= other
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, TimeLeft):
            return self.duration.total_seconds() > other.duration.total_seconds()
        elif isinstance(other, (int, float)):
            return self.duration.total_seconds() > other
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, TimeLeft):
            return self.duration.total_seconds() >= other.duration.total_seconds()
        elif isinstance(other, (int, float)):
            return self.duration.total_seconds() >= other
        return NotImplemented

    def __round__(self, ndigits=None):
        return TimeLeft(round(self.duration.total_seconds(), ndigits))
