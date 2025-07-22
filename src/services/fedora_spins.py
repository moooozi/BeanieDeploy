"""
Fedora spins data processing service.

Handles parsing and validation of Fedora distribution data.
"""

from typing import List, Dict, Any, Tuple, Optional
from config.settings import get_config
from models.spin import Spin


def parse_spins(spins_list: List[Dict[str, Any]]) -> Tuple[Optional[int], List[Spin]]:
    """
    Parse and validate a list of Fedora spins data.
    
    Args:
        spins_list: Raw list of spin dictionaries from API/JSON
        
    Returns:
        Tuple of (live_os_base_index, validated_spins_list)
    """
    accepted_spins_list = []
    live_os_base_index = None
    
    # Validate and process each spin
    for index, current_spin in enumerate(spins_list):
        spin_keys = list(current_spin.keys())
        
        # Check required fields
        required_fields = ("name", "size", "hash256", "dl_link")
        if not all(field in spin_keys for field in required_fields):
            continue
            
        # Add base URLs to download links
        current_spin["dl_link"] = (
            get_config().urls.fedora_base_download + current_spin["dl_link"]
        )
        
        if "torrent_link" in spin_keys:
            current_spin["torrent_link"] = (
                get_config().urls.fedora_torrent_download + current_spin["torrent_link"]
            )
        
        # Create Spin object with validated data
        spin = Spin(
            name=current_spin["name"],  # Already validated above
            size=current_spin["size"],  # Already validated above
            hash256=current_spin["hash256"],  # Already validated above
            dl_link=current_spin["dl_link"],  # Already validated above
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
    
    # Find the base netinstall index
    for index, spin in enumerate(accepted_spins_list):
        if spin.is_base_netinstall:
            live_os_base_index = index
            break
    
    # Filter based on whether we have a base netinstall
    if live_os_base_index is None:
        # No base netinstall found, filter out live images
        final_spin_list = []
        for spin in accepted_spins_list:
            if not spin.is_live_img:
                final_spin_list.append(spin)
    else:
        # Base netinstall found, keep all spins
        final_spin_list = accepted_spins_list
    
    return live_os_base_index, final_spin_list
