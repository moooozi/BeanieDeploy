import queue
import threading



def run_async_function(function, queue: queue.Queue, args=(), kwargs={}):
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
    tkinter, callback=None, wait_for_result=None, queue: queue.Queue = None): # type: ignore
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