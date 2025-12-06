import logging
import tkinter as tk
from threading import Thread

import customtkinter as ctk

from models.page import Page, PageValidationResult
from multilingual import _
from templates.info_frame import InfoFrame
from templates.multi_radio_buttons import MultiRadioButtons
from utils import format_bytes


class Page1(Page):
    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)
        self.distro_var = tk.StringVar(self)
        self.still_loading_label = None
        self.latest_label = None

    def init_page(self):
        self.page_manager.set_title(_("desktop.question"))
        # Primary and secondary buttons use defaults
        self.columnconfigure(0, weight=1)

        self._wait_spin_loading()

        # Access Windows Partition information so they are loaded early
        loader = Thread(target=lambda: self.state.installation.windows_partition_info)
        self.after(200, loader.start)

    def finish_init_page(self):
        """Final initialization after spins are loaded."""
        accepted_spins = self.state.compatibility.accepted_spins
        # Build a single dict for all spins, marking non-featured as advanced
        spin_radio_dict = {}
        for dist in accepted_spins:
            spin_fullname = f"{dist.name} {dist.version}"
            is_featured = dist.is_default or dist.is_featured
            # Get distro hint based on name
            distro_hint = ""
            if is_featured:
                if dist.name == "Fedora Workstation":
                    distro_hint = _("distro.hint.fedora.workstation")
                elif dist.name == "Fedora KDE":
                    distro_hint = _("distro.hint.fedora.kde.plasma")

            spin_radio_dict[spin_fullname] = {
                "name": spin_fullname,
                "description": distro_hint,
                "advanced": not is_featured,
            }
            if dist.is_default and self.distro_var.get() == "":
                self.distro_var.set(spin_fullname)
        # Move default spin to top if present
        if any(dist.is_default for dist in accepted_spins):
            default_spin = next(
                (
                    f"{dist.name} {dist.version}"
                    for dist in accepted_spins
                    if dist.is_default
                ),
                None,
            )
            if default_spin:
                default_entry = spin_radio_dict.pop(default_spin)
                spin_radio_dict = {default_spin: default_entry, **spin_radio_dict}

        frame_distro = MultiRadioButtons(
            self,
            items=spin_radio_dict,
            variable=self.distro_var,
            validation_callback=lambda: self.update_selection_info(),
            advanced_options_txt=_("show.advanced.options"),
        )

        # Make frame_distro leave 1/3 of vertical space above it
        # Used to achieve balanced look with advanced radio hidden initially
        # but their space is still pre-allocated
        frame_distro.grid(row=1, column=0, rowspan=2, sticky="ew")
        self.rowconfigure(0, weight=1, uniform="rows")
        self.rowconfigure(1, weight=1, uniform="rows")
        self.rowconfigure(2, weight=1, uniform="rows")

        self.info_frame_raster = InfoFrame(self, _("info.about.selection"))

        if (
            not self.state.spin_selection.is_using_untested
            and self.state.spin_selection.latest_version
            and self.state.spin_selection.latest_version
            != self.app_config.app.supported_version
        ):
            self.latest_label = ctk.CTkSimpleLabel(
                self,
                text=f"⟳ {_('use.untested.version')}",
                font=self._ui.fonts.smaller,
                text_color=self._ui.colors.primary,
                cursor="hand2",
            )
            self.latest_label.bind("<Button-1>", self._on_use_latest)
            self.latest_label.grid(row=0, column=0, sticky="ew")

        self.update_selection_info()

    def update_selection_info(self):
        """Update the information display based on current selection."""
        spin_index = self._get_selected_spin_index()
        if spin_index is not None:
            accepted_spins = self.state.compatibility.accepted_spins
            selected_spin = accepted_spins[spin_index]

            total_size_bytes = selected_spin.size

            if (
                selected_spin.is_live_img
                and self.state.compatibility.live_os_installer_spin
            ):
                total_size_bytes += self.state.compatibility.live_os_installer_spin.size

            if selected_spin.is_base_netinstall:
                dl_size_txt = _("init.download") % {
                    "size": format_bytes(total_size_bytes)
                }
            else:
                dl_size_txt = _("total.download") % {
                    "size": format_bytes(total_size_bytes)
                }

            dl_spin_name_text = f"{_('selected.dist')}: {selected_spin.full_name}"
            dl_spin_desktop = (
                f"{_('desktop.environment')}: {selected_spin.desktop}"
                if selected_spin.desktop
                else ""
            )

            # Get desktop hint based on desktop environment
            dl_spin_desktop_desc = ""
            if selected_spin.desktop == "KDE Plasma":
                dl_spin_desktop_desc = _("desktop.hint.kde.plasma")
            elif selected_spin.desktop == "GNOME":
                dl_spin_desktop_desc = _("desktop.hint.gnome")

            self.info_frame_raster.flush_labels()
            self.info_frame_raster.add_label("name", dl_spin_name_text)
            self.info_frame_raster.add_label("size", dl_size_txt)
            self.info_frame_raster.add_label("desktop", dl_spin_desktop)
            self.info_frame_raster.add_label("desktop_desc", dl_spin_desktop_desc)
            self.info_frame_raster.grid(row=3, column=0, sticky="sew")

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
            return PageValidationResult(False, "No spin selected.")
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
            total_size_bytes = selected_spin.size

            if (
                selected_spin.is_live_img
                and self.state.compatibility.live_os_installer_spin
            ):
                total_size_bytes += self.state.compatibility.live_os_installer_spin.size

            # Create partition if it doesn't exist and update size
            if self.state.installation.partition is None:
                from models.partition import Partition

                self.state.installation.partition = Partition()

            partition_size_bytes = (
                total_size_bytes + self.app_config.app.temp_part_failsafe_space.bytes
            )
            self.state.installation.partition.tmp_part_size = int(partition_size_bytes)

            # Log the selection
            log = "\\nFedora Spin has been selected, spin details:"
            for key, value in vars(selected_spin).items():
                log += f"\\n --> {key}: {value}"
            logging.debug(log)

    def show_validation_error(self, message: str):
        """Show validation error using popup."""
        # This would integrate with your existing popup system
        # For now, just call the parent implementation
        super().show_validation_error(message)
        # TODO: Implement actual popup display
        # self.show_popup(
        #     title=_("error.validation.title"),
        #     message=message,
        #     type_="warning",
        # )

    def _wait_spin_loading(self):
        """Wait for spins to load before proceeding."""
        if not self.state.compatibility.accepted_spins:
            if self.still_loading_label is None:
                self.still_loading_label = ctk.CTkSimpleLabel(
                    self,
                    text=_("loading.spins"),
                    font=self._ui.fonts.smaller,
                    text_color=self._ui.colors.primary,
                )
                self.still_loading_label.grid(row=2, column=0, sticky="ew")
            self.after(200, self._wait_spin_loading)
        else:
            if self.still_loading_label is not None:
                self.still_loading_label.destroy()
                self.still_loading_label = None
            self.finish_init_page()

    def _on_use_latest(self, _):
        """Handle clicking the use latest label."""
        self.state.spin_selection.is_using_untested = True
        from services.spin_manager import set_spins_in_state

        set_spins_in_state(self.state, self.state.spin_selection.raw_spins_data)
        # Re-init the page
        for widget in self.winfo_children():
            widget.destroy()
        self.distro_var.set("")
        self.finish_init_page()
