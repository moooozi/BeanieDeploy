"""
Business logic for Page1: spin selection, validation, and info.
"""
from models.data_units import DataUnit

def get_full_spin_list(accepted_spins):
    return [f"{dist.name} {dist.version}" for dist in accepted_spins]

def get_featured_and_non_featured_spins(accepted_spins):
    featured_spin_desc = {}
    non_featured_spin_list = []
    for dist in accepted_spins:
        spin_fullname = f"{dist.name} {dist.version}"
        if dist.is_default or dist.is_featured:
            featured_spin_desc[spin_fullname] = {"name": spin_fullname}
        else:
            non_featured_spin_list.append(spin_fullname)
    featured_spin_desc["else"] = {"name": "Something else"}
    return featured_spin_desc, non_featured_spin_list

def get_selected_spin_index(distro_var, full_spin_list):
    distro = distro_var.get()
    if distro in full_spin_list:
        return full_spin_list.index(distro)
    elif distro == "else":
        return None  # Or handle custom selection logic
    return None

def get_selected_spin_info(accepted_spins, spin_index):
    if spin_index is not None:
        selected_spin = accepted_spins[spin_index]
        total_size_unit = DataUnit.from_string(selected_spin.size)
        return {
            "selected_spin": selected_spin,
            "total_size_unit": total_size_unit,
            "is_live_img": selected_spin.is_live_img,
            "is_base_netinstall": selected_spin.is_base_netinstall,
        }
    return None

def validate_spin_selection(spin_index):
    return spin_index is not None

def save_selected_spin_to_state(state, spin_index):
    if spin_index is not None:
        state.installation.selected_spin = state.compatibility.accepted_spins[spin_index]
