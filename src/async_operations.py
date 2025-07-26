import atexit
import multiprocessing
import queue
import threading
import subprocess
from enum import Enum
from typing import Optional, Callable, List

DETACHED_PROCESS_FLAG = 0x00000008


class Status(Enum):
    NOT_STARTED = "Not started"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"


class AsyncOperations:
    def __init__(
        self,
        use_threading=True,
        use_queue=False,
        on_complete: Optional[Callable] = None,
    ):
        self.use_threading = use_threading
        self.use_queue = use_queue
        self.queue: Optional[queue.Queue | multiprocessing.Queue] = (
            multiprocessing.Queue()
            if not use_threading
            else queue.Queue() if use_queue else None
        )
        self.status = Status.NOT_STARTED
        self.output = None
        self.on_complete = on_complete

    @classmethod
    def run(
        cls,
        function: Optional[Callable] = None,
        cmd: Optional[List[str]] = None,
        args=(),
        kwargs=None,
        use_threading=True,
        use_queue=False,
        on_complete: Optional[Callable] = None,
    ):
        if kwargs is None:
            kwargs = {}
        instance = cls(
            use_threading=use_threading,
            use_queue=use_queue,
            on_complete=on_complete,
        )
        instance.run_async_process(
            function=function,
            cmd=cmd,
            args=args,
            kwargs=kwargs,
            on_complete=on_complete,
        )
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
        if process.stdout:
            output = process.stdout.readlines() or ""
            while output and process.poll() is None:
                self._handle_received_output(output)
        self.status = Status.COMPLETED
        if self.on_complete:
            self.on_complete(self.output)

    def _read_function_output(self, function, args, kwargs):
        self.status = Status.RUNNING
        result = function(*args, **kwargs)
        self._handle_received_output(result)
        self.status = Status.COMPLETED
        if self.on_complete:
            self.on_complete(self.output)

    def run_async_process(
        self,
        function: Optional[Callable] = None,
        cmd: Optional[List[str]] = None,
        args=(),
        kwargs=None,
        on_complete: Optional[Callable] = None,
    ):
        if kwargs is None:
            kwargs = {}
        if on_complete is not None:
            self.on_complete = on_complete

        if not (bool(cmd) ^ bool(function)):
            raise ValueError("Either 'cmd' or 'function' must be provided")

        target = None
        target_args = ()
        if cmd:
            if isinstance(cmd, str):
                cmd = [cmd]
            command = (
                cmd + list(args) + [f"{key}={value}" for key, value in kwargs.items()]
            )
            target = self._read_cmd_output
            target_args = (command,)
        elif function:
            target = self._read_function_output
            target_args = (function, args, kwargs)

        if target and target_args:
            if self.use_threading:
                thread = threading.Thread(target=target, args=target_args)
                thread.start()
            else:
                process = multiprocessing.Process(target=target, args=target_args)
                process.start()
                atexit.register(process.terminate)

        return self.queue if self.use_queue else self.output

    def _handle_received_output(self, output):
        if self.use_queue and self.queue:
            self.queue.put(output)
        self.output = output
