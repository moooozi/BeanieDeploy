import json
from pathlib import Path

from models.types import IPLocaleInfo, SpinDictList


def get_dummy_spin_data() -> SpinDictList:
    """Load dummy spin data from dummy.json file."""
    dummy_json_path = Path(__file__).parent.parent / "dummy.json"
    with dummy_json_path.open() as f:
        return json.load(f)


DUMMY_IP_LOCALE = IPLocaleInfo(
    time_zone="Europe/Berlin",
    country_code="DE",
)
