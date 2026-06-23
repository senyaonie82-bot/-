"""Base DXF document framework for the elevation layout drawing.

The initializer creates a blank drawing containing only a frame, title block,
coordinate axes, notes, and an empty legend area. No treatment structures are
drawn in this stage.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import ezdxf

from cad_config import (
    AXIS_LENGTH,
    DXF_INSUNITS_MILLIMETERS,
    ELEVATION_SCALE,
    FRAME_HEIGHT,
    FRAME_WIDTH,
    LEGEND_BLOCK_WIDTH,
    NOTES_BLOCK_WIDTH,
    STANDARD_LAYERS,
    TITLE_BLOCK_HEIGHT,
)


def create_document() -> ezdxf.document.Drawing:
    doc = ezdxf.new("R2010", setup=True)
    doc.units = DXF_INSUNITS_MILLIMETERS
    doc.header["$INSUNITS"] = DXF_INSUNITS_MILLIMETERS

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


def _add_text(
    msp: ezdxf.layouts.Modelspace,
    text: str,
    insert: tuple[float, float],
    *,
    height: float = 2.5,
    layer: str = "TEXT",
) -> None:
    msp.add_text(
        text,
        dxfattribs={"layer": layer, "height": height},
    ).set_placement(insert)


def add_elevation_frame(doc: ezdxf.document.Drawing, extra_notes: Sequence[str] = ()) -> None:
    msp = doc.modelspace()
    half_w = FRAME_WIDTH / 2
    half_h = FRAME_HEIGHT / 2
    title_top = -half_h + TITLE_BLOCK_HEIGHT

    frame_points = [
        (-half_w, -half_h),
        (half_w, -half_h),
        (half_w, half_h),
        (-half_w, half_h),
        (-half_w, -half_h),
    ]
    msp.add_lwpolyline(frame_points, dxfattribs={"layer": "FRAME"})
    msp.add_line(
        (-half_w, title_top),
        (half_w, title_top),
        dxfattribs={"layer": "TITLE_BLOCK"},
    )
    msp.add_line(
        (half_w - NOTES_BLOCK_WIDTH, -half_h),
        (half_w - NOTES_BLOCK_WIDTH, title_top),
        dxfattribs={"layer": "TITLE_BLOCK"},
    )
    msp.add_line(
        (half_w - NOTES_BLOCK_WIDTH - LEGEND_BLOCK_WIDTH, -half_h),
        (half_w - NOTES_BLOCK_WIDTH - LEGEND_BLOCK_WIDTH, title_top),
        dxfattribs={"layer": "TITLE_BLOCK"},
    )
    msp.add_line(
        (-half_w, -half_h + TITLE_BLOCK_HEIGHT / 2),
        (half_w, -half_h + TITLE_BLOCK_HEIGHT / 2),
        dxfattribs={"layer": "TITLE_BLOCK"},
    )

    axis = AXIS_LENGTH / 2
    msp.add_line((-axis, 0), (axis, 0), dxfattribs={"layer": "HIDDEN"})
    msp.add_line((0, -axis / 2), (0, axis / 2), dxfattribs={"layer": "HIDDEN"})

    _add_text(msp, "图名：高程布置图", (-half_w + 18, -half_h + 44), height=12.0, layer="TITLE_BLOCK")
    _add_text(
        msp,
        f"比例控制：{ELEVATION_SCALE.label}，纵向放大 {ELEVATION_SCALE.vertical_exaggeration:g} 倍",
        (-half_w + 18, half_h - 30),
        height=8.0,
    )

    notes_x = half_w - NOTES_BLOCK_WIDTH + 2
    _add_text(msp, "说明：", (notes_x + 8, -half_h + 48), height=8.0, layer="TITLE_BLOCK")
    notes = [
        "1. 本图纵向比例尺为 1:50，横向比例尺为 1:500。",
        "2. 本图标高以 m 计，标高为绝对标高。",
        *extra_notes,
    ]
    for index, note in enumerate(notes):
        _add_text(msp, note, (notes_x + 8, -half_h + 30 - index * 11), height=5.0)

    legend_x = half_w - NOTES_BLOCK_WIDTH - LEGEND_BLOCK_WIDTH + 2
    _add_text(msp, "图例", (legend_x + 8, -half_h + 48), height=8.0, layer="TITLE_BLOCK")
    legend_items = (
        ("污水管", "WASTEWATER_PIPE"),
        ("污泥管", "SLUDGE_PIPE"),
        ("回流污泥管", "RETURN_SLUDGE_PIPE"),
        ("送风管", "AIR_PIPE"),
    )
    for index, (label, layer) in enumerate(legend_items):
        y = -half_h + 32 - index * 8
        msp.add_line((legend_x + 8, y), (legend_x + 54, y), dxfattribs={"layer": layer})
        _add_text(msp, label, (legend_x + 62, y - 2.5), height=4.0)


def save_elevation_frame_dxf(path: Path) -> Path:
    doc = create_document()
    add_elevation_frame(doc)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(path)
    return path
