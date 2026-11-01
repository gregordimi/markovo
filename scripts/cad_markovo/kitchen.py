"""
Kitchen Joinery Geometry.

Builds straight kitchen runs along a wall face from a declarative list of units:
- Birch plywood carcasses whose front edges stay exposed around inset fronts
- Olive green inset doors and drawer fronts (front face olive, edges plywood)
- Recessed plywood plinth, with an optional plywood foot panel at a free run end
- Light solid wood worktop with a real cutout for a steel sink basin
- Black glass hob with cooking zones and a built-in oven front
- Tall fridge-freezer housing with two inset doors

Run-local coordinates: `s` runs along the wall from the run origin and `t` runs
out of the wall into the room, both in cm. Vertical values are in meters.

Supported unit kinds (listed in run order):
  "blind"        carcass only (blind corner, no front)
  "door"         one inset door
  "double_door"  two inset doors
  "drawers"      two deep drawers + one shallow top drawer
  "filler"       fixed inset panel
  "sink"         one inset door + steel basin and tap set into the worktop
  "hob_oven"     hob on the worktop, oven front, shallow drawer below
  "tall_fridge"  tall housing with freezer and fridge doors (no worktop above)
"""

from typing import Dict, List, Tuple
import bpy

from .config import (
    CM,
    KITCHEN_PLINTH_HEIGHT,
    KITCHEN_CARCASS_TOP,
    KITCHEN_WORKTOP_TOP,
    KITCHEN_TALL_TOP,
    KITCHEN_CARCASS_DEPTH,
    KITCHEN_WORKTOP_DEPTH,
    KITCHEN_PLINTH_SETBACK,
    KITCHEN_PANEL_THICKNESS,
    KITCHEN_FRONT_GAP,
    KITCHEN_FRONT_PROUD,
)
from .geometry import create_prism_from_quad, create_round_cylinder_3d

UNIT_KINDS = ("blind", "door", "double_door", "drawers", "filler", "sink", "hob_oven", "tall_fridge")

P = KITCHEN_PANEL_THICKNESS
D = KITCHEN_CARCASS_DEPTH
SINK_BASIN_DEPTH = 20.0 * CM   # m, basin floor 20 cm below the worktop
SINK_WALL = 0.8                # cm, basin wall thickness
SINK_BACK_STRIP = 8.0          # cm, worktop left behind the basin for the tap
SINK_FRONT_STRIP = 12.0        # cm, worktop left in front of the basin
DRAWER_TOP_HEIGHT = 15.0 * CM  # m, shallow top drawer front


class _RunFrame:
    """Maps run-local (s along the wall, t out of the wall) cm coordinates to plan (x, y) cm."""

    def __init__(self, origin: Tuple[float, float], along: Tuple[float, float], out: Tuple[float, float]):
        self.ox, self.oy = float(origin[0]), float(origin[1])
        self.ax, self.ay = float(along[0]), float(along[1])
        self.nx, self.ny = float(out[0]), float(out[1])

    def pt(self, s: float, t: float) -> Tuple[float, float]:
        return (self.ox + self.ax * s + self.nx * t, self.oy + self.ay * s + self.ny * t)

    def quad(self, s0: float, s1: float, t0: float, t1: float) -> list:
        return [self.pt(s0, t0), self.pt(s1, t0), self.pt(s1, t1), self.pt(s0, t1)]


def _box(
    name: str,
    frame: _RunFrame,
    s0: float, s1: float,
    t0: float, t1: float,
    z0: float, z1: float,
    mat: bpy.types.Material,
    col: bpy.types.Collection,
    parent: bpy.types.Object = None,
    front_mat: bpy.types.Material = None,
) -> bpy.types.Object:
    """Creates a run-aligned box. If front_mat is given, the face pointing into the room uses it."""
    obj = create_prism_from_quad(name, frame.quad(s0, s1, t0, t1), z0, z1, mat, col, parent)
    if front_mat is not None:
        obj.data.materials.append(front_mat)
        for poly in obj.data.polygons:
            if poly.normal.x * frame.nx + poly.normal.y * frame.ny > 0.9:
                poly.material_index = 1
    return obj


