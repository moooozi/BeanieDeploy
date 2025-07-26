import customtkinter as ctk
from models.data_units import DataUnit
from templates.info_frame import InfoFrame
from templates.multi_radio_buttons import MultiRadioButtons
from models.page import Page, PageValidationResult
import tkinter as tk
from templates.generic_page_layout import GenericPageLayout


class Page1(Page):
    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)
        self.distro_var = tk.StringVar(self)

    def init_page(self):
        print("🔧 Page1.init_page() called")
        try:
            page_layout = GenericPageLayout(
                self,
                self.LN.desktop_question,
                self.LN.btn_next,
                lambda: self.navigate_next(),  # Use new navigation method
            )
            print("🔧 Page1 GenericPageLayout created")
            page_frame = page_layout.content_frame

            print("🔧 Page1 variables initialized")
        except Exception as e:
            print(f"🔧 Error in Page1.init_page(): {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Use state management instead of globals
        accepted_spins = self.state.compatibility.accepted_spins
        
        # Build a single dict for all spins, marking non-featured as advanced
        spin_radio_dict = {}
        for dist in accepted_spins:
            spin_fullname = f"{dist.name} {dist.version}"
            is_featured = dist.is_default or dist.is_featured
            spin_radio_dict[spin_fullname] = {
                "name": spin_fullname,
                "description": (
                    self.LN.distro_hint[dist.name] if is_featured and dist.name in self.LN.distro_hint else ""
                ),
                "advanced": not is_featured,
            }
            if dist.is_default and self.distro_var.get() == "":
                self.distro_var.set(spin_fullname)
        # Move default spin to top if present
        if any(dist.is_default for dist in accepted_spins):
            default_spin = next((f"{dist.name} {dist.version}" for dist in accepted_spins if dist.is_default), None)
            if default_spin:
                default_entry = spin_radio_dict.pop(default_spin)
                spin_radio_dict = {default_spin: default_entry, **spin_radio_dict}

        frame_distro = MultiRadioButtons(
            page_frame,
            spin_radio_dict,
            self.distro_var,
            lambda: self.update_selection_info(),
        )

        self.info_frame_raster = InfoFrame(page_frame, self.LN.info_about_selection)
        frame_distro.grid_rowconfigure(
            len(frame_distro.children) + 1, weight=1
        )  # GUI bugfix for distro_description
        frame_distro.pack(expand=1, fill="x")
        self.update_selection_info()

    def update_selection_info(self, *args):
        """Update the information display based on current selection."""
        spin_index = self._get_selected_spin_index()
        if spin_index is not None:
            accepted_spins = self.state.compatibility.accepted_spins
            selected_spin = accepted_spins[spin_index]
            
            # Calculate sizes (sizes are string values like "2.5 GB")
            total_size_unit = DataUnit.from_string(selected_spin.size)
            
            if selected_spin.is_live_img and self.state.compatibility.live_os_installer_spin:
                live_os_size_unit = DataUnit.from_string(self.state.compatibility.live_os_installer_spin.size)
                total_size_unit += live_os_size_unit

            if selected_spin.is_base_netinstall:
                dl_size_txt = (
                    self.LN.init_download
                    % total_size_unit.to_human_readable()
                )
            else:
                dl_size_txt = (
                    self.LN.total_download
                    % total_size_unit.to_human_readable()
                )
            
            dl_spin_name_text = f"{self.LN.selected_dist}: {selected_spin.name} {selected_spin.version}"
            dl_spin_desktop = (
                f"{self.LN.desktop_environment}: {selected_spin.desktop}"
                if selected_spin.desktop
                else ""
            )

            if selected_spin.desktop in self.LN.desktop_hints.keys():
                dl_spin_desktop_desc = self.LN.desktop_hints[selected_spin.desktop]
            else:
                dl_spin_desktop_desc = ""

            self.info_frame_raster.flush_labels()
            self.info_frame_raster.add_label("name", dl_spin_name_text)
            self.info_frame_raster.add_label("size", dl_size_txt)
            self.info_frame_raster.add_label("desktop", dl_spin_desktop)
            self.info_frame_raster.add_label("desktop_desc", dl_spin_desktop_desc)
            self.info_frame_raster.pack(side="bottom", fill="x")

    def _get_selected_spin_index(self):
        """Return the index of the currently selected spin, or None if not found."""
        distro = self.distro_var.get()
        spins = self.state.compatibility.accepted_spins
        for idx, dist in enumerate(spins):
            if distro == f"{dist.name} {dist.version}":
                return idx
        return None
    
    def validate_input(self) -> PageValidationResult:
        """Validate that a spin has been selected."""
        if self._get_selected_spin_index() is None:
            return PageValidationResult(
                False, 
                self.LN.popup_msg_no_spin_selected
            )
        return PageValidationResult(True)

    def on_next(self):
        """Handle next action - save the selected spin to state."""
        spin_index = self._get_selected_spin_index()
        if spin_index is not None:
            accepted_spins = self.state.compatibility.accepted_spins
            selected_spin = accepted_spins[spin_index]
            
            # Update state with selected spin
            self.state.set_selected_spin(selected_spin)
            
            # Calculate and update partition size
            total_size_unit = DataUnit.from_string(selected_spin.size)
            
            if selected_spin.is_live_img and self.state.compatibility.live_os_installer_spin:
                live_os_size_unit = DataUnit.from_string(self.state.compatibility.live_os_installer_spin.size)
                total_size_unit += live_os_size_unit
            
            # Create partition if it doesn't exist and update size
            if self.state.installation.partition is None:
                from models.partition import Partition
                self.state.installation.partition = Partition()
            
            partition_size_bytes = total_size_unit.bytes + self.app_config.app.temp_part_failsafe_space.bytes
            self.state.installation.partition.tmp_part_size = int(partition_size_bytes)
            
            # Log the selection
            log = f"\\nFedora Spin has been selected, spin details:"
            for key, value in vars(selected_spin).items():
                log += f"\\n --> {key}: {value}"
            self.logger.info(log)

    def show_validation_error(self, message: str):
        """Show validation error using popup."""
        # This would integrate with your existing popup system
        # For now, just call the parent implementation
        super().show_validation_error(message)
        # TODO: Implement actual popup display
        # self.show_popup(
        #     title=self.LN.popup_title_warning,
        #     message=message,
        #     type_="warning",
        # )
