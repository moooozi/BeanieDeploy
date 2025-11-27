#!/usr/bin/env python3
"""
Elevated Shell Helper - Run commands with elevated privileges.

Usage: elevated_shell.py <command>

Example: elevated_shell.py "bcdedit /enum firmware"
"""
import sys
import os

# Add src to Python path to import privilege_manager
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, '..', '..', 'src')
sys.path.insert(0, src_dir)

from services.privilege_manager import elevated

def main():
    if len(sys.argv) < 2:
        print("Usage: elevated_cmd.py <command>", file=sys.stderr)
        sys.exit(1)

    # Parse command line arguments properly
    import re
    # Split on spaces but preserve quoted strings
    args = re.findall(r'(?:[^\s"]|"(?:\\.|[^"])*")+', ' '.join(sys.argv[1:]))
    # Remove quotes from arguments
    args = [arg.strip('"') for arg in args]

    try:
        # Run the command with elevated privileges as a subprocess list
        proc = elevated.run(args, capture_output=True, text=True)

        # Print stdout
        if proc.stdout:
            print(proc.stdout, end='')

        # Print stderr to stderr
        if proc.stderr:
            print(proc.stderr, end='', file=sys.stderr)

        # Exit with the same return code
        sys.exit(proc.returncode)

    except Exception as e:
        print(f"Error running elevated command: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()