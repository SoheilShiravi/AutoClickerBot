import threading
import time

from Models.base import Task, TaskResult


class DelayTask(Task):
    def __init__(self, seconds: float) -> None:
        self.seconds = seconds

    @property
    def name(self) -> str:
        return f"delay {self.seconds:g}s"

    def run(self, stop: threading.Event) -> TaskResult:
        start = time.monotonic()
        stop.wait(self.seconds)
        return TaskResult(0, time.monotonic() - start)
