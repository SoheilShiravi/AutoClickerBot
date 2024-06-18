import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from pynput import mouse

Point = tuple[int, int]


@dataclass(frozen=True)
class TaskResult:
    clicks: int
    elapsed: float


class Task(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def run(self, stop: threading.Event) -> TaskResult: ...


class ClickTask(Task):
    def __init__(self, delay: float) -> None:
        self.delay = delay
        self._mouse = mouse.Controller()
        self._listener: mouse.Listener | None = None
        self._ignore: Callable[[int, int], bool] = lambda x, y: False
        self._notify: Callable[[str], None] = lambda message: None

    @property
    @abstractmethod
    def is_ready(self) -> bool: ...

    @abstractmethod
    def record(self, point: Point) -> str | None: ...

    @abstractmethod
    def targets(self) -> Iterable[Point]: ...

    def start_recording(
        self,
        ignore: Callable[[int, int], bool],
        notify: Callable[[str], None],
    ) -> None:
        self._ignore = ignore
        self._notify = notify
        self._listener = mouse.Listener(on_click=self._on_click)
        self._listener.start()

    def stop_recording(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener.join()
            self._listener = None

    def run(self, stop: threading.Event) -> TaskResult:
        start = time.monotonic()
        clicks = 0
        for point in self.targets():
            self._mouse.position = point
            self._mouse.click(mouse.Button.left)
            clicks += 1
            if stop.wait(self.delay):
                break
        return TaskResult(clicks, time.monotonic() - start)

    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if not pressed or button != mouse.Button.left:
            return
        point = self._mouse.position
        if self._ignore(*point):
            return
        message = self.record(point)
        if message:
            self._notify(message)
