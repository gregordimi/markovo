"""
==============================================================================
MARKOVO FURNITURE — KITCHEN JOINERY & BUILT-IN APPLIANCES
==============================================================================

Self-contained module defining the kitchen joinery, cabinetry, and appliances.
Designed for:
  1. Isolated Prototyping & Standalone Studio Rendering:
     /Applications/Blender.app/Contents/MacOS/Blender --python scripts/furniture/kitchen.py
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/kitchen.py -- --render
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/kitchen.py -- --render --view iso

  2. Automated Cutlist & Bill of Materials (BOM) Generation:
     python3 scripts/furniture/kitchen.py --cutlist
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/kitchen.py -- --cutlist

  3. Architectural Floor Plan Integration:
     from furniture.kitchen import build_kitchen, DEFAULT_KITCHEN_UNITS
==============================================================================
"""

import sys
import os
import math
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Ensure parent directory (scripts/) is in sys.path when run directly
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Graceful import for Blender environment
try:
    import bpy
    import bmesh
    from mathutils import Vector, Matrix
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    bpy = None
    bmesh = None
    Vector = None
    Matrix = None

# Units
CM = 0.01  # 1 cm = 0.01 m

# ------------------------------------------------------------------------------
# 1. KITCHEN JOINERY PARAMETERS & DIMENSIONS (cm & m)
# ------------------------------------------------------------------------------
PLINTH_HEIGHT = 0.10          # 10 cm recessed plinth
CARCASS_TOP = 0.86            # 86 cm carcass height
WORKTOP_TOP = 0.90            # 90 cm finished worktop height (4 cm thick)
TALL_TOP = 2.10               # 210 cm tall fridge-freezer housing
CARCASS_DEPTH = 60.0          # 60 cm carcass depth
WORKTOP_DEPTH = 63.5          # 63.5 cm worktop depth (3.5 cm overhang)
PLINTH_SETBACK = 6.0          # 6 cm plinth setback
PANEL_THICKNESS = 1.8         # 18 mm birch plywood carcass panels
FRONT_GAP = 0.3               # 3 mm shadow gap around inset fronts
FRONT_PROUD = 0.4             # 4 mm inset front sits proud of carcass edge

# ------------------------------------------------------------------------------
# 2. DEFAULT KITCHEN LAYOUT (Linear Run along the Long Wall)
# ------------------------------------------------------------------------------
DEFAULT_KITCHEN_UNITS = [
    {"kind": "tall_fridge", "width": 60.0, "label": "Fridge-Freezer 60"},
    {"kind": "drawers",     "width": 60.0, "label": "Food Prep / Cutlery 60"},
    {"kind": "sink",        "width": 60.0, "label": "Under-mount Sink 60"},
    {"kind": "door",        "width": 60.0, "label": "Dishwasher / Prep 60"},
    {"kind": "hob_oven",    "width": 60.0, "label": "Induction Hob & Oven 60"},
    {"kind": "drawers",     "width": 60.0, "label": "Pots & Pans Drawers 60"},
    {"kind": "double_door", "width": 80.0, "label": "Tableware / Pantry 80"},
]

# ------------------------------------------------------------------------------
# 3. PBR KITCHEN MATERIALS FACTORY
# ------------------------------------------------------------------------------
def get_or_create_material(name: str):
    """Gets an existing material or creates a clean node-based material."""
    if not HAS_BLENDER:
        return None
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    return mat


def create_kitchen_materials() -> Dict[str, Any]:
    """Creates all PBR materials required for the kitchen cabinetry and appliances."""
    if not HAS_BLENDER:
        return {}
    mats = {}

    # 1. Birch Plywood (Carcasses, Exposed Edges, Plinth)
    ply = get_or_create_material("Kitchen_Birch_Plywood")
    bsdf = ply.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.86, 0.76, 0.60, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.55
    mats["plywood"] = ply

    # 2. Olive Green Inset Fronts (Doors & Drawers)
    olive = get_or_create_material("Kitchen_Olive_Front")
    bsdf = olive.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.24, 0.28, 0.20, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.40
    mats["olive_front"] = olive

    # 3. Light Solid Wood Worktop (Warm Natural Oak/Beech)
    top = get_or_create_material("Kitchen_Wood_Worktop")
    bsdf = top.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.75, 0.58, 0.38, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.35
    mats["worktop"] = top

    # 4. Black Glass Induction Hob
    glass = get_or_create_material("Kitchen_Black_Glass")
    bsdf = glass.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.08
        bsdf.inputs["Metallic"].default_value = 0.10
    mats["black_glass"] = glass

    # 5. Hob Induction Cooking Zone Rings
    ring = get_or_create_material("Kitchen_Hob_Ring")
    bsdf = ring.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.55, 0.55, 0.55, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.40
    mats["hob_ring"] = ring

    # 6. Satin Stainless Steel (Sink Basin, Mixer Tap, Oven Trim, Handles)
    steel = get_or_create_material("Kitchen_Stainless_Steel")
    bsdf = steel.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.80, 0.82, 0.84, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.92
        bsdf.inputs["Roughness"].default_value = 0.22
    mats["steel"] = steel

    return mats


def resolve_kitchen_materials(mats: Dict[str, Any] = None) -> Dict[str, Any]:
    """Resolves material dict mapping from either cad_markovo materials or standalone."""
    if not HAS_BLENDER:
        return {}
    if mats is None:
        mats = {}

    res = {
        "plywood": mats.get("kitchen_plywood") or mats.get("plywood"),
        "olive_front": mats.get("kitchen_olive") or mats.get("olive_front"),
        "worktop": mats.get("kitchen_worktop") or mats.get("worktop"),
        "steel": mats.get("kitchen_steel") or mats.get("steel"),
        "black_glass": mats.get("kitchen_black_glass") or mats.get("black_glass"),
        "hob_ring": mats.get("kitchen_hob_ring") or mats.get("hob_ring"),
    }

    if any(v is None for v in res.values()):
        defaults = create_kitchen_materials()
        for k in res:
            if res[k] is None:
                res[k] = defaults[k]

    return res


# ------------------------------------------------------------------------------
# 4. GEOMETRY PRIMITIVES
# ------------------------------------------------------------------------------
class _RunFrame:
    """Transforms run-local (s along wall, t out into room, in cm) to 3D world (m)."""

    def __init__(self, origin: Tuple[float, float], along: Tuple[float, float], out: Tuple[float, float]):
        self.ox, self.oy = float(origin[0]), float(origin[1])
        self.ax, self.ay = float(along[0]), float(along[1])
        self.nx, self.ny = float(out[0]), float(out[1])

    def pt(self, s: float, t: float) -> Tuple[float, float]:
        return (self.ox + self.ax * s + self.nx * t, self.oy + self.ay * s + self.ny * t)

    def quad(self, s0: float, s1: float, t0: float, t1: float) -> List[Tuple[float, float]]:
        return [self.pt(s0, t0), self.pt(s1, t0), self.pt(s1, t1), self.pt(s0, t1)]


