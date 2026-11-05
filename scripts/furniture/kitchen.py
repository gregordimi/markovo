"""
==============================================================================
MARKOVO FURNITURE — KITCHEN JOINERY & BUILT-IN APPLIANCES
==============================================================================

Self-contained module defining the kitchen joinery, cabinetry, and appliances.
Designed for both:
  1. Isolated Prototyping & Standalone Studio Rendering:
     /Applications/Blender.app/Contents/MacOS/Blender --python scripts/furniture/kitchen.py
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/kitchen.py -- --render

  2. Architectural Floor Plan Integration:
     from furniture.kitchen import build_kitchen, DEFAULT_KITCHEN_UNITS
==============================================================================
"""

import sys
import os
import math
from pathlib import Path
from typing import Dict, List, Tuple

# Ensure parent directory (scripts/) is in sys.path when run directly
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import bpy
import bmesh
from mathutils import Vector, Matrix

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
def get_or_create_material(name: str) -> bpy.types.Material:
    """Gets an existing material or creates a clean node-based material."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    return mat


def create_kitchen_materials() -> Dict[str, bpy.types.Material]:
    """Creates all PBR materials required for the kitchen cabinetry and appliances."""
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


def resolve_kitchen_materials(mats: Dict[str, bpy.types.Material] = None) -> Dict[str, bpy.types.Material]:
    """Resolves material dict mapping from either cad_markovo materials or standalone."""
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
    mat: bpy.types.Material,
    col: bpy.types.Collection,
    parent: bpy.types.Object = None,
) -> bpy.types.Object:
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
    mat: bpy.types.Material,
    col: bpy.types.Collection,
    parent: bpy.types.Object = None,
    front_mat: bpy.types.Material = None,
) -> bpy.types.Object:
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
    mat: bpy.types.Material,
    col: bpy.types.Collection,
    parent: bpy.types.Object = None,
    segments: int = 24,
) -> bpy.types.Object:
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
    col: bpy.types.Collection = None,
    parent: bpy.types.Object = None,
    mats: Dict[str, bpy.types.Material] = None,
    worktop_start: float = None,
    plinth_start: float = 0.0,
    end_panel: bool = True,
    name_prefix: str = "Kitchen_Run",
) -> bpy.types.Object:
    """
    Builds the complete linear kitchen furniture run.
    Can be called standalone or imported into Floor 3 / FloorPlanBuilder.
    """
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
# 7. STANDALONE STUDIO RUNNER (FOR ISOLATED DEV & RENDERING)
# ------------------------------------------------------------------------------
def setup_kitchen_studio(kitchen_root: bpy.types.Object):
    """Sets up an isolated, high-end architectural studio lighting and camera rig."""
    col = bpy.data.collections.new("Kitchen_Studio")
    bpy.context.scene.collection.children.link(col)

    # 1. Key Studio Softbox
    key_light = bpy.data.lights.new("Studio_Key", "AREA")
    key_light.energy = 180.0
    key_light.size = 2.5
    key_light.size_y = 1.5
    key_obj = bpy.data.objects.new("Studio_Key", key_light)
    key_obj.location = (2.2, 2.2, 2.8)
    key_obj.rotation_euler = (math.radians(45.0), math.radians(15.0), math.radians(45.0))
    col.objects.link(key_obj)

    # 2. Fill Light
    fill_light = bpy.data.lights.new("Studio_Fill", "AREA")
    fill_light.energy = 80.0
    fill_light.size = 3.0
    fill_obj = bpy.data.objects.new("Studio_Fill", fill_light)
    fill_obj.location = (2.0, -1.5, 2.0)
    fill_obj.rotation_euler = (math.radians(30.0), math.radians(-25.0), math.radians(110.0))
    col.objects.link(fill_obj)

    # 3. Dedicated Camera Framed directly on the Kitchen Joinery
    cam_data = bpy.data.cameras.new("Kitchen_Studio_Camera")
    cam_data.lens = 28.0
    cam_data.sensor_width = 36.0
    cam_obj = bpy.data.objects.new("Kitchen_Studio_Camera", cam_data)
    #cam_obj.location = (2.6, 2.2, 1.45)

    # Track target at the center of the kitchen run (hob & prep zone)
    #target = Vector((0.35, 2.2, 0.95))
    cam_obj.location = (4.8, 2.2, 1.5)
    target = Vector((0.3, 2.2, 1.05))
    direction = target - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    col.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    # Studio Floor Plane
    floor_mesh = bpy.data.meshes.new("Studio_Floor")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=8.0)
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


def main():
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
    print("[1/2] Constructing Kitchen Joinery & Appliances...")
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
    print("[2/2] Setting up studio lighting and framed camera...")
    setup_kitchen_studio(k_root)

    # Render if requested via '--render'
    if "--render" in sys.argv:
        out_path = Path("renders/kitchen_furniture_preview.png").resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"\n[Render] Rendering studio preview to: {out_path}")
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

