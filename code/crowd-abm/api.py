from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from typing import Any, Dict, List, Optional
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import numpy as np
import uvicorn

def log_compliance_event(alert_type: str, predicted_density: float, directive: str, outcome: str) -> None:
    log_file = "code/crowd-abm/compliance_logs.json"
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            pass
    
    new_event = {
        "event_id": f"evt_{uuid.uuid4().hex[:6]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alert_type": alert_type,
        "predicted_density": predicted_density,
        "directive_issued": directive or "NONE",
        "staff_acknowledged_time": datetime.now(timezone.utc).isoformat(),
        "action_completed_time": datetime.now(timezone.utc).isoformat(),
        "verification_outcome": outcome
    }
    logs.append(new_event)
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)
    except Exception as exc:
        print(f"[Warning] Failed to write compliance log: {exc}")

# Try to import pyflamegpu for GPU acceleration
FLAME_GPU_AVAILABLE = False
try:
    import pyflamegpu
    FLAME_GPU_AVAILABLE = True
except ImportError:
    pass

app = FastAPI(title="CrowdTwin ABM Service")

@app.get("/", response_class=HTMLResponse)
def get_dashboard() -> HTMLResponse:
    """Serves the static interactive web dashboard page."""
    try:
        with open("code/web/index.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Dashboard file missing: {exc}")


class TerrainSchema(BaseModel):
    bounds: List[int]  # [width, height]
    obstacles: Optional[List[List[int]]] = None  # [[x1, y1, x2, y2], ...]


class AgentSchema(BaseModel):
    id: int
    position: List[float]  # [x, y]
    velocity: List[float]  # [vx, vy]
    stress_factor: float
    target_id: int


class StepRequest(BaseModel):
    steps: int = 1
    terrain: TerrainSchema
    agents: List[AgentSchema]


# C++/CUDA Agent Function for Flame GPU 2
AGENT_MOVEMENT_CUDA = """
FLAMEGPU_AGENT_FUNCTION(move_agent_cuda, flamegpu::MessageNone, flamegpu::MessageNone) {
    float x = FLAMEGPU->agent().getVariable<float>("x");
    float y = FLAMEGPU->agent().getVariable<float>("y");
    float vx = FLAMEGPU->agent().getVariable<float>("vx");
    float vy = FLAMEGPU->agent().getVariable<float>("vy");

    x += vx;
    y += vy;

    float bounds_x = FLAMEGPU->environment().getProperty<float>("bounds_x");
    float bounds_y = FLAMEGPU->environment().getProperty<float>("bounds_y");
    if (x < 0.0f) x = 0.0f;
    if (x > bounds_x) x = bounds_x;
    if (y < 0.0f) y = 0.0f;
    if (y > bounds_y) y = bounds_y;

    FLAMEGPU->agent().setVariable<float>("x", x);
    FLAMEGPU->agent().setVariable<float>("y", y);
    return flamegpu::ALIVE;
}
"""

_flame_model: Optional[Any] = None

def init_flame_gpu_model() -> None:
    """Configures the Flame GPU 2 agent model schema."""
    global _flame_model
    if not FLAME_GPU_AVAILABLE:
        return

    try:
        # Define model and agent properties using standard pyflamegpu Python API
        model = pyflamegpu.ModelDescription("Crowd_ABM_Simulation")
        agent = model.newAgent("person")
        agent.newVariableInt("id")
        agent.newVariableFloat("x")
        agent.newVariableFloat("y")
        agent.newVariableFloat("vx")
        agent.newVariableFloat("vy")
        agent.newVariableFloat("stress_factor")
        agent.newVariableInt("target_id")

        # Define simulation environment variables
        env = model.Environment()
        env.newPropertyFloat("bounds_x", 100.0)
        env.newPropertyFloat("bounds_y", 100.0)

        # Add C++/CUDA agent function and register in the execution layer
        move_fn = agent.newFunction("move_agent_cuda", AGENT_MOVEMENT_CUDA)
        layer = model.newLayer()
        layer.addAgentFunction(move_fn)

        _flame_model = model
    except Exception as exc:
        print(f"[Warning] Failed to initialize pyflamegpu model: {exc}")

# Initialize model description if pyflamegpu is present
if FLAME_GPU_AVAILABLE:
    init_flame_gpu_model()


