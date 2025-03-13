from templates.generic_page_layout import GenericPageLayout
import tkinter_templates as tkt
import globals as GV
import functions as fn
from page_manager import Page
import tkinter as tk


class PageRestartRequired(Page):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.restarting_text_var = tk.StringVar()

    def init_page(self):
        page_frame = GenericPageLayout(
            self,
            self.LN.finished_title,
            self.LN.btn_restart_now,
            lambda: fn.quit_and_restart_windows(),
            self.LN.btn_restart_later,
            lambda: fn.app_quit(),
        )
        tkt.add_text_label(
            page_frame, text=self.LN.finished_text, font=tkt.FONTS_smaller, pady=10
        )
        tkt.add_text_label(
            page_frame,
            var=self.restarting_text_var,
            font=tkt.FONTS_small,
            pady=10,
            foreground=tkt.color_blue,
        )

        def countdown_to_restart(time):
            time -= 1
            if time > 0:
                self.restarting_text_var.set(
                    self.LN.finished_text_restarting_now % (int(time))
                )
                self.after(1000, countdown_to_restart, time)
            else:
                fn.quit_and_restart_windows()

        if GV.INSTALL_OPTIONS.auto_restart:
            countdown_to_restart(10)
