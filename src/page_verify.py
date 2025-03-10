import tkinter.ttk as ttk
import tkinter_templates as tkt
import globals as GV
from page_manager import Page
import tkinter as tk


class PageVerify(Page):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.auto_restart_toggle_var = tk.BooleanVar(
            parent, GV.INSTALL_OPTIONS.auto_restart
        )

    def init_page(self):
        page_frame = tkt.generic_page_layout(
            self,
            self.LN.verify_question,
            self.LN.btn_install,
            lambda: self.next_btn_action(),
            self.LN.btn_back,
            lambda: self.validate_back_page(),
        )

        # Constructing user verification text based on user's selections  ++++++++++++++++++++++++++++++++++++++++++++++
        review_sel = []
        if GV.KICKSTART.partition_method == "custom":
            review_sel.append(
                self.LN.verify_text["no_autoinst"] % GV.SELECTED_SPIN.name
            )
        else:
            if GV.KICKSTART.partition_method == "dualboot":
                review_sel.append(
                    self.LN.verify_text["autoinst_dualboot"] % GV.SELECTED_SPIN.name
                )
                review_sel.append(self.LN.verify_text["autoinst_keep_data"])
            elif GV.KICKSTART.partition_method == "replace_win":
                review_sel.append(
                    self.LN.verify_text["autoinst_replace_win"] % GV.SELECTED_SPIN.name
                )
                review_sel.append(self.LN.verify_text["autoinst_rm_all"])
            if GV.INSTALL_OPTIONS.export_wifi:
                review_sel.append(
                    self.LN.verify_text["autoinst_wifi"] % GV.SELECTED_SPIN.name
                )
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        self.info_frame_raster = tkt.InfoFrameRaster(
            page_frame,
        )

        for i, text in enumerate(review_sel):
            self.info_frame_raster.add_label(f"review_{i}", text)
        self.info_frame_raster.pack(side="top", fill="x", pady=10, padx=5)

        page_frame.columnconfigure(0, weight=1)
        page_frame.grid_rowconfigure(0, weight=3)

        check_restart = tkt.add_check_btn(
            page_frame,
            text=self.LN.add_auto_restart,
            var=self.auto_restart_toggle_var,
            pack=True,
        )
        check_restart.pack(ipady=8, side="top", anchor="w")

    def validate_back_page(self, *args):
        if GV.KICKSTART.partition_method == "custom":
            self.switch_page("PageInstallMethod")
        elif GV.KICKSTART.username:
            self.switch_page("PageAutoinstAddition3")
        else:
            self.switch_page("PageAutoinstAddition2")

    def next_btn_action(self, *args):
        GV.INSTALL_OPTIONS.auto_restart = self.auto_restart_toggle_var.get()
        self.switch_page("PageInstall")

    def on_show(self):
        """Called when the page is shown."""
        if self._initiated:
            tkt.init_frame(self)
            self.init_page()
