"""
Spin management services.
Handles parsing and filtering of Fedora spins/variants.
"""
from typing import List, Tuple, Optional
from config.settings import get_config
from models.spin import Spin


def parse_spins(spins_list: List[dict]) -> Tuple[Optional[int], List[Spin]]:
    """
    Parse and filter spins list from JSON data.
    
    Args:
        spins_list: Raw spins data from JSON
        
    Returns:
        Tuple of (live_os_base_index, filtered_spins_list)
    """
    accepted_spins_list = []
    live_os_base_index = None
    config = get_config()

    for index, current_spin in enumerate(spins_list):
        spin_keys = list(current_spin.keys())
        
        # Validate required fields
        required_fields = ("name", "size", "hash256", "dl_link")
        if not all(field in spin_keys for field in required_fields):
            continue

        # Process download URLs
        current_spin["dl_link"] = config.urls.fedora_base_download + current_spin["dl_link"]
        if "torrent_link" in spin_keys:
            current_spin["torrent_link"] = (
                config.urls.fedora_torrent_download + current_spin["torrent_link"]
            )

        # Create Spin object
        size_value = current_spin.get("size", 0)
        if isinstance(size_value, int):
            from models.data_units import DataUnit
            size_str = DataUnit.from_bytes(size_value).to_human_readable()
        else:
            size_str = str(size_value)
            
        spin = Spin(
            name=current_spin.get("name", ""),
            size=size_str,
            hash256=current_spin.get("hash256", ""),
            dl_link=current_spin.get("dl_link", ""),
            is_live_img=current_spin.get("is_live_img", False),
            version=current_spin.get("version", ""),
            desktop=current_spin.get("desktop", ""),
            is_auto_installable=current_spin.get("is_auto_installable", False),
            is_advanced=current_spin.get("is_advanced", False),
            torrent_link=current_spin.get("torrent_link", ""),
            ostree_args=current_spin.get("ostree_args", ""),
            is_base_netinstall=current_spin.get("is_base_netinstall", False),
            is_default=current_spin.get("is_default", False),
            is_featured=current_spin.get("is_featured", False),
        )
        accepted_spins_list.append(spin)

    # Find live OS base index
    for index, spin in enumerate(accepted_spins_list):
        if spin.is_base_netinstall:
            live_os_base_index = index
            break

    # Filter out live images if no base netinstall found
    if live_os_base_index is None:
        final_spin_list = [spin for spin in accepted_spins_list if not spin.is_live_img]
    else:
        final_spin_list = accepted_spins_list

    return live_os_base_index, final_spin_list
