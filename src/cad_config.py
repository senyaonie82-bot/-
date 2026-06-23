"""Common CAD configuration for wastewater treatment plant drawings."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ElevationScale:
    """Elevation drawings use different horizontal and vertical scales."""

    horizontal: int
    vertical: int

    @property
    def vertical_exaggeration(self) -> float:
        return self.horizontal / self.vertical

    @property
    def label(self) -> str:
        return f"H 1:{self.horizontal}, V 1:{self.vertical}"

@dataclass(frozen=True)
class LayerSpec:
    name: str
    description: str
    color: int
    linetype: str = "CONTINUOUS"
    lineweight: int = 25


MODEL_UNITS = "m"
DXF_INSUNITS_METRES = 6
HORIZONTAL_SCALE = 500
VERTICAL_SCALE = 50
ELEVATION_SCALE = ElevationScale(horizontal=HORIZONTAL_SCALE, vertical=VERTICAL_SCALE)
VERTICAL_EXAGGERATION = ELEVATION_SCALE.vertical_exaggeration

FRAME_WIDTH = 160.0
FRAME_HEIGHT = 100.0
TITLE_BLOCK_HEIGHT = 18.0
NOTES_BLOCK_WIDTH = 70.0
LEGEND_BLOCK_WIDTH = 45.0
AXIS_LENGTH = 120.0

STANDARD_LAYERS = (
    LayerSpec("FRAME", "图框", color=7, lineweight=35),
    LayerSpec("TITLE_BLOCK", "标题栏", color=7, lineweight=25),
    LayerSpec("STRUCTURE", "构筑物剖面轮廓", color=5, lineweight=35),
    LayerSpec("WASTEWATER_PIPE", "污水管", color=4, linetype="CONTINUOUS", lineweight=50),
    LayerSpec("SLUDGE_PIPE", "污泥管", color=30, linetype="DASHED", lineweight=35),
    LayerSpec("RETURN_SLUDGE_PIPE", "回流污泥管", color=1, linetype="CENTER", lineweight=35),
    LayerSpec("SUPERNATANT_PIPE", "上清液回流管", color=6, linetype="DASHDOT", lineweight=25),
    LayerSpec("AIR_PIPE", "送风管", color=140, linetype="PHANTOM", lineweight=25),
    LayerSpec("WATER_LEVEL", "水面线", color=160, linetype="DASHED", lineweight=18),
    LayerSpec("ELEVATION_TEXT", "高程标注", color=3, lineweight=18),
    LayerSpec("DIMENSION", "尺寸及坡度标注", color=2, lineweight=18),
    LayerSpec("TEXT", "普通文字", color=7, lineweight=18),
    LayerSpec("HIDDEN", "隐藏线", color=8, linetype="DASHED", lineweight=13),
)


def to_elevation_coordinates(
    horizontal_distance_m: float,
    absolute_elevation_m: float,
    *,
    origin_distance_m: float = 0.0,
    datum_elevation_m: float = 0.0,
) -> tuple[float, float]:
    """Convert real plant distance/elevation to elevation drawing coordinates.

    The horizontal coordinate follows the plant flow distance. The vertical
    coordinate applies the 1:50 vertical scale relative to the 1:500 horizontal
    scale, so vertical differences are exaggerated by 10 times on the drawing.
    """

    x = horizontal_distance_m - origin_distance_m
    y = (absolute_elevation_m - datum_elevation_m) * VERTICAL_EXAGGERATION
    return x, y
