from dataclasses import dataclass
from typing import Any

SpinDictList = list[dict[str, Any]]


@dataclass(frozen=True)
class IPLocaleInfo:
    """IP-based locale information from Fedora's GeoIP service."""

    country_code: str
    time_zone: str
    # ip: str
    # city: str
    # region_name: str
    # region: str
    # postal_code: str
    # country_name: str
    # latitude: float
    # longitude: float
    # metro_code: int | None = None
    # dma_code: int | None = None
    # country_code3: str = ""
