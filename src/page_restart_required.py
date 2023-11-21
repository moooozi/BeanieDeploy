import tkinter_templates as tkt
import globals as GV
import multilingual
import functions as fn
import global_tk_vars as tk_var


def run(app):
    """the page on which user is prompted to restart the device to continue installation (boot into install media)"""
    tkt.init_frame(app)
    global LN, DI_VAR
    LN = multilingual.get_lang()
    DI_VAR = multilingual.get_di_var()
    # *************************************************************************************************************
    page_frame = tkt.generic_page_layout(app, LN.finished_title,
                                         LN.btn_restart_now, lambda: fn.quit_and_restart_windows(),
                                         LN.btn_restart_later, lambda: fn.app_quit())
    tkt.add_text_label(page_frame, text=LN.finished_text, font=tkt.FONTS_smaller, pady=10)
    tkt.add_text_label(page_frame, var=tk_var.restarting_text_var, font=tkt.FONTS_small, pady=10,
                       foreground=tkt.color_blue)

    def countdown_to_restart(time):
        time -= 1
        if time > 0:
            tk_var.restarting_text_var.set(LN.finished_text_restarting_now % (int(time)))
            app.after(1000, countdown_to_restart, time)
        else:
            fn.quit_and_restart_windows()

    if GV.INSTALL_OPTIONS.auto_restart:
        countdown_to_restart(10)