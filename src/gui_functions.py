import queue
import threading
import functions as fn

GLOBAL_QUEUE = queue.Queue()


def run_async_function(function, queue=GLOBAL_QUEUE, args=(), kwargs={}):
    """
    run a function without blocking the GUI
    :param function: the function
    :param queue: the Queue object
    :param args: arguments to be passed to th function
    :param kwargs: keyworded-arguments to be passed to th function
    :return: returns the first output from queue if no callback is specified, or the return of the callback if specified
    """
    if queue:
        kwargs["queue"] = queue
    while queue.qsize():
        queue.get()
    procces = threading.Thread(target=function, args=args, kwargs=kwargs)
    procces.start()


def handle_queue_result(
    tkinter, callback=None, wait_for_result=None, queue=GLOBAL_QUEUE
):
    if callback and wait_for_result:
        raise AttributeError("Cannot use callback and wait_for_result simultaneously")

    def process_queue():
        if not queue.qsize():
            tkinter.after(100, process_queue)
            return
        queue_out = queue.get()
        if callback:
            call = callback(queue_out)
            if call:
                return call
        elif wait_for_result and isinstance(wait_for_result, str):
            if queue_out == wait_for_result:
                return queue_out
        elif wait_for_result and isinstance(wait_for_result, (tuple, list)):
            if queue_out in wait_for_result:
                return queue_out
        else:
            return queue_out
        tkinter.after(100, process_queue)

    process_queue()


def detect_darkmode_in_windows():
    try:
        import winreg
    except ImportError:
        return False
    registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    reg_keypath = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    try:
        reg_key = winreg.OpenKey(registry, reg_keypath)
    except FileNotFoundError:
        return False

    for i in range(1024):
        try:
            value_name, value, _ = winreg.EnumValue(reg_key, i)
            if value_name == "AppsUseLightTheme":
                return value == 0
        except OSError:
            break
    return False


def get_first_tk_parent(widget):
    parent = widget
    while parent.master is not None:
        parent = parent.master
    return parent
