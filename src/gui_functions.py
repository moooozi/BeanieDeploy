import multiprocessing
import queue
import subprocess
import functions as fn
import atexit

GLOBAL_QUEUE = multiprocessing.Queue()


def run_async_function(function, queue=GLOBAL_QUEUE, args=(), kwargs={}):
    """
    run a function without blocking the GUI
    :param function: the function
    :param queue: the Queue object
    :param args: arguments to be passed to th function
    :param kwargs: keyworded-arguments to be passed to th function
    :return: returns the first output from queue if no callback is specified, or the return of the callback if specified
    """
    if queue: kwargs['queue'] = queue
    while queue.qsize(): queue.get()
    procces = multiprocessing.Process(target=function, args=args, kwargs=kwargs)
    procces.start()
    atexit.register(procces.terminate)
    


def handle_queue_result(tkinter, callback=None, wait_for_result=None, queue=GLOBAL_QUEUE):
    """

    :param tkinter: the tkinter instance
    :param callback: callback function to handle Queue communication
    :param queue: the Queue object
    :param wait_for_result: wait for certain queue output
    :return: returns the first output from queue if no callback is specified, or the return of the callback if specified
    """
    if callback and wait_for_result:
        raise AttributeError('Cannot use callback and wait_for_result simultaneously')
    while True:
        while not queue.qsize(): tkinter.after(100, tkinter.update())
        queue_out = queue.get()
        if callback:
            call = callback(queue_out)
            if call: return call
        elif wait_for_result and isinstance(wait_for_result, str):
            if queue_out == wait_for_result:
                return queue_out
        elif wait_for_result and isinstance(wait_for_result, (tuple, list)):
            if queue_out in wait_for_result:
                return queue_out
        else:
            return queue_out


def detect_darkmode_in_windows():
    try:
        import winreg
    except ImportError:
        return False
    registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    reg_keypath = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize'
    try:
        reg_key = winreg.OpenKey(registry, reg_keypath)
    except FileNotFoundError:
        return False

    for i in range(1024):
        try:
            value_name, value, _ = winreg.EnumValue(reg_key, i)
            if value_name == 'AppsUseLightTheme':
                return value == 0
        except OSError:
            break
    return False


def get_first_tk_parent(widget):
    parent = widget
    while parent.master is not None:
        parent = parent.master
    return parent

def run_command(cmd):
    return subprocess.run(cmd, text=True, check=True, capture_output=True,creationflags=DETACHED_PROCESS_FLAG)

def _read_cmd_output(command, output_queue: multiprocessing.Queue):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=DETACHED_PROCESS_FLAG)
    output = process.stdout.readlines() or ''
    while output and process.poll() is None:
        output_queue.put(output)

def _read_function_output(function, output_queue: multiprocessing.Queue, args, kwargs):
    output = function(*args, **kwargs)
    output_queue.put(output)


def run_async_proccess(function=None, cmd=None, args=(), kwargs={}):
    if not (bool(cmd) ^ bool(function)):
        raise ValueError("Either 'cmd' or 'function' must be provided")
    q = multiprocessing.Queue()
    if cmd:
        if isinstance(cmd, str):
            cmd = [cmd]
        command = cmd + list(args) + [f'{key}={value}' for key, value in kwargs.items()]
        p = multiprocessing.Process(target=_read_cmd_output, args=(command,q))
        p.start()
    if function:
        p = multiprocessing.Process(target=_read_function_output, args=(function, q, args, kwargs))
        p.start()
        
    return q

def run_async_process_infinite(tkinter, function=None, cmd=None, args=(), kwargs={}, interval_in_seconds=2, timeout_in_seconds=1, update_frequency_in_ms=100, callback=None):
    if not (bool(cmd) ^ bool(function)):
        raise ValueError("Either 'cmd' or 'function' must be provided")
    q = run_async_proccess(function=function, cmd=cmd, args=args, kwargs=kwargs)
    retry_count = timeout_in_seconds * 1000 / update_frequency_in_ms
    if callback is not None:
        wait_and_handle_queue_output( q, callback, update_frequency_in_ms, retry_count )
    tkinter.after(interval_in_seconds * 1000, self.run_async_process_infinite, function, cmd, args, kwargs, interval_in_seconds, timeout_in_seconds, update_frequency_in_ms, callback)


def wait_and_handle_queue_output(self, output_queue: multiprocessing.Queue, callback, frequency=100, retry_count=0):
    try:
        output = output_queue.get_nowait()
        callback(output)
    except queue.Empty:
        if retry_count:
            self.master.after(frequency, self.wait_and_handle_queue_output, output_queue, callback, frequency, retry_count - 1)
    