import tkinter.ttk as ttk
import tkinter_templates as tkt
import globals as GV
import translations.en as LN
import functions as fn
from init import MID_FRAME


def run(errors):
    """The page on which is decided whether the app can run on the device or not"""
    tkt.init_frame(MID_FRAME)
    # *************************************************************************************************************
    page_frame = tkt.generic_page_layout(MID_FRAME, LN.error_title % GV.APP_SW_NAME,
                                         secondary_btn_txt=LN.btn_quit, secondary_btn_command=lambda: fn.app_quit())

    tkt.add_text_label(page_frame, LN.error_list, pady=10)

    errors_tree = ttk.Treeview(page_frame, columns='error', show='', height=6)
    errors_tree.pack(anchor=GV.UI.DI_VAR['w'], ipady=5, padx=(0, 5), fill='x')
    errors_tree.configure(selectmode='none')
    for i in range(len(errors)):
        errors_tree.insert('', index='end', iid=str(i), values=(errors[i],))
