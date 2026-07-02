# uv run python main.py --camera_link http://10.42.0.205:4747/video
from __future__ import annotations

import argparse
import signal
import subprocess
import sys
import time
from typing import Optional

import httpx


def _wait_for_server(base_server_link: str, timeout_seconds: float) -> bool:
    latest_endpoint = base_server_link.rstrip("/") + "/ingest/latest"
    deadline = time.time() + timeout_seconds

    with httpx.Client(timeout=1.0) as client:
        while time.time() < deadline:
            try:
                response = client.get(latest_endpoint)
                if response.status_code < 500:
                    return True
            except httpx.HTTPError:
                pass
            time.sleep(0.5)

    return False


def _terminate_process(proc: Optional[subprocess.Popen], name: str) -> None:
    if proc is None or proc.poll() is not None:
        return

    print(f"[info] Stopping {name} (pid={proc.pid})")
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except KeyboardInterrupt:
        # User pressed Ctrl+C again while we are shutting down.
        print(f"[warn] Interrupt during shutdown; force-killing {name} (pid={proc.pid})")
        proc.kill()
        try:
            proc.wait(timeout=5)
        except Exception:
            pass
    except subprocess.TimeoutExpired:
        print(f"[warn] Force-killing {name} (pid={proc.pid})")
        proc.kill()
        proc.wait(timeout=5)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run all three components together: FastAPI receiver server, "
            "camera sender, and receiver checker."
        )
    )
    parser.add_argument("--camera_link", required=True, help="Camera/video stream URL.")
    parser.add_argument("--host", default="0.0.0.0", help="Host for FastAPI receiver server.")
    parser.add_argument("--port", type=int, default=8000, help="Port for FastAPI receiver server.")
    parser.add_argument("--model_path", default="yolov8n.pt", help="YOLO model path used by sender.")
    parser.add_argument("--max_fps", type=int, default=30, help="Max processing FPS for sender.")
    parser.add_argument(
        "--check_poll_interval",
        type=float,
        default=1.0,
        help="Polling interval (seconds) for receiver checker.",
    )
    parser.add_argument(
        "--check_duration",
        type=int,
        default=0,
        help="Receiver checker duration in seconds. Use 0 for no timeout.",
    )
    parser.add_argument(
        "--startup_timeout",
        type=float,
        default=15.0,
        help="How long to wait for FastAPI server startup (seconds).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    base_server_link = f"http://127.0.0.1:{args.port}"
    print(f"[info] Receiver base URL: {base_server_link}")

    server_proc: Optional[subprocess.Popen] = None
    sender_proc: Optional[subprocess.Popen] = None
    checker_proc: Optional[subprocess.Popen] = None

    try:
        print("[info] Starting FastAPI receiver server")
        server_proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "crowd_vision.api:app",
                "--host",
                args.host,
                "--port",
                str(args.port),
            ]
        )

        if not _wait_for_server(base_server_link, timeout_seconds=args.startup_timeout):
            raise RuntimeError("FastAPI server did not become ready in time")

        print("[info] Starting sender")
        sender_proc = subprocess.Popen(
            [
                sys.executable,
                "runner.py",
                "--server_link",
                base_server_link,
                "--camera_link",
                args.camera_link,
                "--model_path",
                args.model_path,
                "--max_fps",
                str(args.max_fps),
            ]
        )

        print("[info] Starting receiver checker")
        checker_proc = subprocess.Popen(
            [
                sys.executable,
                "runner.py",
                "--server_link",
                base_server_link,
                "--check_receiver",
                "--check_poll_interval",
                str(args.check_poll_interval),
                "--check_duration",
                str(args.check_duration),
            ]
        )

        while True:
            if server_proc.poll() is not None:
                raise RuntimeError("FastAPI receiver server exited unexpectedly")

            if sender_proc.poll() is not None:
                print("[info] Sender exited")
                break

            if checker_proc is not None and checker_proc.poll() is not None:
                print("[info] Receiver checker completed")
                checker_proc = None

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[info] Stopping all processes on Ctrl+C")
    finally:
        _terminate_process(checker_proc, "receiver checker")
        _terminate_process(sender_proc, "sender")
        _terminate_process(server_proc, "FastAPI receiver server")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.default_int_handler)
    main()
