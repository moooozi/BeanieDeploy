# Password setup service for first-boot user password configuration
# requires: log_dir, username

%post --interpreter=/usr/bin/python --logfile={log_dir}/post_password_setting --nochroot
import subprocess
import tkinter as tk
from tkinter import ttk

# Read username
username = "{username}"

def hash_password_yescrypt(password):
    result = subprocess.run(
        ["mkpasswd", "-m", "yescrypt", password],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()

def validate(*args):
    if password.get() and password.get() == confirm.get():
        btn_continue.config(state="normal")
    else:
        btn_continue.config(state="disabled")

def finish():
    pw = password.get()
    hashed = hash_password_yescrypt(pw)

    subprocess.run(
        ["chroot", "/mnt/sysimage", "chpasswd", "-e"],
        input=f"{username}:{hashed}\n",
        text=True,
        check=True
    )

    root.destroy()

root = tk.Tk()
root.title("Set Password")
root.protocol("WM_DELETE_WINDOW", lambda: None)

password = tk.StringVar()
confirm = tk.StringVar()
password.trace_add("write", validate)
confirm.trace_add("write", validate)

ttk.Label(root, text=f"Enter user password for {username}:").pack(pady=(10, 0))
ttk.Entry(root, textvariable=password, show="*", width=30).pack()

ttk.Label(root, text="Confirm password:").pack(pady=(10, 0))
ttk.Entry(root, textvariable=confirm, show="*", width=30).pack()

btn_continue = ttk.Button(root, text="Continue", state="disabled", command=finish)
btn_continue.pack(pady=20)

root.mainloop()
%end
