from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from itertools import product
from pathlib import Path
from typing import Iterable

from src.api import simulate_payload_bulk, step
from src.backend.python_backend import PythonBackend
from src.core.state import AgentState, SimState
from src.core.terrain import build_default_terrain
from src.core.validators import build_occupancy
from src.movement.hardcoded import AgentVectorPolicy


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    rows: int
    cols: int
    agents: int
    iterations: int
    avg_step_time_ms: float
    steps_per_sec: float
    estimated_state_bytes: int


@dataclass(frozen=True)
class BenchmarkResult:
    scenarios: tuple[ScenarioResult, ...]

    def to_dict(self) -> dict[str, object]:
        return {"scenarios": [asdict(scenario) for scenario in self.scenarios]}


def _estimate_state_bytes(rows: int, cols: int, agent_count: int) -> int:
    return rows * cols * 8 + agent_count * 64


def _build_state(rows: int, cols: int, agent_count: int) -> SimState:
    agents = {}
    cells = list(product(range(rows), range(cols)))
    if agent_count > len(cells):
        raise ValueError("agent_count cannot exceed the number of grid cells")

    for index in range(agent_count):
        row, col = cells[index]
        agents[index + 1] = AgentState(
            agent_id=index + 1,
            row=row,
            col=col,
            d_row=-1.0 if index % 2 == 0 else 0.0,
            d_col=1.0 if index % 2 == 0 else -1.0,
            will=1.0 - (index % 5) * 0.1,
        )

    occupancy = build_occupancy((rows, cols), agents)
    terrain = build_default_terrain((rows, cols))
    return SimState(occupancy=occupancy, terrain=terrain, agents=agents)


def _run_single_scenario(
    name: str,
    rows: int,
    cols: int,
    agent_count: int,
    iterations: int,
) -> ScenarioResult:
    backend = PythonBackend()
    policy = AgentVectorPolicy()
    state = _build_state(rows, cols, agent_count)

    start_ns = time.perf_counter_ns()
    for _ in range(iterations):
        result = step(state, policy=policy, backend=backend)
        state = result.state
    elapsed_ns = time.perf_counter_ns() - start_ns

    avg_step_time_ms = elapsed_ns / iterations / 1_000_000.0
    steps_per_sec = 1_000_000_000.0 / (elapsed_ns / iterations)

    return ScenarioResult(
        name=name,
        rows=rows,
        cols=cols,
        agents=agent_count,
        iterations=iterations,
        avg_step_time_ms=avg_step_time_ms,
        steps_per_sec=steps_per_sec,
        estimated_state_bytes=_estimate_state_bytes(rows, cols, agent_count),
    )


def run_benchmarks(iterations: int = 100, scenarios: Iterable[tuple[str, int, int, int]] | None = None) -> BenchmarkResult:
    if scenarios is None:
        scenarios = (
            ("tiny", 10, 10, 5),
            ("small_conflict", 25, 25, 25),
            ("medium_mix", 50, 50, 100),
        )

    results = []
    for name, rows, cols, agent_count in scenarios:
        results.append(_run_single_scenario(name, rows, cols, agent_count, iterations))
    return BenchmarkResult(scenarios=tuple(results))


def run_fast_forward_target_check(
    *,
    rows: int,
    cols: int,
    agent_count: int,
    steps: int,
) -> dict[str, object]:
    """Check whether N simulated steps complete within one wall-clock second."""

    state = _build_state(rows, cols, agent_count)
    payload = {
        "occupancy": state.occupancy,
        "terrain": state.terrain,
        "agents": [
            {
                "agent_id": agent.agent_id,
                "row": agent.row,
                "col": agent.col,
                "d_row": agent.d_row,
                "d_col": agent.d_col,
                "will": agent.will,
            }
            for agent in state.agents.values()
        ],
        "columnar_output": True,
        "metadata": {
            "config_version": "benchmark",
            "policy_version": "hardcoded-v1",
            "seed": 0,
        },
    }

    start_ns = time.perf_counter_ns()
    out = simulate_payload_bulk(payload, steps=steps)
    elapsed_sec = (time.perf_counter_ns() - start_ns) / 1_000_000_000.0
    metadata = out.get("metadata", {}) if isinstance(out, dict) else {}
    executed_steps = int(metadata.get("simulated_steps", steps)) if isinstance(metadata, dict) else steps
    early_converged = bool(metadata.get("early_converged", False)) if isinstance(metadata, dict) else False

    steps_per_sec = executed_steps / elapsed_sec if elapsed_sec > 0 else float("inf")

    return {
        "rows": rows,
        "cols": cols,
        "agents": agent_count,
        "requested_steps": steps,
        "executed_steps": executed_steps,
        "early_converged": early_converged,
        "elapsed_sec": elapsed_sec,
        "steps_per_sec": steps_per_sec,
        "target_steps_per_sec": float(steps),
        "meets_minute_in_second": elapsed_sec <= 1.0 and executed_steps >= steps,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run repeatable crowd ABM CPU benchmarks.")
    parser.add_argument("--iterations", type=int, default=100, help="Number of simulation steps per scenario.")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON output file.")
    parser.add_argument("--target-check", action="store_true", help="Run minute-in-second target check.")
    parser.add_argument("--rows", type=int, default=400, help="Rows for target-check payload.")
    parser.add_argument("--cols", type=int, default=400, help="Cols for target-check payload.")
    parser.add_argument("--agents", type=int, default=100000, help="Agent count for target-check payload.")
    parser.add_argument("--steps", type=int, default=60, help="Step count for target-check run.")
    args = parser.parse_args(argv)

    if args.target_check:
        payload = run_fast_forward_target_check(
            rows=args.rows,
            cols=args.cols,
            agent_count=args.agents,
            steps=args.steps,
        )
    else:
        result = run_benchmarks(iterations=args.iterations)
        payload = result.to_dict()

    if args.output is not None:
        args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    else:
        print(json.dumps(payload, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
