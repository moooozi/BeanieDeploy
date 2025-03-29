class TimeLeft:
    def __init__(self, seconds, translation):
        if seconds < 0:
            raise ValueError("Time cannot be negative")
        self.seconds = seconds
        self.translation = translation

    @classmethod
    def from_seconds(cls, seconds, translation):
        return cls(seconds, translation)

    @classmethod
    def from_minutes(cls, minutes, translation):
        return cls(minutes * 60, translation)

    @classmethod
    def from_hours(cls, hours, translation):
        return cls(hours * 3600, translation)

    @classmethod
    def from_days(cls, days, translation):
        return cls(days * 86400, translation)

    def to_human_readable(self):
        seconds = self.seconds
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        parts = []
        if days > 0:
            parts.append(
                f"{days} {self.translation.day_plural if days > 1 else self.translation.day_singular}"
            )
        if hours > 0:
            parts.append(
                f"{hours} {self.translation.hour_plural if hours > 1 else self.translation.hour_singular}"
            )
        if minutes > 0:
            parts.append(
                f"{minutes} {self.translation.minute_plural if minutes > 1 else self.translation.minute_singular}"
            )
        if seconds > 0 or not parts:
            parts.append(
                f"{seconds} {self.translation.second_plural if seconds > 1 else self.translation.second_singular}"
            )

        return " ".join(parts) + f" {self.translation.left}"

    def __int__(self):
        return int(self.seconds)

    def __float__(self):
        return float(self.seconds)

    def __repr__(self):
        return f"TimeLeft({self.seconds} seconds)"

    def __str__(self):
        return self.to_human_readable()

    def __add__(self, other):
        if isinstance(other, TimeLeft):
            return TimeLeft(self.seconds + other.seconds, self.translation)
        elif isinstance(other, (int, float)):
            return TimeLeft(self.seconds + other, self.translation)
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, TimeLeft):
            return TimeLeft(self.seconds - other.seconds, self.translation)
        elif isinstance(other, (int, float)):
            return TimeLeft(self.seconds - other, self.translation)
        return NotImplemented

    def __rsub__(self, other):
        if isinstance(other, (int, float)):
            return TimeLeft(other - self.seconds, self.translation)
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return TimeLeft(self.seconds * other, self.translation)
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return TimeLeft(self.seconds / other, self.translation)
        return NotImplemented

    def __rtruediv__(self, other):
        if isinstance(other, (int, float)):
            return TimeLeft(other / self.seconds, self.translation)
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, TimeLeft):
            return self.seconds == other.seconds
        elif isinstance(other, (int, float)):
            return self.seconds == other
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, TimeLeft):
            return self.seconds < other.seconds
        elif isinstance(other, (int, float)):
            return self.seconds < other
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, TimeLeft):
            return self.seconds <= other.seconds
        elif isinstance(other, (int, float)):
            return self.seconds <= other
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, TimeLeft):
            return self.seconds > other.seconds
        elif isinstance(other, (int, float)):
            return self.seconds > other
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, TimeLeft):
            return self.seconds >= other.seconds
        elif isinstance(other, (int, float)):
            return self.seconds >= other
        return NotImplemented

    def __round__(self, ndigits=None):
        return TimeLeft(round(self.seconds, ndigits), self.translation)
