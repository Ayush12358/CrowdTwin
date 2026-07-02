# python main.py --server_link http://localhost:8000 --camera_link http://10.42.0.205:4747/video
from __future__ import annotations

import argparse
import queue
import threading
import time
from typing import Optional
from urllib.parse import urlparse

import cv2
import httpx

from crowd_vision.pipeline import CrowdVisionPipeline, PipelineConfig


def _normalize_server_link(server_link: str) -> str:
	parsed = urlparse(server_link)
	if not parsed.scheme:
		raise ValueError("server_link must include a URL scheme, for example http://localhost:8000")
	if parsed.path in ("", "/"):
		return server_link.rstrip("/") + "/ingest"
	return server_link


def _latest_ingest_link(server_link: str) -> str:
	normalized = _normalize_server_link(server_link)
	if normalized.endswith("/ingest"):
		return normalized + "/latest"
	return normalized.rstrip("/") + "/latest"


def _build_payload(
	source: str,
	frame_index: int,
	timestamp: Optional[float],
	result: dict,
) -> dict:
	return {
		"source": source,
		"frame_index": frame_index,
		"timestamp": timestamp,
		"result": result,
	}


def _to_jsonable(value: object) -> object:
	if value is None or isinstance(value, (str, int, float, bool)):
		return value
	if isinstance(value, dict):
		return {str(k): _to_jsonable(v) for k, v in value.items()}
	if isinstance(value, (list, tuple)):
		return [_to_jsonable(v) for v in value]

	# Handle numpy scalar types without importing numpy.
	if hasattr(value, "item"):
		try:
			return _to_jsonable(value.item())  # type: ignore[no-any-return]
		except Exception:
			pass

	return str(value)


def _sender_worker(server_link: str, payload_queue: "queue.Queue[object]", stop_token: object) -> None:
	last_error_log_at = 0.0
	sent_count = 0
	with httpx.Client(timeout=10.0) as client:
		while True:
			item = payload_queue.get()
			try:
				if item is stop_token:
					return
				assert isinstance(item, dict)
				try:
					json_item = _to_jsonable(item)
					assert isinstance(json_item, dict)
					response = client.post(server_link, json=json_item)
					response.raise_for_status()
					sent_count += 1
					if sent_count == 1 or sent_count % 30 == 0:
						frame_index = item.get("frame_index")
						print(
							f"[ok] Sent payload count={sent_count}, latest_frame_index={frame_index}, endpoint={server_link}"
						)
				except (httpx.HTTPError, TypeError, ValueError) as exc:
					now = time.time()
					if now - last_error_log_at >= 5.0:
						print(f"[warn] Failed to send payload to {server_link}: {exc}")
						last_error_log_at = now
			finally:
				payload_queue.task_done()


def _open_camera_capture(camera_link: str) -> tuple[cv2.VideoCapture, str]:
	cap = cv2.VideoCapture(camera_link)
	if cap.isOpened():
		return cap, camera_link

	parsed = urlparse(camera_link)
	if parsed.scheme == "https":
		fallback_link = parsed._replace(scheme="http").geturl()
		cap.release()
		cap = cv2.VideoCapture(fallback_link)
		if cap.isOpened():
			print(
				f"[info] HTTPS stream could not be opened, using HTTP fallback for camera source: {fallback_link}"
			)
			return cap, fallback_link

	error_message = (
		f"Unable to open camera source: {camera_link}. "
		"If your camera app serves MJPEG over plain HTTP (common on phone camera apps), "
		"use an http:// URL instead of https://."
	)
	raise RuntimeError(error_message)


