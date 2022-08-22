import multiprocessing
import functions as fn

multiprocessing.freeze_support()
GLOBAL_QUEUE = multiprocessing.Queue()


def run_async_function(tkinter, function, callback=None, queue=GLOBAL_QUEUE, args=(), kwargs=None, wait_for_result=None):
    """
    run a function without blocking the GUI
    :param tkinter: the tkinter instance
    :param function: the function
    :param callback: callback function to handle Queue communication
    :param queue: the Queue object
    :param args: arguments to be passed to th function
    :param kwargs: keyworded-arguments to be passed to th function
    :param wait_for_result: wait for certain queue output
    :return: returns the first output from queue if no callback is specified, or the return of the callback if specified
    """
    if kwargs is None: kwargs = {}
    if queue: kwargs['queue'] = queue
    while queue.qsize(): queue.get()
    multiprocessing.Process(target=function, args=args, kwargs=kwargs).start()
    while True:
        while not queue.qsize(): tkinter.after(100, tkinter.update())
        if callback:
            call = callback(queue.get())
            if call: return call
        elif wait_for_result:
            if queue.get() == wait_for_result:
                break
        else:
            return queue.get()


def download_hash_handler(dl_hash):
    go_next = False
    if dl_hash == 1:
        go_next = True
    elif dl_hash == -1:
        question = tkt.open_popup(parent=app, title_txt=LN.job_checksum_failed,
                                  msg_txt=LN.job_checksum_failed_txt,
                                  primary_btn_str=LN.btn_yes, secondary_btn_str=LN.btn_no)
        if question:
            go_next = True
        else:
            question = tkt.open_popup(parent=app, title_txt=LN.cleanup_question,
                                      msg_txt=LN.cleanup_question_txt,
                                      primary_btn_str=LN.btn_yes, secondary_btn_str=LN.btn_no)
            if question:
                fn.rmdir(PATH.WORK_DIR)
            fn.app_quit()
    else:
        question = tkt.open_popup(parent=app, title_txt=LN.job_checksum_mismatch,
                                  msg_txt=LN.job_checksum_mismatch_txt % dl_hash,
                                  primary_btn_str=LN.btn_retry, secondary_btn_str=LN.btn_abort)
        if not question:
            question = tkt.open_popup(parent=app, title_txt=LN.cleanup_question,
                                      msg_txt=LN.cleanup_question_txt,
                                      primary_btn_str=LN.btn_yes, secondary_btn_str=LN.btn_no)
            if question:
                fn.rmdir(PATH.WORK_DIR)
            fn.app_quit()
    return go_next