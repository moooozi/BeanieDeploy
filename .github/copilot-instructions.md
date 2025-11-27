# Copilot Instructions for BeanieDeploy Project

## Elevated Command Tool

The project includes an elevated command helper at `./github/copilot-tools/elevated_cmd.py` for running commands that require administrator privileges.

### Why it exists
- The standard Copilot terminal/shell runs without elevation, but some tasks (like system configuration, firmware access, disk partitioning, etc.) require admin rights.
- This tool allows running such commands securely using the project's privilege management system, which communicates with an elevated helper process via named pipes.

### How to use
- **Only use this tool when a command explicitly requires elevated privileges** (e.g., `bcdedit`, `diskpart`, system registry modifications).
- For all other commands, use the standard shell/terminal.
- Run with: `& C:/Users/mozi/repo/BeanieDeploy/.venv/Scripts/python.exe .github/copilot-tools/elevated_cmd.py <command> [args...]`
- Example: `& C:/Users/mozi/repo/BeanieDeploy/.venv/Scripts/python.exe .github/copilot-tools/elevated_cmd.py mountvol "C:\Temp\Mount" "\\?\Volume{guid}"`

### Important Notes
- Ensure the Python virtual environment is activated before running (use the configured venv at `.venv`).
- The tool captures and displays stdout/stderr and exits with the command's return code.