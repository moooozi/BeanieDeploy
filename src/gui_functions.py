import multiprocessing
import functions as fn

GLOBAL_QUEUE = multiprocessing.Queue()


def run_async_function(function, queue=GLOBAL_QUEUE, args=(), kwargs=None):
    """
    run a function without blocking the GUI
    :param function: the function
    :param queue: the Queue object
    :param args: arguments to be passed to th function
    :param kwargs: keyworded-arguments to be passed to th function
    :return: returns the first output from queue if no callback is specified, or the return of the callback if specified
    """
    if kwargs is None: kwargs = {}
    if queue: kwargs['queue'] = queue
    while queue.qsize(): queue.get()
    multiprocessing.Process(target=function, args=args, kwargs=kwargs).start()


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
