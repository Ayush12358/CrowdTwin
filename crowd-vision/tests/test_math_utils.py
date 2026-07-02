from collections import deque

import numpy as np
import pytest

from crowd_vision.math_utils import (
    HomographyMapper,
    compute_velocity,
    new_history,
    smooth_point,
    speed_from_velocity,
)


def test_compute_velocity_basic() -> None:
    traj = [(0.0, 0.0, 1.0), (2.0, 6.0, 3.0)]
    vx, vy = compute_velocity(traj)
    assert vx == 1.0
    assert vy == 3.0


def test_compute_velocity_zero_dt() -> None:
    traj = [(0.0, 0.0, 1.0), (2.0, 6.0, 1.0)]
    vx, vy = compute_velocity(traj)
    assert vx == 0.0
    assert vy == 0.0


def test_compute_velocity_fewer_than_two_points() -> None:
    assert compute_velocity([]) == (0.0, 0.0)
    assert compute_velocity([(1.0, 2.0, 0.0)]) == (0.0, 0.0)


def test_compute_velocity_negative_dt() -> None:
    traj = [(0.0, 0.0, 5.0), (2.0, 6.0, 3.0)]
    vx, vy = compute_velocity(traj)
    assert vx == 0.0
    assert vy == 0.0


def test_speed_from_velocity() -> None:
    assert speed_from_velocity(3.0, 4.0) == 5.0


def test_speed_from_velocity_zero() -> None:
    assert speed_from_velocity(0.0, 0.0) == 0.0


# ---------------------------------------------------------------------------
# HomographyMapper tests
# ---------------------------------------------------------------------------

class TestHomographyMapper:
    def test_identity_mapping(self) -> None:
        """When image points == world points, mapping should be identity."""
        pts = np.array([[0, 0], [10, 0], [0, 10], [10, 10]], dtype=np.float32)
        mapper = HomographyMapper(pts, pts)
        x, y = mapper.map_to_world(5.0, 5.0)
        assert x == pytest.approx(5.0, abs=1e-2)
        assert y == pytest.approx(5.0, abs=1e-2)

    def test_scaled_mapping(self) -> None:
        """World coords are 10x image coords."""
        image_pts = np.array([[0, 0], [10, 0], [0, 10], [10, 10]], dtype=np.float32)
        world_pts = np.array([[0, 0], [100, 0], [0, 100], [100, 100]], dtype=np.float32)
        mapper = HomographyMapper(image_pts, world_pts)
        x, y = mapper.map_to_world(5.0, 5.0)
        assert x == pytest.approx(50.0, abs=1e-1)
        assert y == pytest.approx(50.0, abs=1e-1)

    def test_invalid_points_raises(self) -> None:
        """Fewer than 4 points should cause cv2.findHomography to fail."""
        import cv2
        image_pts = np.array([[0, 0], [10, 0]], dtype=np.float32)
        world_pts = np.array([[0, 0], [10, 0]], dtype=np.float32)
        with pytest.raises(cv2.error):
            HomographyMapper(image_pts, world_pts)


# ---------------------------------------------------------------------------
# smooth_point tests
# ---------------------------------------------------------------------------

class TestSmoothPoint:
    def test_single_point_returns_itself(self) -> None:
        history: deque = deque()
        result = smooth_point(history, (10.0, 20.0), window=5)
        assert result == (10.0, 20.0)

    def test_window_averages(self) -> None:
        history: deque = deque()
        smooth_point(history, (0.0, 0.0), window=3)
        smooth_point(history, (3.0, 3.0), window=3)
        smooth_point(history, (6.0, 6.0), window=3)
        result = smooth_point(history, (9.0, 9.0), window=3)
        # Last 3 points: (3,3), (6,6), (9,9) -> avg (6, 6)
        assert result == (6.0, 6.0)

    def test_window_evicts_old_entries(self) -> None:
        history: deque = deque()
        for i in range(10):
            result = smooth_point(history, (float(i), float(i)), window=2)
        # Only last 2 points matter: (8,8) and (9,9) -> avg (8.5, 8.5)
        assert result == (8.5, 8.5)

    def test_window_one_returns_current(self) -> None:
        history: deque = deque()
        smooth_point(history, (1.0, 1.0), window=1)
        result = smooth_point(history, (5.0, 5.0), window=1)
        assert result == (5.0, 5.0)

    def test_invalid_window_raises(self) -> None:
        history: deque = deque()
        with pytest.raises(ValueError, match="window must be >= 1"):
            smooth_point(history, (0.0, 0.0), window=0)


def test_new_history_returns_empty_deque() -> None:
    h = new_history()
    assert isinstance(h, deque)
    assert len(h) == 0
