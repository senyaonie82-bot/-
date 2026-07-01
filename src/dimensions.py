"""Confirmed dimension reader.

This module intentionally reads dimensions only from docs/confirmed_dimensions.md.
Unconfirmed tank sizes must stay out of code until the design data is confirmed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIRMED_DIMENSIONS_FILE = ROOT_DIR / "docs" / "confirmed_dimensions.md"


@dataclass(frozen=True)
class RectangularUnit:
    name: str
    length_m: float
    width_m: float
    count: int


@dataclass(frozen=True)
class LinearUnit:
    name: str
    total_length_m: float
    count: int


@dataclass(frozen=True)
class PendingUnit:
    name: str
    note: str


@dataclass(frozen=True)
class ConfirmedDimensions:
    aerated_grit_chamber: RectangularUnit
    a2o_reactor: LinearUnit
    secondary_clarifier: PendingUnit


def _read_confirmed_text(path: Path = CONFIRMED_DIMENSIONS_FILE) -> str:
    return path.read_text(encoding="utf-8")


def load_confirmed_dimensions(path: Path = CONFIRMED_DIMENSIONS_FILE) -> ConfirmedDimensions:
    text = _read_confirmed_text(path)

    grit_match = re.search(r"曝气沉砂池\s+([0-9.]+)×([0-9.]+)（([0-9]+)格）", text)
    a2o_match = re.search(r"A²/O\s+总长\s+([0-9.]+)m（([0-9]+)组）", text)
    secondary_match = re.search(r"二沉池：(.+)", text)

    if not grit_match or not a2o_match or not secondary_match:
        raise ValueError("confirmed_dimensions.md must contain only the approved dimension lines.")

    return ConfirmedDimensions(
        aerated_grit_chamber=RectangularUnit(
            name="曝气沉砂池",
            length_m=float(grit_match.group(1)),
            width_m=float(grit_match.group(2)),
            count=int(grit_match.group(3)),
        ),
        a2o_reactor=LinearUnit(
            name="A²/O 生物反应池",
            total_length_m=float(a2o_match.group(1)),
            count=int(a2o_match.group(2)),
        ),
        secondary_clarifier=PendingUnit(
            name="二沉池",
            note=secondary_match.group(1).strip(),
        ),
    )


__all__ = [
    "CONFIRMED_DIMENSIONS_FILE",
    "ConfirmedDimensions",
    "LinearUnit",
    "PendingUnit",
    "RectangularUnit",
    "load_confirmed_dimensions",
]

