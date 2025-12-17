import json
from pathlib import Path

from models.types import IPLocaleInfo, SpinDictList


def get_fallback_offline_spin_data() -> SpinDictList:
    """Load default offline spin data from dummy.json file."""
    default_spins_json_path = Path(__file__).parent / "resources" / "default_spins.json"
    with default_spins_json_path.open() as f:
        return json.load(f)


DEFAULT_IP_LOCALE = IPLocaleInfo(
    time_zone="Europe/Berlin",
    country_code="DE",
)
