import customtkinter as ctk
from compatibility_checks import CheckType
from models.data_units import DataUnit
from templates.generic_page_layout import GenericPageLayout
from templates.multi_radio_buttons import MultiRadioButtons
import tkinter_templates as tkt
import globals as GV
import functions as fn
from models.page_manager import Page
import tkinter as tk
from sys import argv


class PageInstallMethod(Page):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.install_method_var = tk.StringVar(parent)
        self.dualboot_size_var = tk.StringVar(parent)

    def init_page(self):

        page_layout = GenericPageLayout(
            self,
            self.LN.windows_question % GV.SELECTED_SPIN.name,
            self.LN.btn_next,
            lambda: self.next_btn_action(),
            self.LN.btn_back,
            lambda: self.switch_page("Page1"),
        )
        page_frame = page_layout.content_frame

        self.selected_spin_name = GV.SELECTED_SPIN.name

        space_dualboot = (
            GV.APP_DUALBOOT_REQUIRED_SPACE
            + GV.APP_LINUX_BOOT_PARTITION_SIZE
            + GV.APP_ADDITIONAL_FAILSAFE_SPACE
            + GV.PARTITION.tmp_part_size * 2
        )
        space_clean = (
            GV.APP_LINUX_BOOT_PARTITION_SIZE
            + GV.APP_ADDITIONAL_FAILSAFE_SPACE
            + GV.PARTITION.tmp_part_size * 2
        )

        if "--skip_check" not in argv:
            dualboot_space_available = (
                GV.DONE_CHECKS.checks[CheckType.RESIZABLE].result > space_dualboot
            )
            replace_win_space_available = (
                GV.DONE_CHECKS.checks[CheckType.RESIZABLE].result > space_clean
            )
            max_size = DataUnit.from_bytes(
                GV.DONE_CHECKS.checks[CheckType.RESIZABLE].result
                - GV.SELECTED_SPIN.size
                - GV.APP_ADDITIONAL_FAILSAFE_SPACE
            ).to_gigabytes()
            max_size = round(max_size, 2)
        else:
            dualboot_space_available = True
            replace_win_space_available = True
            max_size = 9999

        is_auto_installable = GV.SELECTED_SPIN.is_auto_installable

        default = "custom" if not is_auto_installable else "replace_win"
        self.install_method_var.set(default)

        dualboot_error_msg = ""
        replace_win_error_msg = ""
        if not is_auto_installable:
            dualboot_error_msg = self.LN.warn_not_available
            replace_win_error_msg = self.LN.warn_not_available
        else:
            if not dualboot_space_available:
                dualboot_error_msg = self.LN.warn_space
            if not replace_win_space_available:
                replace_win_error_msg = self.LN.warn_space

        install_methods_dict = {
            "dualboot": {
                "name": self.LN.windows_options["dualboot"],
                "error": dualboot_error_msg,
                "advanced": True,
            },
            "replace_win": {
                "name": self.LN.windows_options["replace_win"],
                "error": replace_win_error_msg,
                "advanced": False,
            },
            "custom": {
                "name": self.LN.windows_options["custom"],
                "advanced": True,
            },
        }

        radio_buttons = MultiRadioButtons(
            page_frame,
            install_methods_dict,
            self.install_method_var,
            lambda: self.show_more_options_if_needed(),
        )
        radio_buttons.pack(expand=1, fill="x")

        min_size = DataUnit.from_bytes(GV.APP_DUALBOOT_REQUIRED_SPACE).to_gigabytes()
        self.entry1_frame = ctk.CTkFrame(page_frame, height=300)
        self.entry1_frame.pack_propagate(False)
        self.entry1_frame.pack(
            fill="both",
            side="bottom",
        )

        self.warn_backup_sys_drive_files = tkt.add_text_label(
            self.entry1_frame,
            text=self.LN.warn_backup_files_txt % f"{fn.get_sys_drive_letter()}:\\",
            font=tkt.FONTS_smaller,
            foreground=tkt.color_red,
            pack=False,
        )
        self.size_dualboot_txt_pre = tkt.add_text_label(
            self.entry1_frame,
            text=self.LN.dualboot_size_txt % GV.SELECTED_SPIN.name,
            font=tkt.FONTS_smaller,
            pack=False,
        )
        self.size_dualboot_entry = ctk.CTkEntry(
            self.entry1_frame,
            width=10,
            textvariable=self.dualboot_size_var,
        )
        validation_func = self.register(
            lambda x: x.replace(".", "", 1).isdigit()
            and min_size <= float(x) <= max_size
        )
        self.size_dualboot_entry.configure(
            validate="none", validatecommand=(validation_func, "%P")
        )
        self.size_dualboot_txt_post = tkt.add_text_label(
            self.entry1_frame,
            text="(%sGB - %sGB)" % (min_size, max_size),
            font=tkt.FONTS_smaller,
            foreground=tkt.color_blue,
            pack=False,
        )
        tkt.var_tracer(
            self.dualboot_size_var,
            "write",
            lambda *args: self.size_dualboot_entry.validate(),
        )

        self.update_idletasks()
        self.show_more_options_if_needed()  # GUI bugfix

    def show_more_options_if_needed(self):
        self.warn_backup_sys_drive_files.grid_forget()
        self.size_dualboot_txt_pre.grid_forget()
        self.size_dualboot_entry.grid_forget()
        self.size_dualboot_txt_post.grid_forget()
        if self.install_method_var.get() == "dualboot":
            self.size_dualboot_txt_pre.grid(
                pady=5, padx=(10, 0), column=0, row=0, sticky=self.DI_VAR.w
            )
            self.size_dualboot_entry.grid(pady=5, padx=5, column=1, row=0)
            self.size_dualboot_txt_post.grid(
                pady=5, padx=(0, 0), column=2, row=0, sticky=self.DI_VAR.w
            )
        elif self.install_method_var.get() == "replace_win":
            self.warn_backup_sys_drive_files.grid(
                pady=5, padx=(10, 0), column=0, row=0, sticky=self.DI_VAR.w
            )

    def next_btn_action(self, *args):
        if self.install_method_var.get() not in GV.AVAILABLE_INSTALL_METHODS:
            return -1
        GV.KICKSTART.partition_method = self.install_method_var.get()
        if GV.KICKSTART.partition_method == "dualboot":
            self.size_dualboot_entry.validate()
            syntax_invalid = "invalid" in self.size_dualboot_entry.state()
            if syntax_invalid:
                return -1
            GV.PARTITION.shrink_space = DataUnit.from_gigabytes(
                self.dualboot_size_var.get()
            )
        elif GV.KICKSTART.partition_method == "custom":
            GV.PARTITION.shrink_space = 0
            GV.PARTITION.boot_part_size = 0
            GV.PARTITION.efi_part_size = 0
            self.switch_page("PageVerify")
        else:
            self.switch_page("PageAutoinst2")

    def on_show(self):
        if self.selected_spin_name != GV.SELECTED_SPIN.name:
            tkt.flush_frame(self)
            self.init_page()
