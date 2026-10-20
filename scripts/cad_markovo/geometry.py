"""
3D Architectural Geometry Primitives and Parametric CAD Components.

Provides:
- 3D prisms from 2D quadrilaterals and polygons
- Precision wall segments with cutout support
- White uPVC windows with vertical mullions and double-glazing
- Swing doors with White uPVC exterior leaves or warm wood interior leaves
- Stairs with authentic Cement Mosaic treads and risers
- Terrace solid parapets (matching wall material) with overhanging stone coping
- 3D extruded room labels and architectural callouts
"""

import math
import bpy
import bmesh
from mathutils import Vector, Matrix
from .config import (
    CM,
    WALL_HEIGHT,
    DOOR_HEIGHT,
    FRAME_THICKNESS_CM,
    DOOR_OPEN_RATIO,
    TERRACE_PARAPET_HEIGHT,
    TERRACE_COPING_THICKNESS,
    TERRACE_TOTAL_HEIGHT,
    TERRACE_WALL_THICKNESS,
    TERRACE_COPING_WIDTH,
)


def wall_quad(x1: float, y1: float, x2: float, y2: float, thickness: float) -> list:
    """Computes the 4 corners of a rectangular wall footprint given its centerline and thickness (in cm)."""
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return [(x1, y1), (x1, y1), (x1, y1), (x1, y1)]
    ux, uy = dx / length, dy / length
    nx, ny = -uy * (thickness / 2.0), ux * (thickness / 2.0)
    return [
        (x1 + nx, y1 + ny),
        (x2 + nx, y2 + ny),
        (x2 - nx, y2 - ny),
        (x1 - nx, y1 - ny),
    ]


def link_to_collection(obj: bpy.types.Object, col: bpy.types.Collection):
    """Safely links an object to a collection while unlinking from others."""
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)


def create_prism_from_quad(
    name: str,
    corners_2d: list,
    z_bottom: float,
    z_top: float,
    mat: bpy.types.Material,
    col: bpy.types.Collection,
    parent: bpy.types.Object = None,
) -> bpy.types.Object:
    """Creates a 3D box/prism mesh from 4 (x, y) corners in cm and Z bounds in meters."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    verts_btm = [bm.verts.new((x * CM, y * CM, z_bottom)) for x, y in corners_2d]
    verts_top = [bm.verts.new((x * CM, y * CM, z_top)) for x, y in corners_2d]

    bm.faces.new(verts_btm[::-1])  # Normal points downwards
    bm.faces.new(verts_top)        # Normal points upwards
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new([verts_btm[i], verts_btm[j], verts_top[j], verts_top[i]])

    uv_layer = bm.loops.layers.uv.verify()
    for face in bm.faces:
        for loop in face.loops:
            loop[uv_layer].uv = (loop.vert.co.x, loop.vert.co.y)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    if mat:
        obj.data.materials.append(mat)
    link_to_collection(obj, col)
    if parent:
        obj.parent = parent
    return obj


def create_extruded_polygon(
    name: str,
    poly_2d: list,
    z_bottom: float,
    z_top: float,
    mat: bpy.types.Material,
    col: bpy.types.Collection,
    parent: bpy.types.Object = None,
) -> bpy.types.Object:
    """Creates an extruded 3D slab from an arbitrary 2D polygon in cm with real-world planar UVs."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    verts_btm = [bm.verts.new((x * CM, y * CM, z_bottom)) for x, y in poly_2d]
    verts_top = [bm.verts.new((x * CM, y * CM, z_top)) for x, y in poly_2d]

    bm.faces.new(verts_btm[::-1])
    bm.faces.new(verts_top)
    n = len(poly_2d)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([verts_btm[i], verts_btm[j], verts_top[j], verts_top[i]])

    uv_layer = bm.loops.layers.uv.verify()
    for face in bm.faces:
        for loop in face.loops:
            loop[uv_layer].uv = (loop.vert.co.x, loop.vert.co.y)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    if mat:
        obj.data.materials.append(mat)
    link_to_collection(obj, col)
    if parent:
        obj.parent = parent
    return obj


