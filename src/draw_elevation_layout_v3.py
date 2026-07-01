"""Draw elevation layout V3 review draft.

V3 fixes the A2/O partition lengths, adds a broken-line expression for the long
outlet pipe, improves water-level label avoidance, and keeps all unconfirmed
dimensions out of the drawing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties, findSystemFonts

from cad_config import (
    FRAME_HEIGHT,
    FRAME_WIDTH,
    LEGEND_BLOCK_WIDTH,
    NOTES_BLOCK_WIDTH,
    TITLE_BLOCK_HEIGHT,
    to_elevation_coordinates,
)
from dxf_framework import TEXT_STYLE, add_elevation_frame, create_document


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT_DIR / "docs" / "elevation_data.md"
DXF_OUTPUT = ROOT_DIR / "output" / "elevation_layout_v3.dxf"
PNG_OUTPUT = ROOT_DIR / "output" / "elevation_layout_v3.png"
CHECK_OUTPUT = ROOT_DIR / "docs" / "elevation_layout_v3_check.md"
DATUM_ELEVATION_M = 0.0
DRAWING_X_MIN = -390.0
DRAWING_X_MAX = 390.0
LAST_PIPE_DRAWING_LENGTH_MM = 120.0
A2O_PARTITIONS_M = (("厌氧区", 7.5), ("缺氧区", 16.0), ("好氧区", 29.5))


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
    preferred_keywords = (
        "NotoSansCJK",
        "Noto Sans CJK",
        "NotoSerifCJK",
        "Noto Serif CJK",
        "SourceHanSans",
        "Source Han Sans",
        "SourceHanSerif",
        "Source Han Serif",
        "思源黑体",
        "思源宋体",
        "simsun",
        "msyh",
    )
    try:
        system_fonts = [Path(path) for path in findSystemFonts()]
    except Exception:
        system_fonts = []
    explicit_fonts = [
        Path("C:/Windows/Fonts/simsun.ttc"),
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
    ]
    for keyword in preferred_keywords:
        keyword_lower = keyword.lower()
        for candidate in system_fonts + explicit_fonts:
            if keyword_lower in candidate.name.lower() and candidate.exists():
                return FontProperties(fname=str(candidate))
    for candidate in explicit_fonts:
        if candidate.exists():
            return FontProperties(fname=str(candidate))
    return None


def load_elevation_data(path: Path = DATA_PATH) -> tuple[dict[str, float], list[PipeData]]:
    text = path.read_text(encoding="utf-8")
    elevations = {
        match.group(1): float(match.group(2))
        for match in re.finditer(r"-\s*(.+?水面高程|最终出水口水面高程)：([0-9.]+)\s*m", text)
    }
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
        raise ValueError("Expected 8 pipe records in docs/elevation_data.md")
    return elevations, pipes


def build_profiles(elevations: dict[str, float]) -> list[UnitProfile]:
    return [
        UnitProfile(
            "曝气沉砂池",
            width_mm=18.0 * 1000 / 500,
            kind="grit",
            inlet_elevation_m=None,
            outlet_elevation_m=elevations["曝气沉砂池出水水面高程"],
            effective_depth_m=2.0,
            total_height_m=3.9,
            note="2格并联；每格18.0m×3.6m；H=3.9m",
        ),
        UnitProfile(
            "集配水井",
            width_mm=8.0,
            kind="well",
            inlet_elevation_m=elevations["集配水井进水水面高程"],
            outlet_elevation_m=elevations["集配水井出水水面高程"],
            note="简化井体剖面",
        ),
        UnitProfile(
            "初沉池",
            width_mm=35.0 * 1000 / 500,
            kind="primary",
            inlet_elevation_m=elevations["初沉池进水水面高程"],
            outlet_elevation_m=elevations["初沉池出水水面高程"],
            effective_depth_m=3.0,
            total_height_m=6.31,
            note="D=35.0m；有效水深3.0m；H=6.31m",
        ),
        UnitProfile(
            "生物池配水设施",
            width_mm=8.0,
            kind="well",
            inlet_elevation_m=elevations["生物池配水设施进水水面高程"],
            outlet_elevation_m=elevations["生物池配水设施出水水面高程"],
            note="连接A²/O前端",
        ),
        UnitProfile(
            "A²/O 生物反应池",
            width_mm=53.0 * 1000 / 500,
            kind="a2o",
            inlet_elevation_m=elevations["A²/O 生物反应池进水水面高程"],
            outlet_elevation_m=elevations["A²/O 生物反应池出水水面高程"],
            effective_depth_m=5.0,
            total_height_m=None,
            note="每组总长53.0m；有效水深5.0m；分区7.5/16.0/29.5m",
        ),
        UnitProfile(
            "二沉池",
            width_mm=28.0,
            kind="secondary_pending",
            inlet_elevation_m=elevations["二沉池进水水面高程"],
            outlet_elevation_m=elevations["二沉池出水水面高程"],
            note="尺寸待按最新版计算书确认",
        ),
        UnitProfile(
            "消毒接触池",
            width_mm=21.5 * 1000 / 500,
            kind="contact",
            inlet_elevation_m=elevations["消毒接触池进水水面高程"],
            outlet_elevation_m=elevations["消毒接触池出水水面高程"],
            effective_depth_m=3.0,
            total_height_m=4.38,
            note="3廊道；单廊道21.5m×5.0m；H=4.38m",
        ),
        UnitProfile(
            "巴氏计量槽",
            width_mm=12.0,
            kind="parshall",
            inlet_elevation_m=elevations["巴氏计量槽进水水面高程"],
            outlet_elevation_m=elevations["巴氏计量槽出水水面高程"],
            note="喉宽0.90m；h上游=0.634m；h下游≤0.443m",
        ),
        UnitProfile(
            "出水口",
            width_mm=8.0,
            kind="outlet",
            inlet_elevation_m=elevations["最终出水口水面高程"],
            outlet_elevation_m=elevations["最终出水口水面高程"],
        ),
    ]


def place_units(profiles: list[UnitProfile], pipes: list[PipeData]) -> list[PlacedUnit]:
    total_width = sum(profile.width_mm for profile in profiles)
    for index, pipe in enumerate(pipes):
        total_width += LAST_PIPE_DRAWING_LENGTH_MM if index == len(pipes) - 1 else pipe.length_m * 1000 / 500
    if total_width > DRAWING_X_MAX - DRAWING_X_MIN:
        raise ValueError("V3 layout exceeds available drawing width.")
    cursor = -total_width / 2
    placed: list[PlacedUnit] = []
    for index, profile in enumerate(profiles):
        placed_unit = PlacedUnit(profile, cursor, cursor + profile.width_mm)
        placed.append(placed_unit)
        cursor = placed_unit.right
        if index < len(pipes):
            cursor += LAST_PIPE_DRAWING_LENGTH_MM if index == len(pipes) - 1 else pipes[index].length_m * 1000 / 500
    return placed


def _y(elevation_m: float) -> float:
    return to_elevation_coordinates(0, elevation_m, datum_elevation_m=DATUM_ELEVATION_M)[1]


def _add_text(msp: ezdxf.layouts.Modelspace, text: str, xy: tuple[float, float], height: float = 3.2, layer: str = "TEXT") -> None:
    msp.add_text(text, dxfattribs={"layer": layer, "height": height, "style": TEXT_STYLE}).set_placement(xy)


def _water_y(profile: UnitProfile) -> float:
    values = [v for v in (profile.inlet_elevation_m, profile.outlet_elevation_m) if v is not None]
    return _y(max(values))


def _rect_limits(profile: UnitProfile) -> tuple[float, float]:
    water_y = _water_y(profile)
    depth = profile.effective_depth_m or 2.0
    bottom = water_y - depth * 20
    top = bottom + profile.total_height_m * 20 if profile.total_height_m is not None else water_y + 14
    return bottom, top


def _polyline(msp: ezdxf.layouts.Modelspace, points: list[tuple[float, float]], layer: str = "STRUCTURE") -> None:
    msp.add_lwpolyline(points, dxfattribs={"layer": layer})


def _draw_grit(msp: ezdxf.layouts.Modelspace, unit: PlacedUnit) -> None:
    bottom, top = _rect_limits(unit.profile)
    mid = unit.center
    _polyline(msp, [(unit.left, bottom), (unit.right, bottom), (unit.right, top), (unit.left, top), (unit.left, bottom)])
    msp.add_line((mid, bottom), (mid, top), dxfattribs={"layer": "HIDDEN"})
    msp.add_line((unit.left, top), (unit.right, top), dxfattribs={"layer": "STRUCTURE"})
    msp.add_line((unit.left, bottom), (unit.right, bottom), dxfattribs={"layer": "STRUCTURE"})


def _draw_well(msp: ezdxf.layouts.Modelspace, unit: PlacedUnit) -> None:
    values = [v for v in (unit.profile.inlet_elevation_m, unit.profile.outlet_elevation_m) if v is not None]
    bottom = _y(min(values)) - 45
    top = _y(max(values)) + 22
    _polyline(msp, [(unit.left, bottom), (unit.right, bottom), (unit.right, top), (unit.left, top), (unit.left, bottom)])
    msp.add_line((unit.center, bottom), (unit.center, top), dxfattribs={"layer": "HIDDEN"})


def _draw_radial(msp: ezdxf.layouts.Modelspace, unit: PlacedUnit, confirmed: bool) -> None:
    profile = unit.profile
    if confirmed:
        bottom, top = _rect_limits(profile)
        slope_bottom = bottom + 28
    else:
        water_y = _water_y(profile)
        bottom = water_y - 70
        top = water_y + 18
        slope_bottom = bottom + 28
    points = [
        (unit.left, top),
        (unit.right, top),
        (unit.right, slope_bottom),
        (unit.center, bottom),
        (unit.left, slope_bottom),
        (unit.left, top),
    ]
    _polyline(msp, points)
    msp.add_line((unit.center, top), (unit.center, bottom), dxfattribs={"layer": "HIDDEN"})


def _draw_a2o(msp: ezdxf.layouts.Modelspace, unit: PlacedUnit) -> None:
    bottom, top = _rect_limits(unit.profile)
    _polyline(msp, [(unit.left, bottom), (unit.right, bottom), (unit.right, top), (unit.left, top), (unit.left, bottom)])
    width = unit.right - unit.left
    total_length = sum(length for _, length in A2O_PARTITIONS_M)
    x = unit.left
    for _, length in A2O_PARTITIONS_M[:-1]:
        x += width * length / total_length
        msp.add_line((x, bottom), (x, top), dxfattribs={"layer": "HIDDEN"})
    x = unit.left
    for label, length in A2O_PARTITIONS_M:
        zone_width = width * length / total_length
        _add_text(msp, label, (x + zone_width / 2 - 8, top - 12), height=3.0)
        x += zone_width


def _draw_contact(msp: ezdxf.layouts.Modelspace, unit: PlacedUnit) -> None:
    bottom, top = _rect_limits(unit.profile)
    _polyline(msp, [(unit.left, bottom), (unit.right, bottom), (unit.right, top), (unit.left, top), (unit.left, bottom)])
    for factor in (1 / 3, 2 / 3):
        x = unit.left + (unit.right - unit.left) * factor
        msp.add_line((x, bottom), (x, top), dxfattribs={"layer": "HIDDEN"})


def _draw_parshall(msp: ezdxf.layouts.Modelspace, unit: PlacedUnit) -> None:
    water_y = _water_y(unit.profile)
    bottom = water_y - 30
    top = water_y + 16
    throat_left = unit.center - 2.2
    throat_right = unit.center + 2.2
    points = [
        (unit.left, bottom),
        (throat_left, bottom + 10),
        (throat_right, bottom + 10),
        (unit.right, bottom),
        (unit.right, top),
        (unit.left, top),
        (unit.left, bottom),
    ]
    _polyline(msp, points)


def _draw_outlet(msp: ezdxf.layouts.Modelspace, unit: PlacedUnit) -> None:
    water_y = _water_y(unit.profile)
    _polyline(msp, [(unit.left, water_y - 35), (unit.right, water_y - 35), (unit.right, water_y + 12), (unit.left, water_y + 12), (unit.left, water_y - 35)])


def draw_unit(msp: ezdxf.layouts.Modelspace, unit: PlacedUnit) -> None:
    kind = unit.profile.kind
    if kind == "grit":
        _draw_grit(msp, unit)
    elif kind == "well":
        _draw_well(msp, unit)
    elif kind == "primary":
        _draw_radial(msp, unit, confirmed=True)
    elif kind == "a2o":
        _draw_a2o(msp, unit)
    elif kind == "secondary_pending":
        _draw_radial(msp, unit, confirmed=False)
    elif kind == "contact":
        _draw_contact(msp, unit)
    elif kind == "parshall":
        _draw_parshall(msp, unit)
    else:
        _draw_outlet(msp, unit)

    profile = unit.profile
    name_y, note_y = _label_positions(unit)
    _add_text(msp, profile.name, (unit.left, name_y), height=3.8)
    if profile.note:
        _add_text(msp, profile.note, (unit.left, note_y), height=2.6)
    if unit.right - unit.left < 20:
        draw_external_water_labels(msp, unit)
    else:
        if profile.inlet_elevation_m is not None:
            draw_water_line(msp, unit.left + 1.5, unit.center - 1.5, profile.inlet_elevation_m, "进水", True)
        if profile.outlet_elevation_m is not None:
            draw_water_line(msp, unit.center + 1.5, unit.right - 1.5, profile.outlet_elevation_m, "出水", False)


def _label_positions(unit: PlacedUnit) -> tuple[float, float]:
    bottom, top = _unit_vertical_bounds(unit)
    title_top = -FRAME_HEIGHT / 2 + TITLE_BLOCK_HEIGHT
    if bottom - 20 > title_top:
        return bottom - 12, bottom - 20
    return top + 12, top + 4


def _unit_vertical_bounds(unit: PlacedUnit) -> tuple[float, float]:
    profile = unit.profile
    if profile.kind in {"grit", "a2o", "contact"}:
        return _rect_limits(profile)
    if profile.kind == "well":
        values = [v for v in (profile.inlet_elevation_m, profile.outlet_elevation_m) if v is not None]
        return _y(min(values)) - 45, _y(max(values)) + 22
    if profile.kind in {"primary", "secondary_pending"}:
        if profile.kind == "primary":
            return _rect_limits(profile)
        water_y = _water_y(profile)
        return water_y - 70, water_y + 18
    if profile.kind == "parshall":
        water_y = _water_y(profile)
        return water_y - 30, water_y + 16
    water_y = _water_y(profile)
    return water_y - 35, water_y + 12


def draw_water_line(msp: ezdxf.layouts.Modelspace, x1: float, x2: float, elevation_m: float, label: str, above: bool) -> None:
    y = _y(elevation_m)
    msp.add_line((x1, y), (x2, y), dxfattribs={"layer": "WATER_LEVEL"})
    offset = 9 if above else -12
    _add_text(msp, f"{label} {elevation_m:.4f} m", (x1, y + offset), height=2.4, layer="ELEVATION_TEXT")


def draw_external_water_labels(msp: ezdxf.layouts.Modelspace, unit: PlacedUnit) -> None:
    profile = unit.profile
    if profile.inlet_elevation_m is not None:
        y = _y(profile.inlet_elevation_m)
        msp.add_line((unit.left, y), (unit.left - 18, y), dxfattribs={"layer": "WATER_LEVEL"})
        msp.add_line((unit.left - 18, y), (unit.left - 28, y + 12), dxfattribs={"layer": "ELEVATION_TEXT"})
        _add_text(msp, f"进水 {profile.inlet_elevation_m:.4f} m", (unit.left - 54, y + 14), height=2.4, layer="ELEVATION_TEXT")
    if profile.outlet_elevation_m is not None:
        y = _y(profile.outlet_elevation_m)
        msp.add_line((unit.right, y), (unit.right + 18, y), dxfattribs={"layer": "WATER_LEVEL"})
        msp.add_line((unit.right + 18, y), (unit.right + 28, y - 12), dxfattribs={"layer": "ELEVATION_TEXT"})
        _add_text(msp, f"出水 {profile.outlet_elevation_m:.4f} m", (unit.right + 4, y - 19), height=2.4, layer="ELEVATION_TEXT")


def draw_main_pipes(msp: ezdxf.layouts.Modelspace, placed: list[PlacedUnit], pipes: list[PipeData]) -> None:
    for index, pipe in enumerate(pipes):
        start = placed[index]
        end = placed[index + 1]
        y1 = _y(start.profile.outlet_elevation_m or start.profile.inlet_elevation_m or 0)
        y2 = _y(end.profile.inlet_elevation_m or end.profile.outlet_elevation_m or 0)
        if index == len(pipes) - 1:
            draw_broken_pipe(msp, start.right, y1, end.left, y2)
        else:
            msp.add_line((start.right, y1), (end.left, y2), dxfattribs={"layer": "WASTEWATER_PIPE"})
        label_x = (start.right + end.left) / 2 - 7
        if index % 2 == 0:
            label_y = max(y1, y2) + 18
        else:
            label_y = min(y1, y2) - 21
        _add_text(msp, pipe.dn, (label_x, label_y), height=2.8, layer="DIMENSION")
        _add_text(msp, f"i={pipe.slope:.6f}", (label_x, label_y - 5), height=2.8, layer="DIMENSION")
        if index == len(pipes) - 1:
            _add_text(msp, "L=100 m（中间断开）", (label_x, label_y - 10), height=2.8, layer="DIMENSION")


def draw_broken_pipe(msp: ezdxf.layouts.Modelspace, x1: float, y1: float, x2: float, y2: float) -> None:
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    gap = 12
    msp.add_line((x1, y1), (mid_x - gap, mid_y), dxfattribs={"layer": "WASTEWATER_PIPE"})
    msp.add_line((mid_x + gap, mid_y), (x2, y2), dxfattribs={"layer": "WASTEWATER_PIPE"})
    for offset in (-4, 4):
        x = mid_x + offset
        msp.add_line((x - 3, mid_y - 7), (x + 3, mid_y + 7), dxfattribs={"layer": "WASTEWATER_PIPE"})


def draw_return_sludge_and_air(msp: ezdxf.layouts.Modelspace, placed: list[PlacedUnit]) -> None:
    by_name = {unit.profile.name: unit for unit in placed}
    secondary = by_name["二沉池"]
    a2o = by_name["A²/O 生物反应池"]
    return_y = _y(1.45)
    points = [
        (secondary.center, _y(secondary.profile.outlet_elevation_m or 4.1) - 50),
        (secondary.center, return_y),
        (a2o.left + 8, return_y),
        (a2o.left + 8, _y(a2o.profile.inlet_elevation_m or 5.0) - 35),
    ]
    msp.add_lwpolyline(points, dxfattribs={"layer": "RETURN_SLUDGE_PIPE"})
    _add_text(msp, "回流污泥管（高程待确认）", (a2o.left + 10, return_y + 5), height=3.0, layer="DIMENSION")

    air_y = _y(7.0)
    good_zone_x = a2o.left + (a2o.right - a2o.left) * 0.70
    air_points = [
        (a2o.right + 20, air_y),
        (good_zone_x, air_y),
        (good_zone_x, _y(a2o.profile.outlet_elevation_m or 4.7) + 18),
    ]
    msp.add_lwpolyline(air_points, dxfattribs={"layer": "AIR_PIPE"})
    _add_text(msp, "送风管（接入好氧区）", (good_zone_x + 4, air_y + 5), height=3.0, layer="DIMENSION")


def draw_dxf() -> Path:
    elevations, pipes = load_elevation_data()
    placed = place_units(build_profiles(elevations), pipes)
    doc = create_document()
    add_elevation_frame(
        doc,
        extra_notes=(
            "3. 本图连接管长度及相关沿程损失为暂定值，待总平面确定后复核。",
            "4. 二沉池尺寸待按最新版计算书最终确认。",
            "5. 污水连接管竖向位置用于流程与水面表达，管底高程待复核。",
        ),
    )
    msp = doc.modelspace()
    draw_main_pipes(msp, placed, pipes)
    for unit in placed:
        draw_unit(msp, unit)
    draw_return_sludge_and_air(msp, placed)
    DXF_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(DXF_OUTPUT)
    return DXF_OUTPUT


def write_check_file(placed: list[PlacedUnit]) -> Path:
    occupied_width = placed[-1].right - placed[0].left
    text = "\n".join(
        [
            "# 高程布置图 V3 自检",
            "",
            f"- 图框可用宽度：{DRAWING_X_MAX - DRAWING_X_MIN:.1f} mm",
            f"- 主流程实际占用宽度：{occupied_width:.1f} mm",
            "- 是否使用最终出水管断线：是，巴氏计量槽至出水口 DN1100 管采用中部双斜断线表达",
            "- 是否存在未经确认的二沉池尺寸：否，图中仅标注“尺寸待按最新版计算书确认”",
            "- 是否存在未经确认的 A²/O 总高度：否，图中未标注 A²/O 总高度",
            "",
            "## 待后续确认的数据",
            "",
            "- 二沉池池径、总高度、池底高程",
            "- 总平面最终确定后的连接管实际长度",
            "- 各连接管沿程损失、局部损失及管底高程复核值",
            "- 回流污泥管和送风管的实际管径、管底或管中心高程",
            "",
        ]
    )
    CHECK_OUTPUT.write_text(text, encoding="utf-8")
    return CHECK_OUTPUT


def draw_png() -> Path:
    elevations, pipes = load_elevation_data()
    placed = place_units(build_profiles(elevations), pipes)
    font = _font()
    text_kwargs = {"fontproperties": font} if font else {}

    half_w = FRAME_WIDTH / 2
    half_h = FRAME_HEIGHT / 2
    fig, ax = plt.subplots(figsize=(16.5, 11.7), dpi=160)
    ax.set_aspect("equal")
    ax.set_xlim(-half_w - 10, half_w + 10)
    ax.set_ylim(-half_h - 10, half_h + 10)
    ax.axis("off")

    _png_frame(ax, text_kwargs)
    _png_main_pipes(ax, placed, pipes, text_kwargs)
    for unit in placed:
        _png_unit(ax, unit, text_kwargs)
    _png_return_sludge_and_air(ax, placed, text_kwargs)

    PNG_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(PNG_OUTPUT, bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)
    return PNG_OUTPUT


def _png_frame(ax: plt.Axes, text_kwargs: dict) -> None:
    half_w = FRAME_WIDTH / 2
    half_h = FRAME_HEIGHT / 2
    title_top = -half_h + TITLE_BLOCK_HEIGHT
    ax.plot([-half_w, half_w, half_w, -half_w, -half_w], [-half_h, -half_h, half_h, half_h, -half_h], color="black", linewidth=1.0)
    ax.plot([-half_w, half_w], [title_top, title_top], color="black", linewidth=0.7)
    ax.plot([half_w - NOTES_BLOCK_WIDTH, half_w - NOTES_BLOCK_WIDTH], [-half_h, title_top], color="black", linewidth=0.7)
    ax.plot([half_w - NOTES_BLOCK_WIDTH - LEGEND_BLOCK_WIDTH, half_w - NOTES_BLOCK_WIDTH - LEGEND_BLOCK_WIDTH], [-half_h, title_top], color="black", linewidth=0.7)
    ax.plot([-half_w, half_w], [-half_h + TITLE_BLOCK_HEIGHT / 2, -half_h + TITLE_BLOCK_HEIGHT / 2], color="black", linewidth=0.7)
    ax.text(-half_w + 18, half_h - 30, "比例控制：H 1:500，V 1:50，纵向放大 10 倍", fontsize=10, **text_kwargs)
    ax.text(-half_w + 18, -half_h + 44, "图名：高程布置图", fontsize=15, **text_kwargs)
    notes_x = half_w - NOTES_BLOCK_WIDTH + 10
    ax.text(notes_x, -half_h + 50, "说明：", fontsize=9, **text_kwargs)
    ax.text(notes_x, -half_h + 34, "1. 本图纵向比例尺为 1:50，横向比例尺为 1:500。", fontsize=5.5, **text_kwargs)
    ax.text(notes_x, -half_h + 26, "2. 本图标高以 m 计，标高为绝对标高。", fontsize=5.5, **text_kwargs)
    ax.text(notes_x, -half_h + 18, "3. 连接管长度及沿程损失为暂定值，待总平面复核。", fontsize=5.5, **text_kwargs)
    ax.text(notes_x, -half_h + 10, "4. 二沉池尺寸待按最新版计算书最终确认。", fontsize=5.5, **text_kwargs)
    ax.text(notes_x, -half_h + 2, "5. 污水连接管竖向位置用于流程与水面表达，管底高程待复核。", fontsize=5.5, **text_kwargs)
    legend_x = half_w - NOTES_BLOCK_WIDTH - LEGEND_BLOCK_WIDTH + 10
    ax.text(legend_x, -half_h + 50, "图例", fontsize=9, **text_kwargs)
    items = (("污水管", "solid", 2.0), ("污泥管", "dashed", 1.4), ("回流污泥管", "dashdot", 1.4), ("送风管", (0, (5, 2, 1, 2)), 1.2))
    for index, (label, style, width) in enumerate(items):
        y = -half_h + 34 - index * 8
        ax.plot([legend_x, legend_x + 46], [y, y], color="black", linestyle=style, linewidth=width)
        ax.text(legend_x + 54, y - 2.5, label, fontsize=6, **text_kwargs)


def _png_main_pipes(ax: plt.Axes, placed: list[PlacedUnit], pipes: list[PipeData], text_kwargs: dict) -> None:
    for index, pipe in enumerate(pipes):
        start = placed[index]
        end = placed[index + 1]
        y1 = _y(start.profile.outlet_elevation_m or start.profile.inlet_elevation_m or 0)
        y2 = _y(end.profile.inlet_elevation_m or end.profile.outlet_elevation_m or 0)
        if index == len(pipes) - 1:
            _png_broken_pipe(ax, start.right, y1, end.left, y2)
        else:
            ax.plot([start.right, end.left], [y1, y2], color="black", linewidth=1.7)
        label_x = (start.right + end.left) / 2 - 7
        label_y = max(y1, y2) + 18 if index % 2 == 0 else min(y1, y2) - 21
        ax.text(label_x, label_y, pipe.dn, fontsize=4.5, **text_kwargs)
        ax.text(label_x, label_y - 5, f"i={pipe.slope:.6f}", fontsize=4.5, **text_kwargs)
        if index == len(pipes) - 1:
            ax.text(label_x, label_y - 10, "L=100 m（中间断开）", fontsize=4.5, **text_kwargs)


def _png_broken_pipe(ax: plt.Axes, x1: float, y1: float, x2: float, y2: float) -> None:
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    gap = 12
    ax.plot([x1, mid_x - gap], [y1, mid_y], color="black", linewidth=1.7)
    ax.plot([mid_x + gap, x2], [mid_y, y2], color="black", linewidth=1.7)
    for offset in (-4, 4):
        x = mid_x + offset
        ax.plot([x - 3, x + 3], [mid_y - 7, mid_y + 7], color="black", linewidth=1.4)


def _png_unit(ax: plt.Axes, unit: PlacedUnit, text_kwargs: dict) -> None:
    outline, internal = _png_profile_geometry(unit)
    xs, ys = zip(*outline)
    ax.plot(xs, ys, color="black", linewidth=1.0)
    for segment in internal:
        ax.plot([segment[0][0], segment[1][0]], [segment[0][1], segment[1][1]], color="gray", linestyle="--", linewidth=0.7)
    if unit.profile.kind == "a2o":
        bottom, top = _rect_limits(unit.profile)
        width = unit.right - unit.left
        total_length = sum(length for _, length in A2O_PARTITIONS_M)
        x = unit.left
        for label, length in A2O_PARTITIONS_M:
            zone_width = width * length / total_length
            ax.text(x + zone_width / 2 - 7, top - 12, label, fontsize=4.2, **text_kwargs)
            x += zone_width
    name_y, note_y = _label_positions(unit)
    ax.text(unit.left, name_y, unit.profile.name, fontsize=5.1, **text_kwargs)
    if unit.profile.note:
        ax.text(unit.left, note_y, unit.profile.note, fontsize=3.8, **text_kwargs)
    if unit.right - unit.left < 20:
        _png_external_water(ax, unit, text_kwargs)
    else:
        if unit.profile.inlet_elevation_m is not None:
            _png_water(ax, unit.left + 1.5, unit.center - 1.5, unit.profile.inlet_elevation_m, "进水", True, text_kwargs)
        if unit.profile.outlet_elevation_m is not None:
            _png_water(ax, unit.center + 1.5, unit.right - 1.5, unit.profile.outlet_elevation_m, "出水", False, text_kwargs)


def _png_profile_geometry(unit: PlacedUnit) -> tuple[list[tuple[float, float]], list[tuple[tuple[float, float], tuple[float, float]]]]:
    profile = unit.profile
    internal: list[tuple[tuple[float, float], tuple[float, float]]] = []
    if profile.kind in {"grit", "a2o", "contact"}:
        bottom, top = _rect_limits(profile)
        outline = [(unit.left, bottom), (unit.right, bottom), (unit.right, top), (unit.left, top), (unit.left, bottom)]
        if profile.kind == "grit":
            internal.append(((unit.center, bottom), (unit.center, top)))
        if profile.kind == "a2o":
            total = sum(length for _, length in A2O_PARTITIONS_M)
            x1 = unit.left + (unit.right - unit.left) * A2O_PARTITIONS_M[0][1] / total
            x2 = unit.left + (unit.right - unit.left) * (A2O_PARTITIONS_M[0][1] + A2O_PARTITIONS_M[1][1]) / total
            internal.extend([((x1, bottom), (x1, top)), ((x2, bottom), (x2, top))])
        if profile.kind == "contact":
            for factor in (1 / 3, 2 / 3):
                x = unit.left + (unit.right - unit.left) * factor
                internal.append(((x, bottom), (x, top)))
        return outline, internal
    if profile.kind == "well":
        values = [v for v in (profile.inlet_elevation_m, profile.outlet_elevation_m) if v is not None]
        bottom = _y(min(values)) - 45
        top = _y(max(values)) + 22
        return [(unit.left, bottom), (unit.right, bottom), (unit.right, top), (unit.left, top), (unit.left, bottom)], [((unit.center, bottom), (unit.center, top))]
    if profile.kind in {"primary", "secondary_pending"}:
        confirmed = profile.kind == "primary"
        if confirmed:
            bottom, top = _rect_limits(profile)
            slope_bottom = bottom + 28
        else:
            water_y = _water_y(profile)
            bottom = water_y - 70
            top = water_y + 18
            slope_bottom = bottom + 28
        outline = [(unit.left, top), (unit.right, top), (unit.right, slope_bottom), (unit.center, bottom), (unit.left, slope_bottom), (unit.left, top)]
        return outline, [((unit.center, top), (unit.center, bottom))]
    if profile.kind == "parshall":
        water_y = _water_y(profile)
        bottom = water_y - 30
        top = water_y + 16
        outline = [(unit.left, bottom), (unit.center - 2.2, bottom + 10), (unit.center + 2.2, bottom + 10), (unit.right, bottom), (unit.right, top), (unit.left, top), (unit.left, bottom)]
        return outline, []
    water_y = _water_y(profile)
    return [(unit.left, water_y - 35), (unit.right, water_y - 35), (unit.right, water_y + 12), (unit.left, water_y + 12), (unit.left, water_y - 35)], []


def _png_water(ax: plt.Axes, x1: float, x2: float, elevation_m: float, label: str, above: bool, text_kwargs: dict) -> None:
    y = _y(elevation_m)
    ax.plot([x1, x2], [y, y], color="tab:blue", linestyle="--", linewidth=0.8)
    offset = 9 if above else -12
    ax.text(x1, y + offset, f"{label} {elevation_m:.4f} m", fontsize=3.2, color="tab:blue", **text_kwargs)


def _png_external_water(ax: plt.Axes, unit: PlacedUnit, text_kwargs: dict) -> None:
    profile = unit.profile
    if profile.inlet_elevation_m is not None:
        y = _y(profile.inlet_elevation_m)
        ax.plot([unit.left, unit.left - 18, unit.left - 28], [y, y, y + 12], color="tab:blue", linestyle="--", linewidth=0.75)
        ax.text(unit.left - 54, y + 14, f"进水 {profile.inlet_elevation_m:.4f} m", fontsize=3.0, color="tab:blue", **text_kwargs)
    if profile.outlet_elevation_m is not None:
        y = _y(profile.outlet_elevation_m)
        ax.plot([unit.right, unit.right + 18, unit.right + 28], [y, y, y - 12], color="tab:blue", linestyle="--", linewidth=0.75)
        ax.text(unit.right + 4, y - 19, f"出水 {profile.outlet_elevation_m:.4f} m", fontsize=3.0, color="tab:blue", **text_kwargs)


def _png_return_sludge_and_air(ax: plt.Axes, placed: list[PlacedUnit], text_kwargs: dict) -> None:
    by_name = {unit.profile.name: unit for unit in placed}
    secondary = by_name["二沉池"]
    a2o = by_name["A²/O 生物反应池"]
    return_y = _y(1.45)
    ax.plot([secondary.center, secondary.center, a2o.left + 8, a2o.left + 8], [_y(3.4), return_y, return_y, _y(4.4)], color="black", linestyle="dashdot", linewidth=1.4)
    ax.text(a2o.left + 10, return_y + 5, "回流污泥管（高程待确认）", fontsize=4.5, **text_kwargs)
    good_zone_x = a2o.left + (a2o.right - a2o.left) * 0.70
    air_y = _y(7.0)
    ax.plot([a2o.right + 20, good_zone_x, good_zone_x], [air_y, air_y, _y(4.95)], color="black", linestyle=(0, (5, 2, 1, 2)), linewidth=1.3)
    ax.text(good_zone_x + 4, air_y + 5, "送风管（接入好氧区）", fontsize=4.5, **text_kwargs)


if __name__ == "__main__":
    elevations, pipes = load_elevation_data()
    placed_units = place_units(build_profiles(elevations), pipes)
    print(draw_dxf())
    print(draw_png())
    print(write_check_file(placed_units))
