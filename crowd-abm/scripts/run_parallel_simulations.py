from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

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


def _write_status(
    output_dir: Path,
    run_id: int,
    step: int,
    diagnostics: dict[str, float | int],
    elapsed_sec: float,
    rows: int,
    cols: int,
    agent_count: int,
    step_length_m: float,
    tick_seconds: float,
    nominal_avg_steps_per_tick: float,
    cumulative_distance_m: float,
    cumulative_distance_per_agent_m: float,
) -> None:
    run_dir = output_dir / f"run_{run_id:03d}"
    run_dir.mkdir(parents=True, exist_ok=True)

    status_payload = {
        "run_id": run_id,
        "step": step,
        "rows": rows,
        "cols": cols,
        "agents": agent_count,
        "elapsed_sec": elapsed_sec,
        "diagnostics": diagnostics,
        "movement_metrics": {
            "step_length_m": step_length_m,
            "tick_seconds": tick_seconds,
            "nominal_avg_steps_per_tick": nominal_avg_steps_per_tick,
            "nominal_avg_speed_m_per_s": (nominal_avg_steps_per_tick * step_length_m) / tick_seconds,
            "observed_avg_displacement_steps": diagnostics["avg_displacement"],
            "observed_avg_distance_m": diagnostics["avg_displacement"] * step_length_m,
            "observed_avg_speed_m_per_s": (diagnostics["avg_displacement"] * step_length_m) / tick_seconds,
            "cumulative_distance_m": cumulative_distance_m,
            "cumulative_distance_per_agent_m": cumulative_distance_per_agent_m,
        },
    }

    report_path = run_dir / f"status_step_{step:04d}.json"
    report_path.write_text(json.dumps(status_payload, indent=2), encoding="utf-8")


def run_parallel(
    *,
    runs: int,
    rows: int,
    cols: int,
    agent_count: int,
    total_steps: int,
    report_every: int,
    output_dir: Path,
    step_length_m: float,
    tick_seconds: float,
    nominal_avg_steps_per_tick: float,
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

    states = []
    for _ in range(runs):
        occupancy, terrain, agent_id, row, col, d_row, d_col, will = _build_state(rows, cols, agent_count)
        states.append(
            {
                "occupancy": occupancy,
            "terrain": terrain,
                "agent_id": agent_id,
                "row": row,
                "col": col,
                "d_row": d_row,
                "d_col": d_col,
                "will": will,
                "step": 0,
                "last_diagnostics": {
                    "moved_count": 0,
                    "blocked_count": agent_count,
                    "conflict_count": 0,
                    "avg_displacement": 0.0,
                    "tie_break_count": 0,
                    "avg_winner_will": 0.0,
                },
                "cumulative_distance_m": 0.0,
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    start = time.perf_counter()
    global_step = 0

    while True:
        all_done = True
        for run_idx, state in enumerate(states, start=1):
            if int(state["step"]) >= total_steps:
                continue

            all_done = False
            direction = directions[(global_step + run_idx) % len(directions)]
            state["d_row"].fill(direction[0])
            state["d_col"].fill(direction[1])

            next_occupancy, next_row, next_col, diagnostics = _step_arrays(
                state["occupancy"],
                state["terrain"],
                state["agent_id"],
                state["row"],
                state["col"],
                state["d_row"],
                state["d_col"],
                state["will"],
            )

            state["occupancy"] = next_occupancy
            state["row"] = next_row
            state["col"] = next_col
            state["step"] = int(state["step"]) + 1
            state["last_diagnostics"] = diagnostics
            state["cumulative_distance_m"] = float(state["cumulative_distance_m"]) + (
                float(diagnostics["moved_count"]) * float(diagnostics["avg_displacement"]) * step_length_m
            )

            cumulative_distance_per_agent_m = float(state["cumulative_distance_m"]) / float(agent_count)

            if int(state["step"]) % report_every == 0:
                _write_status(
                    output_dir=output_dir,
                    run_id=run_idx,
                    step=int(state["step"]),
                    diagnostics=diagnostics,
                    elapsed_sec=time.perf_counter() - start,
                    rows=rows,
                    cols=cols,
                    agent_count=agent_count,
                    step_length_m=step_length_m,
                    tick_seconds=tick_seconds,
                    nominal_avg_steps_per_tick=nominal_avg_steps_per_tick,
                    cumulative_distance_m=float(state["cumulative_distance_m"]),
                    cumulative_distance_per_agent_m=cumulative_distance_per_agent_m,
                )

        if all_done:
            break
        global_step += 1

    elapsed_sec = time.perf_counter() - start
    summary = {
        "runs": runs,
        "rows": rows,
        "cols": cols,
        "agents": agent_count,
        "total_steps_per_run": total_steps,
        "report_every_steps": report_every,
        "step_length_m": step_length_m,
        "tick_seconds": tick_seconds,
        "nominal_avg_steps_per_tick": nominal_avg_steps_per_tick,
        "nominal_avg_speed_m_per_s": (nominal_avg_steps_per_tick * step_length_m) / tick_seconds,
        "elapsed_sec": elapsed_sec,
        "steps_per_sec_all_runs": (runs * total_steps) / elapsed_sec if elapsed_sec > 0 else 0.0,
        "output_dir": str(output_dir),
    }

    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run parallel crowd simulations with periodic status reports.")
    parser.add_argument("--runs", type=int, default=50)
    parser.add_argument("--rows", type=int, default=400)
    parser.add_argument("--cols", type=int, default=400)
    parser.add_argument("--agents", type=int, default=100000)
    parser.add_argument("--total-steps", type=int, default=15 * 60)
    parser.add_argument("--report-every", type=int, default=60)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/parallel_runs"))
    parser.add_argument("--step-length-m", type=float, default=1.0)
    parser.add_argument("--tick-seconds", type=float, default=1.0)
    parser.add_argument("--nominal-avg-steps-per-tick", type=float, default=1.0)
    args = parser.parse_args()

    if args.total_steps <= 0:
        raise ValueError("--total-steps must be positive")
    if args.report_every <= 0:
        raise ValueError("--report-every must be positive")
    if args.total_steps % args.report_every != 0:
        raise ValueError("--total-steps must be divisible by --report-every")
    if args.step_length_m <= 0:
        raise ValueError("--step-length-m must be positive")
    if args.tick_seconds <= 0:
        raise ValueError("--tick-seconds must be positive")
    if args.nominal_avg_steps_per_tick <= 0:
        raise ValueError("--nominal-avg-steps-per-tick must be positive")

    summary = run_parallel(
        runs=args.runs,
        rows=args.rows,
        cols=args.cols,
        agent_count=args.agents,
        total_steps=args.total_steps,
        report_every=args.report_every,
        output_dir=args.output_dir,
        step_length_m=args.step_length_m,
        tick_seconds=args.tick_seconds,
        nominal_avg_steps_per_tick=args.nominal_avg_steps_per_tick,
    )

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