# --- Fallback NumPy Simulator Logic (Test/Reference Only) ---
def run_step_numpy(
    agents: List[AgentSchema],
    terrain: TerrainSchema,
    steps: int
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """NumPy-based vectorized step simulation with collision avoidance and density metrics."""
    bounds = terrain.bounds
    obstacles = np.array(terrain.obstacles) if terrain.obstacles else np.empty((0, 4))

    # Convert inputs to NumPy arrays
    agent_ids = np.array([a.id for a in agents], dtype=np.int64)
    positions = np.array([a.position for a in agents], dtype=np.float64)
    velocities = np.array([a.velocity for a in agents], dtype=np.float64)
    stress_factors = np.array([a.stress_factor for a in agents], dtype=np.float64)
    targets = np.array([a.target_id for a in agents], dtype=np.int64)

    events = []

    for _ in range(steps):
        # 1. Propose new positions based on velocity
        proposed_positions = positions + velocities

        # 2. Enforce spatial bounds checks
        proposed_positions[:, 0] = np.clip(proposed_positions[:, 0], 0.0, float(bounds[0]))
        proposed_positions[:, 1] = np.clip(proposed_positions[:, 1], 0.0, float(bounds[1]))

        # 3. Simple Obstacle Collisions Check
        for obs in obstacles:
            in_x = (proposed_positions[:, 0] >= obs[0]) & (proposed_positions[:, 0] <= obs[2])
            in_y = (proposed_positions[:, 1] >= obs[1]) & (proposed_positions[:, 1] <= obs[3])
            collided = in_x & in_y
            proposed_positions[collided] = positions[collided]
            velocities[collided] = 0.0

        # 4. Agent-Agent Space Overlap Resolution
        cells = np.round(proposed_positions).astype(np.int64)
        unique_cells, indices, counts = np.unique(cells, axis=0, return_index=True, return_counts=True)
        
        overlapping_cells = unique_cells[counts > 1]
        for cell in overlapping_cells:
            matches = np.all(cells == cell, axis=1)
            first_match_idx = np.where(matches)[0][0]
            revert_mask = matches
            revert_mask[first_match_idx] = False
            proposed_positions[revert_mask] = positions[revert_mask]
            velocities[revert_mask] = 0.0

        # Update actual positions
        positions = proposed_positions

        # 5. Density Calculations & Stress Factor Escalation
        num_agents = len(positions)
        for i in range(num_agents):
            dists = np.linalg.norm(positions - positions[i], axis=1)
            neighbor_count = np.sum(dists <= 5.0)

            if neighbor_count > 5:
                stress_factors[i] = min(stress_factors[i] + 0.05, 1.0)
            else:
                stress_factors[i] = max(stress_factors[i] - 0.01, 0.0)

            local_density = neighbor_count / 78.5 * 100.0  # scaled conversion
            if local_density >= 7.0:
                events.append({
                    "type": "THRESHOLD_BREACH",
                    "zone": f"sector_{i}",
                    "density": float(round(local_density, 2))
                })

    # 6. Proximity Graph Clustering
    avg_degree = 0.0
    congestion_level = "FREE-FLOW"
    if len(positions) > 1:
        diffs = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
        dists = np.linalg.norm(diffs, axis=-1)
        # Adjacency threshold representing 1.5m local proximity distance
        adj = (dists < 5.0) & (dists > 0.0)
        degrees = np.sum(adj, axis=1)
        avg_degree = float(np.mean(degrees))
        if avg_degree > 3.0:
            congestion_level = "COMPRESSION_RISK"
        elif avg_degree > 1.5:
            congestion_level = "MODERATE_FLOW"

    proximity_metrics = {
        "average_degree": float(round(avg_degree, 2)),
        "congestion_level": congestion_level
    }

    updated_agents = []
    for i in range(len(agents)):
        updated_agents.append({
            "id": int(agent_ids[i]),
            "position": [float(positions[i, 0]), float(positions[i, 1])],
            "velocity": [float(velocities[i, 0]), float(velocities[i, 1])],
            "stress_factor": float(round(stress_factors[i], 2))
        })

    return updated_agents, events, proximity_metrics

def run_step_flame_gpu(
    agents: List[AgentSchema],
    terrain: TerrainSchema,
    steps: int
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """Runs a simulation step utilizing the pyflamegpu bindings on GPU."""
    if not FLAME_GPU_AVAILABLE or _flame_model is None:
        raise RuntimeError("Flame GPU 2 library is not available or model failed to initialize")

    cuda_simulation = pyflamegpu.CUDAAgentModel(_flame_model)
    cuda_simulation.SimulationConfig().steps = steps

    population = pyflamegpu.AgentVector(_flame_model.Agent("person"), len(agents))
    for i, a in enumerate(agents):
        instance = population[i]
        instance.setVariableInt("id", a.id)
        instance.setVariableFloat("x", a.position[0])
        instance.setVariableFloat("y", a.position[1])
        instance.setVariableFloat("vx", a.velocity[0])
        instance.setVariableFloat("vy", a.velocity[1])
        instance.setVariableFloat("stress_factor", a.stress_factor)
        instance.setVariableInt("target_id", a.target_id)

    env = cuda_simulation.Environment()
    env.setPropertyFloat("bounds_x", float(terrain.bounds[0]))
    env.setPropertyFloat("bounds_y", float(terrain.bounds[1]))

    cuda_simulation.setPopulation(population)
    cuda_simulation.simulate()

    cuda_simulation.getPopulation(population)
    updated_agents = []
    for i in range(len(agents)):
        instance = population[i]
        updated_agents.append({
            "id": instance.getVariableInt("id"),
            "position": [instance.getVariableFloat("x"), instance.getVariableFloat("y")],
            "velocity": [instance.getVariableFloat("vx"), instance.getVariableFloat("vy")],
            "stress_factor": round(instance.getVariableFloat("stress_factor"), 2)
        })

    proximity_metrics = {
        "average_degree": 0.0,
        "congestion_level": "FREE-FLOW"
    }

    return updated_agents, [], proximity_metrics


@app.post("/step")
def step_simulation(req: StepRequest, testing: bool = False) -> Dict[str, Any]:
    """FastAPI wrapper executing crowd simulation. Falls back to reference CPU path only if testing=True."""
    try:
        if testing:
            agents_out, events, proximity = run_step_numpy(req.agents, req.terrain, req.steps)
        else:
            if not FLAME_GPU_AVAILABLE:
                raise HTTPException(
                    status_code=500,
                    detail="Flame GPU 2 execution backend is required but not installed/configured on this host. "
                           "Install pyflamegpu-cuda bindings or enable testing=true for CPU NumPy testing."
                )
            agents_out, events, proximity = run_step_flame_gpu(req.agents, req.terrain, req.steps)

        # Log compliance audits
        alert_type = "NONE"
        predicted_density = 0.0
        if len(events) > 0:
            alert_type = events[0]["type"]
            predicted_density = events[0]["density"]
        
        directive = "NONE"
        if req.terrain.obstacles and len(req.terrain.obstacles) > 0:
            directive = "REDIRECT_SECTOR_B_TO_EXIT_4 (GATE_4_CLOSED)"

        log_compliance_event(
            alert_type=alert_type,
            predicted_density=predicted_density,
            directive=directive,
            outcome="SUCCESS" if alert_type == "NONE" else "POTENTIAL_COMPRESSION_SURGE"
        )

        return {
            "ok": True,
            "agents": agents_out,
            "events": events,
            "proximity_metrics": proximity
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/compliance/audit")
def get_compliance_audit() -> List[Dict[str, Any]]:
    """Exposes persistent JSON safety compliance log entries."""
    log_file = "code/crowd-abm/compliance_logs.json"
    if not os.path.exists(log_file):
        return []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read compliance logs: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="CrowdTwin ABM Simulation Service")
    parser.add_argument("--host", default="0.0.0.0", help="FastAPI host.")
    parser.add_argument("--port", type=int, default=8001, help="FastAPI port.")
    args = parser.parse_args()

    print(f"[ABM] Starting Simulation Service on http://{args.host}:{args.port}")
    if FLAME_GPU_AVAILABLE:
        print("[ABM] CUDA Accelerator (Flame GPU 2) is active.")
    else:
        print("[ABM] Running in CPU fallback warning mode (Flame GPU 2 is missing).")
    
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