def _build_carcass(prefix, frame, s0, s1, z_top, open_top, ply, col, parent):
    """Builds a plywood carcass. Open-top carcasses (sink) are made of panels so the basin fits."""
    z_bot = KITCHEN_PLINTH_HEIGHT
    if not open_top:
        _box(f"{prefix}_Carcass", frame, s0, s1, 0.0, D, z_bot, z_top, ply, col, parent)
        return
    pz = P * CM
    _box(f"{prefix}_Side_A", frame, s0, s0 + P, 0.0, D, z_bot, z_top, ply, col, parent)
    _box(f"{prefix}_Side_B", frame, s1 - P, s1, 0.0, D, z_bot, z_top, ply, col, parent)
    _box(f"{prefix}_Bottom", frame, s0 + P, s1 - P, 0.0, D, z_bot, z_bot + pz, ply, col, parent)
    _box(f"{prefix}_Back", frame, s0 + P, s1 - P, 0.0, P, z_bot + pz, z_top, ply, col, parent)
    _box(f"{prefix}_Top_Rail", frame, s0 + P, s1 - P, D - P, D, z_top - pz, z_top, ply, col, parent)


def _build_unit(prefix: str, frame: _RunFrame, s0: float, s1: float, kind: str, mats: Dict, col, parent):
    """Builds one carcass with its inset fronts."""
    if kind not in UNIT_KINDS:
        raise ValueError(f"Unknown kitchen unit kind '{kind}'. Expected one of {UNIT_KINDS}.")

    ply = mats["kitchen_plywood"]
    olive = mats["kitchen_olive"]
    z_top = KITCHEN_TALL_TOP if kind == "tall_fridge" else KITCHEN_CARCASS_TOP
    _build_carcass(prefix, frame, s0, s1, z_top, kind == "sink", ply, col, parent)

    # Inset fronts sit inside the exposed 18 mm plywood edges of the carcass.
    fs0, fs1 = s0 + P, s1 - P
    fz0, fz1 = KITCHEN_PLINTH_HEIGHT + P * CM, z_top - P * CM
    gap_cm = KITCHEN_FRONT_GAP
    gap_m = KITCHEN_FRONT_GAP * CM
    t_face = D + KITCHEN_FRONT_PROUD

    def front(tag, a, b, za, zb, face_mat=olive):
        _box(f"{prefix}_{tag}", frame, a, b, t_face - P, t_face, za, zb, ply, col, parent, front_mat=face_mat)

    if kind in ("door", "sink"):
        front("Door", fs0, fs1, fz0, fz1)
    elif kind == "filler":
        front("Filler_Panel", fs0, fs1, fz0, fz1)
    elif kind == "double_door":
        mid = 0.5 * (fs0 + fs1)
        front("Door_A", fs0, mid - 0.5 * gap_cm, fz0, fz1)
        front("Door_B", mid + 0.5 * gap_cm, fs1, fz0, fz1)
    elif kind == "drawers":
        deep_h = (fz1 - fz0 - DRAWER_TOP_HEIGHT - 2.0 * gap_m) / 2.0
        z = fz0
        front("Drawer_Bottom", fs0, fs1, z, z + deep_h)
        z += deep_h + gap_m
        front("Drawer_Middle", fs0, fs1, z, z + deep_h)
        z += deep_h + gap_m
        front("Drawer_Top", fs0, fs1, z, fz1)
    elif kind == "hob_oven":
        drawer_top = fz0 + 9.0 * CM
        front("Drawer", fs0, fs1, fz0, drawer_top)
        front("Oven", fs0, fs1, drawer_top + gap_m, fz1, face_mat=mats["kitchen_black_glass"])
    elif kind == "tall_fridge":
        # Freezer door top lines up with the top of the base unit fronts
        split = KITCHEN_CARCASS_TOP - P * CM
        front("Freezer_Door", fs0, fs1, fz0, split)
        front("Fridge_Door", fs0, fs1, split + gap_m, fz1)


