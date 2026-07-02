from __future__ import annotations

import argparse
import json
import time

import numpy as np

from src.scalable.bulk import _step_arrays


def _build_state(
    rows: int,
    cols: int,
    agent_count: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if agent_count > rows * cols:
        raise ValueError("agent_count cannot exceed rows * cols")

    agent_id = np.arange(1, agent_count + 1, dtype=np.int64)
    row = np.empty(agent_count, dtype=np.int64)
    col = np.empty(agent_count, dtype=np.int64)
    d_row = np.empty(agent_count, dtype=np.float64)
    d_col = np.empty(agent_count, dtype=np.float64)
    will = np.full(agent_count, 0.5, dtype=np.float64)

    idx = 0
    for r in range(rows):
        for c in range(cols):
            if idx >= agent_count:
                break
            row[idx] = r
            col[idx] = c
            idx += 1
        if idx >= agent_count:
            break

    occupancy = np.full((rows, cols), -1, dtype=np.int64)
    terrain = np.full((rows, cols), -1, dtype=np.int64)
    occupancy[row, col] = agent_id

    return occupancy, terrain, agent_id, row, col, d_row, d_col, will


def benchmark_steps_per_second(
    *,
    rows: int,
    cols: int,
    agent_count: int,
    benchmark_seconds: int,
) -> float:
    occupancy, terrain, agent_id, row, col, d_row, d_col, will = _build_state(rows, cols, agent_count)

    directions = np.array(
        [
            (-1.0, 0.0),
            (-1.0, 1.0),
            (0.0, 1.0),
            (1.0, 1.0),
            (1.0, 0.0),
            (1.0, -1.0),
            (0.0, -1.0),
            (-1.0, -1.0),
        ],
        dtype=np.float64,
    )

    iterations = 0
    start = time.perf_counter()
    while time.perf_counter() - start < benchmark_seconds:
        direction = directions[iterations % len(directions)]
        d_row.fill(direction[0])
        d_col.fill(direction[1])
        occupancy, row, col, _ = _step_arrays(
            occupancy,
            terrain,
            agent_id,
            row,
            col,
            d_row,
            d_col,
            will,
        )
        iterations += 1

    elapsed = time.perf_counter() - start
    return iterations / elapsed


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate max 1Hz instance count from measured single-instance throughput.")
    parser.add_argument("--rows", type=int, default=400)
    parser.add_argument("--cols", type=int, default=400)
    parser.add_argument("--agents", type=int, default=100000)
    parser.add_argument("--benchmark-seconds", type=int, default=20)
    parser.add_argument("--target-hz", type=float, default=1.0)
    parser.add_argument("--headroom", type=float, default=0.8, help="Safety factor (e.g. 0.8 keeps 20% headroom)")
    args = parser.parse_args()

    steps_per_second = benchmark_steps_per_second(
        rows=args.rows,
        cols=args.cols,
        agent_count=args.agents,
        benchmark_seconds=args.benchmark_seconds,
    )

    raw_capacity_instances = steps_per_second / args.target_hz
    safe_capacity_instances = int(raw_capacity_instances * args.headroom)

    result = {
        "rows": args.rows,
        "cols": args.cols,
        "agents": args.agents,
        "benchmark_seconds": args.benchmark_seconds,
        "measured_steps_per_second": steps_per_second,
        "target_hz_per_instance": args.target_hz,
        "raw_capacity_instances": raw_capacity_instances,
        "headroom_factor": args.headroom,
        "safe_capacity_instances": safe_capacity_instances,
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
