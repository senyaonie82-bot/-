"""Base DXF document framework for the elevation layout drawing.

The initializer creates a blank drawing containing only a frame, title block,
coordinate axes, notes, and an empty legend area. No treatment structures are
drawn in this stage.
"""

from __future__ import annotations

from pathlib import Path

import ezdxf

from cad_config import (
    AXIS_LENGTH,
    DXF_INSUNITS_METRES,
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


def add_elevation_frame(doc: ezdxf.document.Drawing) -> None:
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

    _add_text(msp, "高程布置图", (-half_w + 4, -half_h + 11.5), height=4.0, layer="TITLE_BLOCK")
    _add_text(msp, "纵向比例尺 1:50", (-half_w + 4, -half_h + 5.5), layer="TITLE_BLOCK")
    _add_text(msp, "横向比例尺 1:500", (-half_w + 4, -half_h + 2.0), layer="TITLE_BLOCK")
    _add_text(
        msp,
        f"比例控制：{ELEVATION_SCALE.label}，纵向放大 {ELEVATION_SCALE.vertical_exaggeration:g} 倍",
        (-half_w + 4, half_h - 7),
        height=2.2,
    )

    notes_x = half_w - NOTES_BLOCK_WIDTH + 2
    _add_text(msp, "说明", (notes_x, -half_h + 11.5), height=3.0, layer="TITLE_BLOCK")
    _add_text(msp, "1. 本图标高以 m 计，标高为绝对标高。", (notes_x, -half_h + 6.5), height=2.0)
    _add_text(
        msp,
        "2. 图中污水管、污泥管、回流污泥管及送风管采用不同线型表示。",
        (notes_x, -half_h + 2.5),
        height=1.8,
    )

    legend_x = half_w - NOTES_BLOCK_WIDTH - LEGEND_BLOCK_WIDTH + 2
    _add_text(msp, "图例", (legend_x, -half_h + 11.5), height=3.0, layer="TITLE_BLOCK")
    _add_text(msp, "（后续填写管线与构筑物图例）", (legend_x, -half_h + 5.0), height=1.9)


def save_elevation_frame_dxf(path: Path) -> Path:
    doc = create_document()
    add_elevation_frame(doc)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(path)
    return path
