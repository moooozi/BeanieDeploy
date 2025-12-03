# Copilot Instructions for BeanieDeploy Project

## Error Checking and Linting

**Always use native VS Code API tools** (`get_errors`) for checking errors/warnings instead of terminal commands like `ruff check` or `mypy`. This ensures consistency with VS Code's Problems panel and avoids discrepancies.

- Use `get_errors(filePaths=["path/to/file.py"])` for specific files
- Use terminal commands only for execution/testing, never for linting/error checking

## Sudo

Use `sudo` for running commands that require administrator privileges on Windows.

### Purpose and Usage
- Standard terminal runs without elevation, but some tasks need admin rights.
- Use `sudo` for commands requiring elevated privileges (e.g., `bcdedit`, registry modifications).
- Run with: `sudo <command> [args...]`
- Example: `sudo bcdedit /enum`