"""Common CAD configuration for the wastewater treatment plant drawings."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DrawingScale:
    """Model space uses metres; paper frame values are also stored in metres."""

    name: str
    model_units: str
    paper_units: str
    model_to_plot: float


@dataclass(frozen=True)
class LayerSpec:
    name: str
    color: int
    linetype: str = "CONTINUOUS"
    lineweight: int = 25


MODEL_UNITS = "m"
DXF_INSUNITS_METRES = 6
DEFAULT_SCALE = DrawingScale(
    name="1:500",
    model_units=MODEL_UNITS,
    paper_units="mm",
    model_to_plot=500.0,
)

FRAME_WIDTH = 120.0
FRAME_HEIGHT = 80.0
AXIS_LENGTH = 100.0

STANDARD_LAYERS = (
    LayerSpec("FRAME", color=7, lineweight=35),
    LayerSpec("AXIS", color=1, linetype="CENTER", lineweight=18),
    LayerSpec("ELEVATION", color=3, lineweight=25),
    LayerSpec("STRUCTURE", color=5, lineweight=25),
    LayerSpec("DIMENSION", color=2, lineweight=18),
    LayerSpec("TEXT", color=7, lineweight=18),
)

