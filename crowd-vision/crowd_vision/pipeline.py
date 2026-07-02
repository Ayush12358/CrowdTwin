from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple
import time

if TYPE_CHECKING:
    import numpy as np

from .math_utils import (
    HomographyMapper,
    compute_velocity,
    new_history,
    smooth_point,
    speed_from_velocity,
)
from .models import TrackState, VectorOutput


@dataclass
class PipelineConfig:
    model_path: str = "yolov8n.pt"
    confidence_threshold: float = 0.3
    max_history: int = 120
    smoothing_window: int = 5
    dense_crowd_threshold: int = 80
    max_fps: int = 30


class CrowdVisionPipeline:
    """End-to-end crowd tracking pipeline using YOLOv8 + ByteTrack."""

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        homography_points: Optional[Tuple["np.ndarray", "np.ndarray"]] = None,
    ):
        self.config = config or PipelineConfig()
        self.model = self._load_detector(self.config.model_path)
        self.mapper: Optional[HomographyMapper] = None
        if homography_points is not None:
            image_points, world_points = homography_points
            self.mapper = HomographyMapper(image_points, world_points)

        self.trajectories: Dict[int, TrackState] = {}
        self.smoothed_history = defaultdict(new_history)
        self.prev_frame: Optional["np.ndarray"] = None

    @staticmethod
    def _load_detector(model_path: str):
        from ultralytics import YOLO

        return YOLO(model_path)

    def process_frame(self, frame: "np.ndarray", timestamp: Optional[float] = None) -> Dict[str, object]:
        import cv2

        t = timestamp if timestamp is not None else time.time()

        # Downscale to 480p if the frame is larger to keep inference fast.
        h, w = frame.shape[:2]
        if h > 480:
            scale = 480.0 / h
            frame = cv2.resize(frame, (int(w * scale), 480), interpolation=cv2.INTER_AREA)

        # Built-in track() can use ByteTrack via tracker config.
        results = self.model.track(
            frame,
            persist=True,
            classes=[0],
            conf=self.config.confidence_threshold,
            tracker="bytetrack.yaml",
            verbose=False,
        )

        outputs: List[VectorOutput] = []
        count = 0

        for res in results:
            if res.boxes.id is None:
                continue

            ids = res.boxes.id.cpu().numpy().astype(int)
            xyxy = res.boxes.xyxy.cpu().numpy()

            for track_id, (x1, y1, x2, y2) in zip(ids, xyxy):
                count += 1
                cx = float((x1 + x2) / 2.0)
                cy = float(y2)

                if self.mapper is not None:
                    wx, wy = self.mapper.map_to_world(cx, cy)
                else:
                    wx, wy = cx, cy

                smoothed = smooth_point(
                    self.smoothed_history[track_id], (wx, wy), self.config.smoothing_window
                )

                track = self.trajectories.get(track_id)
                if track is None:
                    track = TrackState(track_id=track_id, max_history=self.config.max_history)
                    self.trajectories[track_id] = track
                track.add_point(smoothed[0], smoothed[1], t)

                vx, vy = compute_velocity(track.trajectory)
                speed = speed_from_velocity(vx, vy)

                outputs.append(
                    VectorOutput(
                        id=track_id,
                        position=(smoothed[0], smoothed[1]),
                        velocity=(vx, vy),
                        speed=speed,
                    )
                )

        dense_flow = None
        if count >= self.config.dense_crowd_threshold:
            dense_flow = self._compute_optical_flow(frame)

        return {
            "tracks": [o.as_dict() for o in outputs],
            "dense_flow": dense_flow,
            "num_tracks": count,
        }

    def _compute_optical_flow(self, frame: "np.ndarray") -> Optional[Dict[str, float]]:
        import cv2
        import numpy as np

        if self.prev_frame is None:
            self.prev_frame = frame.copy()
            return None

        prev_gray = cv2.cvtColor(self.prev_frame, cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        flow = cv2.calcOpticalFlowFarneback(
            prev_gray,
            curr_gray,
            None,
            pyr_scale=0.5,
            levels=3,
            winsize=15,
            iterations=3,
            poly_n=5,
            poly_sigma=1.2,
            flags=0,
        )

        self.prev_frame = frame.copy()

        vx = flow[..., 0]
        vy = flow[..., 1]

        return {
            "avg_vx": float(np.mean(vx)),
            "avg_vy": float(np.mean(vy)),
            "avg_speed": float(np.mean(np.hypot(vx, vy))),
        }

    def run_video(self, source: str) -> None:
        import cv2

        cap = cv2.VideoCapture(source)
        source_fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = 1.0 / self.config.max_fps if self.config.max_fps > 0 else 0.0

        try:
            while True:
                loop_start = time.time()

                ret, frame = cap.read()
                if not ret:
                    break

                timestamp: Optional[float] = None
                pos_msec = cap.get(cv2.CAP_PROP_POS_MSEC)
                if pos_msec > 0:
                    timestamp = pos_msec / 1000.0
                elif source_fps and source_fps > 0:
                    frame_index = cap.get(cv2.CAP_PROP_POS_FRAMES)
                    if frame_index > 0:
                        timestamp = (frame_index - 1) / source_fps

                _ = self.process_frame(frame, timestamp=timestamp)

                # Sleep to enforce max FPS cap
                if frame_interval > 0:
                    elapsed = time.time() - loop_start
                    sleep_time = frame_interval - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
        finally:
            cap.release()