def _create_prism(
    name: str,
    corners_2d: List[Tuple[float, float]],
    z0: float,
    z1: float,
    mat: Any,
    col: Any,
    parent: Any = None,
):
    """Creates a 3D prism from 4 (x, y) coordinates in cm and Z bounds in meters."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    v_btm = [bm.verts.new((x * CM, y * CM, z0)) for x, y in corners_2d]
    v_top = [bm.verts.new((x * CM, y * CM, z1)) for x, y in corners_2d]

    bm.faces.new(v_btm[::-1])  # Downward normal
    bm.faces.new(v_top)        # Upward normal
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new([v_btm[i], v_btm[j], v_top[j], v_top[i]])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    if mat:
        obj.data.materials.append(mat)
    col.objects.link(obj)
    if parent:
        obj.parent = parent
    return obj


def _create_box(
    name: str,
    frame: _RunFrame,
    s0: float, s1: float,
    t0: float, t1: float,
    z0: float, z1: float,
    mat: Any,
    col: Any,
    parent: Any = None,
    front_mat: Any = None,
):
    """Creates a run-aligned box. If front_mat is provided, the front face uses it."""
    obj = _create_prism(name, frame.quad(s0, s1, t0, t1), z0, z1, mat, col, parent)
    if front_mat is not None:
        obj.data.materials.append(front_mat)
        for poly in obj.data.polygons:
            if poly.normal.x * frame.nx + poly.normal.y * frame.ny > 0.9:
                poly.material_index = 1
    return obj


def _create_cylinder(
    name: str,
    p_bottom: Tuple[float, float, float],
    p_top: Tuple[float, float, float],
    radius_cm: float,
    mat: Any,
    col: Any,
    parent: Any = None,
    segments: int = 24,
):
    """Creates a cylinder between two 3D points (in meters) with radius in cm."""
    v1 = Vector(p_bottom)
    v2 = Vector(p_top)
    diff = v2 - v1
    length = diff.length
    if length < 1e-4:
        return None

    mid = (v1 + v2) * 0.5
    direction = diff.normalized()
    up = Vector((0.0, 0.0, 1.0))
    rot = up.rotation_difference(direction)
    mat_transform = Matrix.Translation(mid) @ rot.to_matrix().to_4x4()

    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=segments,
        radius1=radius_cm * CM,
        radius2=radius_cm * CM,
        depth=length,
        matrix=mat_transform,
    )

    for f in bm.faces:
        f.smooth = True

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    if mat:
        obj.data.materials.append(mat)
    col.objects.link(obj)
    if parent:
        obj.parent = parent
    return obj


# ------------------------------------------------------------------------------
# 5. KITCHEN UNIT ASSEMBLIES
# ------------------------------------------------------------------------------
def _build_carcass(prefix, frame, s0, s1, z_top, open_top, ply, col, parent):
    """Builds the birch plywood cabinet carcass."""
    z_bot = PLINTH_HEIGHT
    if not open_top:
        _create_box(f"{prefix}_Carcass", frame, s0, s1, 0.0, CARCASS_DEPTH, z_bot, z_top, ply, col, parent)
        return
    pz = PANEL_THICKNESS * CM
    _create_box(f"{prefix}_Side_A", frame, s0, s0 + PANEL_THICKNESS, 0.0, CARCASS_DEPTH, z_bot, z_top, ply, col, parent)
    _create_box(f"{prefix}_Side_B", frame, s1 - PANEL_THICKNESS, s1, 0.0, CARCASS_DEPTH, z_bot, z_top, ply, col, parent)
    _create_box(f"{prefix}_Bottom", frame, s0 + PANEL_THICKNESS, s1 - PANEL_THICKNESS, 0.0, CARCASS_DEPTH, z_bot, z_bot + pz, ply, col, parent)


def _build_front(prefix, frame, s0, s1, z0, z1, ply, olive, col, parent):
    """Builds an olive green inset door or drawer front with exposed plywood edges."""
    ds = PANEL_THICKNESS + FRONT_GAP
    fs0, fs1 = s0 + ds, s1 - ds
    ft0 = CARCASS_DEPTH - PANEL_THICKNESS + FRONT_PROUD
    ft1 = CARCASS_DEPTH + FRONT_PROUD
    fz0 = z0 + (FRONT_GAP * CM)
    fz1 = z1 - (FRONT_GAP * CM)
    return _create_box(f"{prefix}_Front", frame, fs0, fs1, ft0, ft1, fz0, fz1, ply, col, parent, front_mat=olive)


def _build_handle(prefix, frame, sc, tc, zc, length_cm, is_vertical, steel, col, parent):
    """Builds a minimalist modern stainless steel bar handle."""
    rad = 0.5  # 1 cm diameter bar
    half_l = length_cm * 0.5
    px, py = frame.pt(sc, tc)

    if is_vertical:
        p1 = (px, py, zc - half_l * CM)
        p2 = (px, py, zc + half_l * CM)
    else:
        # Horizontal handle along s
        p1_x, p1_y = frame.pt(sc - half_l, tc)
        p2_x, p2_y = frame.pt(sc + half_l, tc)
        p1 = (p1_x, p1_y, zc)
        p2 = (p2_x, p2_y, zc)

    _create_cylinder(f"{prefix}_Bar", p1, p2, rad, steel, col, parent)

    # Standoff posts to the front face
    standoff_t = tc - 2.5
    sx1, sy1 = frame.pt(sc - (0 if is_vertical else half_l * 0.7), standoff_t)
    sx2, sy2 = frame.pt(sc + (0 if is_vertical else half_l * 0.7), standoff_t)
    _create_cylinder(f"{prefix}_Post_1", (sx1, sy1, zc - (half_l * 0.7 * CM if is_vertical else 0)),
                     (px if is_vertical else sx1, py if is_vertical else sy1, zc - (half_l * 0.7 * CM if is_vertical else 0)),
                     rad * 0.8, steel, col, parent)


def _build_sink_assembly(prefix, frame, s0, s1, mats, col, parent):
    """Builds under-mount stainless steel basin, drainer strainer, and swan-neck mixer tap."""
    steel = mats["steel"]
    sw = s1 - s0
    sc = s0 + sw * 0.5
    basin_s0 = sc - 22.0
    basin_s1 = sc + 22.0
    basin_t0 = 12.0
    basin_t1 = CARCASS_DEPTH - 10.0

    z_top = WORKTOP_TOP
    z_bot = z_top - 0.20  # 20 cm deep basin

    # Basin walls and bottom
    _create_box(f"{prefix}_Basin_Floor", frame, basin_s0, basin_s1, basin_t0, basin_t1, z_bot, z_bot + 0.01, steel, col, parent)
    _create_box(f"{prefix}_Basin_Wall_N", frame, basin_s0, basin_s1, basin_t1 - 1.0, basin_t1, z_bot, z_top, steel, col, parent)
    _create_box(f"{prefix}_Basin_Wall_S", frame, basin_s0, basin_s1, basin_t0, basin_t0 + 1.0, z_bot, z_top, steel, col, parent)
    _create_box(f"{prefix}_Basin_Wall_W", frame, basin_s0, basin_s0 + 1.0, basin_t0, basin_t1, z_bot, z_top, steel, col, parent)
    _create_box(f"{prefix}_Basin_Wall_E", frame, basin_s1 - 1.0, basin_s1, basin_t0, basin_t1, z_bot, z_top, steel, col, parent)

    # Swan-neck mixer tap
    tap_x, tap_y = frame.pt(sc, 6.0)
    _create_cylinder(f"{prefix}_Tap_Base", (tap_x, tap_y, z_top), (tap_x, tap_y, z_top + 0.26), 1.6, steel, col, parent)
    spout_end_x, spout_end_y = frame.pt(sc, 18.0)
    _create_cylinder(f"{prefix}_Tap_Spout", (tap_x, tap_y, z_top + 0.26), (spout_end_x, spout_end_y, z_top + 0.22), 1.2, steel, col, parent)


def _build_hob_assembly(prefix, frame, s0, s1, mats, col, parent):
    """Builds black glass induction cooktop, 4 induction rings, and built-in oven."""
    glass = mats["black_glass"]
    ring = mats["hob_ring"]
    steel = mats["steel"]

    # Glass cooktop plate
    z0 = WORKTOP_TOP
    z1 = z0 + 0.006  # 6 mm chamfered glass
    hs0, hs1 = s0 + 2.0, s1 - 2.0
    ht0, ht1 = 6.0, CARCASS_DEPTH - 4.0
    _create_box(f"{prefix}_Hob_Plate", frame, hs0, hs1, ht0, ht1, z0, z1, glass, col, parent)

    # 4 Induction cooking zones
    sc, tc = 0.5 * (hs0 + hs1), 0.5 * (ht0 + ht1)
    zones = [(-14.0, -11.0, 9.5), (14.0, -11.0, 7.5), (-14.0, 11.0, 7.5), (14.0, 11.0, 9.5)]
    for i, (ds, dt, r) in enumerate(zones, start=1):
        x, y = frame.pt(sc + ds, tc + dt)
        _create_cylinder(f"{prefix}_Zone_{i}", (x, y, z1), (x, y, z1 + 0.0006), r, ring, col, parent, segments=36)

    # Built-in Oven window & handle
    ft = CARCASS_DEPTH + FRONT_PROUD + 0.5
    oz0 = PLINTH_HEIGHT + 0.15
    oz1 = CARCASS_TOP - 0.05
    _create_box(f"{prefix}_Oven_Glass", frame, s0 + 4.0, s1 - 4.0, ft - 0.4, ft, oz0, oz1, glass, col, parent)
    _build_handle(f"{prefix}_Oven_Handle", frame, sc, ft + 2.5, oz1 - 0.05, 40.0, False, steel, col, parent)


def _build_worktop(prefix, frame, s0, s1, cutouts, mat, col, parent):
    """Builds continuous light solid wood worktop with sink cutout."""
    z0 = CARCASS_TOP
    z1 = WORKTOP_TOP
    w_depth = WORKTOP_DEPTH

    if not cutouts:
        _create_box(f"{prefix}_Slab", frame, s0, s1, 0.0, w_depth, z0, z1, mat, col, parent)
        return

    # Slices around cutout to leave true empty hole for sink basin
    cs0, cs1, ct0, ct1 = cutouts[0]
    if cs0 > s0:
        _create_box(f"{prefix}_Left", frame, s0, cs0, 0.0, w_depth, z0, z1, mat, col, parent)
    if cs1 < s1:
        _create_box(f"{prefix}_Right", frame, cs1, s1, 0.0, w_depth, z0, z1, mat, col, parent)
    if ct0 > 0.0:
        _create_box(f"{prefix}_Back", frame, cs0, cs1, 0.0, ct0, z0, z1, mat, col, parent)
    if ct1 < w_depth:
        _create_box(f"{prefix}_Front", frame, cs0, cs1, ct1, w_depth, z0, z1, mat, col, parent)


# ------------------------------------------------------------------------------
# 6. MASTER BUILDER FUNCTION (PLUG-IN INTERFACE)
# ------------------------------------------------------------------------------
def build_kitchen(
    origin: Tuple[float, float] = (0.0, 0.0),
    along: Tuple[float, float] = (0.0, 1.0),
    out: Tuple[float, float] = (1.0, 0.0),
    units: List[dict] = None,
    col: Any = None,
    parent: Any = None,
    mats: Dict[str, Any] = None,
    worktop_start: float = None,
    plinth_start: float = 0.0,
    end_panel: bool = True,
    name_prefix: str = "Kitchen_Run",
):
    """
    Builds the complete linear kitchen furniture run.
    Can be called standalone or imported into Floor 3 / FloorPlanBuilder.
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender environment (bpy) is required to build 3D mesh geometry.")

    if units is None:
        units = DEFAULT_KITCHEN_UNITS

    if col is None:
        col = bpy.context.scene.collection

    resolved_mats = resolve_kitchen_materials(mats)

    # Empty root object for the kitchen run
    root = bpy.data.objects.new(name_prefix, None)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.4
    col.objects.link(root)
    if parent:
        root.parent = parent

    frame = _RunFrame(origin, along, out)
    ply = resolved_mats["plywood"]
    olive = resolved_mats["olive_front"]
    steel = resolved_mats["steel"]

    spans = []
    s = 0.0
    for idx, u in enumerate(units, start=1):
        kind, width = u["kind"], float(u["width"])
        prefix = f"{name_prefix}_{idx:02d}_{kind}"
        sc = s + width * 0.5
        handle_tc = CARCASS_DEPTH + FRONT_PROUD + 2.5

        if kind == "tall_fridge":
            # Tall housing
            _build_carcass(prefix, frame, s, s + width, TALL_TOP, False, ply, col, root)
            # Bottom freezer door
            _build_front(f"{prefix}_Btm", frame, s, s + width, PLINTH_HEIGHT, 0.85, ply, olive, col, root)
            _build_handle(f"{prefix}_Btm_Handle", frame, s + width - 6.0, handle_tc, 0.80, 25.0, True, steel, col, root)
            # Top fridge door
            _build_front(f"{prefix}_Top", frame, s, s + width, 0.85, TALL_TOP, ply, olive, col, root)
            _build_handle(f"{prefix}_Top_Handle", frame, s + width - 6.0, handle_tc, 1.05, 45.0, True, steel, col, root)

        elif kind == "drawers":
            _build_carcass(prefix, frame, s, s + width, CARCASS_TOP, False, ply, col, root)
            # 3 Inset Drawers (1 shallow top, 2 deep bottom)
            z_top_div = CARCASS_TOP - 0.15
            z_mid_div = (PLINTH_HEIGHT + z_top_div) * 0.5
            _build_front(f"{prefix}_Draw_1", frame, s, s + width, z_top_div, CARCASS_TOP, ply, olive, col, root)
            _build_handle(f"{prefix}_H1", frame, sc, handle_tc, (z_top_div + CARCASS_TOP) * 0.5, 25.0, False, steel, col, root)
            _build_front(f"{prefix}_Draw_2", frame, s, s + width, z_mid_div, z_top_div, ply, olive, col, root)
            _build_handle(f"{prefix}_H2", frame, sc, handle_tc, (z_mid_div + z_top_div) * 0.5, 30.0, False, steel, col, root)
            _build_front(f"{prefix}_Draw_3", frame, s, s + width, PLINTH_HEIGHT, z_mid_div, ply, olive, col, root)
            _build_handle(f"{prefix}_H3", frame, sc, handle_tc, (PLINTH_HEIGHT + z_mid_div) * 0.5, 30.0, False, steel, col, root)

        elif kind == "door":
            _build_carcass(prefix, frame, s, s + width, CARCASS_TOP, False, ply, col, root)
            _build_front(prefix, frame, s, s + width, PLINTH_HEIGHT, CARCASS_TOP, ply, olive, col, root)
            _build_handle(prefix, frame, s + width - 5.0, handle_tc, (PLINTH_HEIGHT + CARCASS_TOP) * 0.5, 25.0, True, steel, col, root)

        elif kind == "double_door":
            _build_carcass(prefix, frame, s, s + width, CARCASS_TOP, False, ply, col, root)
            half_w = width * 0.5
            _build_front(f"{prefix}_L", frame, s, s + half_w, PLINTH_HEIGHT, CARCASS_TOP, ply, olive, col, root)
            _build_handle(f"{prefix}_L", frame, s + half_w - 4.0, handle_tc, (PLINTH_HEIGHT + CARCASS_TOP) * 0.5, 25.0, True, steel, col, root)
            _build_front(f"{prefix}_R", frame, s + half_w, s + width, PLINTH_HEIGHT, CARCASS_TOP, ply, olive, col, root)
            _build_handle(f"{prefix}_R", frame, s + half_w + 4.0, handle_tc, (PLINTH_HEIGHT + CARCASS_TOP) * 0.5, 25.0, True, steel, col, root)

        elif kind == "sink":
            _build_carcass(prefix, frame, s, s + width, CARCASS_TOP, True, ply, col, root)
            _build_front(prefix, frame, s, s + width, PLINTH_HEIGHT, CARCASS_TOP, ply, olive, col, root)
            _build_handle(prefix, frame, s + width - 5.0, handle_tc, (PLINTH_HEIGHT + CARCASS_TOP) * 0.5, 25.0, True, steel, col, root)
            _build_sink_assembly(prefix, frame, s, s + width, resolved_mats, col, root)

        elif kind == "hob_oven":
            _build_carcass(prefix, frame, s, s + width, CARCASS_TOP, False, ply, col, root)
            _build_front(f"{prefix}_BtmDraw", frame, s, s + width, PLINTH_HEIGHT, PLINTH_HEIGHT + 0.12, ply, olive, col, root)
            _build_hob_assembly(prefix, frame, s, s + width, resolved_mats, col, root)

        spans.append((prefix, kind, s, s + width))
        s += width

    total_len = s

    # Continuous Solid Wood Worktop (groups base units; tall units interrupt it)
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
        g_start = max(group[0][2], worktop_start) if worktop_start is not None else group[0][2]
        g_end = group[-1][3]
        sink_cutouts = []
        for _, k, s0, s1 in group:
            if k == "sink":
                sink_cutouts.append((s0 + 7.0, s1 - 7.0, 11.0, CARCASS_DEPTH - 9.0))
        _build_worktop(f"{name_prefix}_Worktop_{g_idx}", frame, g_start, g_end, sink_cutouts, resolved_mats["worktop"], col, root)

    # Recessed Plinth
    _create_box(f"{name_prefix}_Plinth", frame, plinth_start, total_len - (PANEL_THICKNESS if end_panel else 0.0),
                0.0, CARCASS_DEPTH - PLINTH_SETBACK, 0.0, PLINTH_HEIGHT, ply, col, root)

    # End Panel Foot
    if end_panel:
        _create_box(f"{name_prefix}_End_Panel_Foot", frame, total_len - PANEL_THICKNESS, total_len,
                    0.0, CARCASS_DEPTH, 0.0, PLINTH_HEIGHT, ply, col, root)

    return root


