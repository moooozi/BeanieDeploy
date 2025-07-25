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
            print("🔧 Page1 variables initialized")
        except Exception as e:
            print(f"🔧 Error in Page1.init_page(): {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Use state management instead of globals
        accepted_spins = self.state.compatibility.accepted_spins
        
        from core.page1_logic import get_full_spin_list, get_featured_and_non_featured_spins
        self.full_spin_list = get_full_spin_list(accepted_spins)
        featured_spin_desc, self.non_featured_spin_list = get_featured_and_non_featured_spins(accepted_spins)
        # preserve combolist and all GUI features
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
        from core.page1_logic import get_selected_spin_info
        spin_index = self._get_selected_spin_index()
        info = get_selected_spin_info(self.state.compatibility.accepted_spins, spin_index)
        if info:
            selected_spin = info["selected_spin"]
            total_size_unit = info["total_size_unit"]
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
        # preserve combolist logic
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
        from core.page1_logic import validate_spin_selection
        spin_index = self._get_selected_spin_index()
        if not validate_spin_selection(spin_index):
            return PageValidationResult(False, self.LN.popup_msg_no_spin_selected)
        return PageValidationResult(True)

    def on_next(self):
        from core.page1_logic import save_selected_spin_to_state
        spin_index = self._get_selected_spin_index()
        save_selected_spin_to_state(self.state, spin_index)

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
