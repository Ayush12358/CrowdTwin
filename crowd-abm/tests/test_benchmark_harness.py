from __future__ import annotations

import tempfile
import unittest
import json
from pathlib import Path

from src.benchmark.harness import run_benchmarks


class BenchmarkHarnessTests(unittest.TestCase):
    def test_run_benchmarks_returns_structured_results(self) -> None:
        result = run_benchmarks(iterations=2, scenarios=(("toy", 5, 5, 3),))

        self.assertEqual(len(result.scenarios), 1)
        scenario = result.scenarios[0]
        self.assertEqual(scenario.name, "toy")
        self.assertEqual(scenario.rows, 5)
        self.assertEqual(scenario.cols, 5)
        self.assertEqual(scenario.agents, 3)
        self.assertGreaterEqual(scenario.avg_step_time_ms, 0.0)
        self.assertGreater(scenario.steps_per_sec, 0.0)
        self.assertGreater(scenario.estimated_state_bytes, 0)

    def test_benchmark_result_can_be_serialized(self) -> None:
        result = run_benchmarks(iterations=1, scenarios=(("toy", 5, 5, 2),))
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "bench.json"
            output_path.write_text(json.dumps(result.to_dict()), encoding="utf-8")
            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertIn("scenarios", payload)


if __name__ == "__main__":
    unittest.main()