# ------------------------------------------------------------------------------
# 7. STANDALONE STUDIO RIG & MULTI-VIEW CAMERAS
# ------------------------------------------------------------------------------
def setup_kitchen_studio(kitchen_root: Any, view: str = "front"):
    """
    Sets up an isolated, high-end architectural studio lighting and camera rig.
    Supports multiple framing views:
      - 'front': Wide front elevation showing the complete 4.4m run from distance
      - 'iso'  : Wide 3/4 axonometric perspective view
      - 'close': Intimate 3/4 view focused on prep and hob zone
    """
    if not HAS_BLENDER:
        return

    col = bpy.data.collections.new("Kitchen_Studio")
    bpy.context.scene.collection.children.link(col)

    # 1. Key Studio Softbox (Wide enough to softly illuminate entire 4.4m run)
    key_light = bpy.data.lights.new("Studio_Key", "AREA")
    key_light.energy = 260.0
    key_light.size = 5.0
    key_light.size_y = 2.2
    key_obj = bpy.data.objects.new("Studio_Key", key_light)
    key_obj.location = (3.2, 2.2, 3.2)
    key_obj.rotation_euler = (math.radians(40.0), math.radians(0.0), math.radians(65.0))
    col.objects.link(key_obj)

    # 2. Fill Light
    fill_light = bpy.data.lights.new("Studio_Fill", "AREA")
    fill_light.energy = 120.0
    fill_light.size = 4.5
    fill_obj = bpy.data.objects.new("Studio_Fill", fill_light)
    fill_obj.location = (3.0, -1.8, 2.4)
    fill_obj.rotation_euler = (math.radians(30.0), math.radians(-20.0), math.radians(110.0))
    col.objects.link(fill_obj)

    # 3. Framing Camera presets
    cam_data = bpy.data.cameras.new("Kitchen_Studio_Camera")
    cam_data.lens = 28.0
    cam_data.sensor_width = 36.0
    cam_obj = bpy.data.objects.new("Kitchen_Studio_Camera", cam_data)

    if view == "iso":
        # Wide 3/4 perspective showing side panel, worktop surface, and all fronts
        cam_obj.location = (4.5, -0.8, 2.2)
        target = Vector((0.3, 2.2, 0.95))
    elif view == "close":
        # Detail view on hob & prep
        cam_obj.location = (2.6, 2.2, 1.45)
        target = Vector((0.35, 2.2, 0.95))
    else:
        # Default: Full-length front elevation (camera placed at 4.8m so full 4.4m fits comfortably)
        cam_obj.location = (4.8, 2.2, 1.45)
        target = Vector((0.3, 2.2, 1.05))

    direction = target - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    col.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    # Studio Floor Plane (Large 14m seamless plane)
    floor_mesh = bpy.data.meshes.new("Studio_Floor")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=14.0)
    bm.to_mesh(floor_mesh)
    bm.free()
    floor_obj = bpy.data.objects.new("Studio_Floor", floor_mesh)
    floor_obj.location = (0.5, 2.2, 0.0)

    floor_mat = get_or_create_material("Studio_Floor_Mat")
    bsdf = floor_mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.92, 0.93, 0.95, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.50
    floor_obj.data.materials.append(floor_mat)
    col.objects.link(floor_obj)


