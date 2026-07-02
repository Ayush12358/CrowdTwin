from unittest.mock import MagicMock, patch
import sys

import numpy as np
import pytest

from crowd_vision.models import TrackState, VectorOutput
from crowd_vision.pipeline import CrowdVisionPipeline, PipelineConfig


@pytest.fixture()
def mock_yolo():
    """Mock ultralytics.YOLO via sys.modules so tests don't need the real package."""
    mock_yolo_cls = MagicMock()
    mock_module = MagicMock()
    mock_module.YOLO = mock_yolo_cls
    with patch.dict(sys.modules, {"ultralytics": mock_module}):
        yield mock_yolo_cls


@pytest.fixture()
def mock_cv2():
    """Patch cv2.VideoCapture for run_video tests."""
    with patch("cv2.VideoCapture") as mock_vc:
        yield mock_vc


@pytest.fixture()
def pipeline_no_mapper(mock_yolo):
    """Minimal pipeline without homography."""
    mock_yolo.return_value.track.return_value = []
    cfg = PipelineConfig(
        model_path="dummy.pt",
        confidence_threshold=0.3,
        max_history=120,
        smoothing_window=5,
        dense_crowd_threshold=80,
    )
    return CrowdVisionPipeline(config=cfg)


@pytest.fixture()
def pipeline_with_mapper(mock_yolo):
    """Pipeline with a simple identity homography mapper."""
    mock_yolo.return_value.track.return_value = []
    pts = np.array([[0, 0], [10, 0], [0, 10], [10, 10]], dtype=np.float32)
    cfg = PipelineConfig()
    return CrowdVisionPipeline(config=cfg, homography_points=(pts, pts))


class TestPipelineConfig:
    def test_defaults(self) -> None:
        cfg = PipelineConfig()
        assert cfg.model_path == "yolov8n.pt"
        assert cfg.confidence_threshold == 0.3
        assert cfg.max_history == 120
        assert cfg.smoothing_window == 5
        assert cfg.dense_crowd_threshold == 80
        assert cfg.max_fps == 30


class TestCrowdVisionPipelineInit:
    def test_pipeline_initializes_with_defaults(self, mock_yolo) -> None:
        mock_yolo.return_value.track.return_value = []
        p = CrowdVisionPipeline()
        assert p.mapper is None
        assert p.trajectories == {}

    def test_pipeline_creates_mapper_when_provided(self, mock_yolo) -> None:
        mock_yolo.return_value.track.return_value = []
        img_pts = np.array([[0, 0], [10, 0], [0, 10], [10, 10]], dtype=np.float32)
        world_pts = np.array([[0, 0], [100, 0], [0, 100], [100, 100]], dtype=np.float32)
        p = CrowdVisionPipeline(homography_points=(img_pts, world_pts))
        assert p.mapper is not None


