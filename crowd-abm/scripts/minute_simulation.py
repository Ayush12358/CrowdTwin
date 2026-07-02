from __future__ import annotations

import json
import time

import numpy as np

from src.scalable.bulk import _step_arrays


def run_minute_simulation(
    *,
    rows: int = 400,
    cols: int = 400,
    agent_count: int = 100_000,
    run_seconds: int = 60,
) -> dict[str, object]:
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

    start = time.perf_counter()
    iterations = 0
    last_diag: dict[str, float | int] = {}

    while time.perf_counter() - start < run_seconds:
        direction = directions[iterations % len(directions)]
        d_row.fill(direction[0])
        d_col.fill(direction[1])
        occupancy, row, col, last_diag = _step_arrays(
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
    return {
        "rows": rows,
        "cols": cols,
        "agents": agent_count,
        "elapsed_sec": elapsed,
        "iterations_executed": iterations,
        "simulated_seconds_at_1hz": iterations,
        "iterations_per_sec": iterations / elapsed if elapsed > 0 else 0.0,
        "last_step_diagnostics": last_diag,
    }


def main() -> None:
    print(json.dumps(run_minute_simulation()))


if __name__ == "__main__":
    main()
