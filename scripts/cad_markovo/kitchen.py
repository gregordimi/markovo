"""
Markovo 3D CAD — Kitchen Joinery Adapter.

Delegates kitchen cabinetry, joinery, and appliance generation directly to the
modular `furniture.kitchen` package, ensuring zero duplicate definitions.
"""

from typing import Dict, List, Tuple
import bpy

from furniture.kitchen import (
    build_kitchen,
    create_kitchen_materials,
    resolve_kitchen_materials,
    DEFAULT_KITCHEN_UNITS,
)

UNIT_KINDS = ("blind", "door", "double_door", "drawers", "filler", "sink", "hob_oven", "tall_fridge")


def create_kitchen_run_3d(
    name_prefix: str,
    origin: Tuple[float, float],
    along: Tuple[float, float],
    out: Tuple[float, float],
    units: List[dict],
    mats: Dict[str, bpy.types.Material],
    col: bpy.types.Collection,
    parent: bpy.types.Object = None,
    worktop_start: float = None,
    plinth_start: float = 0.0,
    end_panel: bool = True,
) -> bpy.types.Object:
    """
    Adapter function that invokes `furniture.kitchen.build_kitchen`.
    Preserves backwards compatibility with `cad_markovo.builder.FloorPlanBuilder`.
    """
    return build_kitchen(
        origin=origin,
        along=along,
        out=out,
        units=units,
        col=col,
        parent=parent,
        mats=mats,
        worktop_start=worktop_start,
        plinth_start=plinth_start,
        end_panel=end_panel,
        name_prefix=name_prefix,
    )
