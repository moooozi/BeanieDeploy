import json
from pathlib import Path

from models.types import SpinDictList


def get_dummy_spin_data() -> SpinDictList:
    """Load dummy spin data from dummy.json file."""
    dummy_json_path = Path(__file__).parent.parent / "dummy.json"
    with dummy_json_path.open() as f:
        return json.load(f)


DUMMY_IP_LOCALE = {
    "time_zone": "Europe/Berlin",
    "country_code3": "DEU",
    "country_code": "DE",
    "country_name": "Germany",
}
