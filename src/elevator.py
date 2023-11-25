import ctypes
import subprocess
import sys
import functions as fn


class Elevator:

    elevated_object = None

    def __init__(self):
        self.is_elevated = fn.is_admin()
        self.elevated_object = None

    def elevate(self, command):
        if not self.is_elevated:
            if self.elevated_object is None:
                self.elevated_object = subprocess.Popen(['powershell.exe', 'Start-Process',sys.executable,'-Verb RunAs', '-ArgumentList "-u -c import elevator"',],stdout=subprocess.PIPE,stdin=subprocess.PIPE)        
            self.elevated_object.communicate(input=command.encode('utf-8'))
        else:
            process =subprocess.Popen([command,],stdin=subprocess.PIPE)
            process.communicate()

if __name__ == "__main__":
    e = Elevator()
    e.elevate('cmd')
    