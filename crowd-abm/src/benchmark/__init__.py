from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from .harness import BenchmarkResult, ScenarioResult

__all__ = ["BenchmarkResult", "ScenarioResult", "run_benchmarks"]


def __getattr__(name: str) -> Any:
	if name in __all__:
		from . import harness

		return getattr(harness, name)
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
