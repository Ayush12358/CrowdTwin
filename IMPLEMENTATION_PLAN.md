# CrowdTwin: Actionable Greenfield Implementation & Migration Plan

This document defines the actionable design, target schemas, file layouts, API contracts, and phased migration steps for implementing the greenfield refactoring of CrowdTwin. 

We discard the over-engineered multi-process code. Instead, we build a unified, compliance-centric command and safety auditing platform using **Roboflow Supervision** for vision tracking, **Flame GPU 2** for simulation execution, and **FastAPI** for closed-loop safety logs.

All implementation code is structured under the `code/` directory.

---

## 1. Core Stack Specifications

### A. Vision Pipeline (Roboflow Supervision)
* **Library**: `supervision` (imported as `sv`)
* **Tracking**: Use `sv.ByteTrack` for identity tracking.
* **Detections**: Map YOLOv8 model outputs directly into `sv.Detections.from_ultralytics()`.
* **Density Extraction**: Define monitoring zones using `sv.PolygonZone`. Count agents using `zone.trigger(detections=...)`.
* **Flow Analytics**: Use `sv.ByteTrack` and unique `Detections.tracker_id` mappings combined with a thread-safe historical position buffer to compute velocities and flow directions.

### B. Agent-Based Simulator (Flame GPU 2)
* **Library**: `pyflamegpu` (Python bindings for C++/CUDA Flame GPU 2)
* **Model Configuration**:
  ```python
  import pyflamegpu
  model = pyflamegpu.ModelDescription("Crowd_ABM_Simulation")
  agent = model.newAgent("person")
  agent.newVariableFloat("x")
  agent.newVariableFloat("y")
  agent.newVariableFloat("vx")
  agent.newVariableFloat("vy")
  agent.newVariableFloat("stress_factor")
  agent.newVariableInt("target_id")
  ```
* **C++/CUDA Function**: Implement the C++ motion kernel `move_agent_cuda` to compile agent movements and environment boundaries directly onto GPU memory:
  ```cpp
  FLAMEGPU_AGENT_FUNCTION(move_agent_cuda, flamegpu::MessageNone, flamegpu::MessageNone) {
      float x = FLAMEGPU->agent().getVariable<float>("x");
      float y = FLAMEGPU->agent().getVariable<float>("y");
      float vx = FLAMEGPU->agent().getVariable<float>("vx");
      float vy = FLAMEGPU->agent().getVariable<float>("vy");
      x += vx; y += vy;
      // boundary check...
      FLAMEGPU->agent().setVariable<float>("x", x);
      FLAMEGPU->agent().setVariable<float>("y", y);
      return flamegpu::ALIVE;
  }
  ```

### C. Compliance & Auditing Logger (FastAPI)
* **Storage**: Serialized JSON log files (`code/crowd-abm/compliance_logs.json`) providing a persistent audit trail.
* **Closed-loop checks**: Matches operator directives (closed gate, staff redirection) to mobile terminal feedback loops and measures density reductions over the next 15 minutes.
* **Access**: Exposes `GET /compliance/audit` for fire marshal and insurance compliance exports.

---

## 2. Greenfield Directory Layout

```
- CrowdTwin/
  - src/                       # React frontend (Vite, TypeScript, Leaflet maps)
- code/
  - crowd-vision/
    - tests/
      - test_pipeline.py       # Tests for YOLO output parsing and tracking logic
    - main.py                  # Unified FastAPI vision service + tracking thread
    - requirements.txt         # supervision, ultralytics, fastapi, uvicorn
  - crowd-abm/
    - tests/
      - test_simulator.py      # Tests for pyflamegpu/NumPy updates and compliance endpoints
    - api.py                   # FastAPI simulation service + static web dashboard server
    - requirements.txt         # fastapi, uvicorn, numpy, httpx
    - compliance_logs.json     # Stored time-stamped safety audit records
  - web/
    - index.html               # Single-file HTML/JS/Tailwind interactive console
  - docker-compose.yml         # Container orchestration configuration
```

---

## 3. API & Data Contracts

### A. Vision Ingest Payload (`POST /ingest` from Vision -> ABM)
```json
{
  "source": "camera_east_exit",
  "frame_index": 1042,
  "timestamp": 1719943200.5,
  "result": {
    "num_tracks": 2,
    "tracks": [
      {
        "id": 12,
        "position": [3.20, 5.10],
        "velocity": [0.50, -0.20],
        "speed": 0.54
      }
    ]
  }
}
```

### B. ABM Simulation & Proximity Request (`POST /step` from Dashboard -> ABM Service)
```json
{
  "steps": 1,
  "terrain": {
    "bounds": [100, 100],
    "obstacles": [[10, 10, 20, 20]]
  },
  "agents": [
    {
      "id": 12,
      "position": [3.20, 5.10],
      "velocity": [0.50, -0.20],
      "stress_factor": 0.1,
      "target_id": 1
    }
  ]
}
```

### C. Simulation Response Schema (Includes Proximity Graphs & Events)
```json
{
  "ok": true,
  "agents": [
    {
      "id": 12,
      "position": [3.70, 4.90],
      "velocity": [0.50, -0.20],
      "stress_factor": 0.15
    }
  ],
  "proximity_metrics": {
    "average_degree": 4.2,
    "congestion_level": "COMPRESSION_RISK"
  },
  "events": [
    {
      "type": "THRESHOLD_BREACH",
      "zone": "sector_b",
      "density": 7.2
    }
  ]
}
```

### D. Compliance Audit Log Schema (`GET /compliance/audit`)
```json
[
  {
    "event_id": "evt_abc123",
    "timestamp": "2026-07-03T10:15:30Z",
    "alert_type": "THRESHOLD_BREACH",
    "predicted_density": 7.4,
    "directive_issued": "REDIRECT_SECTOR_B_TO_EXIT_4",
    "staff_acknowledged_time": "2026-07-03T10:17:12Z",
    "action_completed_time": "2026-07-03T10:19:05Z",
    "verification_outcome": "SUCCESS"
  }
]
```

---

## 4. Phased Migration Steps

### Phase 1: Setup & Environment Initialization
1. Create `code/` subdirectories.
2. Initialize dependencies in `requirements.txt` files.
3. Install packages in virtual environment.

### Phase 2: Implement Single-Process Vision Service
1. Build `code/crowd-vision/main.py` using `supervision` tracking generators.
2. Run unit tests (`test_pipeline.py`) mocking YOLO and track history calculations.

### Phase 3: Implement pyflamegpu Simulator & Compliance Logger
1. Build `code/crowd-abm/api.py`. Define model boundaries and compile `move_agent_cuda` CUDA functions.
2. Implement NumPy reference solver mapping distance matrices and graph degree calculations.
3. Setup the JSON file logger for compliance audits and `/compliance/audit` endpoint.

### Phase 4: Create Interactive Dashboard
1. Create `code/web/index.html` with Canvas visualization and TailWind CSS.
2. Wire dashboard to connect to vision track feeds and simulator updates.
3. Add a "Download Compliance Log" button.

### Phase 5: Containerize & Verify
1. Create Dockerfiles and `code/docker-compose.yml`.
2. Run all integration and boundary tests.

---

## 5. Verification & Acceptance Tests

* **Test A: Proximity Clustering Test (`code/crowd-abm/tests/test_simulator.py`)**
  * Verify that placing 10 agents within $1.5\text{ meters}$ correctly increases node degree counts and outputs the `"COMPRESSION_RISK"` congestion level.
* **Test B: Compliance Audit Endpoint Test**
  * Query `GET /compliance/audit` and verify that the output conforms to the structured JSON array format.
