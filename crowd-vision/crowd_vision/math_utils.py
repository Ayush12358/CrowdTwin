from __future__ import annotations

import math
from collections import deque
from typing import TYPE_CHECKING, Deque, Iterable, Tuple

if TYPE_CHECKING:
    import numpy as np


class HomographyMapper:
    """Maps image coordinates to world coordinates with a homography matrix."""

    def __init__(self, image_points: "np.ndarray", world_points: "np.ndarray"):
        import cv2

        self.h_matrix, _ = cv2.findHomography(image_points, world_points)
        if self.h_matrix is None:
            raise ValueError("Unable to compute homography matrix from provided points.")

    def map_to_world(self, x: float, y: float) -> Tuple[float, float]:
        import cv2
        import numpy as np

        pt = np.array([[[x, y]]], dtype=np.float32)
        mapped = cv2.perspectiveTransform(pt, self.h_matrix)
        return float(mapped[0][0][0]), float(mapped[0][0][1])


def compute_velocity(traj: Iterable[Tuple[float, float, float]]) -> Tuple[float, float]:
    """Compute velocity from the last two trajectory points."""

    traj = list(traj)
    if len(traj) < 2:
        return 0.0, 0.0

    (x1, y1, t1), (x2, y2, t2) = traj[-2], traj[-1]
    dt = t2 - t1
    if dt <= 0:
        return 0.0, 0.0

    return (x2 - x1) / dt, (y2 - y1) / dt


def speed_from_velocity(vx: float, vy: float) -> float:
    return math.hypot(vx, vy)


def smooth_point(history: Deque[Tuple[float, float]], point: Tuple[float, float], window: int = 5) -> Tuple[float, float]:
    """Moving-average smoothing for jitter reduction."""

    if window < 1:
        raise ValueError("window must be >= 1")

    history.append(point)
    while len(history) > window:
        history.popleft()

    xs = [p[0] for p in history]
    ys = [p[1] for p in history]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def new_history() -> Deque[Tuple[float, float]]:
    return deque()
