import tkinter.ttk as ttk
import page_autoinst_addition_2
import page_verify
import tkinter_templates as tkt
import globals as GV
import multilingual
import global_tk_vars as tk_var
import functions as fn


def run(app):
    """the autoinstall page on which you choose your timezone and keyboard layout"""
    tkt.init_frame(app)
    global LN, DI_VAR
    LN = multilingual.get_lang()
    DI_VAR = multilingual.get_di_var()
    # *************************************************************************************************************
    # GNOME allows User account creation during initial start tour, so we use that and skip creating a user
    if GV.SELECTED_SPIN.desktop == "GNOME":
        GV.KICKSTART.username = ''
        return page_verify.run(app)

    page_frame = tkt.generic_page_layout(app, LN.title_autoinst4,
                                         LN.btn_next, lambda: next_btn_action(),
                                         LN.btn_back, lambda: page_autoinst_addition_2.run(app))

    userinfo_frame = tkt.add_frame_container(page_frame)
    fullname_pre = tkt.add_text_label(userinfo_frame, text=LN.entry_fullname, font=tkt.FONTS_smaller, pack=False)
    fullname_entry = ttk.Entry(userinfo_frame, width=10, textvariable=tk_var.fullname)
    username_pre = tkt.add_text_label(userinfo_frame, text=LN.entry_username, font=tkt.FONTS_smaller, pack=False)
    username_entry = ttk.Entry(userinfo_frame, width=10, textvariable=tk_var.username)

    fullname_pre.grid(pady=5, padx=(10, 0), column=0, row=0, sticky=DI_VAR['w'])
    fullname_entry.grid(pady=5, padx=5, column=1, row=0)
    username_pre.grid(pady=5, padx=(10, 0), column=0, row=1, sticky=DI_VAR['w'])
    username_entry.grid(pady=5, padx=5, column=1, row=1)
    encrypt_pass_note = tkt.add_text_label(userinfo_frame, text=LN.password_reminder_txt, font=tkt.FONTS_smaller,
                                           foreground=tkt.color_blue, pack=False)
    encrypt_pass_note.grid(pady=5, padx=(10, 0), column=0, columnspan=5, row=2, sticky=DI_VAR['nw'])

    validation_func = app.register(lambda var: fn.validate_with_regex(var, valid_username_regex) is True)
    username_entry.config(validate='none', validatecommand=(validation_func, '%P'))
    # Regex
    portable_fs_chars = r'a-zA-Z0-9._-'
    _name_base = r'[a-zA-Z0-9._][' + portable_fs_chars + r']{0,30}([' + portable_fs_chars + r']|\$)?'
    valid_username_regex = r'^' + _name_base + '$'   # A regex for user and group names.

    tkt.var_tracer(tk_var.username, "write", lambda *args: username_entry.validate())

    def next_btn_action(*args):
        username_entry.validate()
        syntax_invalid = 'invalid' in username_entry.state()
        if syntax_invalid:
            return -1
        GV.KICKSTART.username = username_entry.get()
        GV.KICKSTART.fullname = fullname_entry.get()

        return page_verify.run(app)
