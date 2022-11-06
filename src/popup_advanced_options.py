import tkinter as tk
import tkinter.ttk as ttk
import tkinter_templates as tkt
import translations.en as LN
import global_tk_vars as tk_var


def run(parent):
    pop, pop_frame = tkt.open_popup(parent, x_size=500, y_size=700)
    tkt.generic_page_layout(pop_frame, "Advanced Settings", "Confirm", lambda *args: pop.destroy(),)
    auto_install_frame = tk.Frame(pop_frame)
    encryption_frame = tk.Frame(auto_install_frame)
    encrypt_pass_toggle = tkt.add_check_btn(encryption_frame, LN.entry_encrypt_passphrase, tk_var.encrypt_pass_toggle_var, lambda: show_options())
    encrypt_passphrase_entry = ttk.Entry(encryption_frame, show="\u2022", width=10, textvariable=tk_var.encrypt_passphrase_var)
    tpm_unlock = tkt.add_check_btn(encryption_frame, LN.encryption_tpm_unlock, tk_var.encryption_tpm_unlock_toggle_var, pack=False)
    if tk_var.enable_encryption_toggle_var.get():
        encryption_frame.pack(anchor='w')
    else:
        encryption_frame.pack_forget()

    def show_options():
        if tk_var.install_method_var.get() != 'custom':
            auto_install_frame.pack(anchor='w')
        else:
            auto_install_frame.pack_forget()
        if tk_var.encrypt_pass_toggle_var.get():
            encrypt_passphrase_entry.pack()
            tpm_unlock.pack()
        else:
            encrypt_passphrase_entry.pack_forget()
            tpm_unlock.pack_forget()
    show_options()

    pop.wait_window()