# ------------------------------------------------------------------------------
# 8. CUTLIST & BILL OF MATERIALS (BOM) GENERATOR
# ------------------------------------------------------------------------------
def generate_kitchen_cutlist(units: List[dict] = None) -> Dict[str, Any]:
    """
    Computes exact, shop-ready cutlist dimensions (in mm) for all cabinetry panels,
    fronts, drawer boxes, solid wood worktops, hardware, and appliances.
    """
    if units is None:
        units = DEFAULT_KITCHEN_UNITS

    # Standard panel thickness & gaps in mm
    T = int(PANEL_THICKNESS * 10)                        # 18 mm
    GAP = int(FRONT_GAP * 10)                            # 3 mm
    PLINTH_H = int(PLINTH_HEIGHT * 1000)                # 100 mm
    H_BASE = int((CARCASS_TOP - PLINTH_HEIGHT) * 1000)    # 760 mm
    H_TALL = int((TALL_TOP - PLINTH_HEIGHT) * 1000)       # 2000 mm
    D_CARCASS = int(CARCASS_DEPTH * 10)                  # 600 mm
    D_CAB = D_CARCASS - 20                               # 580 mm (standard 20mm service void)
    WORKTOP_T = int((WORKTOP_TOP - CARCASS_TOP) * 1000)  # 40 mm
    WORKTOP_D = int(WORKTOP_DEPTH * 10)                  # 635 mm

    panels = []
    hardware = []
    appliances = []

    def add_panel(name, cabinet, length, width, thick, qty, material, banding="", notes=""):
        panels.append({
            "name": name,
            "cabinet": cabinet,
            "length_mm": int(length),
            "width_mm": int(width),
            "thickness_mm": int(thick),
            "qty": int(qty),
            "material": material,
            "banding": banding,
            "notes": notes,
            "area_m2": (float(length) * float(width) * int(qty)) / 1e6,
        })

    def add_hardware(item, qty, unit_name, category, notes=""):
        hardware.append({
            "item": item,
            "qty": qty,
            "unit": unit_name,
            "category": category,
            "notes": notes,
        })

    total_len_mm = 0
    worktop_start_mm = 0

    for idx, u in enumerate(units, start=1):
        kind = u["kind"]
        w_mm = int(float(u["width"]) * 10)  # cm to mm
        u_label = f"Unit {idx:02d} ({u['label']})"
        inner_w = w_mm - 2 * T  # Carcass inner width between sides
        front_w = inner_w - 2 * GAP  # Inset front width

        if kind == "tall_fridge":
            worktop_start_mm = total_len_mm + w_mm
            # Carcass
            add_panel("Tall_Side_Left", u_label, H_TALL, D_CAB, T, 1, "Birch Plywood 18mm", "Front (1L)", "Tall carcass side")
            add_panel("Tall_Side_Right", u_label, H_TALL, D_CAB, T, 1, "Birch Plywood 18mm", "Front (1L)", "Tall carcass side")
            add_panel("Tall_Top", u_label, inner_w, D_CAB, T, 1, "Birch Plywood 18mm", "Front (1L)", "Top roof panel")
            add_panel("Tall_Bottom", u_label, inner_w, D_CAB, T, 1, "Birch Plywood 18mm", "Front (1L)", "Bottom base panel")
            add_panel("Tall_Divider_Shelf", u_label, inner_w, D_CAB - 20, T, 1, "Birch Plywood 18mm", "Front (1L)", "Fridge/freezer divider")
            add_panel("Tall_Back_Stiffener", u_label, inner_w, 120, T, 2, "Birch Plywood 18mm", "None", "Rear ventilation rails")

            # Fronts (Inset)
            h_btm_front = int((0.85 - PLINTH_HEIGHT) * 1000) - 2 * GAP   # 744 mm
            h_top_front = int((TALL_TOP - 0.85) * 1000) - 2 * GAP        # 1244 mm
            add_panel("Front_Freezer_Door", u_label, h_btm_front, front_w, T, 1, "Olive Faced 18mm", "All 4 Edges", "Freezer inset door")
            add_panel("Front_Fridge_Door", u_label, h_top_front, front_w, T, 1, "Olive Faced 18mm", "All 4 Edges", "Fridge inset door")

            # Hardware & Appliances
            add_hardware("Integrated Fridge Slider Kits / Heavy Inset Hinges", 4, "pcs", "Hinges", "Heavy-duty for integrated fridge doors")
            add_hardware("Stainless Steel Bar Handle 400mm", 1, "pcs", "Handles", "Upper fridge door handle")
            add_hardware("Stainless Steel Bar Handle 250mm", 1, "pcs", "Handles", "Lower freezer door handle")
            add_hardware("Adjustable Cabinet Feet 100mm", 4, "pcs", "Legs", "Heavy duty 250kg load rating")
            appliances.append({"item": "Built-in Integrated 60cm Fridge-Freezer", "brand_spec": "Standard 178cm niche", "qty": 1})

        elif kind == "drawers":
            # Carcass
            add_panel("Base_Side_Left", u_label, H_BASE, D_CAB, T, 1, "Birch Plywood 18mm", "Front (1L)", "Base carcass side")
            add_panel("Base_Side_Right", u_label, H_BASE, D_CAB, T, 1, "Birch Plywood 18mm", "Front (1L)", "Base carcass side")
            add_panel("Base_Bottom", u_label, inner_w, D_CAB, T, 1, "Birch Plywood 18mm", "Front (1L)", "Bottom panel")
            add_panel("Base_Top_Stretcher", u_label, inner_w, 80, T, 2, "Birch Plywood 18mm", "None", "Top tie stretchers")
            add_panel("Base_Back_Panel", u_label, H_BASE - 20, inner_w, 6, 1, "Birch Plywood 6mm", "None", "Rebated back panel")

            # Fronts: 1 Shallow cutlery drawer, 2 deep drawers
            h_top_drawer = 150 - 2 * GAP     # 144 mm
            h_deep_drawer = int((H_BASE - 150) / 2) - 2 * GAP  # 299 mm
            add_panel("Front_Shallow_Drawer", u_label, h_top_drawer, front_w, T, 1, "Olive Faced 18mm", "All 4 Edges", "Top cutlery drawer")
            add_panel("Front_Deep_Drawer", u_label, h_deep_drawer, front_w, T, 2, "Olive Faced 18mm", "All 4 Edges", "Pots & pans / prep drawers")

            # Drawer Boxes (15mm Birch Plywood sides/ends, 6mm bottom)
            add_panel("Box_Shallow_Side", u_label, 500, 90, 15, 2, "Birch Plywood 15mm", "Top (1L)", "Drawer box sides")
            add_panel("Box_Shallow_End", u_label, inner_w - 70, 90, 15, 2, "Birch Plywood 15mm", "Top (1L)", "Drawer box front/back")
            add_panel("Box_Shallow_Bottom", u_label, 500, inner_w - 56, 6, 1, "Birch Plywood 6mm", "None", "Grooved bottom panel")

            add_panel("Box_Deep_Side", u_label, 500, 200, 15, 4, "Birch Plywood 15mm", "Top (1L)", "Deep drawer sides")
            add_panel("Box_Deep_End", u_label, inner_w - 70, 200, 15, 4, "Birch Plywood 15mm", "Top (1L)", "Deep drawer front/back")
            add_panel("Box_Deep_Bottom", u_label, 500, inner_w - 56, 6, 2, "Birch Plywood 6mm", "None", "Grooved bottom panel")

            # Hardware
            add_hardware("Undermount Soft-Close Slides 500mm", 3, "pairs", "Slides", "e.g. Blum Movento or Grass Dynapro")
            add_hardware("Stainless Steel Bar Handle 250mm", 1, "pcs", "Handles", "Top cutlery drawer handle")
            add_hardware("Stainless Steel Bar Handle 300mm", 2, "pcs", "Handles", "Deep drawer handles")
            add_hardware("Adjustable Cabinet Feet 100mm", 4, "pcs", "Legs", "Heavy duty 250kg load rating")

        elif kind == "sink":
            # Carcass (open top with vertical stretchers)
            add_panel("Sink_Side_Left", u_label, H_BASE, D_CAB, T, 1, "Birch Plywood 18mm", "Front (1L)", "Base carcass side")
            add_panel("Sink_Side_Right", u_label, H_BASE, D_CAB, T, 1, "Birch Plywood 18mm", "Front (1L)", "Base carcass side")
            add_panel("Sink_Bottom", u_label, inner_w, D_CAB, T, 1, "Birch Plywood 18mm", "Front (1L)", "Bottom panel")
            add_panel("Sink_Vertical_Stretcher", u_label, inner_w, 80, T, 2, "Birch Plywood 18mm", "Top (1L)", "Vertical rails for sink clearance")
            add_panel("Sink_Back_Panel_Lower", u_label, 200, inner_w, 6, 1, "Birch Plywood 6mm", "None", "Partial back panel for plumbing trap")

            # Front (Single inset door)
            add_panel("Front_Sink_Door", u_label, H_BASE - 2 * GAP, front_w, T, 1, "Olive Faced 18mm", "All 4 Edges", "Inset sink cabinet door")

            # Hardware & Sanitary
            add_hardware("Concealed Inset Hinges 110° Soft-Close", 1, "pair", "Hinges", "e.g. Blum Clip-Top Blumotion")
            add_hardware("Stainless Steel Bar Handle 250mm", 1, "pcs", "Handles", "Vertical door handle")
            add_hardware("Adjustable Cabinet Feet 100mm", 4, "pcs", "Legs", "Heavy duty 250kg load rating")
            appliances.append({"item": "Stainless Steel Under-mount Basin (440 x 380 x 200mm)", "brand_spec": "Brushed satin finish", "qty": 1})
            appliances.append({"item": "Swan-neck Monobloc Kitchen Mixer Tap", "brand_spec": "Satin stainless steel", "qty": 1})
            appliances.append({"item": "Pop-up Waste Strainer & P-Trap Kit", "brand_spec": "Standard 1.5 inch", "qty": 1})

        elif kind == "door":
            # Carcass (Dishwasher bay or food prep shelving cabinet)
            add_panel("Base_Side_Left", u_label, H_BASE, D_CAB, T, 1, "Birch Plywood 18mm", "Front (1L)", "Base carcass side")
            add_panel("Base_Side_Right", u_label, H_BASE, D_CAB, T, 1, "Birch Plywood 18mm", "Front (1L)", "Base carcass side")
            add_panel("Base_Bottom", u_label, inner_w, D_CAB, T, 1, "Birch Plywood 18mm", "Front (1L)", "Bottom panel")
            add_panel("Base_Adjustable_Shelf", u_label, inner_w - 4, D_CAB - 30, T, 1, "Birch Plywood 18mm", "Front (1L)", "Adjustable shelf")
            add_panel("Base_Top_Stretcher", u_label, inner_w, 80, T, 2, "Birch Plywood 18mm", "None", "Top tie stretchers")
            add_panel("Base_Back_Panel", u_label, H_BASE - 20, inner_w, 6, 1, "Birch Plywood 6mm", "None", "Rebated back panel")

            # Front
            add_panel("Front_Cabinet_Door", u_label, H_BASE - 2 * GAP, front_w, T, 1, "Olive Faced 18mm", "All 4 Edges", "Inset prep / DW door")

            # Hardware
            add_hardware("Concealed Inset Hinges 110° Soft-Close", 1, "pair", "Hinges", "e.g. Blum Clip-Top Blumotion")
            add_hardware("Stainless Steel Bar Handle 250mm", 1, "pcs", "Handles", "Vertical door handle")
            add_hardware("Adjustable Cabinet Feet 100mm", 4, "pcs", "Legs", "Heavy duty 250kg load rating")

        elif kind == "hob_oven":
            # Carcass
            add_panel("Oven_Side_Left", u_label, H_BASE, D_CAB, T, 1, "Birch Plywood 18mm", "Front (1L)", "Base carcass side")
            add_panel("Oven_Side_Right", u_label, H_BASE, D_CAB, T, 1, "Birch Plywood 18mm", "Front (1L)", "Base carcass side")
            add_panel("Oven_Bottom", u_label, inner_w, D_CAB, T, 1, "Birch Plywood 18mm", "Front (1L)", "Bottom panel")
            add_panel("Oven_Support_Shelf", u_label, inner_w, D_CAB, T, 1, "Birch Plywood 18mm", "Front (1L)", "Reinforced shelf supporting oven")
            add_panel("Oven_Top_Stretcher", u_label, inner_w, 80, T, 2, "Birch Plywood 18mm", "None", "Top stretchers")

            # Front (Lower low drawer for baking trays)
            h_oven_draw = 120 - 2 * GAP
            add_panel("Front_Oven_Lower_Drawer", u_label, h_oven_draw, front_w, T, 1, "Olive Faced 18mm", "All 4 Edges", "Baking tray drawer front")

            # Low Drawer Box
            add_panel("Box_Tray_Side", u_label, 500, 70, 15, 2, "Birch Plywood 15mm", "Top (1L)", "Low drawer sides")
            add_panel("Box_Tray_End", u_label, inner_w - 70, 70, 15, 2, "Birch Plywood 15mm", "Top (1L)", "Low drawer front/back")
            add_panel("Box_Tray_Bottom", u_label, 500, inner_w - 56, 6, 1, "Birch Plywood 6mm", "None", "Grooved bottom panel")

            # Hardware & Appliances
            add_hardware("Undermount Soft-Close Slides 500mm (Low Profile)", 1, "pair", "Slides", "Drawer under oven")
            add_hardware("Stainless Steel Bar Handle 400mm", 1, "pcs", "Handles", "Oven handle / lower drawer")
            add_hardware("Adjustable Cabinet Feet 100mm", 4, "pcs", "Legs", "Heavy duty 250kg load rating")
            appliances.append({"item": "60cm 4-Zone Induction Cooktop (Black Glass)", "brand_spec": "Cutout: 560 x 490mm", "qty": 1})
            appliances.append({"item": "60cm Built-in Multifunction Electric Oven", "brand_spec": "Niche: 595 x 595 x 550mm", "qty": 1})

        elif kind == "double_door":
            # Carcass (80cm Pantry / Tableware)
            add_panel("Pantry_Side_Left", u_label, H_BASE, D_CAB, T, 1, "Birch Plywood 18mm", "Front (1L)", "Base carcass side")
            add_panel("Pantry_Side_Right", u_label, H_BASE, D_CAB, T, 1, "Birch Plywood 18mm", "Front (1L)", "Base carcass side")
            add_panel("Pantry_Bottom", u_label, inner_w, D_CAB, T, 1, "Birch Plywood 18mm", "Front (1L)", "Bottom panel")
            add_panel("Pantry_Adjustable_Shelf", u_label, inner_w - 4, D_CAB - 30, T, 1, "Birch Plywood 18mm", "Front (1L)", "Wide pantry shelf")
            add_panel("Pantry_Top_Stretcher", u_label, inner_w, 80, T, 2, "Birch Plywood 18mm", "None", "Top tie stretchers")
            add_panel("Pantry_Back_Panel", u_label, H_BASE - 20, inner_w, 6, 1, "Birch Plywood 6mm", "None", "Rebated back panel")

            # Fronts (Pair of doors)
            single_door_w = int((inner_w - 3 * GAP) / 2)  # 376 mm
            add_panel("Front_Pantry_Door_Pair", u_label, H_BASE - 2 * GAP, single_door_w, T, 2, "Olive Faced 18mm", "All 4 Edges", "Pantry inset door pair")

            # Hardware
            add_hardware("Concealed Inset Hinges 110° Soft-Close", 2, "pairs", "Hinges", "e.g. Blum Clip-Top Blumotion")
            add_hardware("Stainless Steel Bar Handle 250mm", 2, "pcs", "Handles", "Vertical door handles")
            add_hardware("Adjustable Cabinet Feet 100mm", 4, "pcs", "Legs", "Heavy duty 250kg load rating")

        total_len_mm += w_mm

    # --------------------------------------------------------------------------
    # Plinth, Finished End Decor Panel & Solid Wood Worktop
    # --------------------------------------------------------------------------
    # Recessed Plinth (split into 2 manageable ~2.2m lengths)
    add_panel("Plinth_Kickboard_A", "Plinth & Trim", 2200, PLINTH_H, T, 1, "Birch Plywood 18mm", "Top (1L)", "Recessed toe-kick board")
    add_panel("Plinth_Kickboard_B", "Plinth & Trim", total_len_mm - 2200, PLINTH_H, T, 1, "Birch Plywood 18mm", "Top (1L)", "Recessed toe-kick board")
    add_panel("Plinth_End_Return_Foot", "Plinth & Trim", D_CAB - 40, PLINTH_H, T, 1, "Birch Plywood 18mm", "Top/Front", "Free end foot panel")

    # Exposed Finished End Decor Panel (Closes the free North end of the base run)
    add_panel("Finished_End_Decor_Panel", "Plinth & Trim", H_BASE + PLINTH_H, D_CARCASS, T, 1, "Birch Plywood 18mm", "Front/Top (2E)", "Exposed North end panel")

    # Solid Wood Worktop
    worktop_len_mm = total_len_mm - worktop_start_mm
    add_panel("Solid_Wood_Worktop", "Countertop", worktop_len_mm, WORKTOP_D, WORKTOP_T, 1, "Solid Wood Oak/Beech 40mm", "All 4 Edges Bullnose/Chamfer",
              f"Continuous solid counter with Sink cutout (440x380mm) and Hob cutout (560x490mm)")

    # Plinth Clips
    add_hardware("Plinth Fastening Clips (to legs)", 12, "pcs", "Plinth", "Locks kickboard to 100mm legs")

    # --------------------------------------------------------------------------
    # Raw Sheet Material Stock Optimization Calculations
    # --------------------------------------------------------------------------
    SHEET_W = 2440
    SHEET_H = 1220
    SHEET_AREA = (SHEET_W * SHEET_H) / 1e6  # 2.977 m2

    mat_areas = {}
    for p in panels:
        m = p["material"]
        mat_areas[m] = mat_areas.get(m, 0.0) + p["area_m2"]

    sheets_summary = {}
    for m, area in mat_areas.items():
        if "Solid Wood" in m:
            sheets_summary[m] = {
                "total_area_m2": round(area, 2),
                "units_required": "1 slab (3800 x 635 x 40mm)",
                "waste_factor": "10%",
            }
        else:
            # 15% saw kerf & scrap allowance
            raw_sheets = (area * 1.15) / SHEET_AREA
            sheets_summary[m] = {
                "total_area_m2": round(area, 2),
                "sheets_2440x1220": math.ceil(raw_sheets),
                "exact_sheets_calc": round(raw_sheets, 2),
                "waste_factor": "15% kerf & offcut",
            }

    return {
        "total_run_length_mm": total_len_mm,
        "total_run_length_m": total_len_mm / 1000.0,
        "panels": panels,
        "hardware": hardware,
        "appliances": appliances,
        "material_summary": sheets_summary,
    }


