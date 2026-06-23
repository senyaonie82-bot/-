"""Generate the blank DXF frame for the CAD project."""

from __future__ import annotations

from pathlib import Path

from dxf_framework import save_blank_dxf


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT_DIR / "output" / "blank_frame.dxf"


if __name__ == "__main__":
    saved = save_blank_dxf(OUTPUT_PATH)
    print(saved)

