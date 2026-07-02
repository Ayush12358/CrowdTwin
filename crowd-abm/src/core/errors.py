from __future__ import annotations


class SimulationError(Exception):
    """Base class for simulation-level failures."""


class ValidationError(SimulationError):
    """Base class for invalid simulation input/state."""


class OccupancyShapeError(ValidationError):
    """Occupancy matrix shape is invalid."""


class TerrainShapeError(ValidationError):
    """Terrain matrix shape is invalid."""


class TerrainValueError(ValidationError):
    """Terrain matrix contains an unsupported tile value."""


class AgentIdMismatchError(ValidationError):
    """Agent dictionary key does not match embedded agent_id."""


class AgentOutOfBoundsError(ValidationError):
    """Agent position is outside the occupancy matrix bounds."""


class DuplicateAgentPositionError(ValidationError):
    """Multiple agents occupy the same position."""


class OccupancyStateMismatchError(ValidationError):
    """Occupancy matrix does not match agent table."""


class PayloadFormatError(ValidationError):
    """External payload structure is invalid."""


class TerrainFormatError(ValidationError):
    """Terrain format source is invalid."""
