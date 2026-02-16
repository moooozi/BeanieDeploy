#!/usr/bin/python3
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import ttk

# Read username from file
with Path("/etc/beanie_should_set_password").open() as f:
    username = f.read().strip()


def hash_password_yescrypt(password):
    result = subprocess.run(
        ["mkpasswd", "-m", "yescrypt", password],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def validate(*_args):
    if password.get() and password.get() == confirm.get():
        btn_continue.config(state="normal")
    else:
        btn_continue.config(state="disabled")


def finish():
    pw = password.get()
    hashed = hash_password_yescrypt(pw)

    subprocess.run(
        ["chpasswd", "-e"], input=f"{username}:{hashed}\n", text=True, check=True
    )

    root.destroy()

    # Clean up: delete service, marker file, and script itself
    Path("/etc/systemd/system/beanie-password-setup.service").unlink()
    Path("/etc/beanie_should_set_password").unlink()
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "start", "display-manager.service"], check=True)
    Path("/usr/local/bin/beanie-password-setup").unlink()


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