def _sink_cutout(s0: float, s1: float) -> Tuple[float, float, float, float]:
    """Returns the basin opening (s0, s1, t0, t1) centered in a sink unit."""
    basin_w = min(50.0, (s1 - s0) - 10.0)
    sc = 0.5 * (s0 + s1)
    return (sc - 0.5 * basin_w, sc + 0.5 * basin_w, SINK_BACK_STRIP, KITCHEN_WORKTOP_DEPTH - SINK_FRONT_STRIP)


def _build_worktop(prefix, frame, s_start, s_end, cutouts, mat, col, parent):
    """Builds a worktop segment from interval slices around sink cutouts (no booleans)."""
    z0, z1 = KITCHEN_CARCASS_TOP, KITCHEN_WORKTOP_TOP
    depth = KITCHEN_WORKTOP_DEPTH
    s = s_start
    piece = 0
    for c0, c1, ct0, ct1 in sorted(cutouts):
        if c0 - s > 0.05:
            piece += 1
            _box(f"{prefix}_Worktop_{piece}", frame, s, c0, 0.0, depth, z0, z1, mat, col, parent)
        piece += 1
        _box(f"{prefix}_Worktop_{piece}", frame, c0, c1, 0.0, ct0, z0, z1, mat, col, parent)
        piece += 1
        _box(f"{prefix}_Worktop_{piece}", frame, c0, c1, ct1, depth, z0, z1, mat, col, parent)
        s = c1
    if s_end - s > 0.05:
        piece += 1
        _box(f"{prefix}_Worktop_{piece}", frame, s, s_end, 0.0, depth, z0, z1, mat, col, parent)


def _build_sink(prefix, frame, cutout, mats, col, parent):
    """Builds a steel basin hanging in the worktop cutout, plus a simple tap."""
    steel = mats["kitchen_steel"]
    s0, s1, t0, t1 = cutout
    zt = KITCHEN_WORKTOP_TOP
    zb = zt - SINK_BASIN_DEPTH
    w = SINK_WALL
    _box(f"{prefix}_Basin_Floor", frame, s0, s1, t0, t1, zb - w * CM, zb, steel, col, parent)
    _box(f"{prefix}_Basin_Wall_Back", frame, s0, s1, t0, t0 + w, zb, zt, steel, col, parent)
    _box(f"{prefix}_Basin_Wall_Front", frame, s0, s1, t1 - w, t1, zb, zt, steel, col, parent)
    _box(f"{prefix}_Basin_Wall_A", frame, s0, s0 + w, t0 + w, t1 - w, zb, zt, steel, col, parent)
    _box(f"{prefix}_Basin_Wall_B", frame, s1 - w, s1, t0 + w, t1 - w, zb, zt, steel, col, parent)

    sc = 0.5 * (s0 + s1)
    tx, ty = frame.pt(sc, 0.5 * t0)
    sx, sy = frame.pt(sc, t0 + 14.0)
    create_round_cylinder_3d(f"{prefix}_Tap", (tx, ty, zt), (tx, ty, zt + 0.26), 1.6, steel, col, parent)
    create_round_cylinder_3d(f"{prefix}_Tap_Spout", (tx, ty, zt + 0.25), (sx, sy, zt + 0.25), 1.1, steel, col, parent)