def run(camera_link: str, server_link: str, model_path: str, max_fps: int) -> None:
	pipeline = CrowdVisionPipeline(PipelineConfig(model_path=model_path, max_fps=max_fps))
	cap, active_camera_link = _open_camera_capture(camera_link)

	normalized_server_link = _normalize_server_link(server_link)
	print(f"[info] Camera source opened: {active_camera_link}")
	print(f"[info] Sending model outputs to: {normalized_server_link}")
	payload_queue: "queue.Queue[object]" = queue.Queue(maxsize=256)
	stop_token = object()
	sender = threading.Thread(
		target=_sender_worker,
		args=(normalized_server_link, payload_queue, stop_token),
		daemon=True,
	)
	sender.start()

	source_fps = cap.get(cv2.CAP_PROP_FPS)
	frame_interval = 1.0 / max_fps if max_fps > 0 else 0.0
	frame_index = 0
	processed_frames = 0

	try:
		while True:
			loop_start = time.time()
			ret, frame = cap.read()
			if not ret:
				if processed_frames == 0:
					print(
						"[warn] Camera opened but no frames were read. "
						"Check the camera stream URL and whether the stream is currently active."
					)
				break

			timestamp: Optional[float] = None
			pos_msec = cap.get(cv2.CAP_PROP_POS_MSEC)
			if pos_msec > 0:
				timestamp = pos_msec / 1000.0
			elif source_fps and source_fps > 0:
				frame_pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
				if frame_pos > 0:
					timestamp = (frame_pos - 1) / source_fps

			result = pipeline.process_frame(frame, timestamp=timestamp)
			payload = _build_payload(active_camera_link, frame_index, timestamp, result)
			processed_frames += 1
			if processed_frames == 1:
				print("[info] First frame processed and queued for sending")

			try:
				payload_queue.put_nowait(payload)
			except queue.Full:
				try:
					_ = payload_queue.get_nowait()
					payload_queue.task_done()
				except queue.Empty:
					pass
				payload_queue.put_nowait(payload)

			frame_index += 1

			if frame_interval > 0:
				elapsed = time.time() - loop_start
				sleep_time = frame_interval - elapsed
				if sleep_time > 0:
					time.sleep(sleep_time)
	finally:
		cap.release()
		payload_queue.put(stop_token)
		sender.join(timeout=10.0)

	if processed_frames == 0:
		raise RuntimeError(
			"No frames were processed from the camera source. "
			"Try the exact HTTP URL from your camera app preview and verify the stream is live."
		)


def check_receiver(server_link: str, poll_interval: float, duration: int) -> None:
	latest_link = _latest_ingest_link(server_link)
	deadline = time.time() + duration if duration > 0 else None
	last_seen_frame_index: Optional[int] = None

	print(f"[info] Polling receiver at: {latest_link}")
	with httpx.Client(timeout=5.0) as client:
		while True:
			if deadline is not None and time.time() >= deadline:
				print("[info] Receiver check completed (duration reached).")
				return

			try:
				response = client.get(latest_link)
				response.raise_for_status()
				payload = response.json()
			except (httpx.HTTPError, ValueError) as exc:
				print(f"[warn] Receiver check request failed: {exc}")
				time.sleep(poll_interval)
				continue

			data = payload.get("data") if isinstance(payload, dict) else None
			if not data:
				print("[wait] No ingested payload yet.")
				time.sleep(poll_interval)
				continue

			frame_index = data.get("frame_index")
			num_tracks = (data.get("result") or {}).get("num_tracks")
			source = data.get("source")

			if frame_index != last_seen_frame_index:
				print(
					f"[ok] Received frame_index={frame_index}, num_tracks={num_tracks}, source={source}"
				)
				last_seen_frame_index = frame_index

			time.sleep(poll_interval)


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Run crowd vision processing and stream outputs to a server.")
	parser.add_argument(
		"--server_link",
		required=True,
		help="HTTP endpoint that receives the model output. If only a base URL is given, /ingest is appended.",
	)
	parser.add_argument(
		"--camera_link",
		default=None,
		help="Camera, video file, or stream URL that OpenCV can read.",
	)
	parser.add_argument(
		"--model_path",
		default="yolov8n.pt",
		help="Path to the YOLO model to use.",
	)
	parser.add_argument(
		"--max_fps",
		type=int,
		default=30,
		help="Maximum processing FPS.",
	)
	parser.add_argument(
		"--check_receiver",
		action="store_true",
		help="Poll the FastAPI receiver endpoint to verify ingested payload updates.",
	)
	parser.add_argument(
		"--check_poll_interval",
		type=float,
		default=1.0,
		help="Polling interval (seconds) for --check_receiver mode.",
	)
	parser.add_argument(
		"--check_duration",
		type=int,
		default=30,
		help="How long to poll in seconds for --check_receiver mode. Use 0 for no timeout.",
	)
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	if args.check_receiver:
		check_receiver(
			server_link=args.server_link,
			poll_interval=args.check_poll_interval,
			duration=args.check_duration,
		)
		return

	if not args.camera_link:
		raise ValueError("--camera_link is required unless --check_receiver is used")

	run(
		camera_link=args.camera_link,
		server_link=args.server_link,
		model_path=args.model_path,
		max_fps=args.max_fps,
	)


if __name__ == "__main__":
	main()
