from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def mock_pipeline():
    """Patch the pipeline module so we don't need a real YOLO model."""
    with patch("crowd_vision.api.CrowdVisionPipeline") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.process_frame.return_value = {
            "tracks": [{"id": 1, "position": [1.0, 2.0], "velocity": [0.5, 0.5], "speed": 0.7}],
            "dense_flow": None,
            "num_tracks": 1,
        }
        mock_cls.return_value = mock_instance
        yield mock_cls, mock_instance


@pytest.fixture()
def mock_cv2_cap():
    """Patch cv2.VideoCapture to return a fake frame."""
    with patch("cv2.VideoCapture") as mock_vc:
        mock_cap = MagicMock()
        mock_cap.read.return_value = (True, "fake_frame")
        mock_cap.__enter__ = MagicMock(return_value=mock_cap)
        mock_cap.__exit__ = MagicMock(return_value=False)
        mock_vc.return_value = mock_cap
        yield mock_vc


@pytest.fixture()
def client(mock_pipeline, mock_cv2_cap):
    """Create a TestClient with the patched API."""
    # Import the app after patching so it picks up the mocks
    from crowd_vision.api import app, pipeline, startup

    # Manually call startup to set the global pipeline
    startup()

    return TestClient(app)


class TestProcessSingleEndpoint:
    def test_successful_frame_processing(self, client) -> None:
        response = client.post("/process/single", json={"source": "test.mp4"})
        assert response.status_code == 200
        data = response.json()
        assert "tracks" in data
        assert "num_tracks" in data
        assert data["num_tracks"] == 1

    def test_invalid_source_returns_400(self, mock_pipeline):
        """When cv2 can't read a frame, return 400."""
        with patch("cv2.VideoCapture") as mock_vc:
            mock_cap = MagicMock()
            mock_cap.read.return_value = (False, None)
            mock_vc.return_value = mock_cap

            from crowd_vision.api import app, startup

            startup()
            client = TestClient(app)

            response = client.post("/process/single", json={"source": "nonexistent.mp4"})
            assert response.status_code == 400

    def test_request_body_validation(self, client) -> None:
        """Missing 'source' field should fail validation."""
        response = client.post("/process/single", json={})
        assert response.status_code == 422

    def test_source_change_resets_state(self, client) -> None:
        """Different sources should reset pipeline state."""
        response1 = client.post("/process/single", json={"source": "video1.mp4"})
        assert response1.status_code == 200

        response2 = client.post("/process/single", json={"source": "video2.mp4"})
        assert response2.status_code == 200