def create_window_3d(
    name_prefix: str,
    idx: int,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    thickness: float,
    z_sill: float,
    z_top: float,
    pvc_mat: bpy.types.Material,
    glass_mat: bpy.types.Material,
    col: bpy.types.Collection,
    parent: bpy.types.Object = None,
):
    """
    Constructs an architectural window assembly with White uPVC frames,
    vertical mullions, and double-glazed insulated glass panes.
    """
    length = math.hypot(x2 - x1, y2 - y1)
    if length < 2.0:
        return
    dx, dy = (x2 - x1) / length, (y2 - y1) / length
    frame_t = FRAME_THICKNESS_CM

    # 1. White uPVC Bottom & Top horizontal frame sashes
    create_prism_from_quad(
        f"{name_prefix}_WinFrameBtm_{idx}",
        wall_quad(x1, y1, x2, y2, thickness + 1.0),
        z_sill,
        z_sill + frame_t * CM,
        pvc_mat,
        col,
        parent,
    )
    create_prism_from_quad(
        f"{name_prefix}_WinFrameTop_{idx}",
        wall_quad(x1, y1, x2, y2, thickness + 1.0),
        z_top - frame_t * CM,
        z_top,
        pvc_mat,
        col,
        parent,
    )

    # 2. White uPVC Vertical posts (ends + interior mullions every ~80 cm)
    num_panels = max(1, round(length / 80.0))
    for p in range(num_panels + 1):
        dist = (p / num_panels) * (length - frame_t)
        px1, py1 = x1 + dx * dist, y1 + dy * dist
        px2, py2 = px1 + dx * frame_t, py1 + dy * frame_t
        create_prism_from_quad(
            f"{name_prefix}_WinMullion_{idx}_{p}",
            wall_quad(px1, py1, px2, py2, thickness + 1.0),
            z_sill + frame_t * CM,
            z_top - frame_t * CM,
            pvc_mat,
            col,
            parent,
        )

    # 3. Operable sash frames & handles for opening segments (segment 0 next to wall is static, segments 1 & 2 opening)
    if num_panels >= 2:
        for p in range(num_panels):
            if p == 0 and num_panels == 3:
                continue  # static / fixed pane next to wall
            d_start = (p / num_panels) * (length - frame_t) + frame_t
            d_end = ((p + 1) / num_panels) * (length - frame_t)
            sash_t = 3.5
            sx1, sy1 = x1 + dx * d_start, y1 + dy * d_start
            sx2, sy2 = x1 + dx * d_end, y1 + dy * d_end

            create_prism_from_quad(
                f"{name_prefix}_WinSashBtm_{idx}_{p}",
                wall_quad(sx1, sy1, sx2, sy2, thickness + 1.5),
                z_sill + frame_t * CM,
                z_sill + (frame_t + sash_t) * CM,
                pvc_mat,
                col,
                parent,
            )
            create_prism_from_quad(
                f"{name_prefix}_WinSashTop_{idx}_{p}",
                wall_quad(sx1, sy1, sx2, sy2, thickness + 1.5),
                z_top - (frame_t + sash_t) * CM,
                z_top - frame_t * CM,
                pvc_mat,
                col,
                parent,
            )
            create_prism_from_quad(
                f"{name_prefix}_WinSashL_{idx}_{p}",
                wall_quad(sx1, sy1, sx1 + dx * sash_t, sy1 + dy * sash_t, thickness + 1.5),
                z_sill + (frame_t + sash_t) * CM,
                z_top - (frame_t + sash_t) * CM,
                pvc_mat,
                col,
                parent,
            )
            create_prism_from_quad(
                f"{name_prefix}_WinSashR_{idx}_{p}",
                wall_quad(sx2 - dx * sash_t, sy2 - dy * sash_t, sx2, sy2, thickness + 1.5),
                z_sill + (frame_t + sash_t) * CM,
                z_top - (frame_t + sash_t) * CM,
                pvc_mat,
                col,
                parent,
            )
            hx = sx2 - dx * (sash_t * 0.5)
            hy = sy2 - dy * (sash_t * 0.5)
            hz = (z_sill + z_top) * 0.5
            create_prism_from_quad(
                f"{name_prefix}_WinHandle_{idx}_{p}",
                wall_quad(hx - dx * 1.5, hy - dy * 1.5, hx + dx * 1.5, hy + dy * 1.5, thickness + 4.5),
                hz - 0.05,
                hz + 0.05,
                pvc_mat,
                col,
                parent,
            )

    # 4. Double-glazed architectural glass pane
    create_prism_from_quad(
        f"{name_prefix}_WinGlass_{idx}",
        wall_quad(x1, y1, x2, y2, 2.5),
        z_sill + frame_t * CM,
        z_top - frame_t * CM,
        glass_mat,
        col,
        parent,
    )


