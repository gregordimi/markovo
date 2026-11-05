"""
==============================================================================
MARKOVO FURNITURE — BATHROOM (FLOOR 3)
==============================================================================

Self-contained module defining the bathroom fixtures, spatial clearances,
and room shell for Floor 3 (Main Level).

Upgrades:
- Curved/contoured geometry (oval toilet bowl & seat, oval recessed sink basin,
  cylindrical pipes/faucets/rain head, beveled cabinetry).
- Framed Granite Floor: Dark granite perimeter border + tiled light granite grid
  in the center with recessed grout joints.
- Granite feature walls behind the shower cabin (West & South shower walls).
- Medium gray bathroom walls.
- Warm Oak Wood vanity cabinet with two drawers under the sink.
- High bird's-eye camera overlooking the entire bathroom unobstructed.
==============================================================================
"""

import sys
import os
import math
from pathlib import Path
from typing import Dict, List, Tuple, Any

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    import bpy
    import bmesh
    from mathutils import Vector, Matrix
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False

CM = 0.01

# Room Dimensions
ROOM_NAME = "Bathroom"
FLOOR_LEVEL = "Floor_3"
ROOM_X_MIN = 0.0    # cm
ROOM_X_MAX = 230.0  # cm
ROOM_Y_MIN = 0.0    # cm
ROOM_Y_MAX = 160.0  # cm
ROOM_WIDTH = ROOM_X_MAX - ROOM_X_MIN    # 230 cm (2.30 m)
ROOM_LENGTH = ROOM_Y_MAX - ROOM_Y_MIN   # 160 cm (1.60 m)
CEILING_HEIGHT = 2.80                   # 2.80 m


def get_or_create_material(name: str):
    if not HAS_BLENDER:
        return None
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    return mat


def _make_granite_material(name: str, color1: Tuple[float, float, float, float],
                           color2: Tuple[float, float, float, float],
                           roughness: float = 0.20, scale: float = 45.0):
    """Creates a procedural speckled granite material using Blender shader nodes."""
    mat = get_or_create_material(name)
    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = roughness
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 12.0
    noise.inputs["Roughness"].default_value = 0.65

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = color1
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = color2

    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])

    mat.diffuse_color = color1
    return mat


def create_materials() -> Dict[str, Any]:
    if not HAS_BLENDER:
        return {}
    mats = {}

    # 1. Dark Granite (Outer Floor Frame & Shower Accent Walls)
    mats["granite_frame"] = _make_granite_material(
        "Mat_Granite_Dark_Frame",
        color1=(0.08, 0.09, 0.10, 1.0),
        color2=(0.24, 0.26, 0.28, 1.0),
        roughness=0.18,
        scale=55.0
    )

    # 2. Mid-Light Speckled Granite (Center Floor Tiles)
    mats["granite_tile"] = _make_granite_material(
        "Mat_Granite_Center_Tile",
        color1=(0.26, 0.28, 0.30, 1.0),
        color2=(0.55, 0.57, 0.59, 1.0),
        roughness=0.22,
        scale=65.0
    )

    # 3. Dark Grout Base
    grout = get_or_create_material("Mat_Tile_Grout")
    bsdf = grout.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.05, 0.05, 0.06, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.85
    grout.diffuse_color = (0.05, 0.05, 0.06, 1.0)
    mats["grout"] = grout

    # 4. Gray Bathroom Walls
    w = get_or_create_material("Mat_Bath_Wall_Gray")
    bsdf = w.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.36, 0.38, 0.41, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.65
    w.diffuse_color = (0.36, 0.38, 0.41, 1.0)
    mats["wall"] = w

    # 5. Sanitary Ceramic (Crisp Glossy White)
    cer = get_or_create_material("Mat_Sanitary_Ceramic")
    bsdf = cer.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.96, 0.96, 0.97, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.08
    cer.diffuse_color = (0.96, 0.96, 0.97, 1.0)
    mats["ceramic"] = cer

    # 6. Warm Oak Wood (Under-Sink Vanity & North Storage Cabinet)
    oak = get_or_create_material("Mat_Oak_Wood")
    bsdf = oak.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.48, 0.29, 0.14, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.35
    oak.diffuse_color = (0.48, 0.29, 0.14, 1.0)
    mats["oak"] = oak

    # 7. Matte Anthracite / Charcoal (North Cabinet Body Accent)
    cab = get_or_create_material("Mat_Cabinet_Anthracite")
    bsdf = cab.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.14, 0.15, 0.17, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.35
    cab.diffuse_color = (0.14, 0.15, 0.17, 1.0)
    mats["anthracite"] = cab

    # 8. Polished Chrome
    ch = get_or_create_material("Mat_Chrome")
    bsdf = ch.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.86, 0.88, 0.90, 1.0)
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.96
        bsdf.inputs["Roughness"].default_value = 0.08
    ch.diffuse_color = (0.86, 0.88, 0.90, 1.0)
    mats["chrome"] = ch

    # 9. Clear Tempered Shower Glass (True transmission for Cycles)
    gl = get_or_create_material("Mat_Shower_Glass")
    bsdf = gl.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.82, 0.93, 0.95, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.04
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = 0.88
        elif "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = 0.88
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = 0.28
    gl.diffuse_color = (0.82, 0.93, 0.95, 0.3)
    mats["glass"] = gl

    return mats


