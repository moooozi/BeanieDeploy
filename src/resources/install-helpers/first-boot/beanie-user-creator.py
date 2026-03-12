#!/usr/bin/env python3
"""
User Creation TUI — stdlib only (curses).

CURSES QUICK-REFERENCE (the three patterns used throughout):

  Color pairs   curses requires you to declare color combos upfront as numbered
                pairs: init_pair(id, fg, bg).  Reference them later with
                color_pair(id).  id 1–7 are set up at the top of main().

  Attributes    curses has no styled-print; you bracket every draw call:
                  stdscr.attron(color_pair(3) | A_BOLD)   ← turn ON
                  stdscr.addstr(y, x, "text")              ← draw
                  stdscr.attroff(color_pair(3) | A_BOLD)  ← turn OFF

  Centering     x = left_edge + (total_width - text_width) // 2
                same idea as CSS margin:auto, just explicit.
"""
import curses
import locale
import os
import re
import subprocess
import sys

# Larger console font used when running on a Linux VT (e.g. Anaconda installer).
# latarcyrheb-sun32 is a standard large font shipped with the kbd package on
# every Fedora system.  Change to e.g. ter-v32b if you prefer Terminus.
VT_FONT_LARGE   = "latarcyrheb-sun32"
VT_FONT_DEFAULT = ""  # empty string → setfont restores the compiled-in default
INPUT_MAX = 128  # max password length accepted
DEFAULTS_FILE = "/etc/beanie_user_creator"


def _read_defaults() -> tuple[str, str]:
    """Return (username, fullname) from DEFAULTS_FILE, or ('', '') if missing."""
    try:
        with open(DEFAULTS_FILE) as f:
            data = {}
            for line in f:
                line = line.strip()
                if "=" in line:
                    k, _, v = line.partition("=")
                    data[k.strip().upper()] = v.strip()
        return data.get("USERNAME", ""), data.get("FULLNAME", "")
    except OSError:
        return "", ""


def hash_yescrypt(password: str) -> str:
    result = subprocess.run(
        ["mkpasswd", "-m", "yescrypt", password],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


# Linux username rules: starts with letter or underscore, followed by
# letters/digits/underscores/dashes/dots, max 32 chars total.
_USERNAME_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9._-]{0,31}$')

def _username_error(name: str) -> str | None:
    """Return a human-readable error string, or None if the name is valid."""
    if not name:
        return None  # empty = not filled in yet, not an error
    if name[0].isdigit():
        return "Username must not start with a digit"
    if not _USERNAME_RE.match(name):
        return "Only letters, digits, . _ - allowed"
    return None


def _w(fn, *args, **kwargs):
    """Ignore curses out-of-bounds write errors (e.g. bottom-right corner)."""
    try:
        fn(*args, **kwargs)
    except curses.error:
        pass


