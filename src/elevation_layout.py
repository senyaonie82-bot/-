"""Elevation layout module for wastewater treatment plant drawings.

This module is reserved for the later elevation profile drawing. It currently
loads confirmed dimensions only, and does not place any treatment structure.
"""

from __future__ import annotations

from dataclasses import dataclass

from dimensions import ConfirmedDimensions, load_confirmed_dimensions


@dataclass(frozen=True)
class ElevationLayoutContext:
    dimensions: ConfirmedDimensions
    datum_name: str = "plant datum"


def create_context() -> ElevationLayoutContext:
    return ElevationLayoutContext(dimensions=load_confirmed_dimensions())


def planned_confirmed_units() -> tuple[str, ...]:
    dims = load_confirmed_dimensions()
    return (
        dims.aerated_grit_chamber.name,
        dims.a2o_reactor.name,
        dims.secondary_clarifier.name,
    )

