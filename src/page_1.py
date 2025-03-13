from tkinter import ttk
import customtkinter as ctk
from templates.info_frame import InfoFrame
from templates.multi_radio_buttons import MultiRadioButtons
import tkinter_templates as tkt
import globals as GV
import functions as fn
import logging
from page_manager import Page
import tkinter as tk
from templates.generic_page_layout import GenericPageLayout


class Page1(Page):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.distro_var = tk.StringVar(parent)

    def init_page(self):
        page_layout = GenericPageLayout(
            self,
            self.LN.desktop_question,
            self.LN.btn_next,
            lambda: self.next_btn_action(),
        )
        page_frame = page_layout.content_frame

        self.full_spin_list = []
        self.non_featured_spin_list = []
        featured_spin_desc = {}
        current_listed_spin_index = 0
        for dist in GV.ACCEPTED_SPINS:
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
            lambda: self.validate_input(),
        )
        self.distro_combolist = ctk.CTkComboBox(
            frame_distro, values=self.non_featured_spin_list, state="readonly"
        )
        self.distro_combolist.bind(
            "<<ComboboxSelected>>", lambda *args: self.validate_input()
        )
        self.distro_combolist.grid(
            ipady=5,
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
        self.validate_input()

    def validate_input(self, *args):
        spin_index = None
        if (distro := self.distro_var.get()) in self.full_spin_list:
            spin_index = self.full_spin_list.index(distro)
            self.distro_combolist.configure(state="disabled")

        elif self.distro_var.get() == "else":
            self.distro_combolist.configure(state="readonly")
            if self.distro_combolist.get() in self.non_featured_spin_list:
                spin_index = self.full_spin_list.index(self.distro_combolist.get())

        if spin_index is not None:
            GV.SELECTED_SPIN = GV.ACCEPTED_SPINS[spin_index]
            total_size = GV.SELECTED_SPIN.size
            total_size += (
                GV.LIVE_OS_INSTALLER_SPIN.size if GV.SELECTED_SPIN.is_live_img else 0
            )
            GV.PARTITION.tmp_part_size = total_size + GV.APP_TEMP_PART_FAILSAFE_SPACE
            if GV.SELECTED_SPIN.is_base_netinstall:
                dl_size_txt = self.LN.init_download % fn.byte_to_gb(total_size)
            else:
                dl_size_txt = self.LN.total_download % fn.byte_to_gb(total_size)
            dl_spin_name_text = f"{self.LN.selected_dist}: {GV.SELECTED_SPIN.name} {GV.SELECTED_SPIN.version}"
            dl_spin_desktop = (
                f"{self.LN.desktop_environment}: {GV.SELECTED_SPIN.desktop}"
                if GV.SELECTED_SPIN.desktop
                else ""
            )

            if GV.SELECTED_SPIN.desktop in self.LN.desktop_hints.keys():
                dl_spin_desktop_desc = self.LN.desktop_hints[GV.SELECTED_SPIN.desktop]
            else:
                dl_spin_desktop_desc = ""

            self.info_frame_raster.flush_labels()
            self.info_frame_raster.add_label("name", dl_spin_name_text)
            self.info_frame_raster.add_label("size", dl_size_txt)
            self.info_frame_raster.add_label("desktop", dl_spin_desktop)
            self.info_frame_raster.add_label("desktop_desc", dl_spin_desktop_desc)
            self.info_frame_raster.pack(side="bottom", fill="x")
        return spin_index

    def next_btn_action(self, *args):
        if self.validate_input() is None:
            return -1
        # LOG #############################################
        log = "\nFedora Spin has been selected, spin details:"
        for key, value in vars(GV.SELECTED_SPIN).items():
            log += "\n --> %s: %s" % (str(key), str(value))
        logging.info(log)
        # #################################################
        return self.switch_page("PageInstallMethod")
