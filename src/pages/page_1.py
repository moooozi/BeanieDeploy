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

            self.full_spin_list = []
            self.non_featured_spin_list = []
            featured_spin_desc = {}
            current_listed_spin_index = 0
            print("🔧 Page1 variables initialized")
        except Exception as e:
            print(f"🔧 Error in Page1.init_page(): {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Use state management instead of globals
        accepted_spins = self.state.compatibility.accepted_spins
        
        for dist in accepted_spins:
            spin_fullname = f"{dist.name} {dist.version}"
            self.full_spin_list.append(spin_fullname)
            if dist.is_default or dist.is_featured:
                featured_spin_desc[spin_fullname] = {
                    "name": spin_fullname,
                    "description": (
                        self.LN.distro_hint[dist.name]
                        if dist.name in self.LN.distro_hint
                        else ""
                    ),
                }
                if dist.is_default:
                    (
                        self.distro_var.set(spin_fullname)
                        if self.distro_var.get() == ""
                        else ""
                    )
                    # Moving the default spin to top of the list:
                    default_spin = [
                        spin_fullname,
                        featured_spin_desc.pop(spin_fullname),
                    ]
                    featured_spin_desc = {
                        default_spin[0]: default_spin[1],
                        **featured_spin_desc,
                    }

                current_listed_spin_index += 1

            else:
                self.non_featured_spin_list.append(spin_fullname)

        featured_spin_desc["else"] = {"name": self.LN.something_else}
        frame_distro = MultiRadioButtons(
            page_frame,
            featured_spin_desc,
            self.distro_var,
            lambda: self.update_selection_info(),
        )
        self.distro_combolist = ctk.CTkComboBox(
            frame_distro,
            values=self.non_featured_spin_list,
            fg_color="#565B5E", # CustomTkinter visual bugfix
            state="readonly",
            command=self.update_selection_info,
        )

        self.distro_combolist.grid(
            ipady=5,
            ipadx=20,
            padx=(30, 0),
            row=len(featured_spin_desc) + 1,
            column=0,
            columnspan=2,
            sticky=self.DI_VAR.nw,
        )

        self.distro_combolist.set(self.LN.choose_distro)

        self.info_frame_raster = InfoFrame(page_frame, self.LN.info_about_selection)
        frame_distro.grid_rowconfigure(
            len(featured_spin_desc) + 1, weight=1
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
        """Get the index of the currently selected spin."""
        spin_index = None
        if (distro := self.distro_var.get()) in self.full_spin_list:
            spin_index = self.full_spin_list.index(distro)
            self.distro_combolist.configure(state="disabled")

        elif self.distro_var.get() == "else":
            self.distro_combolist.configure(state="readonly")
            if self.distro_combolist.get() in self.non_featured_spin_list:
                spin_index = self.full_spin_list.index(self.distro_combolist.get())

        return spin_index

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