def draw_ui(stdscr, username: list, fullname: list, pw1: list, pw2: list, field: int, status: str = ""):
    stdscr.erase()
    max_h, max_w = stdscr.getmaxyx()

    BOX_W  = 54
    BOX_H  = 13   # 4 input rows + match indicator + button + spacing
    LBL_W  = 17   # all labels are exactly 17 chars — keeps input columns aligned
    INPUT_W = BOX_W - 4 - LBL_W  # 33 chars wide
    bx = max(0, (max_w - BOX_W) // 2)
    by = max(2, (max_h - BOX_H - 2) // 2)  # ≥2 reserves space for title above

    CP = curses.color_pair
    B, D, R = curses.A_BOLD, curses.A_DIM, curses.A_REVERSE

    # ── Title ──────────────────────────────────────────────────────────────
    title = "Create your user account"
    _w(stdscr.attron,  CP(1) | B)
    _w(stdscr.addstr,  by - 2, bx + (BOX_W - len(title)) // 2, title)
    _w(stdscr.attroff, CP(1) | B)

    # ── Box ────────────────────────────────────────────────────────────────
    _w(stdscr.attron, CP(1))
    _w(stdscr.addstr, by, bx, "╭" + "─" * (BOX_W - 2) + "╮")
    for row in range(1, BOX_H - 1):
        _w(stdscr.addstr, by + row, bx, "│" + " " * (BOX_W - 2) + "│")
    _w(stdscr.addstr, by + BOX_H - 1, bx, "╰" + "─" * (BOX_W - 2) + "╯")
    _w(stdscr.attroff, CP(1))

    # ── Input fields ───────────────────────────────────────────────────────
    # Each entry: (row_offset, label_17_chars, buffer, masked)
    fields_def = [
        (1,  "Username:        ", username, False),
        (3,  "Full name:       ", fullname, False),
        (5,  "New password:    ", pw1,      True),
        (7,  "Confirm password:", pw2,      True),
    ]

    for i, (row_off, lbl, buf, masked) in enumerate(fields_def):
        _w(stdscr.attron,  CP(2))
        _w(stdscr.addstr,  by + row_off, bx + 2, lbl)
        _w(stdscr.attroff, CP(2))

        text = "".join(buf)
        visible = ("*" * len(text)) if masked else text
        display = visible[-INPUT_W:].ljust(INPUT_W)
        attr = (CP(6) | B) if field == i else CP(7)
        _w(stdscr.attron,  attr)
        _w(stdscr.addstr,  by + row_off, bx + 2 + LBL_W, display)
        _w(stdscr.attroff, attr)

    # ── Status line (username errors, password match, or apply errors) ───────
    uname_err = _username_error("".join(username))
    can_apply = bool(username) and uname_err is None and bool(pw1) and pw1 == pw2
    if status:
        ind = status[:BOX_W - 4]
        _w(stdscr.attron,  CP(4) | B)
        _w(stdscr.addstr,  by + 9, bx + 2, ind)
        _w(stdscr.attroff, CP(4) | B)
    elif uname_err:
        _w(stdscr.attron,  CP(4) | B)
        _w(stdscr.addstr,  by + 9, bx + (BOX_W - len(uname_err)) // 2, uname_err)
        _w(stdscr.attroff, CP(4) | B)
    elif pw1 and pw2:
        ind, cp = (
            ("✓  Passwords match",        CP(3) | B) if pw1 == pw2
            else ("✗  Passwords do not match", CP(4) | B)
        )
        _w(stdscr.attron,  cp)
        _w(stdscr.addstr,  by + 9, bx + (BOX_W - len(ind)) // 2, ind)
        _w(stdscr.attroff, cp)

    # ── Apply button ───────────────────────────────────────────────────────
    btn  = "[ Apply ]"
    bx_b = bx + (BOX_W - len(btn)) // 2
    cp_b = (CP(3) | B | (R if field == 4 else 0)) if can_apply else (CP(4) | D)
    _w(stdscr.attron,  cp_b)
    _w(stdscr.addstr,  by + 11, bx_b, btn)
    _w(stdscr.attroff, cp_b)

    # ── Hint ───────────────────────────────────────────────────────────────
    hint = "Tab/Arrows · navigate    Enter · confirm    Esc · quit"
    _w(stdscr.attron,  D)
    _w(stdscr.addstr,  by + BOX_H + 1, bx + (BOX_W - len(hint)) // 2, hint)
    _w(stdscr.attroff, D)

    # ── Cursor position ────────────────────────────────────────────────────
    row_offsets = [1, 3, 5, 7]  # matches fields_def order
    try:
        if field < 4:
            curses.curs_set(1)
            buf = [username, fullname, pw1, pw2][field]
            stdscr.move(by + row_offsets[field], bx + 2 + LBL_W + min(len(buf), INPUT_W))
        else:
            curses.curs_set(0)
    except curses.error:
        pass

    stdscr.refresh()
    return can_apply, INPUT_W


def main(stdscr, default_username: str = "", default_fullname: str = ""):
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN,   -1)                 # title / border
    curses.init_pair(2, curses.COLOR_WHITE,  -1)                 # labels
    curses.init_pair(3, curses.COLOR_GREEN,  -1)                 # match / success
    curses.init_pair(4, curses.COLOR_RED,    -1)                 # mismatch / error
    curses.init_pair(5, curses.COLOR_YELLOW, -1)                 # (reserved)
    curses.init_pair(6, curses.COLOR_BLACK,  curses.COLOR_CYAN)  # focused input
    curses.init_pair(7, curses.COLOR_BLACK,  curses.COLOR_WHITE) # unfocused input
    stdscr.keypad(True)

    username: list[str] = list(default_username)
    fullname: list[str] = list(default_fullname)
    pw1: list[str] = []
    pw2: list[str] = []
    field = 0   # 0=username  1=fullname  2=pw1  3=pw2  4=apply
    status = ""  # error message shown in the status line; cleared on next keypress
    uname = ""

    while True:
        can_apply, INPUT_W = draw_ui(stdscr, username, fullname, pw1, pw2, field, status)
        key = stdscr.getch()
        status = ""  # clear after the user acts

        if key == curses.KEY_RESIZE:
            continue

        if key in (9, curses.KEY_DOWN):           # Tab / ↓ → next field
            if field < 3:
                field += 1
            elif field == 3 and can_apply:
                field = 4

        elif key == curses.KEY_UP:                # ↑ → previous field
            if field > 0:
                field -= 1

        elif key in (curses.KEY_ENTER, 10, 13):  # Enter
            if field < 3:
                field += 1
            elif field == 3 and can_apply:
                field = 4
            elif field == 4 and can_apply:
                uname = "".join(username)
                fname = "".join(fullname)
                try:
                    subprocess.run(
                        ["useradd", "-G", "wheel", "-c", fname, "-m", uname],
                        capture_output=True, text=True, check=True,
                    )
                    hashed = hash_yescrypt("".join(pw1))
                    subprocess.run(
                        ["chpasswd", "-e"],
                        input=f"{uname}:{hashed}\n",
                        text=True, check=True,
                    )
                    break  # success
                except subprocess.CalledProcessError as e:
                    # Stay in form; show the error from stderr (or fallback to str(e))
                    status = (e.stderr.strip() if hasattr(e, 'stderr') and e.stderr else str(e))
                    field = 0  # send user back to first field to correct

        elif key in (curses.KEY_BACKSPACE, 127, 8):
            bufs = [username, fullname, pw1, pw2]
            if field < 4 and bufs[field]:
                bufs[field].pop()

        elif 32 <= key <= 126:                    # Printable ASCII only
            if field == 0 and key != 32 and len(username) < INPUT_MAX:  # no spaces in username
                username.append(chr(key))
            elif field == 1 and len(fullname) < INPUT_MAX:
                fullname.append(chr(key))
            elif field == 2 and len(pw1) < INPUT_MAX:
                pw1.append(chr(key))
            elif field == 3 and len(pw2) < INPUT_MAX:
                pw2.append(chr(key))

    # ── Success message (only reached on clean apply) ──────────────────────
    curses.curs_set(0)
    stdscr.erase()
    max_h, max_w = stdscr.getmaxyx()
    msg = f"✓  User '{uname}' created successfully!"
    _w(stdscr.attron,  curses.color_pair(3) | curses.A_BOLD)
    _w(stdscr.addstr,  max_h // 2, max(0, (max_w - len(msg)) // 2), msg)
    _w(stdscr.attroff, curses.color_pair(3) | curses.A_BOLD)
    stdscr.refresh()
    curses.napms(2000)
    try:
        os.unlink(DEFAULTS_FILE)
    except OSError:
        pass
    return 0


def _on_linux_vt() -> str | None:
    """Return the VT path if stdout is a real Linux VT (/dev/ttyN), else None."""
    try:
        tty = os.ttyname(sys.stdout.fileno())
        if tty.startswith("/dev/tty") and tty[len("/dev/tty"):].isdigit():
            return tty
    except Exception:
        pass
    return None


def _setfont(font: str, console: str = "") -> None:
    """Call setfont, silently ignore any error (missing binary / font)."""
    try:
        cmd = ["setfont"]
        if console:
            cmd += ["-C", console]
        if font:
            cmd.append(font)
        subprocess.run(cmd, check=True, capture_output=True)
    except Exception:
        pass


if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, "")   # enable UTF-8 for box-drawing chars

    default_username, default_fullname = _read_defaults()

    vt_path = _on_linux_vt()
    if vt_path:
        _setfont(VT_FONT_LARGE, vt_path)

    try:
        rc = curses.wrapper(lambda stdscr: main(stdscr, default_username, default_fullname))
    finally:
        if vt_path:
            _setfont(VT_FONT_DEFAULT, vt_path)

    sys.exit(rc)