def _add_box_to_bmesh(
    bm: bmesh.types.BMesh,
    hx: float, hy: float,
    ux: float, uy: float,
    nx: float, ny: float,
    s0: float, s1: float,
    t0: float, t1: float,
    bz0: float, bz1: float,
    mat_idx: int = 0,
):
    """Adds an oriented 3D cuboid box to a bmesh using door-leaf local coordinates."""
    pts_2d = [
        (hx + ux * s0 + nx * t0, hy + uy * s0 + ny * t0),
        (hx + ux * s1 + nx * t0, hy + uy * s1 + ny * t0),
        (hx + ux * s1 + nx * t1, hy + uy * s1 + ny * t1),
        (hx + ux * s0 + nx * t1, hy + uy * s0 + ny * t1),
    ]
    verts_btm = [bm.verts.new((x * CM, y * CM, bz0)) for x, y in pts_2d]
    verts_top = [bm.verts.new((x * CM, y * CM, bz1)) for x, y in pts_2d]

    f_btm = bm.faces.new(verts_btm[::-1])
    f_btm.material_index = mat_idx
    f_top = bm.faces.new(verts_top)
    f_top.material_index = mat_idx

    for i in range(4):
        j = (i + 1) % 4
        f_side = bm.faces.new([verts_btm[i], verts_btm[j], verts_top[j], verts_top[i]])
        f_side.material_index = mat_idx


