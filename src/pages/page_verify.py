import logging
import tkinter as tk

import customtkinter as ctk

from config.settings import PartitioningMethod
from models.data_units import DataUnit
from models.page import Page, PageValidationResult
from multilingual import _
from services.system import (
    get_current_windows_keyboard,
    get_current_windows_locale,
    get_current_windows_timezone,
)
from templates.ctk_treeview import CTkTreeView
from templates.generic_page_layout import GenericPageLayout
from tkinter_templates import flush_frame


class PageVerify(Page):
    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)

        # Initialize install options if it doesn't exist
        if not self.state.installation.install_options:
            from models.install_options import InstallOptions

            self.state.installation.install_options = InstallOptions()

        install_options = self.state.installation.install_options
        self.auto_restart_toggle_var = tk.BooleanVar(
            parent, install_options.auto_restart if install_options else False
        )

    def init_page(self):
        page_layout = GenericPageLayout(
            self,
            _("verify.question"),
            _("btn.install"),
            lambda: self.navigate_next(),
            _("btn.back"),
            lambda: self.navigate_previous(),
        )
        page_frame = page_layout.content_frame

        # Get data from state
        selected_spin = self.state.installation.selected_spin

        if not selected_spin:
            logging.error("No spin selected when showing verify page")
            return

        self.info_frame_raster = CTkTreeView(
            page_frame, title=_("verify.installation.summary")
        )

        # Build the review structure
        self._build_review_structure()

        self.info_frame_raster.grid(row=0, column=0, sticky="nsew")

        page_frame.columnconfigure(0, weight=1)
        page_frame.grid_rowconfigure(0, weight=5, uniform="rows")
        page_frame.grid_rowconfigure(1, weight=1, uniform="rows")

        check_restart = ctk.CTkCheckBox(
            page_frame,
            text=_("add.auto.restart"),
            variable=self.auto_restart_toggle_var,
            onvalue=True,
            offvalue=False,
            width=99,
        )
        check_restart.grid(row=1, column=0, sticky="w")

    def validate_input(self) -> PageValidationResult:
        """Validate the installation settings."""
        # All verification settings are valid by default
        return PageValidationResult(True)

    def on_next(self):
        """Save final installation settings and prepare for installation."""
        install_options = self.state.installation.install_options
        if install_options:
            install_options.auto_restart = self.auto_restart_toggle_var.get()

        logging.info(
            f"Installation verified. Auto restart: {install_options.auto_restart if install_options else False}"
        )

    def on_show(self):
        """Called when the page is shown - reinitialize to show current selections."""
        if self._initiated:
            flush_frame(self)
            self._initiated = False
            self.init_page()
            self._initiated = True

    def _build_review_structure(self):
        """Build the nested review structure in the tree view."""
        selected_spin = self.state.installation.selected_spin
        kickstart = self.state.installation.kickstart
        install_options = self.state.installation.install_options
        partition = self.state.installation.partition

        # Selected distribution
        if selected_spin:
            spin_info = f"{selected_spin.name} {selected_spin.version}"
            if selected_spin.desktop:
                spin_info += f" ({selected_spin.desktop})"
            self.info_frame_raster.insert(
                "", "end", text=f"Selected Distribution: {spin_info}"
            )

        # Installation method and details
        if install_options and install_options.partition_method and selected_spin:
            method = install_options.partition_method
            if method == PartitioningMethod.DUALBOOT:
                self.info_frame_raster.insert(
                    "",
                    "end",
                    text=_("verify.install.dualboot")
                    % {"distro_name": selected_spin.name},
                )
            elif method == PartitioningMethod.REPLACE_WIN:
                self.info_frame_raster.insert(
                    "",
                    "end",
                    text=_("verify.install.replace")
                    % {"distro_name": selected_spin.name},
                )
            elif method == PartitioningMethod.CUSTOM:
                self.info_frame_raster.insert(
                    "",
                    "end",
                    text=_("verify.install.custom")
                    % {"distro_name": selected_spin.name},
                )

            # Partition shrink for dualboot or custom
            if (
                method in [PartitioningMethod.DUALBOOT, PartitioningMethod.CUSTOM]
                and partition
                and hasattr(partition, "shrink_space")
                and partition.shrink_space
            ):
                windows_part = self.state.installation.windows_partition_info
                if windows_part:
                    new_size = DataUnit(windows_part.size - partition.shrink_space)
                    self.info_frame_raster.insert(
                        "",
                        "end",
                        text=_("verify.partition.shrink")
                        % {
                            "partition": f"{windows_part.drive_letter}:",
                            "size": new_size.to_gibibytes(),
                        },
                    )

        # Encryption
        if (
            kickstart
            and hasattr(kickstart.partitioning, "is_encrypted")
            and kickstart.partitioning.is_encrypted
        ):
            self.info_frame_raster.insert("", "end", text=_("verify.encryption.info"))

        # WiFi export
        if (
            install_options
            and hasattr(install_options, "export_wifi")
            and install_options.export_wifi
            and selected_spin
        ):
            self.info_frame_raster.insert(
                "",
                "end",
                text=_("verify.autoinst.wifi") % {"distro_name": selected_spin.name},
            )

        # Localization settings (nested)
        current_locale = get_current_windows_locale() or _("verify.unknown")
        current_timezone = get_current_windows_timezone() or _("verify.unknown")
        current_keyboard = get_current_windows_keyboard() or _("verify.unknown")

        if kickstart and (
            kickstart.locale_settings.locale
            or kickstart.locale_settings.timezone
            or kickstart.locale_settings.keymap
        ):
            localization_parent = self.info_frame_raster.insert(
                "", "end", text="Localization Settings"
            )

            if kickstart.locale_settings.locale:
                locale_parent = self.info_frame_raster.insert(
                    localization_parent, "end", text=_("verify.locale.current")
                )
                self.info_frame_raster.insert(
                    locale_parent,
                    "end",
                    text=_("verify.settings.selected")
                    % {"selected": kickstart.locale_settings.locale},
                )
                self.info_frame_raster.insert(
                    locale_parent,
                    "end",
                    text=_("verify.settings.current") % {"current": current_locale},
                )
            if kickstart.locale_settings.timezone:
                timezone_parent = self.info_frame_raster.insert(
                    localization_parent, "end", text=_("verify.timezone.current")
                )
                self.info_frame_raster.insert(
                    timezone_parent,
                    "end",
                    text=_("verify.settings.selected")
                    % {"selected": kickstart.locale_settings.timezone},
                )
                self.info_frame_raster.insert(
                    timezone_parent,
                    "end",
                    text=_("verify.settings.current") % {"current": current_timezone},
                )
            if kickstart.locale_settings.keymap:
                keyboard_parent = self.info_frame_raster.insert(
                    localization_parent, "end", text=_("verify.keyboard.current")
                )
                self.info_frame_raster.insert(
                    keyboard_parent,
                    "end",
                    text=_("verify.settings.selected")
                    % {"selected": kickstart.locale_settings.keymap},
                )
                self.info_frame_raster.insert(
                    keyboard_parent,
                    "end",
                    text=_("verify.settings.current") % {"current": current_keyboard},
                )

        # Expand all tree items by default
        self.info_frame_raster.expand_all()