class TestProcessFrame:
    def test_empty_detections_return_empty_tracks(self, pipeline_no_mapper) -> None:
        """When model returns no boxes, output should have zero tracks."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = pipeline_no_mapper.process_frame(frame, timestamp=0.0)
        assert result["tracks"] == []
        assert result["num_tracks"] == 0
        assert result["dense_flow"] is None

    def test_single_detection_returns_track(self, mock_yolo) -> None:
        """A single person detection should produce a VectorOutput."""
        # Build a mock detection result
        mock_box = MagicMock()
        mock_box.id = MagicMock()
        mock_box.id.cpu.return_value.numpy.return_value = np.array([1])
        mock_box.xyxy = MagicMock()
        mock_box.xyxy.cpu.return_value.numpy.return_value = np.array([[100, 100, 200, 300]])
        mock_result = MagicMock()
        mock_result.boxes = mock_box

        mock_yolo.return_value.track.return_value = [mock_result]

        cfg = PipelineConfig(dense_crowd_threshold=80)
        p = CrowdVisionPipeline(config=cfg)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = p.process_frame(frame, timestamp=1.0)
        assert result["num_tracks"] == 1
        track = result["tracks"][0]
        assert track["id"] == 1
        assert "position" in track
        assert "velocity" in track
        assert "speed" in track

    def test_trajectory_persists_across_frames(self, mock_yolo) -> None:
        """Same track ID across two frames should accumulate trajectory."""
        mock_box = MagicMock()
        mock_box.id = MagicMock()
        mock_box.id.cpu.return_value.numpy.return_value = np.array([42])
        mock_box.xyxy = MagicMock()
        mock_box.xyxy.cpu.return_value.numpy.return_value = np.array([[100, 100, 200, 300]])
        mock_result = MagicMock()
        mock_result.boxes = mock_box

        mock_yolo.return_value.track.return_value = [mock_result]

        cfg = PipelineConfig(dense_crowd_threshold=80)
        p = CrowdVisionPipeline(config=cfg)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        _ = p.process_frame(frame, timestamp=0.0)
        _ = p.process_frame(frame, timestamp=1.0)

        # The TrackState should have 2 points in trajectory
        track_state = p.trajectories[42]
        assert len(track_state.trajectory) == 2

    def test_none_box_id_is_skipped(self, mock_yolo) -> None:
        """Detection results with boxes.id == None should be skipped."""
        mock_result = MagicMock()
        mock_result.boxes = MagicMock()
        mock_result.boxes.id = None
        mock_yolo.return_value.track.return_value = [mock_result]

        cfg = PipelineConfig(dense_crowd_threshold=80)
        p = CrowdVisionPipeline(config=cfg)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = p.process_frame(frame, timestamp=0.0)
        assert result["tracks"] == []
        assert result["num_tracks"] == 0

    def test_optical_flow_triggered_at_dense_threshold(self, mock_yolo) -> None:
        """When detection count >= dense_crowd_threshold, optical flow runs."""
        # Create 80 detections to trigger dense flow
        mock_results = []
        for i in range(80):
            mock_box = MagicMock()
            mock_box.id = MagicMock()
            mock_box.id.cpu.return_value.numpy.return_value = np.array([i])
            mock_box.xyxy = MagicMock()
            mock_box.xyxy.cpu.return_value.numpy.return_value = np.array(
                [[100 + i, 100 + i, 200 + i, 300 + i]]
            )
            mock_result = MagicMock()
            mock_result.boxes = mock_box
            mock_results.append(mock_result)

        mock_yolo.return_value.track.return_value = mock_results

        cfg = PipelineConfig(dense_crowd_threshold=80)
        p = CrowdVisionPipeline(config=cfg)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # First frame: optical flow returns None because no prev_frame
        result1 = p.process_frame(frame, timestamp=0.0)
        assert result1["num_tracks"] == 80

        # Second frame: optical flow should compute
        result2 = p.process_frame(frame, timestamp=1.0)
        assert result2["dense_flow"] is not None
        assert "avg_vx" in result2["dense_flow"]
        assert "avg_vy" in result2["dense_flow"]
        assert "avg_speed" in result2["dense_flow"]


class TestRunVideo:
    def test_run_video_opens_and_releases(self, mock_yolo, mock_cv2) -> None:
        """run_video should open and release the capture."""
        mock_cap = MagicMock()
        mock_cap.read.side_effect = [(False, None)]  # Immediately end
        mock_cv2.return_value = mock_cap
        mock_cap.get.return_value = 30.0  # fake FPS

        mock_yolo.return_value.track.return_value = []

        cfg = PipelineConfig()
        p = CrowdVisionPipeline(config=cfg)
        p.run_video("dummy.mp4")
        mock_cap.release.assert_called_once()

    def test_run_video_respects_max_fps(self, mock_yolo, mock_cv2) -> None:
        """run_video should sleep between frames to enforce FPS cap."""
        mock_cap = MagicMock()
        # Return two frames then stop
        mock_cap.read.side_effect = [
            (True, np.zeros((480, 640, 3), dtype=np.uint8)),
            (False, None),
        ]
        mock_cap.get.return_value = 30.0
        mock_cv2.return_value = mock_cap

        mock_yolo.return_value.track.return_value = []

        cfg = PipelineConfig(max_fps=30)
        p = CrowdVisionPipeline(config=cfg)

        with patch("crowd_vision.pipeline.time.sleep") as mock_sleep:
            p.run_video("dummy.mp4")
            # Should have been called with positive sleep duration
            if mock_sleep.called:
                call_args = mock_sleep.call_args_list
                for call in call_args:
                    assert call[0][0] > 0


class TestDownscaling:
    def test_high_res_frame_is_downscaled_to_480p(self, mock_yolo) -> None:
        """A 1080p frame should be resized to 480p height before inference."""
        mock_yolo.return_value.track.return_value = []
        cfg = PipelineConfig()
        p = CrowdVisionPipeline(config=cfg)

        # 1920x1080 frame
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        p.process_frame(frame, timestamp=0.0)

        # Verify the model received a 480p-height frame
        call_args = mock_yolo.return_value.track.call_args
        input_frame = call_args[0][0]
        assert input_frame.shape[0] == 480
        assert input_frame.shape[1] == int(1920 * 480 / 1080)

    def test_low_res_frame_is_not_upscaled(self, mock_yolo) -> None:
        """A 360p frame should pass through without upscaling."""
        mock_yolo.return_value.track.return_value = []
        cfg = PipelineConfig()
        p = CrowdVisionPipeline(config=cfg)

        frame = np.zeros((360, 640, 3), dtype=np.uint8)
        p.process_frame(frame, timestamp=0.0)

        call_args = mock_yolo.return_value.track.call_args
        input_frame = call_args[0][0]
        assert input_frame.shape[:2] == (360, 640)
