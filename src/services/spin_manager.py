"""
Spin management services.
Handles parsing and filtering of Fedora spins/variants.
"""
from typing import List
from models.spin import Spin
from models.types import SpinDictList


def parse_spins(spins_list: SpinDictList) -> List[Spin]:
    """
    Parse and filter spins list from JSON data.

    Args:
        spins_list: Raw spins data from JSON

    Returns:
        List of filtered Spin objects
    """
    accepted_spins_list: List[Spin] = []

    # Find the latest version
    latest_version = '0'
    for release in spins_list:
        version = release.get('version', '0')
        if version.isdigit() and int(version) > int(latest_version):
            latest_version = version

    # Filter for x86_64, ISO files, desired variants, and latest version only
    desired_variants = {'Workstation', 'KDE', 'Silverblue', 'Kinoite', 'Everything'}

    for release in spins_list:
        # Filter criteria
        if (release.get('arch') != 'x86_64' or
            not release.get('link', '').endswith('.iso') or
            release.get('variant') not in desired_variants or
            release.get('version') != latest_version):
            continue

        # Map variant to desktop name
        variant = release.get('variant', '')
        desktop_map = {
            'Workstation': 'GNOME',
            'KDE': 'KDE Plasma',
            'Silverblue': 'GNOME',
            'Kinoite': 'KDE Plasma',
        }
        desktop = desktop_map.get(variant, '')

        # Create spin name
        subvariant = release.get('subvariant', '')
        if subvariant and subvariant != variant:
            spin_name = f"Fedora {variant} {subvariant}"
        else:
            spin_name = f"Fedora {variant}"

        # Determine if it's a live image
        is_live = 'Live' in release.get('link', '') or variant in ['Workstation', 'KDE']

        # Determine if it's base netinstall (Everything)
        is_base_netinstall = variant == 'Everything'

        # Create Spin object
        spin = Spin(
            name=spin_name,
            size=int(release.get('size', 0)),
            hash256=release.get('sha256', ''),
            dl_link=release.get('link', ''),
            is_live_img=is_live,
            version=release.get('version', ''),
            desktop=desktop,
            is_auto_installable=variant in ['Workstation', 'KDE', 'Silverblue', 'Kinoite'],  # These have live installers
            is_advanced=variant == 'Everything',  # Everything is more advanced
            ostree_args='',  # Not applicable for these variants
            is_base_netinstall=is_base_netinstall,
            is_default=variant == 'KDE',  # Workstation is the default
            is_featured=variant in ['Workstation', 'KDE']  # Feature the main desktop variants
        )
        accepted_spins_list.append(spin)

    # Sort by variant priority (Workstation first, then KDE, then Everything)
    variant_priority = {'KDE': -2, "Workstation": -1, 'Everything': 10}
    accepted_spins_list.sort(key=lambda s: variant_priority.get(s.name.split()[1], 0))

    return accepted_spins_list
