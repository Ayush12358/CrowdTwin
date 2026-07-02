from __future__ import annotations

from src.core.errors import TerrainShapeError, TerrainValueError

TILE_EMPTY = -1
TILE_WALL = 0
TILE_GATE = 1
TILE_PATH = 2
TILE_ATTRACTION = 3
TILE_SEAT = 4

VALID_TERRAIN_TILES = frozenset(
    {
        TILE_EMPTY,
        TILE_WALL,
        TILE_GATE,
        TILE_PATH,
        TILE_ATTRACTION,
        TILE_SEAT,
    }
)
WALKABLE_TERRAIN_TILES = frozenset(
    {
        TILE_EMPTY,
        TILE_GATE,
        TILE_PATH,
        TILE_ATTRACTION,
        TILE_SEAT,
    }
)


def is_walkable_tile(tile: int) -> bool:
    return tile in WALKABLE_TERRAIN_TILES


def build_default_terrain(shape: tuple[int, int], *, fill_tile: int = TILE_EMPTY) -> list[list[int]]:
    rows, cols = shape
    if rows <= 0 or cols <= 0:
        raise TerrainShapeError("shape must contain positive rows and columns")
    if fill_tile not in VALID_TERRAIN_TILES:
        raise TerrainValueError(f"invalid terrain tile value: {fill_tile}")
    return [[fill_tile for _ in range(cols)] for _ in range(rows)]
