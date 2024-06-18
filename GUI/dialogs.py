import math
import tkinter
from collections.abc import Callable
from typing import Any

import ttkbootstrap as ttk

from config import BUTTON_WIDTH, DEFAULT_RANDOM_CLICKS, PADDING


class Dialog(ttk.Toplevel):
    def __init__(self, parent: tkinter.Misc, title: str) -> None:
        super().__init__(title=title, transient=parent, resizable=(False, False))
        self.result: Any = None
        self._entries: list[ttk.Entry] = []
        half = PADDING // 2

        self._body = ttk.Frame(self)
        self._body.grid(row=0, column=0, columnspan=2, padx=half, pady=half, sticky="nsew")
        ttk.Button(self, text="Cancel", bootstyle="danger", width=BUTTON_WIDTH, command=self.destroy).grid(
            row=1, column=0, padx=half, pady=half, sticky="ew"
        )
        ttk.Button(self, text="OK", bootstyle="success", width=BUTTON_WIDTH, command=self._submit).grid(
            row=1, column=1, padx=half, pady=half, sticky="ew"
        )

        self.bind("<Return>", lambda event: self._submit())
        self.bind("<Escape>", lambda event: self.destroy())

    def show(self) -> Any:
        self.place_window_center()
        self.grab_set()
        self._entries[0].focus_set()
        self._entries[0].select_range(0, "end")
        self.wait_window()
        return self.result

    def parse(self) -> Any:
        raise NotImplementedError

    def _add_field(self, label: str, default: object) -> ttk.Entry:
        column = len(self._entries)
        frame = ttk.Labelframe(self._body, text=label, bootstyle="info")
        frame.grid(row=0, column=column, padx=PADDING // 2, pady=PADDING // 2, sticky="ew")
        self._body.columnconfigure(column, weight=1)

        entry = ttk.Entry(frame, bootstyle="info", width=BUTTON_WIDTH)
        entry.insert(0, str(default))
        entry.pack(fill="x", padx=PADDING // 2, pady=PADDING // 2)
        self._entries.append(entry)
        return entry

    def _submit(self) -> None:
        try:
            self.result = self.parse()
        except ValueError:
            self.bell()
            return
        self.destroy()

    @staticmethod
    def _read(entry: ttk.Entry, cast: Callable[[str], float], minimum: float, optional: bool = False) -> Any:
        text = entry.get().strip()
        if optional and not text:
            entry.configure(bootstyle="info")
            return None
        try:
            value = cast(text)
        except ValueError:
            value = None
        if value is None or not math.isfinite(value) or value < minimum:
            entry.configure(bootstyle="danger")
            entry.focus_set()
            raise ValueError(text)
        entry.configure(bootstyle="info")
        return value


class DelayDialog(Dialog):
    def __init__(self, parent: tkinter.Misc, title: str, label: str, default: float) -> None:
        super().__init__(parent, title)
        self._delay = self._add_field(label, default)

    def parse(self) -> float:
        return self._read(self._delay, float, minimum=0)


class RandomClicksDialog(Dialog):
    def __init__(self, parent: tkinter.Misc) -> None:
        super().__init__(parent, "Random Clicks")
        self._clicks = self._add_field("Clicks", DEFAULT_RANDOM_CLICKS)
        self._duration = self._add_field("Or duration (s)", "")

    def parse(self) -> tuple[int | None, float | None]:
        duration = self._read(self._duration, float, minimum=0, optional=True)
        if duration:
            return None, duration
        return self._read(self._clicks, int, minimum=1), None
