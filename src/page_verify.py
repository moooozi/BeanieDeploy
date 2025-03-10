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
        review_tree = ttk.Treeview(page_frame, columns="error", show="", height=3)
        review_tree.configure(selectmode="none")

        for i in range(len(review_sel)):
            review_tree.insert("", index="end", iid=str(i), values=(review_sel[i],))
        review_tree.grid(
            row=0,
            column=0,
            ipady=5,
            pady=10,
            padx=(0, 5),
            sticky="news",
        )

        # additions options (checkboxes)

        page_frame.columnconfigure(0, weight=1)
        page_frame.grid_rowconfigure(0, weight=3)

        check_restart = tkt.add_check_btn(
            page_frame,
            text=self.LN.add_auto_restart,
            var=self.auto_restart_toggle_var,
            pack=False,
        )
        check_restart.grid(ipady=8, row=1, column=0, sticky=self.DI_VAR.nsw)

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
