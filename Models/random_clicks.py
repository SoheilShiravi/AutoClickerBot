import math
import random
import time
from collections.abc import Iterator

from config import CLICK_DELAY
from Models.base import ClickTask, Point


class RandomClicks(ClickTask):
    def __init__(
        self,
        clicks: int | None = None,
        duration: float | None = None,
        delay: float = CLICK_DELAY,
    ) -> None:
        super().__init__(delay)
        self.clicks = clicks
        self.duration = duration
        self.center: Point | None = None
        self.corner: Point | None = None

    @property
    def name(self) -> str:
        limit = f"{self.duration:g}s" if self.duration else f"×{self.clicks}"
        return f"random {limit}"

    @property
    def is_ready(self) -> bool:
        return self.center is not None and self.corner is not None

    def record(self, point: Point) -> str | None:
        if self.center is None:
            self.center = point
            return "center recorded, now click the corner"
        if self.corner is None:
            self.corner = point
            return 'corner recorded, press "Set"'
        return None

    def targets(self) -> Iterator[Point]:
        radius = math.dist(self.center, self.corner)
        if self.duration:
            deadline = time.monotonic() + self.duration
            while time.monotonic() < deadline:
                yield self._random_point(radius)
        else:
            for _ in range(self.clicks):
                yield self._random_point(radius)

    def _random_point(self, radius: float) -> Point:
        x, y = self.center
        distance = random.uniform(0, radius)
        angle = random.uniform(0, math.tau)
        return round(x + distance * math.cos(angle)), round(y + distance * math.sin(angle))
