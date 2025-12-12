"""
Spin management services.
Handles parsing and filtering of Fedora spins/variants.
"""

from models.spin import Spin
from models.types import SpinDictList


def parse_spins(spins_list: SpinDictList) -> tuple[list[Spin], str]:
    """
    Parse and filter spins list from JSON data.

    Args:
        spins_list: Raw spins data from JSON

    Returns:
        Tuple of (list of filtered Spin objects, latest version found)
    """
    accepted_spins_list: list[Spin] = []

    # Find the latest version
    latest_version = "0"
    for release in spins_list:
        version_str = release.get("version", "0")
        if version_str.isdigit() and int(version_str) > int(latest_version):
            latest_version = version_str

    # Use provided version or latest

    # Filter for x86_64, ISO files, desired variants, and target version
    desired_variants = {"Workstation", "KDE", "Silverblue", "Kinoite", "Everything"}

    for release in spins_list:
        # Filter criteria
        if (
            release.get("arch") != "x86_64"
            or not release.get("link", "").endswith(".iso")
            or release.get("variant") not in desired_variants
        ):
            continue

        # Map variant to desktop name
        variant = release.get("variant", "")
        desktop_map = {
            "Workstation": "GNOME",
            "KDE": "KDE Plasma",
            "Silverblue": "GNOME",
            "Kinoite": "KDE Plasma",
        }
        desktop = desktop_map.get(variant, "")

        # Create spin name
        subvariant = release.get("subvariant", "")
        if subvariant and subvariant != variant:
            spin_name = f"Fedora {variant} {subvariant}"
        else:
            spin_name = f"Fedora {variant}"

        # Determine if it's a live image
        is_live = "Live" in release.get("link", "") or variant in ["Workstation", "KDE"]

        # Determine if it's base netinstall (Everything)
        is_base_netinstall = variant == "Everything"

        # Set ostree_args for Silverblue and Kinoite
        if variant in ["Silverblue", "Kinoite"]:
            ostree_args = f'--osname="fedora" --remote="fedora" --url="file:///ostree/repo" --ref="fedora/{release.get("version", "")}/x86_64/{variant.lower()}" --nogpg'
        else:
            ostree_args = ""

        # Create Spin object
        spin = Spin(
            name=spin_name,
            size=int(release.get("size", 0)),
            hash256=release.get("sha256", ""),
            dl_link=release.get("link", ""),
            is_live_img=is_live,
            version=release.get("version", ""),
            desktop=desktop,
            is_auto_installable=variant
            in [
                "Workstation",
                "KDE",
                "Silverblue",
                "Kinoite",
            ],  # These have live installers
            is_advanced=variant == "Everything",  # Everything is more advanced
            ostree_args=ostree_args,
            is_base_netinstall=is_base_netinstall,
            is_default=variant == "KDE",  # Workstation is the default
            is_featured=variant
            in ["Workstation", "KDE"],  # Feature the main desktop variants
        )
        accepted_spins_list.append(spin)

    # Sort by variant priority (Workstation first, then KDE, then Everything)
    variant_priority = {"KDE": -2, "Workstation": -1, "Everything": 10}
    accepted_spins_list.sort(key=lambda s: variant_priority.get(s.name.split()[1], 0))

    return accepted_spins_list, latest_version