def _build_hob(prefix, frame, s0, s1, mats, col, parent):
    """Builds a black glass hob resting on the worktop with four cooking zones."""
    glass = mats["kitchen_black_glass"]
    ring = mats["kitchen_hob_ring"]
    z0 = KITCHEN_WORKTOP_TOP
    z1 = z0 + 0.6 * CM
    hs0, hs1 = s0 + 0.5, s1 - 0.5
    ht0, ht1 = 4.0, 56.0
    _box(f"{prefix}_Hob", frame, hs0, hs1, ht0, ht1, z0, z1, glass, col, parent)

    sc, tc = 0.5 * (hs0 + hs1), 0.5 * (ht0 + ht1)
    zones = [(-14.0, -12.0, 9.5), (14.0, -12.0, 7.0), (-14.0, 12.0, 7.0), (14.0, 12.0, 9.5)]
    for i, (ds, dt, r) in enumerate(zones, start=1):
        x, y = frame.pt(sc + ds, tc + dt)
        create_round_cylinder_3d(f"{prefix}_Hob_Zone_{i}", (x, y, z1), (x, y, z1 + 0.0008), r, ring, col, parent, segments=40)
        create_round_cylinder_3d(f"{prefix}_Hob_Zone_{i}_Inner", (x, y, z1), (x, y, z1 + 0.0012), r - 0.7, glass, col, parent, segments=40)


def create_kitchen_run_3d(
    name_prefix: str,
    origin: Tuple[float, float],
    along: Tuple[float, float],
    out: Tuple[float, float],
    units: List[dict],
    mats: Dict[str, bpy.types.Material],
    col: bpy.types.Collection,
    parent: bpy.types.Object = None,
    worktop_start: float = 0.0,
    plinth_start: float = 0.0,
    end_panel: bool = False,
):
    """
    Builds a straight kitchen run.

    origin:        plan point (cm) on the wall face where the run starts
    along / out:   unit vectors along the wall and out of the wall into the room
    units:         [{"kind": ..., "width": cm}, ...] in run order
    worktop_start: trims the worktop start (cm), e.g. where it meets a corner worktop
    plinth_start:  plinth start (cm, may be negative to meet a corner plinth)
    end_panel:     closes the plinth gap at the free end with a plywood foot panel
    """
    frame = _RunFrame(origin, along, out)
    ply = mats["kitchen_plywood"]

    spans = []
    s = 0.0
    for idx, unit in enumerate(units, start=1):
        kind, width = unit["kind"], float(unit["width"])
        prefix = f"{name_prefix}_{idx:02d}_{kind}"
        _build_unit(prefix, frame, s, s + width, kind, mats, col, parent)
        spans.append((prefix, kind, s, s + width))
        s += width
    total = s

    # Worktop over each contiguous group of base units (tall units interrupt it)
    groups, current = [], []
    for span in spans:
        if span[1] == "tall_fridge":
            if current:
                groups.append(current)
            current = []
        else:
            current.append(span)
    if current:
        groups.append(current)

    for g_idx, group in enumerate(groups, start=1):
        g_start = max(group[0][2], worktop_start)
        g_end = group[-1][3]
        cutouts = [_sink_cutout(s0, s1) for _, kind, s0, s1 in group if kind == "sink"]
        _build_worktop(f"{name_prefix}_Top{g_idx}", frame, g_start, g_end, cutouts, mats["kitchen_worktop"], col, parent)

    for prefix, kind, s0, s1 in spans:
        if kind == "sink":
            _build_sink(prefix, frame, _sink_cutout(s0, s1), mats, col, parent)
        elif kind == "hob_oven":
            _build_hob(prefix, frame, s0, s1, mats, col, parent)

    # Recessed plinth, closed at a free end by a plywood foot panel flush with the end side
    plinth_end = total - P if end_panel else total
    _box(f"{name_prefix}_Plinth", frame, plinth_start, plinth_end, 0.0, D - KITCHEN_PLINTH_SETBACK,
         0.0, KITCHEN_PLINTH_HEIGHT, ply, col, parent)
    if end_panel:
        _box(f"{name_prefix}_End_Panel_Foot", frame, total - P, total, 0.0, D,
             0.0, KITCHEN_PLINTH_HEIGHT, ply, col, parent)
