from crowd_vision.models import TrackState, VectorOutput


class TestTrackState:
    def test_initial_state_is_empty(self) -> None:
        ts = TrackState(track_id=1)
        assert len(ts.trajectory) == 0
        assert ts.track_id == 1

    def test_add_point_appends_trajectory(self) -> None:
        ts = TrackState(track_id=1)
        ts.add_point(1.0, 2.0, 0.0)
        ts.add_point(3.0, 4.0, 1.0)
        assert len(ts.trajectory) == 2
        assert ts.trajectory[0] == (1.0, 2.0, 0.0)
        assert ts.trajectory[1] == (3.0, 4.0, 1.0)

    def test_max_history_truncates_old_entries(self) -> None:
        ts = TrackState(track_id=1, max_history=3)
        for i in range(5):
            ts.add_point(float(i), float(i), float(i))
        assert len(ts.trajectory) == 3
        # Oldest entries should be evicted
        assert ts.trajectory[0] == (2.0, 2.0, 2.0)
        assert ts.trajectory[-1] == (4.0, 4.0, 4.0)

    def test_default_max_history_is_120(self) -> None:
        ts = TrackState(track_id=1)
        assert ts.max_history == 120


class TestVectorOutput:
    def test_as_dict_format(self) -> None:
        vo = VectorOutput(id=12, position=(3.2, 5.1), velocity=(0.5, -0.2), speed=0.54)
        result = vo.as_dict()
        assert result == {
            "id": 12,
            "position": [3.2, 5.1],
            "velocity": [0.5, -0.2],
            "speed": 0.54,
        }

    def test_as_dict_with_zero_values(self) -> None:
        vo = VectorOutput(id=0, position=(0.0, 0.0), velocity=(0.0, 0.0), speed=0.0)
        result = vo.as_dict()
        assert result["id"] == 0
        assert result["position"] == [0.0, 0.0]
        assert result["velocity"] == [0.0, 0.0]
        assert result["speed"] == 0.0