def export_cutlist_csv(filepath: str, cutlist: Dict[str, Any] = None):
    """
    Exports the panels cutlist to a standard CSV directly compatible with
    CutList Optimizer (cutlistoptimizer.com), Cutlist Plus fx, and Excel.
    """
    if cutlist is None:
        cutlist = generate_kitchen_cutlist()

    out_path = Path(filepath).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Part Name",
            "Cabinet",
            "Length (mm)",
            "Width (mm)",
            "Thickness (mm)",
            "Qty",
            "Material",
            "Edge Banding",
            "Notes"
        ])
        for p in cutlist["panels"]:
            writer.writerow([
                p["name"],
                p["cabinet"],
                p["length_mm"],
                p["width_mm"],
                p["thickness_mm"],
                p["qty"],
                p["material"],
                p["banding"],
                p["notes"]
            ])

    return out_path


def export_cutlist_markdown(filepath: str, cutlist: Dict[str, Any] = None):
    """
    Exports a comprehensive, formatted Bill of Materials (BOM) and Cutlist report in Markdown.
    """
    if cutlist is None:
        cutlist = generate_kitchen_cutlist()

    out_path = Path(filepath).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Markovo Kitchen — Shop Cutlist & Bill of Materials (BOM)")
    lines.append(f"\n- **Total Kitchen Run Length**: {cutlist['total_run_length_mm']} mm ({cutlist['total_run_length_m']} m)")
    lines.append(f"- **Finished Worktop Height**: 900 mm | **Base Carcass Depth**: 600 mm")
    lines.append(f"- **Style**: Exposed Birch Plywood Carcasses + Inset Olive Green Fronts + 40mm Solid Wood Countertop\n")

    lines.append("## 1. Raw Sheet Material Requirements (2440 x 1220 mm Boards)")
    lines.append("| Material | Net Area (m²) | Waste Factor | Estimated Stock Required |")
    lines.append("| :--- | :---: | :---: | :--- |")
    for mat, info in cutlist["material_summary"].items():
        if "sheets_2440x1220" in info:
            lines.append(f"| **{mat}** | {info['total_area_m2']} m² | {info['waste_factor']} | **{info['sheets_2440x1220']} full sheets** ({info['exact_sheets_calc']} net) |")
        else:
            lines.append(f"| **{mat}** | {info['total_area_m2']} m² | {info['waste_factor']} | **{info['units_required']}** |")

    lines.append("\n---\n")
    lines.append("## 2. Complete Panel Cutlist (Sorted by Cabinet)")
    lines.append("| Part Name | Cabinet / Unit | Length (mm) | Width (mm) | Thick (mm) | Qty | Material | Edge Banding | Notes |")
    lines.append("| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- | :--- |")
    for p in cutlist["panels"]:
        lines.append(f"| `{p['name']}` | {p['cabinet']} | {p['length_mm']} | {p['width_mm']} | {p['thickness_mm']} | {p['qty']} | {p['material']} | {p['banding']} | {p['notes']} |")

    lines.append("\n---\n")
    lines.append("## 3. Hardware & Fittings Shopping List")
    lines.append("| Item Description | Quantity | Category | Notes / Suggested Brand |")
    lines.append("| :--- | :---: | :--- | :--- |")
    for h in cutlist["hardware"]:
        lines.append(f"| {h['item']} | **{h['qty']} {h['unit']}** | {h['category']} | {h['notes']} |")

    lines.append("\n---\n")
    lines.append("## 4. Built-in Appliances & Sanitary Checklist")
    lines.append("| Appliance / Fixture | Specification / Niche Dimensions | Qty | Status |")
    lines.append("| :--- | :--- | :---: | :---: |")
    for a in cutlist["appliances"]:
        lines.append(f"| **{a['item']}** | {a['brand_spec']} | {a['qty']} | Pending Procurement |")

    lines.append("\n---\n")
    lines.append("> **CutList Optimizer Import Note**:\n> The companion CSV file [`renders/kitchen_cutlist.csv`](file:///Users/gdimitrov/projects/markovo/renders/kitchen_cutlist.csv) can be directly imported into [CutList Optimizer](https://www.cutlistoptimizer.com/) to calculate the exact saw layout on 2440x1220mm sheets.\n")

    content = "\n".join(lines)
    with open(out_path, mode="w", encoding="utf-8") as f:
        f.write(content)

    return out_path


