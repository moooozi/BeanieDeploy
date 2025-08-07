"""
Non-GUI logic for compatibility checks and error parsing.
"""

from dataclasses import dataclass
from compatibility_checks import CheckType, DoneChecks
from typing import List, Optional
from config.settings import ConfigManager
from models.spin import Spin
from translations.en import Translation


def parse_errors(
    done_checks: DoneChecks, app_config: ConfigManager, LN: Translation
) -> List[str]:
    errors: List[str] = []
    if done_checks.checks[CheckType.ARCH].returncode != 0:
        errors.append(LN.error_arch_9)
    elif (
        done_checks.checks[CheckType.ARCH].result
        not in app_config.ui.accepted_architectures
    ):
        errors.append(LN.error_arch_0)
    if done_checks.checks[CheckType.UEFI].returncode != 0:
        errors.append(LN.error_uefi_9)
    elif done_checks.checks[CheckType.UEFI].result != "uefi":
        errors.append(LN.error_uefi_0)
    if done_checks.checks[CheckType.RAM].returncode != 0:
        errors.append(LN.error_totalram_9)
    elif done_checks.checks[CheckType.RAM].result < app_config.app.minimal_required_ram:
        errors.append(LN.error_totalram_0)
    if done_checks.checks[CheckType.SPACE].returncode != 0:
        errors.append(LN.error_space_9)
    elif (
        done_checks.checks[CheckType.SPACE].result
        < app_config.app.minimal_required_space
    ):
        errors.append(LN.error_space_0)
    if done_checks.checks[CheckType.RESIZABLE].returncode != 0:
        errors.append(LN.error_resizable_9)
    elif (
        done_checks.checks[CheckType.RESIZABLE].result
        < app_config.app.minimal_required_space
    ):
        errors.append(LN.error_resizable_0)
    return errors


@dataclass
class FilteredSpinsResult:
    spins: List[Spin]
    live_os_installer_index: Optional[int]


def filter_spins(all_spins: List[Spin]) -> FilteredSpinsResult:
    accepted_spins: List[Spin] = []
    live_os_installer_index: Optional[int] = None
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
