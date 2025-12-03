# Copilot Instructions for BeanieDeploy Project

## Error Checking and Linting

**Always use native VS Code API tools** (`get_errors`) for checking errors/warnings instead of terminal commands like `ruff check` or `mypy`. This ensures consistency with VS Code's Problems panel and avoids discrepancies.

- Use `get_errors(filePaths=["path/to/file.py"])` for specific files
- Use terminal commands only for execution/testing, never for linting/error checking

## Sudo

Recent builds of Windows 11 have added native sudo support, and it is enabled on this system.

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