import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import supervision as sv

# Import code.crowd-vision.main logic
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import main


class TestVisionPipeline(unittest.TestCase):
    def setUp(self):
        # Correctly reset global state inside the target main module under its lock
        with main._tracks_lock:
            main._latest_tracks = None
            main._track_history.clear()

    @patch('main.YOLO')
    @patch('supervision.Detections.from_ultralytics')
    def test_pure_process_single_frame(self, mock_from_ultralytics, mock_yolo):
        # 1. Mock YOLO model and Detections creation
        mock_model_instance = MagicMock()
        mock_yolo.return_value = mock_model_instance

        # Return a simple untracked detection from YOLO output parsing
        untracked_detections = sv.Detections(
            xyxy=np.array([[100.0, 100.0, 150.0, 150.0]], dtype=np.float32),
            class_id=np.array([0], dtype=np.int32),
            confidence=np.array([0.9], dtype=np.float32)
        )
        mock_from_ultralytics.return_value = untracked_detections

        # 2. Mock Tracker to return a deterministic tracked detection
        mock_tracker = MagicMock()
        tracked_detections_1 = sv.Detections(
            xyxy=np.array([[100.0, 100.0, 150.0, 150.0]], dtype=np.float32),
            class_id=np.array([0], dtype=np.int32),
            confidence=np.array([0.9], dtype=np.float32),
            tracker_id=np.array([12], dtype=np.int32)
        )
        mock_tracker.update_with_detections.return_value = tracked_detections_1

        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # 3. Process first frame (t = 1000.0)
        tracks_payload = main.process_single_frame(
            frame=dummy_frame,
            model=mock_model_instance,
            tracker=mock_tracker,
            current_timestamp=1000.0
        )

        # Assert tracking payload properties
        self.assertEqual(len(tracks_payload), 1)
        track = tracks_payload[0]
        self.assertEqual(track["id"], 12)
        self.assertEqual(track["position"], [125.0, 125.0])  # Center of [100, 100, 150, 150]
        self.assertEqual(track["velocity"], [0.0, 0.0])      # No history yet -> 0 velocity
        self.assertEqual(track["speed"], 0.0)

        # 4. Process second frame at t = 1002.0 (+2 seconds) with updated coordinates
        tracked_detections_2 = sv.Detections(
            xyxy=np.array([[110.0, 110.0, 160.0, 160.0]], dtype=np.float32),
            class_id=np.array([0], dtype=np.int32),
            confidence=np.array([0.9], dtype=np.float32),
            tracker_id=np.array([12], dtype=np.int32)
        )
        mock_tracker.update_with_detections.return_value = tracked_detections_2

        tracks_payload_2 = main.process_single_frame(
            frame=dummy_frame,
            model=mock_model_instance,
            tracker=mock_tracker,
            current_timestamp=1002.0
        )

        # Delta position: dx = 10, dy = 10 over dt = 2.0 -> vx = 5.0, vy = 5.0
        self.assertEqual(len(tracks_payload_2), 1)
        track_2 = tracks_payload_2[0]
        self.assertEqual(track_2["position"], [135.0, 135.0])
        self.assertAlmostEqual(track_2["velocity"][0], 5.0, places=2)
        self.assertAlmostEqual(track_2["velocity"][1], 5.0, places=2)
        self.assertAlmostEqual(track_2["speed"], (5.0**2 + 5.0**2)**0.5, places=2)

    def test_api_endpoint_initial_state(self):
        # Assert that the API `/ingest/latest` returns None before any frames are processed
        response = main.latest_ingest()
        self.assertTrue(response["ok"])
        self.assertIsNone(response["data"])


if __name__ == '__main__':
    unittest.main()