def print_cutlist_summary(cutlist: Dict[str, Any]):
    """Prints a clean, concise ASCII summary of the cutlist to the terminal."""
    print("\n" + "=" * 78)
    print(f"  MARKOVO KITCHEN — BILL OF MATERIALS & CUTLIST SUMMARY ({cutlist['total_run_length_mm']} mm)")
    print("=" * 78)
    print("\n[Raw Material Stock Requirements (2440 x 1220 mm Sheets)]")
    print(f"  {'Material':<32} {'Net Area':<12} {'Stock Required'}")
    print("  " + "-" * 72)
    for mat, info in cutlist["material_summary"].items():
        if "sheets_2440x1220" in info:
            print(f"  {mat:<32} {info['total_area_m2']} m2        {info['sheets_2440x1220']} sheets ({info['exact_sheets_calc']} net)")
        else:
            print(f"  {mat:<32} {info['total_area_m2']} m2        {info['units_required']}")

    print("\n[Total Panels Count]:", len(cutlist["panels"]), "unique parts |", sum(p["qty"] for p in cutlist["panels"]), "total panels")
    print("[Total Hardware Items]:", len(cutlist["hardware"]), "specifications")
    print("[Appliances & Sanitary]:", len(cutlist["appliances"]), "items")
    print("=" * 78 + "\n")


