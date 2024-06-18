from collections.abc import Iterable

from config import STEP_DELAY
from Models.base import ClickTask, Point


class PathClicks(ClickTask):
    def __init__(self, delay: float = STEP_DELAY) -> None:
        super().__init__(delay)
        self.points: list[Point] = []

    @property
    def name(self) -> str:
        return f"steps ×{len(self.points)}"

    @property
    def is_ready(self) -> bool:
        return bool(self.points)

    def record(self, point: Point) -> str:
        self.points.append(point)
        return f"step {len(self.points)} recorded"

    def targets(self) -> Iterable[Point]:
        return tuple(self.points)
