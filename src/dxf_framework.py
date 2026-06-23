"""Base DXF document framework.

The initializer creates a blank drawing containing only a frame and coordinate axes.
No wastewater treatment structures are drawn in this stage.
"""

from __future__ import annotations

from pathlib import Path

import ezdxf

from cad_config import (
    AXIS_LENGTH,
    DEFAULT_SCALE,
    DXF_INSUNITS_METRES,
    FRAME_HEIGHT,
    FRAME_WIDTH,
    STANDARD_LAYERS,
)


def create_document() -> ezdxf.document.Drawing:
    doc = ezdxf.new("R2010", setup=True)
    doc.units = DXF_INSUNITS_METRES
    doc.header["$INSUNITS"] = DXF_INSUNITS_METRES

    for spec in STANDARD_LAYERS:
        if spec.name not in doc.layers:
            doc.layers.new(
                spec.name,
                dxfattribs={
                    "color": spec.color,
                    "linetype": spec.linetype,
                    "lineweight": spec.lineweight,
                },
            )

    return doc


def add_blank_frame(doc: ezdxf.document.Drawing) -> None:
    msp = doc.modelspace()
    half_w = FRAME_WIDTH / 2
    half_h = FRAME_HEIGHT / 2

    frame_points = [
        (-half_w, -half_h),
        (half_w, -half_h),
        (half_w, half_h),
        (-half_w, half_h),
        (-half_w, -half_h),
    ]
    msp.add_lwpolyline(frame_points, dxfattribs={"layer": "FRAME"})

    axis = AXIS_LENGTH / 2
    msp.add_line((-axis, 0), (axis, 0), dxfattribs={"layer": "AXIS"})
    msp.add_line((0, -axis), (0, axis), dxfattribs={"layer": "AXIS"})
    msp.add_text(
        f"Blank CAD frame, units: m, scale control: {DEFAULT_SCALE.name}",
        dxfattribs={"layer": "TEXT", "height": 2.5},
    ).set_placement((-half_w + 4, half_h - 6))


def save_blank_dxf(path: Path) -> Path:
    doc = create_document()
    add_blank_frame(doc)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(path)
    return path