def export_kitchen_dae(filepath: str):
    """
    Exports all kitchen objects to standard COLLADA 1.4.1 (.dae),
    the native 3D file format that SketchUp imports out of the box.
    """
    import xml.etree.ElementTree as ET
    out_path = Path(filepath).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    root = ET.Element("COLLADA", xmlns="http://www.collada.org/2005/11/COLLADASchema", version="1.4.1")
    asset = ET.SubElement(root, "asset")
    ET.SubElement(asset, "unit", name="meter", meter="1")
    up = ET.SubElement(asset, "up_axis")
    up.text = "Z_UP"

    lib_geoms = ET.SubElement(root, "library_geometries")
    lib_scenes = ET.SubElement(root, "library_visual_scenes")
    vscene = ET.SubElement(lib_scenes, "visual_scene", id="Scene", name="Scene")

    mesh_objects = [o for o in bpy.context.scene.objects if o.type == "MESH" and o.name.startswith("Kitchen_Run")]

    for obj in mesh_objects:
        mesh = obj.to_mesh()
        clean_name = obj.name.replace(" ", "_").replace(".", "_")
        geom_id = f"geom-{clean_name}"
        geom = ET.SubElement(lib_geoms, "geometry", id=geom_id, name=obj.name)
        mesh_elem = ET.SubElement(geom, "mesh")

        # Vertices
        pos_id = f"{geom_id}-positions"
        source = ET.SubElement(mesh_elem, "source", id=pos_id)
        verts = [v.co for v in mesh.vertices]
        pos_array_id = f"{pos_id}-array"
        pos_array = ET.SubElement(source, "float_array", id=pos_array_id, count=str(len(verts) * 3))
        pos_array.text = " ".join(f"{v.x:.6f} {v.y:.6f} {v.z:.6f}" for v in verts)

        tech = ET.SubElement(source, "technique_common")
        accessor = ET.SubElement(tech, "accessor", source=f"#{pos_array_id}", count=str(len(verts)), stride="3")
        ET.SubElement(accessor, "param", name="X", type="float")
        ET.SubElement(accessor, "param", name="Y", type="float")
        ET.SubElement(accessor, "param", name="Z", type="float")

        vertices_elem = ET.SubElement(mesh_elem, "vertices", id=f"{geom_id}-vertices")
        ET.SubElement(vertices_elem, "input", semantic="POSITION", source=f"#{pos_id}")

        # Triangles
        mesh.calc_loop_triangles()
        tri_count = len(mesh.loop_triangles)
        if tri_count > 0:
            triangles = ET.SubElement(mesh_elem, "triangles", count=str(tri_count))
            ET.SubElement(triangles, "input", semantic="VERTEX", source=f"#{geom_id}-vertices", offset="0")
            p_elem = ET.SubElement(triangles, "p")
            indices = []
            for tri in mesh.loop_triangles:
                indices.extend(tri.vertices)
            p_elem.text = " ".join(str(idx) for idx in indices)

        # Node in visual scene
        node = ET.SubElement(vscene, "node", id=clean_name, name=obj.name)
        ET.SubElement(node, "instance_geometry", url=f"#{geom_id}")

        obj.to_mesh_clear()

    scene_elem = ET.SubElement(root, "scene")
    ET.SubElement(scene_elem, "instance_visual_scene", url="#Scene")

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
    return out_path