def create_8panel_interior_door_leaf(
    name: str,
    hx: float, hy: float,
    lx: float, ly: float,
    z0: float, z1: float,
    wood_mat: bpy.types.Material,
    handle_mat: bpy.types.Material,
    col: bpy.types.Collection,
    parent: bpy.types.Object = None,
) -> bpy.types.Object:
    """
    Constructs an 8-panel traditional solid wood door leaf precisely matching the reference photo.
    Features:
    - 2 columns x 4 rows of recessed/raised molded wood panels
    - Perimeter stiles, bottom kick rail, top rail, and 3 cross rails
    - Raised panel centers with profiled border reveals on both front and rear faces
    - Brushed metal lever handle and vertical escutcheon backplate at ergonomic height (~1.00 m)
    """
    dx, dy = lx - hx, ly - hy
    W = math.hypot(dx, dy)
    if W < 1e-3:
        return None
    ux, uy = dx / W, dy / W
    nx, ny = -uy, ux

    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    # Base inner core slab (recessed field web)
    _add_box_to_bmesh(bm, hx, hy, ux, uy, nx, ny, 0.0, W, -1.0, 1.0, z0, z1, mat_idx=0)

    # Architectural framing dimensions (in cm and meters)
    w_stile = 10.0
    w_mullion = 6.0
    h_btm = 18.0 * CM
    h_top = 12.0 * CM
    h_cross = 6.0 * CM

    H_tot = z1 - z0
    H_panels = H_tot - h_btm - h_top - 3.0 * h_cross
    h_panel = H_panels / 4.0

    col_spans = [
        (w_stile, W / 2.0 - w_mullion / 2.0),
        (W / 2.0 + w_mullion / 2.0, W - w_stile),
    ]

    # Build stiles, rails, and raised panel fields on front (+1 to +2 cm) and rear (-2 to -1 cm)
    for side_t0, side_t1, sign in [(1.0, 2.0, 1.0), (-2.0, -1.0, -1.0)]:
        # Left & Right vertical stiles
        _add_box_to_bmesh(bm, hx, hy, ux, uy, nx, ny, 0.0, w_stile, side_t0, side_t1, z0, z1, mat_idx=0)
        _add_box_to_bmesh(bm, hx, hy, ux, uy, nx, ny, W - w_stile, W, side_t0, side_t1, z0, z1, mat_idx=0)

        # Center vertical mullion
        _add_box_to_bmesh(
            bm, hx, hy, ux, uy, nx, ny,
            W / 2.0 - w_mullion / 2.0, W / 2.0 + w_mullion / 2.0,
            side_t0, side_t1, z0 + h_btm, z1 - h_top, mat_idx=0
        )

        # Bottom kick rail & Top rail
        _add_box_to_bmesh(bm, hx, hy, ux, uy, nx, ny, w_stile, W - w_stile, side_t0, side_t1, z0, z0 + h_btm, mat_idx=0)
        _add_box_to_bmesh(bm, hx, hy, ux, uy, nx, ny, w_stile, W - w_stile, side_t0, side_t1, z1 - h_top, z1, mat_idx=0)

        # 3 intermediate cross rails dividing the 4 panel tiers
        for r in range(1, 4):
            rz0 = z0 + h_btm + r * h_panel + (r - 1) * h_cross
            _add_box_to_bmesh(bm, hx, hy, ux, uy, nx, ny, w_stile, W - w_stile, side_t0, side_t1, rz0, rz0 + h_cross, mat_idx=0)

        # 8 Raised molded panel fields (2 columns x 4 rows)
        for cs0, cs1 in col_spans:
            for r in range(4):
                pz0 = z0 + h_btm + r * (h_panel + h_cross)
                pz1 = pz0 + h_panel
                # Molded field inset with subtle bevel reveal
                _add_box_to_bmesh(
                    bm, hx, hy, ux, uy, nx, ny,
                    cs0 + 1.2, cs1 - 1.2,
                    side_t0, side_t0 + 0.45 * sign,
                    pz0 + 0.012, pz1 - 0.012,
                    mat_idx=0,
                )

        # Brushed silver hardware: Escutcheon plate & lever handle at z = 1.00 m
        hs0, hs1 = W - 7.5, W - 4.5
        # Backplate
        _add_box_to_bmesh(
            bm, hx, hy, ux, uy, nx, ny,
            hs0, hs1,
            side_t1, side_t1 + 0.5 * sign,
            0.92, 1.08,
            mat_idx=1,
        )
        # Handle spindle & horizontal lever arm
        _add_box_to_bmesh(
            bm, hx, hy, ux, uy, nx, ny,
            hs0 + 0.5, hs1 - 0.5,
            side_t1 + 0.5 * sign, side_t1 + 5.0 * sign,
            0.99, 1.01,
            mat_idx=1,
        )
        _add_box_to_bmesh(
            bm, hx, hy, ux, uy, nx, ny,
            hs0 - 8.5, hs1 - 0.5,
            side_t1 + 4.0 * sign, side_t1 + 5.0 * sign,
            0.985, 1.015,
            mat_idx=1,
        )

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    if wood_mat:
        obj.data.materials.append(wood_mat)
    if handle_mat:
        obj.data.materials.append(handle_mat)

    link_to_collection(obj, col)
    if parent:
        obj.parent = parent
    return obj


def create_exterior_pvc_door_leaf(
    name: str,
    hx: float, hy: float,
    lx: float, ly: float,
    z0: float, z1: float,
    pvc_mat: bpy.types.Material,
    glass_mat: bpy.types.Material,
    col: bpy.types.Collection,
    parent: bpy.types.Object = None,
) -> bpy.types.Object:
    """Constructs a modern White uPVC balcony door leaf with insulated double-glazing."""
    dx, dy = lx - hx, ly - hy
    W = math.hypot(dx, dy)
    if W < 1e-3:
        return None
    ux, uy = dx / W, dy / W
    nx, ny = -uy, ux

    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    w_frame = 9.0
    h_btm = 35.0 * CM
    h_top = 10.0 * CM

    # Outer White uPVC frame profile
    _add_box_to_bmesh(bm, hx, hy, ux, uy, nx, ny, 0.0, w_frame, -2.25, 2.25, z0, z1, mat_idx=0)
    _add_box_to_bmesh(bm, hx, hy, ux, uy, nx, ny, W - w_frame, W, -2.25, 2.25, z0, z1, mat_idx=0)
    _add_box_to_bmesh(bm, hx, hy, ux, uy, nx, ny, w_frame, W - w_frame, -2.25, 2.25, z0, z0 + h_btm, mat_idx=0)
    _add_box_to_bmesh(bm, hx, hy, ux, uy, nx, ny, w_frame, W - w_frame, -2.25, 2.25, z1 - h_top, z1, mat_idx=0)

    # Double-glazed architectural glass insert
    _add_box_to_bmesh(
        bm, hx, hy, ux, uy, nx, ny,
        w_frame, W - w_frame, -1.2, 1.2,
        z0 + h_btm, z1 - h_top,
        mat_idx=1,
    )

    # White uPVC lever handle at z = 1.00 m
    for sign in (1.0, -1.0):
        _add_box_to_bmesh(
            bm, hx, hy, ux, uy, nx, ny,
            W - 7.0, W - 4.5,
            2.25 * sign, (2.25 + 4.5) * sign,
            0.99, 1.01,
            mat_idx=0,
        )
        _add_box_to_bmesh(
            bm, hx, hy, ux, uy, nx, ny,
            W - 15.0, W - 4.5,
            (2.25 + 3.5) * sign, (2.25 + 4.5) * sign,
            0.985, 1.015,
            mat_idx=0,
        )

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    if pvc_mat:
        obj.data.materials.append(pvc_mat)
    if glass_mat:
        obj.data.materials.append(glass_mat)

    link_to_collection(obj, col)
    if parent:
        obj.parent = parent
    return obj


