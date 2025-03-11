import multiprocessing
import queue
import threading
import subprocess
from enum import Enum

DETACHED_PROCESS_FLAG = 0x00000008


class Status(Enum):
    NOT_STARTED = "Not started"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"


class AsyncOperations:
    def __init__(self, use_threading=True, use_queue=False):
        self.use_threading = use_threading
        self.use_queue = use_queue
        self.queue = (
            multiprocessing.Queue()
            if not use_threading
            else queue.Queue() if use_queue else None
        )
        self.status = Status.NOT_STARTED
        self.output = []

    @classmethod
    def run(
        cls,
        function=None,
        cmd=None,
        args=(),
        kwargs={},
        use_threading=True,
        use_queue=False,
    ):
        instance = cls(use_threading=use_threading, use_queue=use_queue)
        instance.run_async_process(function=function, cmd=cmd, args=args, kwargs=kwargs)
        return instance

    def _read_cmd_output(self, command):
        self.status = Status.RUNNING
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=DETACHED_PROCESS_FLAG,
        )
        output = process.stdout.readlines() or ""
        while output and process.poll() is None:
            self._handle_received_output(output)
        self.status = Status.COMPLETED

    def _read_function_output(self, function, args, kwargs):
        self.status = Status.RUNNING
        result = function(*args, **kwargs)
        self._handle_received_output(result)
        self.status = Status.COMPLETED

    def run_async_process(self, function=None, cmd=None, args=(), kwargs={}):
        if not (bool(cmd) ^ bool(function)):
            raise ValueError("Either 'cmd' or 'function' must be provided")

        if cmd:
            if isinstance(cmd, str):
                cmd = [cmd]
            command = (
                cmd + list(args) + [f"{key}={value}" for key, value in kwargs.items()]
            )
            target = self._read_cmd_output
            target_args = (command,)
        if function:
            target = self._read_function_output
            target_args = (function, args, kwargs)

        if self.use_threading:
            thread = threading.Thread(target=target, args=target_args)
            thread.start()
        else:
            process = multiprocessing.Process(target=target, args=target_args)
            process.start()

        return self.queue if self.use_queue else self.output

    def _handle_received_output(self, output):
        if self.use_queue:
            self.queue.put(output)
        self.output.append(output)