# ------------------------------------------------------------------------------
# 9. CLI ENTRY POINT & RUNNER
# ------------------------------------------------------------------------------
def main():
    # Parse CLI arguments
    argv = sys.argv
    is_cutlist = "--cutlist" in argv or "--bom" in argv
    is_render = "--render" in argv
    is_sketchup = "--sketchup" in argv or "--dae" in argv or "--export-dae" in argv or "--obj" in argv

    # Determine view preset
    view = "front"
    for idx, arg in enumerate(argv):
        if arg == "--view" and idx + 1 < len(argv):
            view = argv[idx + 1]

    # Handle Cutlist Generation
    if is_cutlist or not HAS_BLENDER:
        cutlist = generate_kitchen_cutlist()
        csv_path = export_cutlist_csv("renders/kitchen_cutlist.csv", cutlist)
        md_path = export_cutlist_markdown("renders/kitchen_cutlist.md", cutlist)
        print_cutlist_summary(cutlist)
        print(f"[Cutlist] Exported CutList Optimizer CSV: {csv_path}")
        print(f"[Cutlist] Exported Bill of Materials Markdown: {md_path}")
        if not is_render and not HAS_BLENDER:
            return

    # If Blender is present, execute 3D build / render
    if HAS_BLENDER:
        print("\n" + "=" * 70)
        print("  MARKOVO FURNITURE — KITCHEN STANDALONE STUDIO")
        print("=" * 70)

        # 1. Clean existing scene
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete(use_global=False)
        for b in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.collections):
            for block in list(b):
                b.remove(block)

        # 2. Build Kitchen Run at origin (0, 0) running along Y
        mats = create_kitchen_materials()
        print("[1/3] Constructing Kitchen Joinery & Appliances...")
        k_root = build_kitchen(
            origin=(0.0, 0.0),
            along=(0.0, 1.0),
            out=(1.0, 0.0),
            units=DEFAULT_KITCHEN_UNITS,
            mats=mats,
            end_panel=True,
        )
        print(f"      - Built {len(DEFAULT_KITCHEN_UNITS)} units (Total length: 440 cm):")
        for u in DEFAULT_KITCHEN_UNITS:
            print(f"        * {u['kind']:<15} {u['width']} cm ({u['label']})")

        # 3. Studio Rig & Camera
        print(f"[2/3] Setting up studio lighting and framed camera (view='{view}')...")
        setup_kitchen_studio(k_root, view=view)

        # Export native COLLADA (.dae) for SketchUp if requested
        if is_sketchup:
            out_dae = export_kitchen_dae("renders/markovo_kitchen.dae")
            print(f"[SketchUp] Exported native COLLADA DAE for SketchUp: {out_dae}")

        # Render if requested via '--render'
        if is_render:
            out_path = Path("renders/kitchen_furniture_preview.png").resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"\n[3/3] [Render] Rendering studio preview to: {out_path}")
            scene = bpy.context.scene
            scene.render.engine = "CYCLES"
            if hasattr(scene, "cycles"):
                scene.cycles.device = "CPU"
                scene.cycles.samples = 32
                scene.cycles.use_denoising = True
            scene.render.resolution_x = 1920
            scene.render.resolution_y = 1080
            scene.render.filepath = str(out_path)
            bpy.ops.render.render(write_still=True)
            print(f"[Render] Preview complete: {out_path}")

        print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
