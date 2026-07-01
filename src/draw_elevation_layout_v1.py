"""Draw elevation layout V1 for the main wastewater process.

This drawing is a first-pass elevation layout based on temporary elevation
data. It does not draw the fine screen, lifting pump station, or sludge
treatment system because usable elevation data for those units is not confirmed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from cad_config import (
    FRAME_HEIGHT,
    FRAME_WIDTH,
    LEGEND_BLOCK_WIDTH,
    NOTES_BLOCK_WIDTH,
    TITLE_BLOCK_HEIGHT,
    to_elevation_coordinates,
)
from dxf_framework import add_elevation_frame, create_document


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT_DIR / "docs" / "elevation_data.md"
DXF_OUTPUT = ROOT_DIR / "output" / "elevation_layout_v1.dxf"
PNG_OUTPUT = ROOT_DIR / "output" / "elevation_layout_v1.png"
DATUM_ELEVATION_M = 0.0


@dataclass(frozen=True)
class PipeData:
    start: str
    end: str
    q_m3_s: float
    dn: str
    length_m: float
    slope: float
    friction_loss_m: float
    local_loss_m: float


@dataclass(frozen=True)
class UnitProfile:
    name: str
    key: str
    width_mm: float
    kind: str
    inlet_elevation_m: float | None
    outlet_elevation_m: float | None
    effective_depth_m: float | None = None
    total_height_m: float | None = None
    note: str | None = None


@dataclass(frozen=True)
class PlacedUnit:
    profile: UnitProfile
    left: float
    right: float

    @property
    def center(self) -> float:
        return (self.left + self.right) / 2


def _font() -> FontProperties | None:
    for candidate in (
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/simsun.ttc"),
    ):
        if candidate.exists():
            return FontProperties(fname=str(candidate))
    return None


def load_elevation_data(path: Path = DATA_PATH) -> tuple[dict[str, float], list[PipeData]]:
    text = path.read_text(encoding="utf-8")
    elevation_pattern = re.compile(r"-\s*(.+?水面高程|最终出水口水面高程)：([0-9.]+)\s*m")
    elevations = {match.group(1): float(match.group(2)) for match in elevation_pattern.finditer(text)}

    pipe_pattern = re.compile(
        r"\d+\.\s*(.+?)\s*→\s*(.+?)\n\s*"
        r"Q=([0-9.]+)\s*m³/s；(DN[0-9]+)；L=([0-9.]+)\s*m；"
        r"i=([0-9.]+)；沿程损失=([0-9.]+)\s*m；局部损失=([0-9.]+)\s*m"
    )
    pipes = [
        PipeData(
            start=match.group(1),
            end=match.group(2),
            q_m3_s=float(match.group(3)),
            dn=match.group(4),
            length_m=float(match.group(5)),
            slope=float(match.group(6)),
            friction_loss_m=float(match.group(7)),
            local_loss_m=float(match.group(8)),
        )
        for match in pipe_pattern.finditer(text)
    ]
    if len(pipes) != 8:
        raise ValueError("Expected 8 connection pipe records in docs/elevation_data.md")
    return elevations, pipes


def build_profiles(elevations: dict[str, float]) -> list[UnitProfile]:
    return [
        UnitProfile(
            "曝气沉砂池",
            "曝气沉砂池",
            width_mm=18.0 * 1000 / 500,
            kind="rect",
            inlet_elevation_m=None,
            outlet_elevation_m=elevations["曝气沉砂池出水水面高程"],
            effective_depth_m=2.0,
            total_height_m=3.9,
            note="2格并联",
        ),
        UnitProfile(
            "集配水井",
            "集配水井",
            width_mm=6.0,
            kind="well",
            inlet_elevation_m=elevations["集配水井进水水面高程"],
            outlet_elevation_m=elevations["集配水井出水水面高程"],
            note="配水构筑物",
        ),
        UnitProfile(
            "初沉池",
            "初沉池",
            width_mm=35.0 * 1000 / 500,
            kind="radial",
            inlet_elevation_m=elevations["初沉池进水水面高程"],
            outlet_elevation_m=elevations["初沉池出水水面高程"],
            effective_depth_m=3.0,
            total_height_m=6.31,
            note="2座辐流式",
        ),
        UnitProfile(
            "生物池配水设施",
            "生物池配水设施",
            width_mm=6.0,
            kind="well",
            inlet_elevation_m=elevations["生物池配水设施进水水面高程"],
            outlet_elevation_m=elevations["生物池配水设施出水水面高程"],
            note="配水设施",
        ),
        UnitProfile(
            "A²/O 生物反应池",
            "A²/O 生物反应池",
            width_mm=53.0 * 1000 / 500,
            kind="rect",
            inlet_elevation_m=elevations["A²/O 生物反应池进水水面高程"],
            outlet_elevation_m=elevations["A²/O 生物反应池出水水面高程"],
            effective_depth_m=5.0,
            total_height_m=None,
            note="2组并联，V1用代表性剖面",
        ),
        UnitProfile(
            "二沉池",
            "二沉池",
            width_mm=24.0,
            kind="secondary_pending",
            inlet_elevation_m=elevations["二沉池进水水面高程"],
            outlet_elevation_m=elevations["二沉池出水水面高程"],
            note="尺寸待按最新版计算书确认",
        ),
        UnitProfile(
            "消毒接触池",
            "消毒接触池",
            width_mm=21.5 * 1000 / 500,
            kind="contact",
            inlet_elevation_m=elevations["消毒接触池进水水面高程"],
            outlet_elevation_m=elevations["消毒接触池出水水面高程"],
            effective_depth_m=3.0,
            total_height_m=4.38,
            note="2座并联，每座3廊道",
        ),
        UnitProfile(
            "巴氏计量槽",
            "巴氏计量槽",
            width_mm=10.0,
            kind="parshall",
            inlet_elevation_m=elevations["巴氏计量槽进水水面高程"],
            outlet_elevation_m=elevations["巴氏计量槽出水水面高程"],
            note="喉宽0.90m",
        ),
        UnitProfile(
            "出水口",
            "出水口",
            width_mm=8.0,
            kind="outlet",
            inlet_elevation_m=elevations["最终出水口水面高程"],
            outlet_elevation_m=elevations["最终出水口水面高程"],
        ),
    ]


def place_units(profiles: list[UnitProfile], pipes: list[PipeData]) -> list[PlacedUnit]:
    total_width = sum(profile.width_mm for profile in profiles)
    total_width += sum(pipe.length_m * 1000 / 500 for pipe in pipes)
    cursor = -total_width / 2
    placed: list[PlacedUnit] = []
    for index, profile in enumerate(profiles):
        placed_unit = PlacedUnit(profile, cursor, cursor + profile.width_mm)
        placed.append(placed_unit)
        cursor = placed_unit.right
        if index < len(pipes):
            cursor += pipes[index].length_m * 1000 / 500
    return placed


def _y(elevation_m: float) -> float:
    return to_elevation_coordinates(0.0, elevation_m, datum_elevation_m=DATUM_ELEVATION_M)[1]


def _text(msp: ezdxf.layouts.Modelspace, text: str, xy: tuple[float, float], height: float = 4.0, layer: str = "TEXT") -> None:
    msp.add_text(text, dxfattribs={"layer": layer, "height": height}).set_placement(xy)


def _water_line(msp: ezdxf.layouts.Modelspace, x1: float, x2: float, elevation_m: float, label: str, label_above: bool = True) -> None:
    y = _y(elevation_m)
    msp.add_line((x1, y), (x2, y), dxfattribs={"layer": "WATER_LEVEL"})
    offset = 9 if label_above else -13
    _text(msp, f"{label} {elevation_m:.4f} m", (x1, y + offset), height=2.7, layer="ELEVATION_TEXT")


def _outline_rect(msp: ezdxf.layouts.Modelspace, unit: PlacedUnit) -> None:
    profile = unit.profile
    water = max(x for x in (profile.inlet_elevation_m, profile.outlet_elevation_m) if x is not None)
    top = _y(water) + 10 if profile.total_height_m is None else _y(water) - profile.effective_depth_m * 20 + profile.total_height_m * 20
    bottom = _y(water) - (profile.effective_depth_m or 2.0) * 20
    points = [(unit.left, bottom), (unit.right, bottom), (unit.right, top), (unit.left, top), (unit.left, bottom)]
    msp.add_lwpolyline(points, dxfattribs={"layer": "STRUCTURE"})


def _outline_well(msp: ezdxf.layouts.Modelspace, unit: PlacedUnit) -> None:
    elevations = [x for x in (unit.profile.inlet_elevation_m, unit.profile.outlet_elevation_m) if x is not None]
    top = _y(max(elevations)) + 18
    bottom = _y(min(elevations)) - 42
    points = [(unit.left, bottom), (unit.right, bottom), (unit.right, top), (unit.left, top), (unit.left, bottom)]
    msp.add_lwpolyline(points, dxfattribs={"layer": "STRUCTURE"})


def _outline_radial(msp: ezdxf.layouts.Modelspace, unit: PlacedUnit) -> None:
    profile = unit.profile
    water = max(x for x in (profile.inlet_elevation_m, profile.outlet_elevation_m) if x is not None)
    if profile.total_height_m and profile.effective_depth_m:
        bottom = _y(water) - profile.effective_depth_m * 20
        top = bottom + profile.total_height_m * 20
    else:
        bottom = _y(water) - 70
        top = _y(water) + 16
    center = unit.center
    points = [
        (unit.left, top),
        (unit.right, top),
        (unit.right, bottom + 24),
        (center, bottom),
        (unit.left, bottom + 24),
        (unit.left, top),
    ]
    msp.add_lwpolyline(points, dxfattribs={"layer": "STRUCTURE"})


def _outline_contact(msp: ezdxf.layouts.Modelspace, unit: PlacedUnit) -> None:
    _outline_rect(msp, unit)
    for factor in (1 / 3, 2 / 3):
        x = unit.left + (unit.right - unit.left) * factor
        water = max(unit.profile.inlet_elevation_m or 0, unit.profile.outlet_elevation_m or 0)
        bottom = _y(water) - (unit.profile.effective_depth_m or 3.0) * 20
        top = bottom + (unit.profile.total_height_m or 4.38) * 20
        msp.add_line((x, bottom), (x, top), dxfattribs={"layer": "HIDDEN"})


def _outline_parshall(msp: ezdxf.layouts.Modelspace, unit: PlacedUnit) -> None:
    water = max(unit.profile.inlet_elevation_m or 0, unit.profile.outlet_elevation_m or 0)
    bottom = _y(water) - 26
    top = _y(water) + 12
    mid = unit.center
    points = [
        (unit.left, bottom),
        (mid - 2, bottom + 8),
        (mid + 2, bottom + 8),
        (unit.right, bottom),
        (unit.right, top),
        (unit.left, top),
        (unit.left, bottom),
    ]
    msp.add_lwpolyline(points, dxfattribs={"layer": "STRUCTURE"})


def draw_unit(msp: ezdxf.layouts.Modelspace, unit: PlacedUnit) -> None:
    kind = unit.profile.kind
    if kind == "rect":
        _outline_rect(msp, unit)
    elif kind == "well":
        _outline_well(msp, unit)
    elif kind in {"radial", "secondary_pending"}:
        _outline_radial(msp, unit)
    elif kind == "contact":
        _outline_contact(msp, unit)
    elif kind == "parshall":
        _outline_parshall(msp, unit)
    else:
        _outline_rect(msp, unit)

    profile = unit.profile
    _text(msp, profile.name, (unit.left, _y(2.7)), height=4.2)
    if profile.note:
        _text(msp, profile.note, (unit.left, _y(2.5)), height=3.2)
    if profile.inlet_elevation_m is not None:
        _water_line(msp, unit.left + 1.5, unit.center - 1.5, profile.inlet_elevation_m, "进水")
    elif profile.outlet_elevation_m is not None:
        _water_line(msp, unit.left + 1.5, unit.center - 1.5, profile.outlet_elevation_m, "进水待确认", label_above=False)
    if profile.outlet_elevation_m is not None:
        _water_line(msp, unit.center + 1.5, unit.right - 1.5, profile.outlet_elevation_m, "出水", label_above=False)


def draw_pipes(msp: ezdxf.layouts.Modelspace, placed: list[PlacedUnit], pipes: list[PipeData]) -> None:
    for index, pipe in enumerate(pipes):
        start = placed[index]
        end = placed[index + 1]
        start_elevation = start.profile.outlet_elevation_m or start.profile.inlet_elevation_m
        end_elevation = end.profile.inlet_elevation_m or end.profile.outlet_elevation_m
        if start_elevation is None or end_elevation is None:
            continue
        x1 = start.right
        x2 = end.left
        y1 = _y(start_elevation)
        y2 = _y(end_elevation)
        msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "WASTEWATER_PIPE"})
        label_x = (x1 + x2) / 2
        if index % 2 == 0:
            label_y = max(y1, y2) + 18
        else:
            label_y = min(y1, y2) - 20
        _text(msp, pipe.dn, (label_x - 8, label_y), height=3.0, layer="DIMENSION")
        _text(msp, f"i={pipe.slope:.6f}", (label_x - 8, label_y - 5), height=3.0, layer="DIMENSION")


def draw_dxf() -> Path:
    elevations, pipes = load_elevation_data()
    profiles = build_profiles(elevations)
    placed = place_units(profiles, pipes)

    doc = create_document()
    add_elevation_frame(
        doc,
        extra_notes=("3. 本图连接管长度及相关沿程损失为暂定值，待总平面确定后复核。",),
    )
    msp = doc.modelspace()
    draw_pipes(msp, placed, pipes)
    for unit in placed:
        draw_unit(msp, unit)
    DXF_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(DXF_OUTPUT)
    return DXF_OUTPUT


def draw_png() -> Path:
    elevations, pipes = load_elevation_data()
    profiles = build_profiles(elevations)
    placed = place_units(profiles, pipes)
    font = _font()
    text_kwargs = {"fontproperties": font} if font else {}

    half_w = FRAME_WIDTH / 2
    half_h = FRAME_HEIGHT / 2
    fig, ax = plt.subplots(figsize=(14.1, 10.0), dpi=140)
    ax.set_aspect("equal")
    ax.set_xlim(-half_w - 10, half_w + 10)
    ax.set_ylim(-half_h - 10, half_h + 10)
    ax.axis("off")

    title_top = -half_h + TITLE_BLOCK_HEIGHT
    ax.plot([-half_w, half_w, half_w, -half_w, -half_w], [-half_h, -half_h, half_h, half_h, -half_h], color="black", linewidth=1.0)
    ax.plot([-half_w, half_w], [title_top, title_top], color="black", linewidth=0.7)
    ax.plot([half_w - NOTES_BLOCK_WIDTH, half_w - NOTES_BLOCK_WIDTH], [-half_h, title_top], color="black", linewidth=0.7)
    ax.plot([half_w - NOTES_BLOCK_WIDTH - LEGEND_BLOCK_WIDTH, half_w - NOTES_BLOCK_WIDTH - LEGEND_BLOCK_WIDTH], [-half_h, title_top], color="black", linewidth=0.7)
    ax.plot([-half_w, half_w], [-half_h + TITLE_BLOCK_HEIGHT / 2, -half_h + TITLE_BLOCK_HEIGHT / 2], color="black", linewidth=0.7)

    ax.text(-half_w + 18, half_h - 30, "比例控制：H 1:500，V 1:50，纵向放大 10 倍", fontsize=9, **text_kwargs)
    ax.text(-half_w + 18, -half_h + 44, "图名：高程布置图", fontsize=14, **text_kwargs)
    ax.text(half_w - NOTES_BLOCK_WIDTH + 10, -half_h + 50, "说明：", fontsize=9, **text_kwargs)
    ax.text(half_w - NOTES_BLOCK_WIDTH + 10, -half_h + 32, "1. 本图纵向比例尺为 1:50，横向比例尺为 1:500。", fontsize=7, **text_kwargs)
    ax.text(half_w - NOTES_BLOCK_WIDTH + 10, -half_h + 20, "2. 本图标高以 m 计，标高为绝对标高。", fontsize=7, **text_kwargs)
    ax.text(half_w - NOTES_BLOCK_WIDTH + 10, -half_h + 8, "3. 连接管长度及沿程损失为暂定值，待总平面复核。", fontsize=7, **text_kwargs)
    legend_x = half_w - NOTES_BLOCK_WIDTH - LEGEND_BLOCK_WIDTH + 10
    ax.text(legend_x, -half_h + 50, "图例", fontsize=9, **text_kwargs)
    legend_items = (("污水管", "solid", 2.0), ("污泥管", "dashed", 1.5), ("回流污泥管", "dashdot", 1.5), ("送风管", (0, (5, 2, 1, 2)), 1.2))
    for index, (label, style, width) in enumerate(legend_items):
        y = -half_h + 34 - index * 8
        ax.plot([legend_x, legend_x + 46], [y, y], color="black", linestyle=style, linewidth=width)
        ax.text(legend_x + 54, y - 2.5, label, fontsize=6, **text_kwargs)

    for index, pipe in enumerate(pipes):
        start = placed[index]
        end = placed[index + 1]
        y1 = _y(start.profile.outlet_elevation_m or start.profile.inlet_elevation_m or 0)
        y2 = _y(end.profile.inlet_elevation_m or end.profile.outlet_elevation_m or 0)
        ax.plot([start.right, end.left], [y1, y2], color="black", linewidth=1.6)
        label_x = (start.right + end.left) / 2
        if index % 2 == 0:
            label_y = max(y1, y2) + 18
        else:
            label_y = min(y1, y2) - 20
        ax.text(label_x - 8, label_y, pipe.dn, fontsize=4.3, **text_kwargs)
        ax.text(label_x - 8, label_y - 5, f"i={pipe.slope:.6f}", fontsize=4.3, **text_kwargs)

    for unit in placed:
        _draw_unit_png(ax, unit, text_kwargs)

    PNG_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(PNG_OUTPUT, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    return PNG_OUTPUT


def _draw_unit_png(ax: plt.Axes, unit: PlacedUnit, text_kwargs: dict[str, FontProperties]) -> None:
    profile = unit.profile
    elevations = [x for x in (profile.inlet_elevation_m, profile.outlet_elevation_m) if x is not None]
    water = max(elevations)
    if profile.kind in {"radial", "secondary_pending"}:
        if profile.total_height_m and profile.effective_depth_m:
            bottom = _y(water) - profile.effective_depth_m * 20
            top = bottom + profile.total_height_m * 20
        else:
            bottom = _y(water) - 70
            top = _y(water) + 16
        points = [(unit.left, top), (unit.right, top), (unit.right, bottom + 24), (unit.center, bottom), (unit.left, bottom + 24), (unit.left, top)]
    elif profile.kind == "well":
        top = _y(max(elevations)) + 18
        bottom = _y(min(elevations)) - 42
        points = [(unit.left, bottom), (unit.right, bottom), (unit.right, top), (unit.left, top), (unit.left, bottom)]
    elif profile.kind == "parshall":
        bottom = _y(water) - 26
        top = _y(water) + 12
        points = [(unit.left, bottom), (unit.center - 2, bottom + 8), (unit.center + 2, bottom + 8), (unit.right, bottom), (unit.right, top), (unit.left, top), (unit.left, bottom)]
    else:
        bottom = _y(water) - (profile.effective_depth_m or 2.0) * 20
        top = _y(water) + 10 if profile.total_height_m is None else bottom + profile.total_height_m * 20
        points = [(unit.left, bottom), (unit.right, bottom), (unit.right, top), (unit.left, top), (unit.left, bottom)]
    xs, ys = zip(*points)
    ax.plot(xs, ys, color="black", linewidth=1.0)
    if profile.kind == "contact":
        for factor in (1 / 3, 2 / 3):
            x = unit.left + (unit.right - unit.left) * factor
            ax.plot([x, x], [min(ys), max(ys)], color="gray", linestyle="--", linewidth=0.8)
    ax.text(unit.left, _y(2.7), profile.name, fontsize=5.5, **text_kwargs)
    if profile.note:
        ax.text(unit.left, _y(2.5), profile.note, fontsize=4.5, **text_kwargs)
    if profile.inlet_elevation_m is not None:
        ax.plot([unit.left + 1.5, unit.center - 1.5], [_y(profile.inlet_elevation_m), _y(profile.inlet_elevation_m)], color="tab:blue", linestyle="--", linewidth=0.9)
        ax.text(unit.left + 1.5, _y(profile.inlet_elevation_m) + 9, f"进水 {profile.inlet_elevation_m:.4f} m", fontsize=3.3, color="tab:blue", **text_kwargs)
    if profile.outlet_elevation_m is not None:
        ax.plot([unit.center + 1.5, unit.right - 1.5], [_y(profile.outlet_elevation_m), _y(profile.outlet_elevation_m)], color="tab:blue", linestyle="--", linewidth=0.9)
        ax.text(unit.center + 1.5, _y(profile.outlet_elevation_m) - 13, f"出水 {profile.outlet_elevation_m:.4f} m", fontsize=3.3, color="tab:blue", **text_kwargs)


if __name__ == "__main__":
    print(draw_dxf())
    print(draw_png())
