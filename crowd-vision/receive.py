from __future__ import annotations

import argparse
import json
import time
from typing import Any, Optional
from urllib.parse import urlparse

import httpx


def _normalize_server_link(server_link: str) -> str:
	parsed = urlparse(server_link)
	if not parsed.scheme:
		raise ValueError("server_link must include a scheme, for example http://localhost:8000")
	if parsed.path in ("", "/"):
		return server_link.rstrip("/") + "/ingest"
	return server_link


def _latest_link(server_link: str) -> str:
	normalized = _normalize_server_link(server_link)
	if normalized.endswith("/ingest"):
		return normalized + "/latest"
	return normalized.rstrip("/") + "/latest"


def _print_summary(data: dict[str, Any]) -> None:
	frame_index = data.get("frame_index")
	source = data.get("source")
	result = data.get("result") or {}
	num_tracks = result.get("num_tracks")
	tracks = result.get("tracks") or []
	dense_flow = result.get("dense_flow")
	print(
		f"[ok] frame_index={frame_index} num_tracks={num_tracks} "
		f"tracks_len={len(tracks)} dense_flow={'yes' if dense_flow else 'no'} source={source}"
	)


def receive(server_link: str, poll_interval: float, duration: int, print_json: bool) -> None:
	latest_link = _latest_link(server_link)
	deadline = time.time() + duration if duration > 0 else None
	last_seen_frame_index: Optional[int] = None

	print(f"[info] Listening for outputs at: {latest_link}")
	with httpx.Client(timeout=5.0) as client:
		while True:
			if deadline is not None and time.time() >= deadline:
				print("[info] Receiver stopped (duration reached).")
				return

			try:
				response = client.get(latest_link)
				response.raise_for_status()
				payload = response.json()
			except (httpx.HTTPError, ValueError) as exc:
				print(f"[warn] Receive request failed: {exc}")
				time.sleep(poll_interval)
				continue

			data = payload.get("data") if isinstance(payload, dict) else None
			if not data:
				print("[wait] No ingested payload yet.")
				time.sleep(poll_interval)
				continue

			if not isinstance(data, dict):
				print(f"[warn] Unexpected payload format: {data}")
				time.sleep(poll_interval)
				continue

			frame_index = data.get("frame_index")
			if frame_index == last_seen_frame_index:
				time.sleep(poll_interval)
				continue

			last_seen_frame_index = frame_index
			_print_summary(data)
			if print_json:
				print(json.dumps(data, indent=2, sort_keys=True))

			time.sleep(poll_interval)


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Receive and display model outputs from FastAPI ingest endpoint.")
	parser.add_argument(
		"--server_link",
		default="http://127.0.0.1:8000",
		help="FastAPI server base URL or ingest URL.",
	)
	parser.add_argument(
		"--poll_interval",
		type=float,
		default=1.0,
		help="Polling interval in seconds.",
	)
	parser.add_argument(
		"--duration",
		type=int,
		default=0,
		help="How long to run in seconds. Use 0 for no timeout.",
	)
	parser.add_argument(
		"--print_json",
		action="store_true",
		help="Print full payload JSON for each new frame.",
	)
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	receive(
		server_link=args.server_link,
		poll_interval=args.poll_interval,
		duration=args.duration,
		print_json=args.print_json,
	)


if __name__ == "__main__":
	main()
