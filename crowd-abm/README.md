# Crowd ABM

Uses matrix based approach to model crowd movement. Moving all calculations to the GPU using CUDA. This allows for very large crowds to be simulated in faster than real time.

We already receive a map of all the people in the crowd every 1 second. This library will focus on one thing: taking in a map and running the simulation. Repeating the above every one second will be handled by another script.

This is to be built from scratch. We will not use Mesa or any other ABM library. We will use NumPy and CuPy for matrix operations, and Numba for JIT compilation where it helps.

## Goal

Build a simulation core that accepts a crowd map and movement inputs, updates agent positions according to behavior rules, and returns the next state of the map. The behavior policy should start as hardcoded rules, but later become trainable from data.

## Scope

In scope:

- Single-step simulation updates
- Crowd movement on a discrete 2D grid
- Collision handling and occupancy constraints
- CPU-first implementation with GPU acceleration as an optimization layer

Out of scope:

- Long-running orchestration that calls the simulator every second
- Visualization and UI
- Complex behavior models that depend on external ABM frameworks

## Inputs And Outputs

### Inputs

- Current crowd map
- Per-agent movement vectors or intended directions
- Optional map metadata such as obstacles, boundaries, and cell capacity

### Outputs

- Updated crowd map after one simulation step
- Optional diagnostics such as moved agents, blocked agents, and collisions

## Core Model

### State

- Number of agents
- 2D grid dimensions, coordinate system, and obstacle layout
- Agent positions, velocities, and occupancy state
- Neighbor relationships for the eight movement directions
- Agent behavior vectors or policy matrix

### Fixed Behavior Rules

- How agents choose or accept movement on a 2D grid
- How agents resolve conflicts when multiple agents target the same cell
- How walls, blocked cells, and occupied cells are handled
- How direction vectors map to the eight neighboring cells
- Whether movement is synchronous or resolved in phases
- Which parts of the behavior are hardcoded initially versus learned later

## Implementation Plan

1. Choose the 2D grid representation, likely a dense row/column matrix, and define the data structures for the map and agent state.
2. Define the behavior policy interface so the same simulator can use either hardcoded rules or a learned policy.
3. Implement a CPU reference simulator with clear, testable movement rules.
4. Add validation for input shape, boundaries, and invalid movement vectors.
5. Write unit tests for core cases such as empty 2D grids, blocked moves, eight-neighbor transitions, collisions, and policy selection.
6. Log behavior decisions during simulation so future training data can be collected.
7. Profile the CPU version and identify the bottlenecks.
8. Move array-heavy operations to NumPy or CuPy and keep the CPU version as a fallback.
9. Use Numba for the small set of hot loops that are not efficient as pure array operations.
10. Compare CPU and GPU outputs to confirm the same behavior.
11. Add a simple public API for one-step simulation so the external scheduler can call it each second.

## Milestones

- M1: Define the map and agent data model
- M2: Ship a correct CPU simulation step
- M3: Add tests and validation
- M4: Port performance-critical paths to GPU
- M5: Benchmark and tune for larger crowds

## Open Questions

- Is the crowd map a dense grid, sparse grid, or list of agent coordinates?
- What is the structure of the behavior vector or policy matrix for each agent?
- Which agent features should be inputs to the learned policy?
- Should movement be deterministic, stochastic, or mixed?
- How should conflicts be resolved when multiple agents target the same cell?
- What is the maximum expected crowd size and map resolution?
- Do we need continuous movement later, or is a 2D grid model enough?

## Current Implementation Notes

- Terrain map tiles are now represented separately from occupancy via an optional `terrain` matrix in payloads.
- If `terrain` is omitted, the API defaults to an all-walkable map (`-1` tiles) for backward compatibility.
- `elements.md` includes a `## Terrain Grid` section that can be parsed with `terrain_from_elements_file(...)` from `src.api`.
- The public step API supports optional event and metadata payloads.
- If your upstream JSON matches `crowd-vision/show.py` (`data.result.tracks` with `id`, `position`, `velocity`), use `tracks_payload_to_sim_payload(...)` or `step_payload_from_tracks(...)` in `src.api`.
- A vectorized large-scale API is available as `step_payload_bulk` for high agent-count workloads.
- For very large runs, pass `columnar_output: true` in the payload to avoid per-agent dict output overhead.
- A fast-forward multi-step API is available as `simulate_payload_bulk(payload, steps=...)` to reduce per-step serialization overhead.
- Optional GPU acceleration is available via `step_payload_bulk_gpu` (uses CuPy when installed, falls back to CPU if enabled).
- Kaggle packaging is prepared via `kaggle_main.py` and `kernel-metadata.json`; after Kaggle auth, run `kaggle kernels push -p .` from the repo root.
- The simulator now delegates step execution through a backend seam, with the pure-Python backend as the default implementation.
- Benchmarking is available through the stdlib harness at `python -m src.benchmark.harness`.
- Throughput target check for "simulate 60s in 1s" is available via `python -m src.benchmark.harness --target-check --steps 60 --agents 100000 --rows 400 --cols 400`.
- Parallel multi-run execution with periodic status files is available via `python scripts/run_parallel_simulations.py`.
- Defaults are set to `--total-steps 900` and `--report-every 60`, so each run emits 15 status files plus a global `summary.json`.
- Status reports now include `movement_metrics` with physical units (meters and m/s), using defaults `--step-length-m 1.0` and `--nominal-avg-steps-per-tick 1.0`.
- Orchestrator-style payload integration coverage is provided in `tests/test_payload_integration.py`.
- A committed CPU baseline benchmark artifact is available at `benchmarks/baseline_cpu.json`.
- Refresh the baseline with `.venv/bin/python -m src.benchmark.harness --iterations 50 --output benchmarks/baseline_cpu.json`.
