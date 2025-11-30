"""
Non-GUI logic for compatibility checks and error parsing.
"""

from dataclasses import dataclass

from models.spin import Spin


@dataclass
class FilteredSpinsResult:
    spins: list[Spin]
    live_os_installer_index: int | None


def filter_spins(all_spins: list[Spin]) -> FilteredSpinsResult:
    accepted_spins: list[Spin] = []
    live_os_installer_index: int | None = None
    for spin in all_spins:
        accepted_spins.append(spin)
    for index, spin in enumerate(accepted_spins):
        if spin.is_base_netinstall:
            live_os_installer_index = index
            break
    if live_os_installer_index is None:
        filtered_spins = [spin for spin in accepted_spins if not spin.is_live_img]
    else:
        filtered_spins = accepted_spins
    return FilteredSpinsResult(
        spins=filtered_spins, live_os_installer_index=live_os_installer_index
    )