# ==============================================================================
# GEOMETRY HELPERS (Boxes, Beveled Boxes, Cylinders, Stadium/Oval Curves)
# ==============================================================================

def _link_mesh(name: str, bm: Any, mat: Any, col: Any, parent: Any = None, smooth: bool = False):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    if smooth:
        for poly in mesh.polygons:
            poly.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    if mat:
        obj.data.materials.append(mat)
    col.objects.link(obj)
    if parent:
        obj.parent = parent
    return obj


def _create_box(name: str, x0: float, x1: float, y0: float, y1: float, z0: float, z1: float,
                mat: Any, col: Any, parent: Any = None):
    bm = bmesh.new()
    v_btm = [
        bm.verts.new((x0 * CM, y0 * CM, z0)),
        bm.verts.new((x1 * CM, y0 * CM, z0)),
        bm.verts.new((x1 * CM, y1 * CM, z0)),
        bm.verts.new((x0 * CM, y1 * CM, z0)),
    ]
    v_top = [
        bm.verts.new((x0 * CM, y0 * CM, z1)),
        bm.verts.new((x1 * CM, y0 * CM, z1)),
        bm.verts.new((x1 * CM, y1 * CM, z1)),
        bm.verts.new((x0 * CM, y1 * CM, z1)),
    ]
    bm.faces.new(v_btm[::-1])
    bm.faces.new(v_top)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new([v_btm[i], v_btm[j], v_top[j], v_top[i]])
    return _link_mesh(name, bm, mat, col, parent, smooth=False)


