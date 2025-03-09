import ctypes
import subprocess
import sys
import json


def is_admin():
    return ctypes.windll.shell32.IsUserAnAdmin()


def run_command(command):
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout, result.stderr


if __name__ == "__main__":
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()

    while True:
        try:
            input_data = input()
            if input_data.strip().lower() == "exit":
                break
            command = json.loads(input_data)
            stdout, stderr = run_command(command)
            output = {"stdout": stdout, "stderr": stderr}
            print(json.dumps(output))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