def create_door_3d(
    name_prefix: str,
    idx: int,
    hx: float,
    hy: float,
    x2: float,
    y2: float,
    radius: float,
    start_angle: float,
    end_angle: float,
    wall_angle: float,
    thickness: float,
    is_exterior: bool,
    pvc_mat: bpy.types.Material,
    wood_mat: bpy.types.Material,
    door_frame_mat: bpy.types.Material,
    handle_mat: bpy.types.Material = None,
    glass_mat: bpy.types.Material = None,
    col: bpy.types.Collection = None,
    parent: bpy.types.Object = None,
):
    """
    Constructs an architectural door assembly.
    Exterior doors to balconies/terraces use White uPVC profiles and glazed panes.
    Interior doors use traditional 8-panel solid wood leaves and brushed metal handles.
    """
    # Calculate open angle swing
    open_angle = (
        end_angle
        if abs(end_angle - wall_angle) > abs(start_angle - wall_angle)
        else start_angle
    )
    display_angle = wall_angle + (open_angle - wall_angle) * DOOR_OPEN_RATIO
    rad_disp = math.radians(display_angle)

    lx = hx + radius * math.cos(rad_disp)
    ly = hy + radius * math.sin(rad_disp)

    # Frame head material: White PVC for exterior balcony doors, frame mat for interior
    head_mat = pvc_mat if is_exterior else door_frame_mat
    create_prism_from_quad(
        f"{name_prefix}_DoorHead_{idx}",
        wall_quad(hx, hy, x2, y2, thickness + 1.5),
        DOOR_HEIGHT - 0.03,
        DOOR_HEIGHT,
        head_mat,
        col,
        parent,
    )

    # Door leaf: 8-Panel traditional wood leaf for interior; Glazed uPVC for exterior
    if is_exterior:
        create_exterior_pvc_door_leaf(
            f"{name_prefix}_DoorLeaf_{idx}",
            hx, hy, lx, ly,
            0.01, DOOR_HEIGHT - 0.03,
            pvc_mat, glass_mat,
            col, parent,
        )
    else:
        create_8panel_interior_door_leaf(
            f"{name_prefix}_DoorLeaf_{idx}",
            hx, hy, lx, ly,
            0.01, DOOR_HEIGHT - 0.03,
            wood_mat, handle_mat,
            col, parent,
        )

    # 2D/3D floor swing arc curve
    curve = bpy.data.curves.new(f"{name_prefix}_DoorArc_{idx}", type="CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = 0.008
    spline = curve.splines.new("POLY")
    steps = 18
    t1, t2 = min(start_angle, end_angle), max(start_angle, end_angle)
    spline.points.add(steps)
    for s in range(steps + 1):
        ang = math.radians(t1 + (t2 - t1) * (s / steps))
        px = (hx + radius * math.cos(ang)) * CM
        py = (hy + radius * math.sin(ang)) * CM
        spline.points[s].co = (px, py, 0.005, 1.0)

    arc_obj = bpy.data.objects.new(f"{name_prefix}_DoorArc_{idx}", curve)
    arc_mat = pvc_mat if is_exterior else door_frame_mat
    arc_obj.data.materials.append(arc_mat)
    link_to_collection(arc_obj, col)
    if parent:
        arc_obj.parent = parent


def create_terrace_parapet_and_coping(
    name_prefix: str,
    edge_key: str,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    wall_mat: bpy.types.Material,
    coping_mat: bpy.types.Material,
    col: bpy.types.Collection,
    parent: bpy.types.Object = None,
):
    """
    Constructs a solid masonry terrace parapet wall using the EXACT SAME material as the walls,
    topped with an architectural stone terrace coping featuring an overhang.
    No glass is used.
    """
    # 1. Solid Parapet Wall (Matching Wall Material)
    create_prism_from_quad(
        f"{name_prefix}_ParapetWall_{edge_key}",
        wall_quad(x1, y1, x2, y2, TERRACE_WALL_THICKNESS),
        0.0,
        TERRACE_PARAPET_HEIGHT,
        wall_mat,
        col,
        parent,
    )

    # 2. Terrace Coping (Architectural stone cap with overhang)
    create_prism_from_quad(
        f"{name_prefix}_TerraceCoping_{edge_key}",
        wall_quad(x1, y1, x2, y2, TERRACE_COPING_WIDTH),
        TERRACE_PARAPET_HEIGHT,
        TERRACE_TOTAL_HEIGHT,
        coping_mat,
        col,
        parent,
    )


def create_round_cylinder_3d(
    name: str,
    p1: tuple,
    p2: tuple,
    radius_cm: float,
    mat: bpy.types.Material,
    col: bpy.types.Collection,
    parent: bpy.types.Object = None,
    segments: int = 16,
) -> bpy.types.Object:
    """Creates a smooth round cylindrical aluminum tube/post between two (x_cm, y_cm, z_m) points."""
    v1 = Vector((p1[0] * CM, p1[1] * CM, p1[2]))
    v2 = Vector((p2[0] * CM, p2[1] * CM, p2[2]))
    diff = v2 - v1
    length = diff.length
    if length < 1e-5:
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
    if parent:
        obj.parent = parent
    link_to_collection(obj, col)
    return obj


def create_stairs_3d(
    name_prefix: str,
    x: float,
    y: float,
    w: float,
    h: float,
    num_treads: int,
    direction: str,
    label: str,
    stair_mat: bpy.types.Material,
    text_mat: bpy.types.Material,
    col: bpy.types.Collection,
    parent: bpy.types.Object = None,
):
    """
    Constructs 3D stairs with custom tread/riser material.
    """
    step_w = w / float(num_treads)
    step_h = WALL_HEIGHT / float(num_treads)

    for i in range(num_treads):
        sx = x + i * step_w
        tread_idx = i + 1 if direction == "right" else (num_treads - i)
        z_top = tread_idx * step_h
        z_btm = max(0.0, z_top - step_h - 0.08)

        quad = [(sx, y), (sx + step_w, y), (sx + step_w, y + h), (sx, y + h)]
        create_prism_from_quad(
            f"{name_prefix}_Step_{i+1}",
            quad,
            z_btm,
            z_top,
            stair_mat,
            col,
            parent,
        )

    if label:
        create_text_label_3d(
            name_prefix,
            label,
            x + w / 2.0,
            y + h / 2.0,
            z=WALL_HEIGHT * 0.55,
            size=14.0,
            mat=text_mat,
            col=col,
            parent=parent,
        )


def create_curved_stairs_with_railing_3d(
    name_prefix: str,
    x: float,
    y: float,
    w: float,
    h: float,
    num_treads: int,
    direction: str,
    label: str,
    stair_mat: bpy.types.Material,
    railing_mat: bpy.types.Material,
    text_mat: bpy.types.Material,
    has_railing: bool = True,
    col: bpy.types.Collection = None,
    parent: bpy.types.Object = None,
):
    """
    Constructs 3D main stairs ascending from the lower landing (next to the balcony door)
    to the upper landing (in front of the attic door) with symmetrical curves at BOTH ends:
    1. Bottom curved / round winder steps 1..5 in corner [15, 100], y in [120, 205],
       fanning through 90 degrees around pivot (100, 205) starting at landing level (z=0.175 m)
       up to z=0.875 m.
    2. Middle straight steps 6..11 running along x from 100 to 265, y in [120, 205],
       ascending from z=1.05 m up to z=1.925 m.
    3. Top curved / round winder steps 12..16 in corner [265, 350], y in [120, 205],
       fanning through 90 degrees around pivot (265, 205) ascending from z=2.10 m
       up to z=2.80 m (stepping directly onto the Floor 4 landing).
    4. Sleek round aluminum railing (central newel posts, intermediate balusters,
       continuous sloping top handrail, round safety rails).
    """
    num_curved_btm = 5
    num_straight = 6
    num_curved_top = 5
    total_steps = num_curved_btm + num_straight + num_curved_top  # 16 steps
    step_h = WALL_HEIGHT / float(total_steps)  # 0.175 m per rise

    pivot_btm_x = 100.0
    pivot_top_x = 265.0
    pivot_y = y + h  # 205.0 cm
    radius = 85.0

    # 1. Bottom Curved Section: Steps 1..5 starting from the lower landing next to balcony door
    # Curves through 90 deg around pivot (100, 205) from theta = pi (180 deg) to 1.5*pi (270 deg)
    for k in range(num_curved_btm):
        z_top = (k + 1) * step_h
        z_btm = max(0.0, z_top - step_h - 0.08)

        ang_start = math.pi + k * (0.5 * math.pi / float(num_curved_btm))
        ang_end = math.pi + (k + 1) * (0.5 * math.pi / float(num_curved_btm))

        arc_points = []
        subdivisions = 4
        for s in range(subdivisions + 1):
            t = s / float(subdivisions)
            ang = ang_start + t * (ang_end - ang_start)
            arc_points.append((pivot_btm_x + radius * math.cos(ang), pivot_y + radius * math.sin(ang)))

        poly_2d = [(pivot_btm_x, pivot_y)] + arc_points
        create_extruded_polygon(
            f"{name_prefix}_Btm_Curved_Step_{k + 1}",
            poly_2d,
            z_btm,
            z_top,
            stair_mat,
            col,
            parent,
        )

    # 2. Middle Straight Section: Steps 6..11 running along x from 100 to 265, y in [120, 205]
    straight_w = (pivot_top_x - pivot_btm_x) / float(num_straight)  # 165 / 6 = 27.5 cm
    for i in range(num_straight):
        x_left = pivot_btm_x + i * straight_w
        x_right = pivot_btm_x + (i + 1) * straight_w
        z_top = (num_curved_btm + i + 1) * step_h
        z_btm = max(0.0, z_top - step_h - 0.08)

        quad = [(x_left, y), (x_right, y), (x_right, y + h), (x_left, y + h)]
        create_prism_from_quad(
            f"{name_prefix}_Straight_Step_{num_curved_btm + i + 1}",
            quad,
            z_btm,
            z_top,
            stair_mat,
            col,
            parent,
        )

    # 3. Top Curved Section: Steps 12..16 curving into the upper landing in front of the attic door
    # Curves through 90 deg around pivot (265, 205) from theta = 1.5*pi (270 deg) to 2.0*pi (360 deg)
    for m in range(num_curved_top):
        z_top = (num_curved_btm + num_straight + m + 1) * step_h
        z_btm = max(0.0, z_top - step_h - 0.08)

        ang_start = 1.5 * math.pi + m * (0.5 * math.pi / float(num_curved_top))
        ang_end = 1.5 * math.pi + (m + 1) * (0.5 * math.pi / float(num_curved_top))

        arc_points = []
        subdivisions = 4
        for s in range(subdivisions + 1):
            t = s / float(subdivisions)
            ang = ang_start + t * (ang_end - ang_start)
            arc_points.append((pivot_top_x + radius * math.cos(ang), pivot_y + radius * math.sin(ang)))

        poly_2d = [(pivot_top_x, pivot_y)] + arc_points
        create_extruded_polygon(
            f"{name_prefix}_Top_Curved_Step_{num_curved_btm + num_straight + m + 1}",
            poly_2d,
            z_btm,
            z_top,
            stair_mat,
            col,
            parent,
        )

    # 4. Round Aluminum Railing along open inner flight (y = 203.5 cm, from x = 100 to 265)
    if has_railing and railing_mat:
        railing_y = y + h - 1.5  # 203.5 cm
        handrail_height = 0.90   # 0.90 m above tread line

        z_btm_rail = num_curved_btm * step_h
        z_top_rail = (num_curved_btm + num_straight) * step_h

        # Central / Corner Round Newel Post at bottom turn (100.0, 203.5)
        create_round_cylinder_3d(
            f"{name_prefix}_Alu_Btm_Corner_Newel_Post",
            (pivot_btm_x, railing_y, 0.0),
            (pivot_btm_x, railing_y, z_btm_rail + handrail_height),
            radius_cm=2.5,  # 5.0 cm diameter
            mat=railing_mat,
            col=col,
            parent=parent,
        )

        # Central / Corner Round Newel Post at top turn (265.0, 203.5)
        create_round_cylinder_3d(
            f"{name_prefix}_Alu_Top_Corner_Newel_Post",
            (pivot_top_x, railing_y, z_top_rail),
            (pivot_top_x, railing_y, WALL_HEIGHT + handrail_height),
            radius_cm=2.5,  # 5.0 cm diameter
            mat=railing_mat,
            col=col,
            parent=parent,
        )

        # Intermediate Round Baluster Posts along straight run (every 2 steps)
        post_indices = [1, 3]
        for p_idx in post_indices:
            px = pivot_btm_x + (p_idx + 0.5) * straight_w
            pz_base = (num_curved_btm + p_idx + 1) * step_h
            pz_top = pz_base + handrail_height
            create_round_cylinder_3d(
                f"{name_prefix}_Alu_Post_{p_idx+1}",
                (px, railing_y, pz_base),
                (px, railing_y, pz_top),
                radius_cm=1.6,  # 3.2 cm diameter
                mat=railing_mat,
                col=col,
                parent=parent,
            )

        # Round Sloping Top Handrail (4.5 cm diameter pipe)
        p_start = (pivot_btm_x, railing_y, z_btm_rail + handrail_height)
        p_end = (pivot_top_x, railing_y, z_top_rail + handrail_height)
        create_round_cylinder_3d(
            f"{name_prefix}_Alu_Handrail_Top",
            p_start,
            p_end,
            radius_cm=2.25,  # 4.5 cm diameter
            mat=railing_mat,
            col=col,
            parent=parent,
        )

        # Intermediate Round Safety Rails (2 parallel round tubes, 2.0 cm diameter)
        for r_offset in (0.30, 0.60):
            p1 = (pivot_btm_x, railing_y, z_btm_rail + r_offset)
            p2 = (pivot_top_x, railing_y, z_top_rail + r_offset)
            create_round_cylinder_3d(
                f"{name_prefix}_Alu_MidRail_{int(r_offset*100)}",
                p1,
                p2,
                radius_cm=1.0,  # 2.0 cm diameter
                mat=railing_mat,
                col=col,
                parent=parent,
            )

    if label:
        create_text_label_3d(
            name_prefix,
            label,
            182.5,
            y + h * 0.5,
            z=WALL_HEIGHT * 0.55,
            size=14.0,
            mat=text_mat,
            col=col,
            parent=parent,
        )


def create_text_label_3d(
    name_prefix: str,
    text_str: str,
    x: float,
    y: float,
    z: float = 0.02,
    size: float = 22.0,
    rotation_z: float = 0.0,
    mat: bpy.types.Material = None,
    col: bpy.types.Collection = None,
    parent: bpy.types.Object = None,
) -> bpy.types.Object:
    """Creates an extruded 3D font text label for room designations and dimensions."""
    curve = bpy.data.curves.new(name=f"Text_{text_str}", type="FONT")
    curve.body = text_str
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.size = size * CM
    curve.extrude = 0.008

    obj = bpy.data.objects.new(f"{name_prefix}_Label_{text_str}", curve)
    obj.location = (x * CM, y * CM, z)
    obj.rotation_euler = (0.0, 0.0, math.radians(rotation_z))
    if mat:
        obj.data.materials.append(mat)
    if col:
        link_to_collection(obj, col)
    if parent:
        obj.parent = parent
    return obj