def _create_beveled_box(name: str, x0: float, x1: float, y0: float, y1: float, z0: float, z1: float,
                        bevel_cm: float, mat: Any, col: Any, parent: Any = None):
    bm = bmesh.new()
    v_btm = [
        bm.verts.new((x0 * CM, y0 * CM, z0)),
        bm.verts.new((x1 * CM, y0 * CM, z0)),
        bm.verts.new((x1 * CM, y1 * CM, z0)),
        bm.verts.new((x0 * CM, y1 * CM, z0)),
    ]
    v_top = [
        bm.verts.new((x0 * CM, y0 * CM, z1)),
        bm.verts.new((x1 * CM, y0 * CM, z1)),
        bm.verts.new((x1 * CM, y1 * CM, z1)),
        bm.verts.new((x0 * CM, y1 * CM, z1)),
    ]
    bm.faces.new(v_btm[::-1])
    bm.faces.new(v_top)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new([v_btm[i], v_btm[j], v_top[j], v_top[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.bevel(
        bm,
        geom=list(bm.edges),
        offset=bevel_cm * CM,
        offset_type='OFFSET',
        segments=3,
        profile=0.5
    )
    return _link_mesh(name, bm, mat, col, parent, smooth=True)


def _create_cylinder(name: str, cx: float, cy: float, radius_cm: float, z0: float, z1: float,
                     mat: Any, col: Any, parent: Any = None, segments: int = 32):
    bm = bmesh.new()
    v_btm = []
    v_top = []
    for i in range(segments):
        ang = 2.0 * math.pi * i / segments
        px = (cx + radius_cm * math.cos(ang)) * CM
        py = (cy + radius_cm * math.sin(ang)) * CM
        v_btm.append(bm.verts.new((px, py, z0)))
        v_top.append(bm.verts.new((px, py, z1)))
    bm.faces.new(v_btm[::-1])
    bm.faces.new(v_top)
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new([v_btm[i], v_btm[j], v_top[j], v_top[i]])
    return _link_mesh(name, bm, mat, col, parent, smooth=True)


def _create_stadium_prism(name: str, x_back: float, x_front_center: float, cy: float,
                          radius_y: float, z0: float, z1: float,
                          taper_bottom: float, mat: Any, col: Any, parent: Any = None, segments: int = 24):
    """Creates a D-shaped / stadium toilet contour (flat against wall at x_back, semicircular nose at front)."""
    bm = bmesh.new()
    pts_top = [(x_back, cy - radius_y)]
    for i in range(segments + 1):
        ang = -math.pi / 2.0 + math.pi * i / segments
        px = x_front_center + radius_y * math.cos(ang)
        py = cy + radius_y * math.sin(ang)
        pts_top.append((px, py))
    pts_top.append((x_back, cy + radius_y))

    v_btm = []
    v_top = []
    for px, py in pts_top:
        # Slight inward taper at bottom for a contoured ceramic bowl look
        bx = x_back + (px - x_back) * taper_bottom
        by = cy + (py - cy) * taper_bottom
        v_btm.append(bm.verts.new((bx * CM, by * CM, z0)))
        v_top.append(bm.verts.new((px * CM, py * CM, z1)))

    n = len(v_top)
    bm.faces.new(v_btm[::-1])
    bm.faces.new(v_top)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([v_btm[i], v_btm[j], v_top[j], v_top[i]])
    return _link_mesh(name, bm, mat, col, parent, smooth=True)


def _create_oval_ring(name: str, cx: float, cy: float, rx_out: float, ry_out: float,
                      rx_in: float, ry_in: float, z0: float, z1: float,
                      mat: Any, col: Any, parent: Any = None, segments: int = 36):
    """Creates a smooth oval ring (used for toilet seat and curved sink basin walls)."""
    bm = bmesh.new()
    out_btm, out_top = [], []
    in_btm, in_top = [], []
    for i in range(segments):
        ang = 2.0 * math.pi * i / segments
        c, s = math.cos(ang), math.sin(ang)
        out_btm.append(bm.verts.new(((cx + rx_out * c) * CM, (cy + ry_out * s) * CM, z0)))
        out_top.append(bm.verts.new(((cx + rx_out * c) * CM, (cy + ry_out * s) * CM, z1)))
        in_btm.append(bm.verts.new(((cx + rx_in * c) * CM, (cy + ry_in * s) * CM, z0)))
        in_top.append(bm.verts.new(((cx + rx_in * c) * CM, (cy + ry_in * s) * CM, z1)))

    for i in range(segments):
        j = (i + 1) % segments
        # Outer wall
        bm.faces.new([out_btm[i], out_btm[j], out_top[j], out_top[i]])
        # Inner wall
        bm.faces.new([in_btm[j], in_btm[i], in_top[i], in_top[j]])
        # Top rim
        bm.faces.new([out_top[i], out_top[j], in_top[j], in_top[i]])
        # Bottom rim
        bm.faces.new([in_btm[i], in_btm[j], out_btm[j], out_btm[i]])

    return _link_mesh(name, bm, mat, col, parent, smooth=True)


# ==============================================================================
# ARCHITECTURAL SHELL & GRANITE FLOOR / WALLS
# ==============================================================================

def build_room_shell(col: Any, mats: Dict[str, Any], parent: Any = None) -> Any:
    """Builds the gray room walls, framed granite floor, and shower granite accent walls."""
    root = bpy.data.objects.new("Bathroom_Shell", None)
    col.objects.link(root)
    if parent:
        root.parent = parent

    w = mats["wall"]
    gf = mats["granite_frame"]
    gt = mats["granite_tile"]
    grout = mats["grout"]

    # 1. Subfloor & Dark Grout Bed
    _create_box("BA_Floor_Slab", ROOM_X_MIN, ROOM_X_MAX, ROOM_Y_MIN, ROOM_Y_MAX, -0.15, 0.0, grout, col, root)

    # 2. GRANITE FLOOR: Outer Perimeter Frame (22 cm wide dark granite border) + Inner Tiled Grid
    B = 22.0  # Frame border width in cm
    z_tile = 0.012
    # 4 Border Frame Slabs
    _create_beveled_box("BA_Granite_Frame_South", 0, 230, 0, B, 0.0, z_tile, 0.2, gf, col, root)
    _create_beveled_box("BA_Granite_Frame_North", 0, 230, 160 - B, 160, 0.0, z_tile, 0.2, gf, col, root)
    _create_beveled_box("BA_Granite_Frame_West", 0, B, B, 160 - B, 0.0, z_tile, 0.2, gf, col, root)
    _create_beveled_box("BA_Granite_Frame_East", 230 - B, 230, B, 160 - B, 0.0, z_tile, 0.2, gf, col, root)

    # Inner Granite Tiles (6 cols x 4 rows inside x=22..208, y=22..138 with 0.4 cm grout gap)
    ix0, ix1 = B, 230.0 - B
    iy0, iy1 = B, 160.0 - B
    nx, ny = 6, 4
    dx = (ix1 - ix0) / nx
    dy = (iy1 - iy0) / ny
    gap = 0.35
    for r in range(ny):
        for c in range(nx):
            tx0 = ix0 + c * dx + gap
            tx1 = ix0 + (c + 1) * dx - gap
            ty0 = iy0 + r * dy + gap
            ty1 = iy0 + (r + 1) * dy - gap
            _create_beveled_box(f"BA_Granite_Tile_{r}_{c}", tx0, tx1, ty0, ty1, 0.0, z_tile, 0.15, gt, col, root)

    # 3. GRAY PERIMETER WALLS
    # North Wall (y=160..172)
    _create_box("BA_Wall_North", ROOM_X_MIN, ROOM_X_MAX, ROOM_Y_MAX, ROOM_Y_MAX + 12, 0.0, CEILING_HEIGHT, w, col, root)
    # West Wall (x=-12..0)
    _create_box("BA_Wall_West", ROOM_X_MIN - 12, ROOM_X_MIN, ROOM_Y_MIN, ROOM_Y_MAX, 0.0, CEILING_HEIGHT, w, col, root)
    # NW Plumbing Shaft (x=0..45, y=115..160)
    _create_box("BA_Shaft_NW", ROOM_X_MIN, ROOM_X_MIN + 45, ROOM_Y_MAX - 45, ROOM_Y_MAX, 0.0, CEILING_HEIGHT, w, col, root)

    # South Wall & East Wall (Hidden from camera rays so the top-down view is never blocked)
    w_south = _create_box("BA_Wall_South", ROOM_X_MIN, ROOM_X_MAX, ROOM_Y_MIN - 12, ROOM_Y_MIN, 0.0, CEILING_HEIGHT, w, col, root)
    w_east_s = _create_box("BA_Wall_East_Pier_S", ROOM_X_MAX, ROOM_X_MAX + 12, 0, 10, 0.0, CEILING_HEIGHT, w, col, root)
    w_east_l = _create_box("BA_Wall_East_Lintel", ROOM_X_MAX, ROOM_X_MAX + 12, 10, 80, 2.10, CEILING_HEIGHT, w, col, root)
    w_east_n = _create_box("BA_Wall_East_North", ROOM_X_MAX, ROOM_X_MAX + 12, 80, ROOM_Y_MAX, 0.0, CEILING_HEIGHT, w, col, root)

    for wall_obj in (w_south, w_east_s, w_east_l, w_east_n):
        wall_obj.visible_camera = False

    # 4. GRANITE WALL CLADDING BEHIND THE SHOWER CABIN (West & South walls inside shower x=0..85, y=0..80)
    # West Shower Granite Slab (4 rows of large-format 80x70 cm granite slabs)
    for idx in range(4):
        z_low = idx * 0.70 + 0.002
        z_high = (idx + 1) * 0.70 - 0.002
        _create_beveled_box(f"BA_Shower_Granite_West_{idx}", 0.0, 2.0, 0.0, 80.0, z_low, z_high, 0.15, gf, col, root)
        _create_beveled_box(f"BA_Shower_Granite_South_{idx}", 2.0, 82.0, 0.0, 2.0, z_low, z_high, 0.15, gf, col, root)

    return root


# ==============================================================================
# CURVED & CONTOURED BATHROOM FIXTURES
# ==============================================================================

def build_bathroom_furniture(col: Any, mats: Dict[str, Any], parent: Any = None) -> Any:
    """Builds curved, standard-sized bathroom fixtures and oak wood cabinetry."""
    root = bpy.data.objects.new("Bathroom_Furniture", None)
    col.objects.link(root)
    if parent:
        root.parent = parent

    cer = mats["ceramic"]
    oak = mats["oak"]
    anth = mats["anthracite"]
    ch = mats["chrome"]
    gl = mats["glass"]
    gf = mats["granite_frame"]
    w = mats["wall"]

    # -------------------------------------------------------------------------
    # 1. WALK-IN SHOWER (SW Corner: 82 x 82 cm curved-edge tray + granite wall)
    # -------------------------------------------------------------------------
    # Outer beveled acrylic tray curb + recessed floor pan
    _create_beveled_box("Shower_Tray_Rim_N", 0, 82, 76, 82, 0.01, 0.06, 0.5, cer, col, root)
    _create_beveled_box("Shower_Tray_Rim_E", 76, 82, 0, 76, 0.01, 0.06, 0.5, cer, col, root)
    _create_beveled_box("Shower_Tray_Floor", 2, 76, 2, 76, 0.01, 0.035, 0.3, cer, col, root)
    # Circular Chrome Drain in NE corner (matching sketch)
    _create_cylinder("Shower_Drain_Circle", 64.0, 64.0, 4.5, 0.035, 0.042, ch, col, root)

    # Solid Partition Wall on North side of shower (x=0..85, y=82..90, height 2.15 m)
    # Lined with Granite on the inside (South face) and Gray plaster on the outside (North face)
    _create_beveled_box("Shower_Partition_Core", 0, 85, 84, 90, 0.0, 2.15, 0.3, w, col, root)
    _create_beveled_box("Shower_Partition_Granite_Inner", 0, 85, 82, 84, 0.0, 2.15, 0.2, gf, col, root)

    # Sliding Glass Enclosure on East side (x=78..81, y=0..82)
    _create_box("Shower_Glass_Fixed", 80.0, 81.0, 39.0, 82.0, 0.06, 2.05, gl, col, root)
    _create_box("Shower_Glass_Slide", 78.2, 79.2, 2.0, 43.0, 0.06, 2.05, gl, col, root)
    _create_beveled_box("Shower_Track_Bar", 77.5, 81.8, 0.0, 82.0, 2.03, 2.07, 0.2, ch, col, root)
    _create_cylinder("Shower_Door_Handle", 77.5, 38.0, 0.8, 0.95, 1.25, ch, col, root)

    # Curved Cylindrical Shower Column & Round Rain Head in SW corner
    _create_cylinder("Shower_Pipe_Vertical", 8.0, 8.0, 1.2, 0.95, 2.12, ch, col, root)
    _create_beveled_box("Shower_Mixer_Bar", 5.0, 11.0, 5.0, 22.0, 1.02, 1.07, 0.8, ch, col, root)
    _create_beveled_box("Shower_Head_Arm", 7.0, 34.0, 7.0, 9.5, 2.09, 2.12, 0.4, ch, col, root)
    _create_cylinder("Shower_Rain_Head_Disc", 32.0, 22.0, 13.0, 2.06, 2.09, ch, col, root, segments=40)

    # -------------------------------------------------------------------------
    # 2. CONTOURED OVAL TOILET (Mounted to East face of NW Shaft x=45, y=136)
    # -------------------------------------------------------------------------
    tx_wall = 45.0
    ty_mid = 136.0

    # Beveled Cistern Tank against shaft wall (x=45..60, y=117..155)
    _create_beveled_box("Toilet_Cistern_Tank", tx_wall, tx_wall + 15.0, ty_mid - 19.0, ty_mid + 19.0, 0.40, 0.84, 1.5, cer, col, root)
    _create_beveled_box("Toilet_Cistern_Lid", tx_wall - 0.5, tx_wall + 16.0, ty_mid - 19.8, ty_mid + 19.8, 0.84, 0.87, 0.8, cer, col, root)
    _create_cylinder("Toilet_Flush_Btn", tx_wall + 8.0, ty_mid, 2.5, 0.87, 0.88, ch, col, root)

    # Curved Stadium Pedestal Base (z=0.0..0.37) & Upper Rim (z=0.37..0.41)
    _create_stadium_prism("Toilet_Pedestal_Base", tx_wall, tx_wall + 34.0, ty_mid, 14.5, 0.0, 0.37, 0.78, cer, col, root)
    _create_stadium_prism("Toilet_Bowl_Outer", tx_wall + 12.0, tx_wall + 37.0, ty_mid, 18.0, 0.22, 0.40, 0.65, cer, col, root)

    # Contoured Oval Toilet Seat Ring (z=0.40..0.435) + Dark Inner Water Basin
    _create_oval_ring("Toilet_Oval_Seat", tx_wall + 33.5, ty_mid, 19.5, 18.0, 11.5, 10.5, 0.40, 0.435, cer, col, root)
    _create_cylinder("Toilet_Water_Well", tx_wall + 32.0, ty_mid, 10.0, 0.24, 0.36, gf, col, root)

    # -------------------------------------------------------------------------
    # 3. NORTH WALL STORAGE CABINET (Oak Wood Doors + Anthracite Frame)
    # -------------------------------------------------------------------------
    cx0, cx1 = 105.0, 185.0
    cy0, cy1 = 140.0, 160.0

    _create_beveled_box("Cabinet_North_Carcass", cx0, cx1, cy0 + 2.5, cy1, 0.90, 1.90, 0.4, anth, col, root)
    _create_beveled_box("Cabinet_North_Door_L", cx0 + 0.5, cx0 + 39.6, cy0, cy0 + 2.5, 0.905, 1.895, 0.4, oak, col, root)
    _create_beveled_box("Cabinet_North_Door_R", cx0 + 40.4, cx1 - 0.5, cy0, cy0 + 2.5, 0.905, 1.895, 0.4, oak, col, root)
    _create_cylinder("Cabinet_Knob_L", cx0 + 36.0, cy0 - 1.0, 1.0, 1.02, 1.18, ch, col, root)
    _create_cylinder("Cabinet_Knob_R", cx0 + 44.0, cy0 - 1.0, 1.0, 1.02, 1.18, ch, col, root)

    # -------------------------------------------------------------------------
    # 4. OAK WOOD UNDER-SINK VANITY & CURVED OVAL WASHBASIN (East Wall, NE)
    # -------------------------------------------------------------------------
    vx0, vx1 = 184.0, 230.0
    vy0, vy1 = 84.0, 146.0
    vy_mid = (vy0 + vy1) / 2.0  # 115.0

    # Oak Wood Vanity Cabinet Body (z=0.18..0.80 m) + Two Beveled Oak Drawer Fronts + Recessed Plinth
    _create_beveled_box("Sink_Oak_Plinth", vx0 + 6.0, vx1, vy0 + 2.0, vy1 - 2.0, 0.0, 0.18, 0.3, anth, col, root)
    _create_beveled_box("Sink_Oak_Carcass", vx0 + 2.5, vx1, vy0, vy1, 0.18, 0.80, 0.5, oak, col, root)
    # Lower & Upper Oak Drawers facing West into the room
    _create_beveled_box("Sink_Oak_Drawer_Bottom", vx0, vx0 + 2.5, vy0 + 1.0, vy1 - 1.0, 0.19, 0.48, 0.5, oak, col, root)
    _create_beveled_box("Sink_Oak_Drawer_Top", vx0, vx0 + 2.5, vy0 + 1.0, vy1 - 1.0, 0.495, 0.79, 0.5, oak, col, root)
    # Chrome Drawer Pull Bars
    _create_beveled_box("Sink_Pull_Bottom", vx0 - 1.8, vx0, vy_mid - 10.0, vy_mid + 10.0, 0.43, 0.45, 0.3, ch, col, root)
    _create_beveled_box("Sink_Pull_Top", vx0 - 1.8, vx0, vy_mid - 10.0, vy_mid + 10.0, 0.74, 0.76, 0.3, ch, col, root)

    # Ceramic Countertop Slab (z=0.80..0.83) + Curved Oval Vessel Rim (z=0.82..0.90)
    _create_beveled_box("Sink_Counter_Slab", vx0 - 1.0, vx1, vy0 - 1.0, vy1 + 1.0, 0.80, 0.83, 0.6, cer, col, root)
    _create_oval_ring("Sink_Oval_Basin", vx0 + 21.0, vy_mid, 16.5, 23.5, 13.0, 19.5, 0.82, 0.90, cer, col, root)
    _create_cylinder("Sink_Drain_Plug", vx0 + 21.0, vy_mid, 2.2, 0.83, 0.838, ch, col, root)

    # Cylindrical Chrome Faucet Mixer
    _create_cylinder("Sink_Faucet_Base", vx1 - 6.5, vy_mid, 2.2, 0.83, 0.98, ch, col, root)
    _create_beveled_box("Sink_Faucet_Spout", vx1 - 19.0, vx1 - 5.5, vy_mid - 1.2, vy_mid + 1.2, 0.95, 0.975, 0.5, ch, col, root)
    _create_beveled_box("Sink_Faucet_Lever", vx1 - 8.5, vx1 - 4.5, vy_mid - 1.0, vy_mid + 6.0, 0.98, 0.995, 0.3, ch, col, root)

    # Rounded Pill Mirror on East Wall above Sink
    _create_beveled_box("Sink_Mirror_Frame", vx1 - 2.0, vx1, vy0 + 4.0, vy1 - 4.0, 1.02, 1.88, 0.8, ch, col, root)

    return root


# ==============================================================================
# TOP-DOWN BIRD'S-EYE STUDIO CAMERA & LIGHTING
# ==============================================================================

def setup_studio(parent_obj: Any):
    col = bpy.data.collections.new("Studio_Rig")
    bpy.context.scene.collection.children.link(col)

    # Warm White Main Overhead Ceiling Fill
    key = bpy.data.lights.new("BA_Key", "AREA")
    key.energy = 110.0
    key.size = 2.0
    key.color = (1.0, 0.98, 0.94)
    key_obj = bpy.data.objects.new("BA_Key", key)
    key_obj.location = (1.15, 0.80, 2.72)
    key_target = Vector((1.15, 0.80, 0.0))
    key_obj.rotation_euler = (key_target - key_obj.location).to_track_quat("-Z", "Y").to_euler()
    col.objects.link(key_obj)

    # High Angled Rim Light to highlight curved ceramic & granite reflections
    rim = bpy.data.lights.new("BA_Rim", "AREA")
    rim.energy = 90.0
    rim.size = 1.8
    rim.color = (0.94, 0.97, 1.0)
    rim_obj = bpy.data.objects.new("BA_Rim", rim)
    rim_obj.location = (2.10, -0.40, 3.20)
    rim_target = Vector((0.95, 0.95, 0.60))
    rim_obj.rotation_euler = (rim_target - rim_obj.location).to_track_quat("-Z", "Y").to_euler()
    col.objects.link(rim_obj)

    # High Bird's-Eye Camera above the room looking down at the entire floor plan
    cam_data = bpy.data.cameras.new("BA_Camera")
    cam_data.lens = 28.0
    cam_obj = bpy.data.objects.new("BA_Camera", cam_data)
    cam_obj.location = (1.45, -0.35, 4.40)
    target = Vector((1.12, 0.82, 0.55))
    cam_obj.rotation_euler = (target - cam_obj.location).to_track_quat("-Z", "Y").to_euler()
    col.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj


def export_collada_dae(filepath: str, include_furniture: bool = True):
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

    prefixes = ("BA_", "Shower_", "Toilet_", "Cabinet_", "Sink_") if include_furniture else ("BA_",)
    mesh_objs = [o for o in bpy.context.scene.objects if o.type == "MESH" and any(o.name.startswith(p) for p in prefixes)]

    for obj in mesh_objs:
        mesh = obj.to_mesh()
        clean = obj.name.replace(" ", "_").replace(".", "_")
        geom_id = f"geom-{clean}"
        geom = ET.SubElement(lib_geoms, "geometry", id=geom_id, name=obj.name)
        mesh_elem = ET.SubElement(geom, "mesh")

        pos_id = f"{geom_id}-pos"
        source = ET.SubElement(mesh_elem, "source", id=pos_id)
        verts = [v.co for v in mesh.vertices]
        arr_id = f"{pos_id}-arr"
        arr = ET.SubElement(source, "float_array", id=arr_id, count=str(len(verts) * 3))
        arr.text = " ".join(f"{v.x:.6f} {v.y:.6f} {v.z:.6f}" for v in verts)

        tech = ET.SubElement(source, "technique_common")
        acc = ET.SubElement(tech, "accessor", source=f"#{arr_id}", count=str(len(verts)), stride="3")
        ET.SubElement(acc, "param", name="X", type="float")
        ET.SubElement(acc, "param", name="Y", type="float")
        ET.SubElement(acc, "param", name="Z", type="float")

        ve = ET.SubElement(mesh_elem, "vertices", id=f"{geom_id}-v")
        ET.SubElement(ve, "input", semantic="POSITION", source=f"#{pos_id}")

        mesh.calc_loop_triangles()
        if len(mesh.loop_triangles) > 0:
            tri = ET.SubElement(mesh_elem, "triangles", count=str(len(mesh.loop_triangles)))
            ET.SubElement(tri, "input", semantic="VERTEX", source=f"#{geom_id}-v", offset="0")
            p = ET.SubElement(tri, "p")
            indices = [idx for t in mesh.loop_triangles for idx in t.vertices]
            p.text = " ".join(str(i) for i in indices)

        node = ET.SubElement(vscene, "node", id=clean, name=obj.name)
        ET.SubElement(node, "instance_geometry", url=f"#{geom_id}")
        obj.to_mesh_clear()

    scene_elem = ET.SubElement(root, "scene")
    ET.SubElement(scene_elem, "instance_visual_scene", url="#Scene")

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
    return out_path


def main():
    if not HAS_BLENDER:
        print("[Error] Blender Python environment is required to run this module.")
        return

    argv = sys.argv
    is_render = "--render" in argv
    is_sketchup = "--sketchup" in argv or "--dae" in argv
    is_shell_only = "--export-shell" in argv

    print("\n" + "=" * 70)
    print(f"  MARKOVO FURNITURE — {ROOM_NAME.upper()} ({ROOM_WIDTH:.0f} x {ROOM_LENGTH:.0f} cm)")
    print("=" * 70)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for b in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.collections):
        for block in list(b):
            b.remove(block)

    mats = create_materials()
    col = bpy.context.scene.collection

    print("[1/3] Building architectural room shell & granite floor/walls...")
    shell = build_room_shell(col, mats)

    if not is_shell_only:
        print("[2/3] Constructing curved bathroom fixtures & oak cabinetry...")
        furn = build_bathroom_furniture(col, mats, parent=shell)
    else:
        print("[2/3] Skipping furniture (--export-shell requested)...")

    print("[3/3] Setting up overhead bird's-eye camera and studio lighting...")
    setup_studio(shell)

    if is_shell_only:
        out_dae = export_collada_dae("renders/room_bathroom_shell.dae", include_furniture=False)
        print(f"\n[SketchUp] Exported empty room shell to: {out_dae}")
    elif is_sketchup:
        out_dae = export_collada_dae("renders/room_bathroom_furniture.dae", include_furniture=True)
        print(f"\n[SketchUp] Exported room + furniture to: {out_dae}")

    if is_render:
        out_png = Path("renders/bathroom_preview.png").resolve()
        out_png.parent.mkdir(parents=True, exist_ok=True)
        print(f"\n[Render] Rendering preview to: {out_png}")
        scene = bpy.context.scene
        scene.render.engine = "CYCLES"
        if hasattr(scene, "cycles"):
            scene.cycles.device = "CPU"
            scene.cycles.samples = 48
            scene.cycles.use_denoising = True
        scene.render.resolution_x = 1920
        scene.render.resolution_y = 1080
        scene.render.filepath = str(out_png)
        bpy.ops.render.render(write_still=True)
        print(f"[Render] Preview complete: {out_png}")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()