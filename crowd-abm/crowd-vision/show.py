
# PYTHONPATH=. uv run python3 show.py --server_link http://127.0.0.1:8000 --output_image live_plot.png
from __future__ import annotations

import argparse
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


def _extract_tracks(data: dict[str, Any]) -> list[dict[str, Any]]:
	result = data.get("result")
	if not isinstance(result, dict):
		return []
	tracks = result.get("tracks")
	if not isinstance(tracks, list):
		return []
	return [t for t in tracks if isinstance(t, dict)]


def _draw_tracks(ax: Any, tracks: list[dict[str, Any]], frame_index: Any) -> None:
	ax.clear()

	if not tracks:
		ax.set_title(f"Frame {frame_index} | no tracks")
		ax.set_xlabel("x")
		ax.set_ylabel("y")
		ax.grid(True, alpha=0.3)
		return

	xs: list[float] = []
	ys: list[float] = []
	vxs: list[float] = []
	vys: list[float] = []

	for track in tracks:
		position = track.get("position")
		velocity = track.get("velocity")
		if not isinstance(position, list) or len(position) != 2:
			continue
		if not isinstance(velocity, list) or len(velocity) != 2:
			continue

		x = float(position[0])
		y = float(position[1])
		vx = float(velocity[0])
		vy = float(velocity[1])
		xs.append(x)
		ys.append(y)
		vxs.append(vx)
		vys.append(vy)

		track_id = track.get("id")
		if track_id is not None:
			ax.text(x, y, str(track_id), fontsize=8, ha="left", va="bottom")

	if not xs:
		ax.set_title(f"Frame {frame_index} | no valid tracks")
		ax.set_xlabel("x")
		ax.set_ylabel("y")
		ax.grid(True, alpha=0.3)
		return

	ax.scatter(xs, ys, s=25)
	ax.quiver(xs, ys, vxs, vys, angles="xy", scale_units="xy", scale=1.0, width=0.003)

	min_x = min(xs)
	max_x = max(xs)
	min_y = min(ys)
	max_y = max(ys)
	pad_x = max((max_x - min_x) * 0.2, 10.0)
	pad_y = max((max_y - min_y) * 0.2, 10.0)

	ax.set_xlim(min_x - pad_x, max_x + pad_x)
	ax.set_ylim(min_y - pad_y, max_y + pad_y)
	ax.set_title(f"Frame {frame_index} | tracks={len(xs)}")
	ax.set_xlabel("x")
	ax.set_ylabel("y")
	ax.grid(True, alpha=0.3)


def show(server_link: str, poll_interval: float, duration: int, output_image: str) -> None:
	try:
		import matplotlib
		import matplotlib.pyplot as plt
	except ImportError as exc:
		raise RuntimeError(
			"matplotlib is required for show.py. Install it with: uv add matplotlib"
		) from exc

	latest_endpoint = _latest_link(server_link)
	deadline = time.time() + duration if duration > 0 else None
	last_seen_frame_index: Optional[Any] = None
	backend = matplotlib.get_backend().lower()
	interactive = not backend.endswith("agg")

	if interactive:
		plt.ion()
	fig, ax = plt.subplots(figsize=(8, 6))
	if interactive and hasattr(fig.canvas.manager, "set_window_title"):
		fig.canvas.manager.set_window_title("Crowd Vision: Track Positions + Velocity")
	ax.set_title("Waiting for first payload...")
	ax.set_xlabel("x")
	ax.set_ylabel("y")
	ax.grid(True, alpha=0.3)
	if interactive:
		plt.show(block=False)

	print(f"[info] Plotting from: {latest_endpoint}")
	if not interactive:
		print(f"[info] Non-interactive backend detected ({backend}); saving frames to {output_image}")

	with httpx.Client(timeout=5.0) as client:
		while True:
			if deadline is not None and time.time() >= deadline:
				print("[info] Plotter stopped (duration reached).")
				break

			if interactive and not plt.fignum_exists(fig.number):
				print("[info] Plot window closed.")
				break

			try:
				response = client.get(latest_endpoint)
				response.raise_for_status()
				payload = response.json()
			except (httpx.HTTPError, ValueError) as exc:
				print(f"[warn] Failed to fetch latest ingest payload: {exc}")
				if interactive:
					plt.pause(0.001)
				time.sleep(poll_interval)
				continue

			data = payload.get("data") if isinstance(payload, dict) else None
			if not isinstance(data, dict):
				if interactive:
					plt.pause(0.001)
				time.sleep(poll_interval)
				continue

			frame_index = data.get("frame_index")
			if frame_index == last_seen_frame_index:
				if interactive:
					plt.pause(0.001)
				time.sleep(poll_interval)
				continue

			tracks = _extract_tracks(data)
			_draw_tracks(ax, tracks, frame_index)
			if interactive:
				fig.canvas.draw_idle()
				plt.pause(0.001)
			else:
				fig.savefig(output_image, dpi=120, bbox_inches="tight")
			last_seen_frame_index = frame_index

			time.sleep(poll_interval)

	if interactive:
		plt.ioff()
	if interactive and plt.fignum_exists(fig.number):
		plt.show()


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Plot track points and velocity vectors from FastAPI ingest output."
	)
	parser.add_argument(
		"--server_link",
		default="http://127.0.0.1:8000",
		help="FastAPI server base URL or ingest URL.",
	)
	parser.add_argument(
		"--poll_interval",
		type=float,
		default=0.2,
		help="Polling interval in seconds.",
	)
	parser.add_argument(
		"--duration",
		type=int,
		default=0,
		help="How long to run in seconds. Use 0 for no timeout.",
	)
	parser.add_argument(
		"--output_image",
		default="live_plot.png",
		help="Output image path used in headless mode (Agg backend).",
	)
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	show(
		server_link=args.server_link,
		poll_interval=args.poll_interval,
		duration=args.duration,
		output_image=args.output_image,
	)


if __name__ == "__main__":
	main()
