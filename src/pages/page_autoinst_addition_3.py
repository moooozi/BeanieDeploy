import customtkinter as ctk
from templates.generic_page_layout import GenericPageLayout
from models.page import Page, PageValidationResult
import tkinter as tk
from tkinter_templates import FrameContainer, TextLabel, FONTS_smaller, color_blue, var_tracer


class PageAutoinstAddition3(Page):
    def __init__(self, parent, page_name: str, *args, **kwargs):
        super().__init__(parent, page_name, *args, **kwargs)
        
        # Initialize kickstart if it doesn't exist
        if not self.state.installation.kickstart:
            from models.kickstart import Kickstart
            self.state.installation.kickstart = Kickstart()
            
        kickstart = self.state.installation.kickstart
        self.fullname = tk.StringVar(parent, kickstart.fullname if kickstart.fullname else "")
        self.username = tk.StringVar(parent, kickstart.username if kickstart.username else "")

    def init_page(self):
        # Get selected spin from state
        selected_spin = self.state.installation.selected_spin
        if not selected_spin:
            self.logger.error("No spin selected when initializing user account page")
            return

        page_layout = GenericPageLayout(
            self,
            self.LN.title_autoinst4,
            self.LN.btn_next,
            lambda: self.navigate_next(),
            self.LN.btn_back,
            lambda: self.navigate_previous(),
        )
        page_frame = page_layout.content_frame

        
        userinfo_frame = FrameContainer(page_frame)
        userinfo_frame.pack(fill="x", expand=1)
        
        fullname_pre = TextLabel(
            userinfo_frame,
            text=self.LN.entry_fullname,
            font=FONTS_smaller,
        )
        self.fullname_entry = ctk.CTkEntry(
            userinfo_frame, width=200, textvariable=self.fullname
        )
        username_pre = TextLabel(
            userinfo_frame,
            text=self.LN.entry_username,
            font=FONTS_smaller,
        )
        self.username_entry = ctk.CTkEntry(
            userinfo_frame, width=200, textvariable=self.username
        )

        fullname_pre.grid(pady=5, padx=(10, 0), column=0, row=0, sticky=self.DI_VAR.w)
        self.fullname_entry.grid(pady=5, padx=5, column=1, row=0)
        username_pre.grid(pady=5, padx=(10, 0), column=0, row=1, sticky=self.DI_VAR.w)
        self.username_entry.grid(pady=5, padx=5, column=1, row=1)
        
        encrypt_pass_note = TextLabel(
            userinfo_frame,
            text=self.LN.password_reminder_txt,
            font=FONTS_smaller,
            foreground=color_blue,
        )
        encrypt_pass_note.grid(
            pady=5, padx=(10, 0), column=0, columnspan=5, row=2, sticky=self.DI_VAR.nw
        )

        # Setup username validation
        # Note: CTkEntry doesn't support built-in validation like tkinter Entry
        # We'll validate manually in validate_input()

        var_tracer(
            self.username, "write", lambda *args: self._on_username_change()
        )

    def _on_username_change(self):
        """Called when username changes."""
        # Could implement real-time feedback here if needed
        pass

    def _validate_username_format(self, username: str) -> bool:
        """Validate username format using regex."""
        import re
        # Regex for valid usernames
        portable_fs_chars = r"a-zA-Z0-9._-"
        _name_base = (
            r"[a-zA-Z0-9._]["
            + portable_fs_chars
            + r"]{0,30}(["
            + portable_fs_chars
            + r"]|\$)?"
        )
        valid_username_regex = r"^" + _name_base + "$"
        
        return bool(re.match(valid_username_regex, username))

    def validate_input(self) -> PageValidationResult:
        """Validate the user account information."""
        # Check if this is GNOME - no validation needed
        selected_spin = self.state.installation.selected_spin
        if selected_spin and selected_spin.desktop == "GNOME":
            return PageValidationResult(True)
            
        # Validate username format for non-GNOME cases
        if not hasattr(self, 'username_entry'):
            return PageValidationResult(False, "Page not properly initialized")
            
        # Username is required
        username = self.username_entry.get().strip()
        if not username:
            return PageValidationResult(False, "Username is required")
            
        # Validate username format
        if not self._validate_username_format(username):
            return PageValidationResult(False, "Username format is invalid")
            return PageValidationResult(False, "Username is required")
            
        return PageValidationResult(True)

    def on_next(self):
        """Save the user account information to state."""
        kickstart = self.state.installation.kickstart
        if kickstart:
            # Check if we have form fields (normal case) or if this is GNOME (skipped case)
            selected_spin = self.state.installation.selected_spin
            if selected_spin and selected_spin.desktop == "GNOME":
                # GNOME allows user account creation during initial start tour
                kickstart.username = ""
                kickstart.fullname = ""
                self.logger.info("GNOME detected: skipping user account creation")
            elif hasattr(self, 'username_entry') and hasattr(self, 'fullname_entry'):
                # Normal case with form fields
                kickstart.username = self.username_entry.get().strip()
                kickstart.fullname = self.fullname_entry.get().strip()
                self.logger.info(f"User account: username={kickstart.username}, fullname={kickstart.fullname}")
            else:
                # Fallback case
                kickstart.username = ""
                kickstart.fullname = ""
                self.logger.warning("User account page not properly initialized")
