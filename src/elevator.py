import ctypes
import subprocess
import sys
import functions as fn


class Elevator:

    elevated_object = None

    def __init__(self):
        self.elevated_object = None

    def create_elevated_object(self, command):
        if not self.is_elevated:
            if self.elevated_object is None:
                self.elevated_object = subprocess.Popen(['powershell.exe', 'Start-Process',sys.executable,'-Verb RunAs', '-ArgumentList "-u -c import elevator"',],stdout=subprocess.PIPE,stdin=subprocess.PIPE)        
            self.elevated_object.communicate(input=command.encode('utf-8'))
        else:
            process =subprocess.Popen([command,],stdin=subprocess.PIPE)
            process.communicate()
            
    def is_elevated():
        return ctypes.windll.shell32.IsUserAnAdmin()
    
    def elevate_this(self, args):
        args = " ".join(sys.argv) + " " + args
        if not self.is_admin():
            result = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, args, None, 1)
            if result <= 32:
                #error = ctypes.windll.kernel32.GetLastError()
                #print(f"Error code: {error}")
                return False
            else:
                return True
        else:
            return True
        
if __name__ == "__main__":
    e = Elevator()
    e.elevate('cmd')
    