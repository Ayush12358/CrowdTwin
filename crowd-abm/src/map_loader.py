from __future__ import annotations

from pathlib import Path

from src.core.errors import TerrainFormatError
from src.core.terrain import VALID_TERRAIN_TILES


def parse_terrain_grid_markdown(markdown_text: str) -> list[list[int]]:
    """Parse terrain from the first fenced grid under the 'Terrain Grid' header."""

    lines = markdown_text.splitlines()
    header_idx = None
    for idx, line in enumerate(lines):
        if line.strip().lower() == "## terrain grid":
            header_idx = idx
            break

    if header_idx is None:
        raise TerrainFormatError("missing '## Terrain Grid' section")

    fence_start = None
    for idx in range(header_idx + 1, len(lines)):
        if lines[idx].strip().startswith("```"):
            fence_start = idx
            break
    if fence_start is None:
        raise TerrainFormatError("missing fenced grid block under '## Terrain Grid'")

    fence_end = None
    for idx in range(fence_start + 1, len(lines)):
        if lines[idx].strip().startswith("```"):
            fence_end = idx
            break
    if fence_end is None:
        raise TerrainFormatError("unterminated fenced grid block")

    raw_rows = [line.strip() for line in lines[fence_start + 1 : fence_end] if line.strip()]
    if not raw_rows:
        raise TerrainFormatError("terrain grid block is empty")

    terrain: list[list[int]] = []
    expected_cols = -1
    for row_idx, row_text in enumerate(raw_rows):
        tokens = row_text.replace(",", " ").split()
        if not tokens:
            raise TerrainFormatError(f"terrain row {row_idx} is empty")

        try:
            row = [int(token) for token in tokens]
        except ValueError as exc:
            raise TerrainFormatError(f"terrain row {row_idx} contains a non-integer token") from exc

        if expected_cols == -1:
            expected_cols = len(row)
            if expected_cols == 0:
                raise TerrainFormatError("terrain grid must have at least one column")
        elif len(row) != expected_cols:
            raise TerrainFormatError("terrain rows must have consistent length")

        for tile in row:
            if tile not in VALID_TERRAIN_TILES:
                raise TerrainFormatError(f"terrain contains unsupported tile value: {tile}")

        terrain.append(row)

    return terrain


def load_terrain_from_elements_file(path: str | Path) -> list[list[int]]:
    source_path = Path(path)
    text = source_path.read_text(encoding="utf-8")
    return parse_terrain_grid_markdown(text)
