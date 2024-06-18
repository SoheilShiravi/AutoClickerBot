import queue
import threading
from collections.abc import Callable

from pynput import keyboard

from config import DEFAULT_DELAY, EVENT_POLL_MS, STEP_DELAY
from GUI import DelayDialog, MainWindow, Mode, RandomClicksDialog
from Models import ClickTask, DelayTask, PathClicks, RandomClicks, Task


class Controller:
    def __init__(self) -> None:
        self.view = MainWindow()
        self.tasks: list[Task] = []
        self._recording: ClickTask | None = None
        self._events: queue.SimpleQueue[tuple[Callable[..., object], tuple[object, ...]]] = queue.SimpleQueue()
        self._stop = threading.Event()

        self.view.steps_button.configure(command=self._add_steps)
        self.view.random_button.configure(command=self._add_random_clicks)
        self.view.delay_button.configure(command=self._add_delay)
        self.view.set_button.configure(command=self._finish_recording)
        self.view.run_button.configure(command=self._run)

    def run(self) -> None:
        self._process_events()
        self.view.mainloop()

    def _post(self, callback: Callable[..., object], *args: object) -> None:
        self._events.put((callback, args))

    def _process_events(self) -> None:
        while not self._events.empty():
            callback, args = self._events.get()
            callback(*args)
        self.view.after(EVENT_POLL_MS, self._process_events)

    def _add_steps(self) -> None:
        delay = DelayDialog(self.view, "Steps", "Delay between clicks (s)", STEP_DELAY).show()
        if delay is not None:
            self._start_recording(PathClicks(delay), 'click every step you want, then press "Set"')

    def _add_random_clicks(self) -> None:
        settings = RandomClicksDialog(self.view).show()
        if settings is not None:
            clicks, duration = settings
            self._start_recording(RandomClicks(clicks=clicks, duration=duration), "click the center of the target")

    def _add_delay(self) -> None:
        seconds = DelayDialog(self.view, "Delay", "Delay (s)", DEFAULT_DELAY).show()
        if seconds is not None:
            self._enqueue(DelayTask(seconds))

    def _start_recording(self, task: ClickTask, hint: str) -> None:
        self._recording = task
        self.view.set_mode(Mode.RECORDING)
        self.view.log(hint)
        task.start_recording(ignore=self.view.contains, notify=lambda message: self._post(self.view.log, message))

    def _finish_recording(self) -> None:
        task, self._recording = self._recording, None
        if task is None:
            return
        task.stop_recording()
        self.view.set_mode(Mode.IDLE)
        if task.is_ready:
            self._enqueue(task)
        else:
            self.view.log("recording incomplete, task discarded")

    def _enqueue(self, task: Task) -> None:
        self.tasks.append(task)
        self.view.add_task(task.name, lambda: self._remove_task(task))
        self.view.log(f"{task.name} added to queue")

    def _remove_task(self, task: Task) -> None:
        index = self.tasks.index(task)
        del self.tasks[index]
        self.view.remove_task(index)
        self.view.log(f"{task.name} removed from queue")

    def _run(self) -> None:
        if not self.tasks:
            self.view.log("there is no task")
            return
        self.view.set_mode(Mode.RUNNING)
        self._stop.clear()
        threading.Thread(target=self._execute_tasks, daemon=True).start()

    def _execute_tasks(self) -> None:
        self._post(self.view.log, "running all tasks, press Esc to stop")
        try:
            with keyboard.Listener(on_press=self._on_key_press):
                for index, task in enumerate(self.tasks):
                    self._post(self.view.highlight_task, index, True)
                    result = task.run(self._stop)
                    self._post(self.view.highlight_task, index, False)
                    self._post(self.view.log, f"{task.name} done after {result.elapsed:.2f}s and {result.clicks} clicks")
                    if self._stop.is_set():
                        self._post(self.view.log, "stopped by Esc")
                        break
        except Exception as error:
            self._post(self.view.log, f"run failed: {error!r}")
        finally:
            self._post(self.view.set_mode, Mode.IDLE)

    def _on_key_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        if key == keyboard.Key.esc:
            self._stop.set()


def main() -> None:
    Controller().run()
