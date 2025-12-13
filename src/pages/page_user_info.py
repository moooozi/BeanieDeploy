import logging
import tkinter as tk

import vgkit as vgk
import win32api

from models.page import Page, PageValidationResult
from multilingual import _


def get_username():
    """Get the current Windows username, sanitized for Fedora compatibility."""
    try:
        username = win32api.GetUserName().lower()
        # Ensure it starts with a letter
        if username and not username[0].isalpha():
            username = "user" + username
        # Remove invalid characters and limit length
        import re

        username = re.sub(r"[^a-z0-9_-]", "", username)[:32]
        # Ensure it matches the regex
        if re.match(r"^[a-z][a-z0-9_-]{0,31}$", username):
            return username
        return ""
    except Exception as e:
        logging.warning(f"Failed to get username: {e}")
        return ""


def get_full_name():
    """Get the current Windows user's full name."""
    try:
        return win32api.GetUserNameEx(win32api.NameDisplay)
    except Exception as e:
        logging.warning(f"Failed to get full name: {e}")
        return ""


class PageUserInfo(Page):
    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)

        # Initialize user info variables with Windows defaults
        self.full_name_var = tk.StringVar(value=get_full_name())
        self.username_var = tk.StringVar(value=get_username())

    def init_page(self):
        self.page_manager.set_title(_("user.info.title"))

        # Full Name entry
        full_name_label = vgk.Label(
            self,
            text=_("entry.fullname"),
            font=self._ui.fonts.smaller,
        )
        full_name_label.grid(row=1, column=0, sticky=self._ui.di.w, pady=(10, 5))

        self.full_name_entry = vgk.Entry(
            self,
            textvariable=self.full_name_var,
            width=300,
        )
        self.full_name_entry.grid(row=2, column=0, sticky=self._ui.di.w, pady=(0, 10))

        # Username entry
        username_label = vgk.Label(
            self,
            text=_("entry.username"),
            font=self._ui.fonts.smaller,
        )
        username_label.grid(row=3, column=0, sticky=self._ui.di.w, pady=(10, 5))

        self.username_entry = vgk.Entry(
            self,
            textvariable=self.username_var,
            width=300,
        )
        self.username_entry.grid(row=4, column=0, sticky=self._ui.di.w, pady=(0, 10))
        self.username_entry.bind("<KeyRelease>", self._on_username_change)

        # Error label for validation messages
        self.error_label = vgk.Label(
            self,
            text="",
            font=self._ui.fonts.smaller,
            text_color=self._ui.colors.red,
            justify=self._ui.di.l,
        )
        self.error_label.grid(row=5, column=0, sticky=self._ui.di.w, pady=(0, 10))
        self.error_label.grid_remove()  # Hide by default

        self.grid_columnconfigure(0, weight=1)

        # Configure grid for vertical centering
        self.grid_rowconfigure(0, weight=1)  # Top spacer
        self.grid_rowconfigure(6, weight=1)  # Bottom spacer

    def validate_input(self) -> PageValidationResult:
        """Validate that username is filled and valid, full name is optional."""
        import re

        username = self.username_var.get().strip()

        if not username:
            return PageValidationResult(False, _("user.username.required"))

        # Validate username: start with lowercase letter, only lowercase letters, numbers, hyphens, underscores, 1-32 chars
        username_regex = r"^[a-z][a-z0-9_-]{0,31}$"
        if not re.match(username_regex, username):
            return PageValidationResult(False, _("user.username.invalid"))

        # Full name is optional, no validation needed

        return PageValidationResult(True)

    def on_next(self):
        """Save the user info to state."""
        full_name = self.full_name_var.get().strip()
        username = self.username_var.get().strip()

        # Save to kickstart config
        kickstart = self.state.installation.kickstart
        if kickstart:
            kickstart.user_full_name = full_name
            kickstart.user_username = username

        logging.info(f"User info saved: full_name='{full_name}', username='{username}'")

    def show_validation_error(self, message: str):
        """Show validation error in the error label."""
        self.error_label.configure(text=message)
        self.error_label.grid()
        super().show_validation_error(message)

    def _on_username_change(self, _event):
        """Clear the error label when user types in username field."""
        self.error_label.grid_remove()
