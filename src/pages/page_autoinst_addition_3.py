import customtkinter as ctk
from templates.generic_page_layout import GenericPageLayout
import tkinter_templates as tkt
from models.page import Page, PageValidationResult
import tkinter as tk


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
            
        # GNOME allows User account creation during initial start tour, so we use that and skip creating a user
        if selected_spin.desktop == "GNOME":
            kickstart = self.state.installation.kickstart
            if kickstart:
                kickstart.username = ""
            self.navigate_to("PageVerify")
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

        userinfo_frame = tkt.add_frame_container(page_frame, fill="x", expand=1)
        fullname_pre = tkt.add_text_label(
            userinfo_frame,
            text=self.LN.entry_fullname,
            font=tkt.FONTS_smaller,
            pack=False,
        )
        self.fullname_entry = ctk.CTkEntry(
            userinfo_frame, width=200, textvariable=self.fullname
        )
        username_pre = tkt.add_text_label(
            userinfo_frame,
            text=self.LN.entry_username,
            font=tkt.FONTS_smaller,
            pack=False,
        )
        self.username_entry = ctk.CTkEntry(
            userinfo_frame, width=200, textvariable=self.username
        )

        fullname_pre.grid(pady=5, padx=(10, 0), column=0, row=0, sticky=self.DI_VAR.w)
        self.fullname_entry.grid(pady=5, padx=5, column=1, row=0)
        username_pre.grid(pady=5, padx=(10, 0), column=0, row=1, sticky=self.DI_VAR.w)
        self.username_entry.grid(pady=5, padx=5, column=1, row=1)
        encrypt_pass_note = tkt.add_text_label(
            userinfo_frame,
            text=self.LN.password_reminder_txt,
            font=tkt.FONTS_smaller,
            foreground=tkt.color_blue,
            pack=False,
        )
        encrypt_pass_note.grid(
            pady=5, padx=(10, 0), column=0, columnspan=5, row=2, sticky=self.DI_VAR.nw
        )

        # Setup username validation
        validation_func = self.register(
            lambda var: self._validate_username_format(var)
        )
        self.username_entry.configure(
            validate="none", validatecommand=(validation_func, "%P")
        )

        tkt.var_tracer(
            self.username, "write", lambda *args: self.username_entry.validate()
        )

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
        # Validate username format
        if not hasattr(self, 'username_entry'):
            return PageValidationResult(False, "Page not properly initialized")
            
        self.username_entry.validate()
        syntax_invalid = "invalid" in self.username_entry.state()
        if syntax_invalid:
            return PageValidationResult(False, "Username format is invalid")
            
        # Username is required
        username = self.username_entry.get().strip()
        if not username:
            return PageValidationResult(False, "Username is required")
            
        return PageValidationResult(True)

    def on_next(self):
        """Save the user account information to state."""
        kickstart = self.state.installation.kickstart
        if kickstart:
            kickstart.username = self.username_entry.get().strip()
            kickstart.fullname = self.fullname_entry.get().strip()
            
            self.logger.info(f"User account: username={kickstart.username}, fullname={kickstart.fullname}")
