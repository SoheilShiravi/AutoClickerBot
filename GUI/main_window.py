import ctypes
import os
import sys
import tkinter
import webbrowser
from collections.abc import Callable
from ctypes import wintypes
from enum import Enum, auto

import ttkbootstrap as ttk
from PIL import Image, ImageTk

from config import (
    APP_ICON,
    APP_LOGO,
    APP_TITLE,
    BUTTON_WIDTH,
    LOGO_SIZE,
    PADDING,
    TASK_PANEL_WIDTH,
    TASK_WIDTH,
    TELEGRAM_CHANNEL_URL,
    THEME,
    WINDOW_MIN_SIZE,
)

if sys.platform == "win32":
    _user32 = ctypes.WinDLL("user32")
    _user32.WindowFromPoint.argtypes = (wintypes.POINT,)
    _user32.WindowFromPoint.restype = wintypes.HWND
    _user32.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
    _user32.GetWindowThreadProcessId.restype = wintypes.DWORD


def _process_at(x: int, y: int) -> int:
    pid = wintypes.DWORD()
    _user32.GetWindowThreadProcessId(_user32.WindowFromPoint(wintypes.POINT(x, y)), ctypes.byref(pid))
    return pid.value


class Mode(Enum):
    IDLE = auto()
    RECORDING = auto()
    RUNNING = auto()


class TaskRow(ttk.Frame):
    def __init__(self, master: tkinter.Misc, number: int, name: str, on_remove: Callable[[], None]) -> None:
        super().__init__(master, padding=(8, 6))
        self._number = ttk.Label(self, width=2)
        self._name = ttk.Label(self, text=name)
        self._remove = ttk.Button(self, text="✕", width=2, command=on_remove)
        self._number.pack(side="left")
        self._name.pack(side="left", fill="x", expand=True)
        self._remove.pack(side="right")
        self.set_number(number)
        self.highlight(False)

    def set_number(self, number: int) -> None:
        self._number.configure(text=str(number))

    def highlight(self, active: bool) -> None:
        surface = "@primary" if active else "@card"
        self.configure(bootstyle=surface)
        self._number.configure(bootstyle=f"{surface} secondary")
        self._name.configure(bootstyle=surface)
        self._remove.configure(bootstyle=f"{surface} danger ghost")

    def set_removable(self, removable: bool) -> None:
        self._remove.configure(state="normal" if removable else "disabled")


class MainWindow(ttk.App):
    def __init__(self) -> None:
        super().__init__(title=APP_TITLE, theme=THEME, iconphoto=None, minsize=WINDOW_MIN_SIZE)
        self._bounds = (0, 0, 0, 0)
        with Image.open(APP_ICON) as icon:
            self._icon = ImageTk.PhotoImage(icon, master=self)
        self.iconphoto(True, self._icon)

        self.steps_button = ttk.Button(self, text="Add Steps", bootstyle="primary", width=BUTTON_WIDTH)
        self.random_button = ttk.Button(self, text="Add Random Clicks", bootstyle="primary", width=BUTTON_WIDTH)
        self.delay_button = ttk.Button(self, text="Add Delay", bootstyle="primary", width=BUTTON_WIDTH)
        self.set_button = ttk.Button(self, text="Set", bootstyle="warning")
        self.run_button = ttk.Button(self, text="Run", bootstyle="success")

        self._log = ttk.ScrolledText(self, state="disabled", wrap="word", height=10)
        self._task_panel = ttk.Frame(self, bootstyle="dark")
        self._task_list = ttk.ScrolledFrame(self._task_panel, bootstyle="dark", width=TASK_PANEL_WIDTH)
        self._task_rows: list[TaskRow] = []

        self._layout()
        self.bind("<Configure>", self._track_bounds, add="+")
        self.set_mode(Mode.IDLE)

    def _layout(self) -> None:
        half = PADDING // 2

        self._create_logo().grid(row=0, column=0, rowspan=2, padx=PADDING, pady=PADDING)
        for column, button in enumerate((self.steps_button, self.random_button, self.delay_button), start=1):
            button.grid(row=0, column=column, padx=PADDING, pady=(PADDING, 0))
        self.set_button.grid(row=1, column=1, columnspan=3, padx=PADDING, sticky="new")

        ttk.Separator(self, bootstyle="success").grid(row=2, column=0, columnspan=4, padx=PADDING, sticky="ew")
        self._log.grid(row=3, column=0, columnspan=4, padx=PADDING, pady=half, sticky="nsew")
        self.run_button.grid(row=4, column=0, columnspan=4, padx=PADDING, pady=(0, PADDING), sticky="ew")

        self._task_panel.grid(row=0, column=4, rowspan=5, padx=(0, PADDING), pady=PADDING, sticky="ns")
        ttk.Label(
            self._task_panel,
            text="Tasks",
            width=TASK_WIDTH,
            bootstyle="light",
            anchor="center",
            font="TkHeadingFont",
            relief="raised",
        ).pack(fill="x")
        self._task_list.pack(fill="both", expand=True)

        self.rowconfigure(3, weight=1)
        self.columnconfigure((1, 2, 3), weight=1)

    def _create_logo(self) -> ttk.Label:
        with Image.open(APP_LOGO) as image:
            self._logo = ImageTk.PhotoImage(image.resize((LOGO_SIZE, LOGO_SIZE), Image.Resampling.LANCZOS), master=self)
        logo = ttk.Label(self, image=self._logo, cursor="hand2")
        logo.bind("<Button-1>", lambda event: webbrowser.open_new_tab(TELEGRAM_CHANNEL_URL))
        return logo

    def _track_bounds(self, event: tkinter.Event) -> None:
        if event.widget is self:
            border = self.winfo_rootx() - self.winfo_x()
            self._bounds = (
                self.winfo_x(),
                self.winfo_y(),
                self.winfo_rootx() + self.winfo_width() + border,
                self.winfo_rooty() + self.winfo_height() + border,
            )

    def contains(self, x: int, y: int) -> bool:
        if sys.platform == "win32":
            return _process_at(x, y) == os.getpid()
        left, top, right, bottom = self._bounds
        return left <= x < right and top <= y < bottom

    def set_mode(self, mode: Mode) -> None:
        idle = "normal" if mode is Mode.IDLE else "disabled"
        for button in (self.steps_button, self.random_button, self.delay_button, self.run_button):
            button.configure(state=idle)
        self.set_button.configure(state="normal" if mode is Mode.RECORDING else "disabled")
        for row in self._task_rows:
            row.set_removable(mode is not Mode.RUNNING)
            if mode is not Mode.RUNNING:
                row.highlight(False)

    def log(self, message: str) -> None:
        self._log.configure(state="normal")
        self._log.insert("end", f"--- {message}\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def add_task(self, name: str, on_remove: Callable[[], None]) -> None:
        row = TaskRow(self._task_list, len(self._task_rows) + 1, name, on_remove)
        row.pack(fill="x", padx=5, pady=3)
        self._task_rows.append(row)

    def remove_task(self, index: int) -> None:
        self._task_rows.pop(index).destroy()
        for number, row in enumerate(self._task_rows[index:], start=index + 1):
            row.set_number(number)

    def highlight_task(self, index: int, active: bool) -> None:
        self._task_rows[index].highlight(active)
