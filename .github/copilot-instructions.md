# Copilot Instructions for BeanieDeploy Project

## App starting point

- Run `.venv/Scripts/python.exe src/main.py` to start the application.
- For other scripts, run them similarly from the `.venv/Scripts/python.exe` interpreter.

## Error Checking and Linting

**Always use native VS Code API tools** (`get_errors`) for checking errors/warnings instead of terminal commands like `ruff check` or `mypy`. This ensures consistency with VS Code's Problems panel and avoids discrepancies.

- Use `get_errors(filePaths=["path/to/file.py"])` for specific files
- Use terminal commands only for execution/testing, never for linting/error checking

## Sudo

Recent Windows 11 builds have native sudo support, and it is enabled on this system.

### Purpose and Usage
- Standard terminal runs without elevation, but some tasks need admin rights.
- Usage: `sudo <command> [args...]`

### Sudo Dos and Don'ts

**Don't:**
- `sudo echo "Hello world"` (echo is a cmdlet, not a binary)

**Do:**
- `sudo powershell -Command 'echo "Hello World"'` (powershell is a binary)
- `sudo cmd /c 'echo Hello World'` (cmd is a binary)
- `sudo bcdedit /enum` (bcdedit is a binary)

## `requers` Library Usage

`requers` is a Rust-based HTTP client library with a Python interface. It provides a `get` method that resembles `requests.get`, and `download_file` for large file downloads.

### Instructions

- `requers` is located in `lib/requers`.
- When you modify `requers`, re-build and re-install with a single command: `.venv/Scripts/python.exe -m pip install lib/requers`


## CustomTkinter
The project uses a modified CustomTkinter, with performance optimized widgets. These are:
- `CTkSimpleLabel`: Must always be used instead of `CTkLabel`.
- `CTkContainer`:  Simplified version of `CTkFrame`; should generally be preferred.
