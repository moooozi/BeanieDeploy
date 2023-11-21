import tkinter.ttk as ttk
import tkinter_templates as tkt
import globals as GV
import multilingual
import functions as fn


def run(app, errors):
    """The page on which is decided whether the app can run on the device or not"""
    tkt.init_frame(app)
    global LN, DI_VAR
    LN = multilingual.get_lang()
    DI_VAR = multilingual.get_di_var()
    # *************************************************************************************************************
    page_frame = tkt.generic_page_layout(app, LN.error_title % GV.APP_SW_NAME,
                                         secondary_btn_txt=LN.btn_quit, secondary_btn_command=lambda: fn.app_quit())

    tkt.add_text_label(page_frame, LN.error_list, pady=10)

    errors_tree = ttk.Treeview(page_frame, columns='error', show='', height=6)
    errors_tree.pack(ipady=5, padx=(0, 5), fill='x')
    errors_tree.configure(selectmode='none')
    for i in range(len(errors)):
        errors_tree.insert('', index='end', iid=str(i), values=(errors[i],))
