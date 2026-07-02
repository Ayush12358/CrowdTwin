# crowd-vision

Crowd tracking and movement vector extraction for CCTV/RTSP-style video sources.

## What it does

1. Reads frames from a video file, webcam, or live stream with OpenCV
2. Detects and tracks people with YOLOv8 + ByteTrack
3. Computes position, velocity, and speed for each track
4. Optionally maps image coordinates into world coordinates with homography
5. Falls back to optical flow for dense crowd movement
6. Exposes results through a FastAPI receiver endpoint

## Installation

Using `uv`:

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Quick start

Run the pipeline directly on a local video file:

```bash
PYTHONPATH=. uv run python3 main.py --server_link http://127.0.0.1:8000 --camera_link input.mp4
```

## One-command workflow

To run the FastAPI receiver, the camera sender, and the receiver checker together:

```bash
PYTHONPATH=. uv run python3 run_all.py --camera_link http://10.42.0.205:4747/video
```

That script starts:

1. `uvicorn crowd_vision.api:app`
2. the sender in `main.py`
3. the receiver checker in `main.py`

Useful flags:

```bash
PYTHONPATH=. uv run python3 run_all.py --camera_link http://10.42.0.205:4747/video --check_duration 0
PYTHONPATH=. uv run python3 run_all.py --camera_link http://10.42.0.205:4747/video --max_fps 20
```

`--check_duration 0` means the checker keeps polling until you stop the process.

## Camera source

The `--camera_link` argument can be:

- a video file path such as `input.mp4`
- a webcam index supported by OpenCV
- a live stream URL such as `http://10.42.0.205:4747/video`

If you pass an `https://` stream URL and OpenCV cannot open it, the sender will try the same URL over `http://` automatically.

## API receiver

Start the API manually:

```bash
PYTHONPATH=. uv run uvicorn crowd_vision.api:app --host 0.0.0.0 --port 8000
```

Send one frame through the API endpoint:

```bash
curl -X POST http://localhost:8000/process/single \
  -H "Content-Type: application/json" \
  -d '{"source":"input.mp4"}'
```

### `/process/single` response

The API returns the full pipeline result:

```json
{
  "tracks": [
    {
      "id": 12,
      "position": [3.2, 5.1],
      "velocity": [0.5, -0.2],
      "speed": 0.54
    }
  ],
  "dense_flow": null,
  "num_tracks": 1
}
```

### `/ingest` payload

The sender posts each processed frame to `/ingest` with this shape:

```json
{
  "source": "input.mp4",
  "frame_index": 0,
  "timestamp": 0.0,
  "result": {
    "tracks": [],
    "dense_flow": null,
    "num_tracks": 0
  }
}
```

### `/ingest/latest` response

The receiver stores the latest payload under `data`:

```json
{
  "ok": true,
  "data": {
    "source": "input.mp4",
    "frame_index": 0,
    "timestamp": 0.0,
    "result": {
      "tracks": [],
      "dense_flow": null,
      "num_tracks": 0
    }
  }
}
```

## Receive output in a separate script

Use `receive.py` to print the latest ingested output:

```bash
PYTHONPATH=. uv run python3 receive.py --server_link http://127.0.0.1:8000
```

Print full JSON for each new frame:

```bash
PYTHONPATH=. uv run python3 receive.py --server_link http://127.0.0.1:8000 --print_json
```

## Plot output

Use `show.py` to plot track points and velocity vectors from the ingest endpoint:

```bash
PYTHONPATH=. uv run python3 show.py --server_link http://127.0.0.1:8000
```

In a headless environment, `show.py` saves the latest plot to `live_plot.png` by default.

## Homography calibration

Pass paired points in image and world coordinates:

```python
import numpy as np
from crowd_vision.pipeline import CrowdVisionPipeline

image_points = np.array([[100, 200], [400, 200], [120, 500], [450, 500]], dtype=np.float32)
world_points = np.array([[0, 0], [10, 0], [0, 20], [10, 20]], dtype=np.float32)

pipeline = CrowdVisionPipeline(homography_points=(image_points, world_points))
```

## Notes

- Frames larger than 480p are automatically downscaled to keep inference fast.
- `main.py` runs the sender loop.
- `run_all.py` launches the sender, receiver, and checker together.
- `receive.py` reads the latest ingested payload.
- `show.py` visualizes the latest track positions and velocity vectors.
