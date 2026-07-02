# CrowdTwin

Predictive Crowd Safety & Spatial Analytics Command Center.

For the complete product concept, target personas, and monetization model, see [IDEA.md](IDEA.md).

## Repository Layout
* **`CrowdTwin/`**: React web dashboard (Vite, TypeScript, Leaflet maps).
* **`crowd-vision/`** *(In Refactoring)*: Planned single-process tracking pipeline utilizing Roboflow Supervision.
* **`crowd-abm/`** *(In Refactoring)*: Planned simulation engine utilizing Flame GPU 2.

*For the complete greenfield design, API contracts, schemas, and migration steps, see [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).*

---

## Quick Start

### 1. Web Dashboard (Active)
Run the React mockup dashboard:
```bash
cd CrowdTwin
bun install
bun run dev
```

### 2. Vision & ABM Services (Refactoring Phase)
The previous Python backends have been discarded to transition to a leaner, single-process tracking model and a Flame GPU 2 simulation backend.
* **Implementation Specs**: See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).
* **Target Layout**: New directories will be populated step-by-step following the migration phases.
