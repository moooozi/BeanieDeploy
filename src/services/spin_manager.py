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

    # Find the latest version (supports formats like "43" or "44 Beta").
    latest_version = "0"
    for release in spins_list:
        version_str = str(release.get("version", "0")).strip()
        version_token = version_str.split(maxsplit=1)[0] if version_str else "0"
        if version_token.isdigit() and int(version_token) > int(latest_version):
            latest_version = version_token

    # Use provided version or latest

    # Filter for x86_64, ISO files, and desired subvariants
    desired_subvariants = {
        "KDE",
        "Workstation",
        # "COSMIC",
        "Kinoite",
        "Silverblue",
        # "COSMIC-Atomic",
        "Everything",
    }

    spin_name_map = {
        "KDE": "Fedora Workstation KDE",
        "Workstation": "Fedora Workstation",
        "COSMIC": "Fedora COSMIC",
        "Kinoite": "Fedora Kinoite",
        "Silverblue": "Fedora Silverblue",
        "COSMIC-Atomic": "Fedora COSMIC Atomic",
        "Everything": "Fedora Everything",
    }

    for release in spins_list:
        # Filter criteria
        if release.get("arch") != "x86_64" or not release.get("link", "").endswith(
            ".iso"
        ):
            continue

        variant = release.get("variant", "")
        subvariant = release.get("subvariant", "")
        version_str = str(release.get("version", "")).strip()
        version = version_str.split(maxsplit=1)[0] if version_str else ""

        if subvariant not in desired_subvariants:
            continue

        # Map subvariant to desktop name
        desktop_map = {
            "Workstation": "GNOME",
            "KDE": "KDE",
            "Silverblue": "GNOME",
            "Kinoite": "KDE",
            "COSMIC": "COSMIC",
            "COSMIC-Atomic": "COSMIC",
        }
        desktop = desktop_map.get(subvariant, "")

        # Create spin name
        spin_name = spin_name_map.get(subvariant, f"Fedora {subvariant}")

        # Determine if it's a live image
        is_live = "Live" in release.get("link", "") or variant in [
            "Workstation",
            "KDE",
            "Spins",
        ]

        # Determine if it's base netinstall (Everything)
        is_base_netinstall = subvariant == "Everything"

        # Set ostree_args for Silverblue and Kinoite
        if subvariant in [
            "Silverblue",
            "Kinoite",
            # "COSMIC-Atomic",
        ]:
            ostree_args = f'--osname="fedora" --remote="fedora" --url="file:///ostree/repo" --ref="fedora/{version}/x86_64/{variant.lower()}" --nogpg'
        else:
            ostree_args = ""

        # Create Spin object
        spin = Spin(
            name=spin_name,
            size=int(release.get("size", 0)),
            hash256=release.get("sha256", ""),
            dl_link=release.get("link", ""),
            is_live_img=is_live,
            version=version,
            full_version=version_str,
            desktop=desktop,
            is_auto_installable=subvariant
            not in [
                "Everything",
            ],
            is_advanced=subvariant == "Everything",  # Everything is more advanced
            ostree_args=ostree_args,
            is_base_netinstall=is_base_netinstall,
            is_default=subvariant == "KDE",  # KDE is the default
            is_featured=subvariant
            in ["Workstation", "KDE", "COSMIC"],  # Feature the main desktop variants
        )
        accepted_spins_list.append(spin)

    # Sort by desired display priority
    variant_priority = {
        "Fedora KDE Spin": -6,
        "Fedora Workstation": -5,
        "Fedora COSMIC": -4,
        "Fedora Kinoite": -3,
        "Fedora Silverblue": -2,
        "Fedora COSMIC Atomic": -1,
        "Fedora Everything": 10,
    }
    accepted_spins_list.sort(key=lambda s: variant_priority.get(s.name, 0))

    return accepted_spins_list, latest_version
