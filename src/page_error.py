from templates.generic_page_layout import GenericPageLayout
from templates.info_frame import InfoFrame
import tkinter_templates as tkt
import globals as GV
import functions as fn
from page_manager import Page


class PageError(Page):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.errors = []

    def init_page(self):
        page_layout = GenericPageLayout(
            self,
            self.LN.error_title % GV.APP_SW_NAME,
            secondary_btn_txt=self.LN.btn_quit,
            secondary_btn_command=lambda: fn.app_quit(),
        )
        self.page_frame = page_layout.content_frame
        tkt.add_text_label(self.page_frame, self.LN.error_list, pady=10)

        self.info_frame_raster = InfoFrame(self.page_frame)
        self.info_frame_raster.pack(fill="x", pady=5, padx=10)

    def set_errors(self, errors):
        self.init_page()
        self._initiated = True
        self.errors = errors
        self.info_frame_raster.flush_labels()

        for i, error in enumerate(self.errors):
            self.info_frame_raster.add_label(f"error_{i}", error)
