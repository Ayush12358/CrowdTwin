from __future__ import annotations

import argparse
import sys
import threading
import time
from typing import Any, Dict, List, Optional

import cv2
from fastapi import FastAPI
import numpy as np
import supervision as sv
from ultralytics import YOLO
import uvicorn

app = FastAPI(title="CrowdTwin Vision Ingest Service")

# Thread-safe global storage for the latest tracked state
_tracks_lock = threading.Lock()
_latest_tracks: Optional[Dict[str, Any]] = None
_running = True

# Track history cache to compute velocity: track_id -> (last_x, last_y, last_timestamp)
_track_history: Dict[int, tuple[float, float, float]] = {}


def process_single_frame(
    frame: np.ndarray,
    model: YOLO,
    tracker: sv.ByteTrack,
    current_timestamp: float
) -> List[Dict[str, Any]]:
    """Resizes frame, runs YOLO prediction, tracks detections, and calculates velocities."""
    # Downscale frame for speed if height exceeds 480px
    height, width = frame.shape[:2]
    if height > 480:
        scale = 480.0 / height
        frame = cv2.resize(frame, (int(width * scale), 480))

    # Run YOLOv8 detection
    results = model(frame, verbose=False)[0]
    detections = sv.Detections.from_ultralytics(results)

    # Filter detections for person class only (class ID 0 in COCO model)
    detections = detections[detections.class_id == 0]

    # Update ByteTrack tracker
    tracked_detections = tracker.update_with_detections(detections)

    tracks_payload = []

    if tracked_detections.tracker_id is not None:
        for bbox, tracker_id in zip(tracked_detections.xyxy, tracked_detections.tracker_id):
            # Calculate center point of bounding box
            x_center = float((bbox[0] + bbox[2]) / 2.0)
            y_center = float((bbox[1] + bbox[3]) / 2.0)

            # Compute velocity based on tracker_id history
            vx, vy, speed = 0.0, 0.0, 0.0
            if tracker_id in _track_history:
                last_x, last_y, last_t = _track_history[tracker_id]
                dt = current_timestamp - last_t
                if dt > 0.01:
                    vx = (x_center - last_x) / dt
                    vy = (y_center - last_y) / dt
                    speed = float((vx**2 + vy**2)**0.5)

            # Update history cache
            _track_history[tracker_id] = (x_center, y_center, current_timestamp)

            tracks_payload.append({
                "id": int(tracker_id),
                "position": [x_center, y_center],
                "velocity": [vx, vy],
                "speed": speed
            })

    return tracks_payload


def capture_and_track_loop(camera_link: str, model_path: str, max_fps: int) -> None:
    """Continuously captures frames, runs inference/tracking, and computes velocities."""
    global _latest_tracks, _running

    if max_fps <= 0:
        raise ValueError("max_fps must be a positive integer greater than 0")

    print(f"[Vision] Initializing YOLO model: {model_path}")
    model = YOLO(model_path)
    tracker = sv.ByteTrack()

    # Coerce digit-only camera link to integer for local webcam indexes
    if isinstance(camera_link, str) and camera_link.isdigit():
        source: Any = int(camera_link)
    else:
        source = camera_link

    print(f"[Vision] Opening camera stream: {source}")
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[Error] Failed to open camera stream: {source}")
        return

    frame_index = 0
    fps_delay = 1.0 / max_fps

    while _running:
        start_time = time.time()
        ret, frame = cap.read()
        if not ret:
            # Reconnect or rewind video source if file
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            time.sleep(0.1)
            continue

        current_timestamp = time.time()
        
        # Call pure process function
        tracks_payload = process_single_frame(frame, model, tracker, current_timestamp)

        # Thread-safely update the latest ingested tracks
        with _tracks_lock:
            _latest_tracks = {
                "source": str(source),
                "frame_index": frame_index,
                "timestamp": current_timestamp,
                "result": {
                    "num_tracks": len(tracks_payload),
                    "tracks": tracks_payload
                }
            }

        frame_index += 1

        # Enforce max FPS delay
        elapsed = time.time() - start_time
        if elapsed < fps_delay:
            time.sleep(fps_delay - elapsed)

    cap.release()


@app.get("/ingest/latest")
def latest_ingest() -> Dict[str, Any]:
    """Exposes the latest tracking results to the ABM simulator or frontend."""
    with _tracks_lock:
        if _latest_tracks is None:
            return {"ok": True, "data": None}
        return {"ok": True, "data": _latest_tracks}


@app.on_event("shutdown")
def shutdown_event() -> None:
    global _running
    _running = False


def main() -> None:
    parser = argparse.ArgumentParser(description="CrowdTwin Vision Ingestion Service")
    parser.add_argument("--host", default="0.0.0.0", help="FastAPI host link.")
    parser.add_argument("--port", type=int, default=8000, help="FastAPI port.")
    parser.add_argument("--camera_link", required=True, help="Video file or camera stream link.")
    parser.add_argument("--model_path", default="yolov8n.pt", help="Path to YOLOv8 weights.")
    parser.add_argument("--max_fps", type=int, default=30, help="Maximum tracking frame rate.")
    args = parser.parse_args()

    # Start capture/tracking loop in a background daemon thread
    bg_thread = threading.Thread(
        target=capture_and_track_loop,
        args=(args.camera_link, args.model_path, args.max_fps),
        daemon=True
    )
    bg_thread.start()

    print(f"[Vision] Starting API receiver on http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
