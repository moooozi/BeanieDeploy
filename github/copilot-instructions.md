# Copilot Instructions for BeanieDeploy Project

## Elevated Shell Tool

The project includes an elevated shell helper at `./github/copilot-tools/elevated_shell.py` for running commands that require administrator privileges.

### Why it exists
- The standard Copilot terminal/shell runs without elevation, but some tasks (like system configuration, firmware access, disk partitioning, etc.) require admin rights.
- This tool allows running such commands securely using the project's privilege management system, which communicates with an elevated helper process via named pipes.

### How to use
- **Only use this tool when a command explicitly requires elevated privileges** (e.g., `bcdedit`, `diskpart`, system registry modifications).
- For all other commands, use the standard shell/terminal.
- Run with: `python github/copilot-tools/elevated_shell.py "<command>"`
- Example: `python github/copilot-tools/elevated_shell.py "bcdedit /enum firmware"`

### Important Notes
- Ensure the Python virtual environment is activated before running (use the configured venv at `.venv`).
- The tool captures and displays stdout/stderr and exits with the command's return code.