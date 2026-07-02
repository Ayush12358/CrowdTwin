from fastapi.testclient import TestClient
import unittest
from unittest.mock import MagicMock, patch

# Import code.crowd-abm.api logic
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from api import app, run_step_numpy, AgentSchema, TerrainSchema


class TestABMSimulator(unittest.TestCase):
    def test_numpy_simple_movement(self):
        # Test agent moves in free space according to its velocity vector
        agents = [
            AgentSchema(id=1, position=[10.0, 10.0], velocity=[1.5, -2.0], stress_factor=0.0, target_id=0)
        ]
        terrain = TerrainSchema(bounds=[100, 100])
        
        updated, events, proximity = run_step_numpy(agents, terrain, steps=1)
        self.assertEqual(proximity["congestion_level"], "FREE-FLOW")
        
        self.assertEqual(len(updated), 1)
        agent = updated[0]
        self.assertEqual(agent["id"], 1)
        self.assertEqual(agent["position"], [11.5, 8.0])
        self.assertEqual(agent["velocity"], [1.5, -2.0])

    def test_numpy_bounds_checks(self):
        # Test agent is constrained inside specified bounds
        agents = [
            # Heading out on X-max
            AgentSchema(id=1, position=[99.5, 50.0], velocity=[2.0, 0.0], stress_factor=0.0, target_id=0),
            # Heading out on Y-min
            AgentSchema(id=2, position=[50.0, 0.5], velocity=[0.0, -3.0], stress_factor=0.0, target_id=0)
        ]
        terrain = TerrainSchema(bounds=[100, 100])

        updated, events, proximity = run_step_numpy(agents, terrain, steps=1)

        self.assertEqual(updated[0]["position"], [100.0, 50.0])
        self.assertEqual(updated[1]["position"], [50.0, 0.0])

    def test_numpy_obstacle_collision(self):
        # Test agent reverts position when colliding with a terrain obstacle
        agents = [
            # Heading directly into obstacle bounds [20, 20, 30, 30]
            AgentSchema(id=1, position=[19.0, 25.0], velocity=[2.0, 0.0], stress_factor=0.0, target_id=0)
        ]
        terrain = TerrainSchema(
            bounds=[100, 100],
            obstacles=[[20, 20, 30, 30]]
        )
        updated, events, proximity = run_step_numpy(agents, terrain, steps=1)

        # Should revert to original position [19.0, 25.0] and zero velocity
        self.assertEqual(updated[0]["position"], [19.0, 25.0])
        self.assertEqual(updated[0]["velocity"], [0.0, 0.0])

    def test_numpy_agent_agent_collision_overlap(self):
        # Test that multiple agents heading into the same grid cell are resolved
        agents = [
            # Both heading towards center cell around [50.0, 50.0]
            AgentSchema(id=1, position=[49.0, 50.0], velocity=[1.0, 0.0], stress_factor=0.0, target_id=0),
            AgentSchema(id=2, position=[51.0, 50.0], velocity=[-1.0, 0.0], stress_factor=0.0, target_id=0)
        ]
        terrain = TerrainSchema(bounds=[100, 100])

        updated, events, proximity = run_step_numpy(agents, terrain, steps=1)

        # One of them should succeed, other should revert to original position
        pos1 = updated[0]["position"]
        pos2 = updated[1]["position"]

        # Assert no overlaps (they should not end up at the exact same location)
        self.assertNotEqual(pos1, pos2)

    def test_numpy_density_event(self):
        # Test that high local density generates a THRESHOLD_BREACH event
        # Place 10 agents very close to each other
        agents = []
        for i in range(10):
            agents.append(
                AgentSchema(id=i, position=[50.0 + i*0.1, 50.0 + i*0.1], velocity=[0.0, 0.0], stress_factor=0.0, target_id=0)
            )
        terrain = TerrainSchema(bounds=[100, 100])

        updated, events, proximity = run_step_numpy(agents, terrain, steps=1)
        self.assertEqual(proximity["congestion_level"], "COMPRESSION_RISK")
        self.assertTrue(any(e["type"] == "THRESHOLD_BREACH" for e in events))

    def test_api_endpoint_testing_mode(self):
        client = TestClient(app)
        payload = {
            "steps": 1,
            "terrain": {
                "bounds": [100, 100],
                "obstacles": []
            },
            "agents": [
                {
                    "id": 1,
                    "position": [10.0, 10.0],
                    "velocity": [1.0, 1.0],
                    "stress_factor": 0.0,
                    "target_id": 0
                }
            ]
        }
        response = client.post("/step?testing=true", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["agents"][0]["position"], [11.0, 11.0])
        self.assertIn("proximity_metrics", data)
        self.assertEqual(data["proximity_metrics"]["congestion_level"], "FREE-FLOW")

    def test_api_endpoint_production_fail_fast(self):
        client = TestClient(app)
        payload = {
            "steps": 1,
            "terrain": {
                "bounds": [100, 100],
                "obstacles": []
            },
            "agents": []
        }
        # Calls the production path which must fail fast because pyflamegpu C++ model functions are not fully loaded/compiled
        response = client.post("/step", json=payload)
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("detail", data)

    def test_api_endpoint_dashboard(self):
        client = TestClient(app)
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("CROWD-TWIN", response.text)

    def test_api_endpoint_compliance_audit(self):
        client = TestClient(app)
        # Call step first to generate a log entry
        payload = {
            "steps": 1,
            "terrain": {
                "bounds": [100, 100],
                "obstacles": []
            },
            "agents": []
        }
        client.post("/step?testing=true", json=payload)
        
        # Call compliance audit
        response = client.get("/compliance/audit")
        self.assertEqual(response.status_code, 200)
        logs = response.json()
        self.assertGreater(len(logs), 0)
        first_log = logs[0]
        self.assertIn("event_id", first_log)
        self.assertIn("timestamp", first_log)
        self.assertIn("verification_outcome", first_log)


if __name__ == '__main__':
    unittest.main()
