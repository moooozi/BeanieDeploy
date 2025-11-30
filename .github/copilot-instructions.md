# Copilot Instructions for BeanieDeploy Project

## Error Checking and Linting

**Always use native VS Code API tools** (`get_errors`) for checking errors/warnings instead of terminal commands like `ruff check` or `mypy`. This ensures consistency with VS Code's Problems panel and avoids discrepancies.

- Use `get_errors(filePaths=["path/to/file.py"])` for specific files
- Use terminal commands only for execution/testing, never for linting/error checking

## Elevated Command Tool

The project includes an elevated command helper at `./github/copilot-tools/elevated_cmd.py` for running commands that require administrator privileges.

### Purpose and Usage
- Standard Copilot terminal runs without elevation, but some tasks need admin rights.
- Use this tool for commands requiring elevated privileges (e.g., `bcdedit`, registry modifications); use standard shell for others.
- Run with: `& C:/Users/mozi/repo/BeanieDeploy/.venv/Scripts/python.exe .github/copilot-tools/elevated_cmd.py <command> [args...]`
- Example: `& C:/Users/mozi/repo/BeanieDeploy/.venv/Scripts/python.exe .github/copilot-tools/elevated_cmd.py bcdedit /enum`
- Activate the Python virtual environment (`.venv`) before running; captures stdout/stderr and exits with command's return code.