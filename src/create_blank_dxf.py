"""Generate the elevation layout frame DXF."""

from __future__ import annotations

from pathlib import Path

from dxf_framework import save_elevation_frame_dxf


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT_DIR / "output" / "elevation_layout_frame.dxf"


if __name__ == "__main__":
    saved = save_elevation_frame_dxf(OUTPUT_PATH)
    print(saved)
