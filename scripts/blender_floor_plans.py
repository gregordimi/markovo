import bpy
import bmesh
import math
from mathutils import Vector, Matrix

# ==============================================================================
# CONFIGURATION & ARCHITECTURAL CONSTANTS
# ==============================================================================
CM = 0.01  # Convert centimeters to Blender meters (100 cm = 1.0 m)

# Set STACK_FLOORS = True to stack Floor 4 directly on top of Floor 3 in 3D,
# or False to place them side-by-side (matching the 2-panel matplotlib plot).
STACK_FLOORS = False

WALL_HEIGHT = 280.0 * CM      # 2.80 m ceiling height
SLAB_THICK = 15.0 * CM        # 0.15 m floor slab thickness
DOOR_HEIGHT = 210.0 * CM      # 2.10 m door height
WIN_SILL = 90.0 * CM          # 0.90 m window sill height
WIN_TOP = 210.0 * CM          # 2.10 m window head height
RAILING_HEIGHT = 100.0 * CM   # 1.00 m balcony railing height
DOOR_OPEN_RATIO = 0.45        # How far doors are swung open in 3D (0.0=closed, 1.0=90 deg)


# ==============================================================================
# SCENE CLEANUP & COLLECTION HELPERS
# ==============================================================================
def clear_scene():
    """Removes all existing objects, meshes, materials, and collections."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    for block_list in (
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.curves,
        bpy.data.lights,
        bpy.data.cameras,
        bpy.data.collections,
    ):
        for block in list(block_list):
            block_list.remove(block)


def get_or_create_collection(name, parent=None):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    if parent is None:
        bpy.context.scene.collection.children.link(col)
    else:
        parent.children.link(col)
    return col


def link_to_collection(obj, col):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)


# ==============================================================================
# MATERIAL CREATION (Compatible with Blender 3.x, 4.x, and 5.x)
# ==============================================================================
def make_material(name, rgba, roughness=0.5, metallic=0.0, transmission=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.diffuse_color = rgba

    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = rgba[3]
        if transmission > 0:
            if "Transmission Weight" in bsdf.inputs:
                bsdf.inputs["Transmission Weight"].default_value = transmission
            elif "Transmission" in bsdf.inputs:
                bsdf.inputs["Transmission"].default_value = transmission

    if rgba[3] < 1.0:
        if hasattr(mat, "blend_method"):
            mat.blend_method = "BLEND"
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"

    return mat


def create_materials():
    return {
        "wall": make_material("Wall_Mat", (0.29, 0.29, 0.29, 1.0), roughness=0.7),
        "wall_cap": make_material("Wall_Cap_Mat", (0.12, 0.12, 0.12, 1.0), roughness=0.6),
        "slab": make_material("Floor_Slab_Mat", (0.92, 0.91, 0.88, 1.0), roughness=0.6),
        "balcony": make_material("Balcony_Mat", (0.82, 0.82, 0.82, 1.0), roughness=0.7),
        "void": make_material("Roof_Void_Mat", (0.75, 0.75, 0.77, 1.0), roughness=0.85),
        "shaft": make_material("Shaft_Mat", (0.85, 0.85, 0.85, 1.0), roughness=0.5),
        "glass": make_material("Window_Glass_Mat", (0.0, 0.55, 0.55, 0.35), roughness=0.08, transmission=0.85),
        "win_frame": make_material("Window_Frame_Mat", (0.0, 0.38, 0.38, 1.0), roughness=0.3, metallic=0.4),
        "door": make_material("Door_Mat", (0.45, 0.32, 0.22, 1.0), roughness=0.45),
        "door_frame": make_material("Door_Frame_Mat", (0.18, 0.18, 0.18, 1.0), roughness=0.4),
        "stairs": make_material("Stairs_Mat", (0.78, 0.76, 0.72, 1.0), roughness=0.55),
        "railing": make_material("Railing_Mat", (0.20, 0.20, 0.22, 1.0), roughness=0.3, metallic=0.7),
        "text": make_material("Text_Mat", (0.08, 0.08, 0.08, 1.0), roughness=0.4),
        "dim": make_material("Dim_Mat", (0.0, 0.33, 0.65, 1.0), roughness=0.4),
    }


# ==============================================================================
# GEOMETRY PRIMITIVES
# ==============================================================================
def create_prism_from_quad(name, corners_2d, z_bottom, z_top, mat, col, parent=None):
    """Creates a 3D prism mesh from 4 (x, y) corners in cm and Z bounds in meters."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    verts_btm = [bm.verts.new((x * CM, y * CM, z_bottom)) for x, y in corners_2d]
    verts_top = [bm.verts.new((x * CM, y * CM, z_top)) for x, y in corners_2d]

    bm.faces.new(verts_btm[::-1])
    bm.faces.new(verts_top)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new([verts_btm[i], verts_btm[j], verts_top[j], verts_top[i]])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    link_to_collection(obj, col)
    if parent:
        obj.parent = parent
    return obj


def create_extruded_polygon(name, poly_2d, z_bottom, z_top, mat, col, parent=None):
    """Creates an extruded 3D slab from an arbitrary 2D polygon in cm."""
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

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    link_to_collection(obj, col)
    if parent:
        obj.parent = parent
    return obj


def wall_quad(x1, y1, x2, y2, thickness):
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    nx, ny = -uy * (thickness / 2.0), ux * (thickness / 2.0)
    return [
        (x1 + nx, y1 + ny),
        (x2 + nx, y2 + ny),
        (x2 - nx, y2 - ny),
        (x1 - nx, y1 - ny),
    ]


# ==============================================================================
# FLOOR BUILDER CLASS (Collects Walls, Windows, Doors & Cuts Openings Cleanly)
# ==============================================================================
class FloorPlanBuilder:
    def __init__(self, name, mats, root_offset=(0.0, 0.0, 0.0)):
        self.name = name
        self.mats = mats
        self.col = get_or_create_collection(name)
        self.root = bpy.data.objects.new(f"{name}_Root", None)
        self.root.empty_display_type = "PLAIN_AXES"
        self.root.empty_display_size = 0.5
        self.root.location = Vector(root_offset)
        link_to_collection(self.root, self.col)

        self.walls = []
        self.windows = []
        self.doors = []

    def add_wall(self, x1, y1, x2, y2, thickness=15.0):
        self.walls.append((float(x1), float(y1), float(x2), float(y2), float(thickness)))

    def add_window(self, x1, y1, x2, y2, thickness=15.0, label=None):
        self.windows.append({
            "x1": float(x1), "y1": float(y1),
            "x2": float(x2), "y2": float(y2),
            "thickness": float(thickness),
            "label": label,
        })

    def add_door(self, hx, hy, radius, start_angle, end_angle, wall_angle, thickness=15.0, is_exterior=False):
        rad_w = math.radians(wall_angle)
        x2 = hx + radius * math.cos(rad_w)
        y2 = hy + radius * math.sin(rad_w)
        self.doors.append({
            "hx": float(hx), "hy": float(hy),
            "x2": float(x2), "y2": float(y2),
            "radius": float(radius),
            "start_angle": float(start_angle),
            "end_angle": float(end_angle),
            "wall_angle": float(wall_angle),
            "thickness": float(thickness),
            "is_exterior": is_exterior,
        })

    def add_slab_polygon(self, label, poly_2d, z_bottom=-SLAB_THICK, z_top=0.0, mat_key="slab"):
        create_extruded_polygon(
            f"{self.name}_{label}",
            poly_2d,
            z_bottom,
            z_top,
            self.mats[mat_key],
            self.col,
            self.root,
        )

    def add_balcony(self, label, x, y, w, h, open_edges=("N", "E", "S", "W")):
        poly = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        create_extruded_polygon(
            f"{self.name}_{label}_Slab",
            poly,
            -SLAB_THICK,
            0.0,
            self.mats["balcony"],
            self.col,
            self.root,
        )

        # Add balcony railings along exposed perimeter edges
        edge_map = {
            "S": (x, y, x + w, y),
            "E": (x + w, y, x + w, y + h),
            "N": (x + w, y + h, x, y + h),
            "W": (x, y + h, x, y),
        }
        for edge_key in open_edges:
            ex1, ey1, ex2, ey2 = edge_map[edge_key]
            # Top handrail bar
            create_prism_from_quad(
                f"{self.name}_{label}_RailTop_{edge_key}",
                wall_quad(ex1, ey1, ex2, ey2, 5.0),
                RAILING_HEIGHT - 0.04,
                RAILING_HEIGHT,
                self.mats["railing"],
                self.col,
                self.root,
            )
            # Glass balustrade panel
            create_prism_from_quad(
                f"{self.name}_{label}_RailGlass_{edge_key}",
                wall_quad(ex1, ey1, ex2, ey2, 2.0),
                0.05,
                RAILING_HEIGHT - 0.04,
                self.mats["glass"],
                self.col,
                self.root,
            )

    def add_stairs(self, x, y, w, h, num_treads=10, direction="right", label="STAIRS"):
        step_w = w / float(num_treads)
        step_h = WALL_HEIGHT / float(num_treads)

        for i in range(num_treads):
            sx = x + i * step_w
            tread_idx = i + 1 if direction == "right" else (num_treads - i)
            z_top = tread_idx * step_h
            z_btm = max(0.0, z_top - step_h - 0.08)

            quad = [(sx, y), (sx + step_w, y), (sx + step_w, y + h), (sx, y + h)]
            create_prism_from_quad(
                f"{self.name}_{label}_Step_{i+1}",
                quad,
                z_btm,
                z_top,
                self.mats["stairs"],
                self.col,
                self.root,
            )

        if label:
            self.add_text_label(label, x + w / 2.0, y + h / 2.0, z=WALL_HEIGHT * 0.55, size=14.0)

    def add_text_label(self, text_str, x, y, z=0.02, size=22.0, rotation_z=0.0, mat_key="text"):
        curve = bpy.data.curves.new(name=f"Text_{text_str}", type="FONT")
        curve.body = text_str
        curve.align_x = "CENTER"
        curve.align_y = "CENTER"
        curve.size = size * CM
        curve.extrude = 0.008

        obj = bpy.data.objects.new(f"{self.name}_Label_{text_str}", curve)
        obj.location = (x * CM, y * CM, z)
        obj.rotation_euler = (0.0, 0.0, math.radians(rotation_z))
        obj.data.materials.append(self.mats[mat_key])
        link_to_collection(obj, self.col)
        obj.parent = self.root
        return obj

    def _build_3d_window_segment(self, idx, x1, y1, x2, y2, thickness, z0, z1):
        """Builds a 3D window frame, mullions, and double-glazed glass pane."""
        length = math.hypot(x2 - x1, y2 - y1)
        if length < 2.0:
            return
        dx, dy = (x2 - x1) / length, (y2 - y1) / length
        frame_t = 4.0  # 4 cm frame thickness

        # Bottom & Top horizontal frame bars
        create_prism_from_quad(
            f"{self.name}_WinFrameBtm_{idx}",
            wall_quad(x1, y1, x2, y2, thickness + 1.0),
            z0, z0 + frame_t * CM,
            self.mats["win_frame"], self.col, self.root,
        )
        create_prism_from_quad(
            f"{self.name}_WinFrameTop_{idx}",
            wall_quad(x1, y1, x2, y2, thickness + 1.0),
            z1 - frame_t * CM, z1,
            self.mats["win_frame"], self.col, self.root,
        )

        # Vertical posts (ends + interior mullions every ~80 cm)
        num_panels = max(1, round(length / 80.0))
        for p in range(num_panels + 1):
            dist = (p / num_panels) * (length - frame_t)
            px1, py1 = x1 + dx * dist, y1 + dy * dist
            px2, py2 = px1 + dx * frame_t, py1 + dy * frame_t
            create_prism_from_quad(
                f"{self.name}_WinMullion_{idx}_{p}",
                wall_quad(px1, py1, px2, py2, thickness + 1.0),
                z0 + frame_t * CM, z1 - frame_t * CM,
                self.mats["win_frame"], self.col, self.root,
            )

        # Glass pane
        create_prism_from_quad(
            f"{self.name}_WinGlass_{idx}",
            wall_quad(x1, y1, x2, y2, 2.5),
            z0 + frame_t * CM, z1 - frame_t * CM,
            self.mats["glass"], self.col, self.root,
        )

    def _build_3d_door(self, idx, d):
        """Builds a 3D door frame, partially open door leaf, and floor swing arc."""
        hx, hy = d["hx"], d["hy"]
        x2, y2 = d["x2"], d["y2"]
        radius = d["radius"]
        thickness = d["thickness"]
        wall_angle = d["wall_angle"]
        start_angle, end_angle = d["start_angle"], d["end_angle"]

        # Determine open angle from matplotlib logic
        open_angle = (
            end_angle
            if abs(end_angle - wall_angle) > abs(start_angle - wall_angle)
            else start_angle
        )
        # Partially open the 3D door leaf so both door and opening are clear
        display_angle = wall_angle + (open_angle - wall_angle) * DOOR_OPEN_RATIO
        rad_disp = math.radians(display_angle)

        lx = hx + radius * math.cos(rad_disp)
        ly = hy + radius * math.sin(rad_disp)

        # Door frame head bar
        create_prism_from_quad(
            f"{self.name}_DoorHead_{idx}",
            wall_quad(hx, hy, x2, y2, thickness + 1.5),
            DOOR_HEIGHT - 0.03, DOOR_HEIGHT,
            self.mats["door_frame"], self.col, self.root,
        )

        # Door leaf (glazed panel if exterior balcony door, solid wood if interior)
        leaf_mat = self.mats["win_frame"] if d["is_exterior"] else self.mats["door"]
        create_prism_from_quad(
            f"{self.name}_DoorLeaf_{idx}",
            wall_quad(hx, hy, lx, ly, 4.0),
            0.01, DOOR_HEIGHT - 0.03,
            leaf_mat, self.col, self.root,
        )

        # Floor swing arc curve
        curve = bpy.data.curves.new(f"{self.name}_DoorArc_{idx}", type="CURVE")
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

        arc_obj = bpy.data.objects.new(f"{self.name}_DoorArc_{idx}", curve)
        arc_obj.data.materials.append(self.mats["door_frame"])
        link_to_collection(arc_obj, self.col)
        arc_obj.parent = self.root

    def build_geometry(self):
        """Constructs all walls with exact window and door cutouts, then adds 3D fixtures."""
        for w_idx, (x1, y1, x2, y2, thick) in enumerate(self.walls):
            dx, dy = x2 - x1, y2 - y1
            L = math.hypot(dx, dy)
            if L < 1e-3:
                continue
            ux, uy = dx / L, dy / L
            nx, ny = -uy, ux

            # Find all doors & windows collinear with this wall
            wall_doors = []
            wall_wins = []
            cut_points = {0.0, L}

            for d in self.doors:
                dist1 = abs((d["hx"] - x1) * nx + (d["hy"] - y1) * ny)
                dist2 = abs((d["x2"] - x1) * nx + (d["y2"] - y1) * ny)
                if dist1 < 2.5 and dist2 < 2.5:
                    s1 = (d["hx"] - x1) * ux + (d["hy"] - y1) * uy
                    s2 = (d["x2"] - x1) * ux + (d["y2"] - y1) * uy
                    a, b = max(0.0, min(s1, s2)), min(L, max(s1, s2))
                    if b - a > 1.0:
                        wall_doors.append((a, b))
                        cut_points.update([a, b])

            for w in self.windows:
                dist1 = abs((w["x1"] - x1) * nx + (w["y1"] - y1) * ny)
                dist2 = abs((w["x2"] - x1) * nx + (w["y2"] - y1) * ny)
                if dist1 < 2.5 and dist2 < 2.5:
                    s1 = (w["x1"] - x1) * ux + (w["y1"] - y1) * uy
                    s2 = (w["x2"] - x1) * ux + (w["y2"] - y1) * uy
                    a, b = max(0.0, min(s1, s2)), min(L, max(s1, s2))
                    if b - a > 1.0:
                        wall_wins.append((a, b))
                        cut_points.update([a, b])

            sorted_pts = sorted(cut_points)
            for s_idx in range(len(sorted_pts) - 1):
                a, b = sorted_pts[s_idx], sorted_pts[s_idx + 1]
                if b - a < 0.5:
                    continue
                mid = 0.5 * (a + b)
                sx1, sy1 = x1 + ux * a, y1 + uy * a
                sx2, sy2 = x1 + ux * b, y1 + uy * b
                quad = wall_quad(sx1, sy1, sx2, sy2, thick)

                has_door = any(da <= mid <= db for da, db in wall_doors)
                has_win = any(wa <= mid <= wb for wa, wb in wall_wins)

                if has_door:
                    # Lintel above door
                    create_prism_from_quad(
                        f"{self.name}_Wall_{w_idx}_LintelD_{s_idx}",
                        quad, DOOR_HEIGHT, WALL_HEIGHT,
                        self.mats["wall"], self.col, self.root,
                    )
                elif has_win:
                    # Sill below window + Lintel above window
                    create_prism_from_quad(
                        f"{self.name}_Wall_{w_idx}_SillW_{s_idx}",
                        quad, 0.0, WIN_SILL,
                        self.mats["wall"], self.col, self.root,
                    )
                    create_prism_from_quad(
                        f"{self.name}_Wall_{w_idx}_LintelW_{s_idx}",
                        quad, WIN_TOP, WALL_HEIGHT,
                        self.mats["wall"], self.col, self.root,
                    )
                else:
                    # Full-height solid wall segment
                    create_prism_from_quad(
                        f"{self.name}_Wall_{w_idx}_Solid_{s_idx}",
                        quad, 0.0, WALL_HEIGHT,
                        self.mats["wall"], self.col, self.root,
                    )

        # Build 3D Windows (skipping sub-spans occupied by integrated balcony doors)
        win_counter = 0
        for w in self.windows:
            x1, y1, x2, y2 = w["x1"], w["y1"], w["x2"], w["y2"]
            dx, dy = x2 - x1, y2 - y1
            L = math.hypot(dx, dy)
            ux, uy = dx / L, dy / L
            nx, ny = -uy, ux

            pts = {0.0, L}
            overlapping_doors = []
            for d in self.doors:
                dist1 = abs((d["hx"] - x1) * nx + (d["hy"] - y1) * ny)
                dist2 = abs((d["x2"] - x1) * nx + (d["y2"] - y1) * ny)
                if dist1 < 2.5 and dist2 < 2.5:
                    s1 = (d["hx"] - x1) * ux + (d["hy"] - y1) * uy
                    s2 = (d["x2"] - x1) * ux + (d["y2"] - y1) * uy
                    a, b = max(0.0, min(s1, s2)), min(L, max(s1, s2))
                    if b - a > 1.0:
                        overlapping_doors.append((a, b))
                        pts.update([a, b])

            s_pts = sorted(pts)
            for i in range(len(s_pts) - 1):
                a, b = s_pts[i], s_pts[i + 1]
                mid = 0.5 * (a + b)
                if b - a > 2.0 and not any(da <= mid <= db for da, db in overlapping_doors):
                    win_counter += 1
                    self._build_3d_window_segment(
                        win_counter,
                        x1 + ux * a, y1 + uy * a,
                        x1 + ux * b, y1 + uy * b,
                        w["thickness"], WIN_SILL, WIN_TOP,
                    )

        # Build 3D Doors
        for d_idx, d in enumerate(self.doors):
            self._build_3d_door(d_idx + 1, d)


# ==============================================================================
# FLOOR 3 - MAIN LEVEL PLAN DEFINITION
# ==============================================================================
def build_floor_3_3d(mats):
    f3 = FloorPlanBuilder("Floor_3_Main_Level", mats, root_offset=(0.0, 0.0, 0.0))

    # Interior Floor Slab
    f3.add_slab_polygon(
        "Interior_Slab",
        [(0, 120), (700, 120), (700, 920), (350, 920), (350, 1040), (0, 1040)],
    )

    # 3 Balconies
    f3.add_balcony("NE_Balcony", 350, 920, 350, 120, open_edges=("N", "E"))
    f3.add_balcony("SE_Balcony", 377, 0, 323, 120, open_edges=("S", "E", "W"))
    f3.add_balcony("West_Balcony", -120, 195, 120, 355, open_edges=("N", "W", "S"))

    # Outer & Structural Walls (15 cm)
    f3.add_wall(0, 1040, 350, 1040, 15)      # Kitchen North wall
    f3.add_wall(350, 1040, 350, 920, 15)     # Balcony divider West
    f3.add_wall(350, 920, 700, 920, 15)      # Living Room North wall
    f3.add_wall(700, 920, 700, 120, 15)      # East exterior wall
    f3.add_wall(0, 1040, 0, 120, 15)         # West exterior wall
    f3.add_wall(0, 120, 377, 120, 15)        # South stairwell wall
    f3.add_wall(377, 120, 700, 120, 15)      # Bedroom South wall

    # Internal Partitions
    f3.add_wall(155, 550, 230, 550, 10)      # Utility stub (leaves 155 cm opening)
    f3.add_wall(230, 550, 230, 290, 10)      # Utility + Bath East wall
    f3.add_wall(0, 450, 230, 450, 10)        # Bath North wall
    f3.add_wall(0, 290, 377, 290, 10)        # Bath South + Hallway entry wall
    f3.add_wall(377, 500, 700, 500, 12)      # Bedroom North wall
    f3.add_wall(377, 500, 377, 120, 12)      # Bedroom West wall

    # 50x50 Shaft/Shower in Bath
    create_prism_from_quad(
        "Floor_3_Bath_Shaft_50x50",
        [(0, 400), (50, 400), (50, 450), (0, 450)],
        0.0, WALL_HEIGHT,
        mats["shaft"], f3.col, f3.root,
    )

    # Windows & Glazed Assemblies
    f3.add_window(56, 1040, 294, 1040, label="238 (3x79.3)")
    f3.add_door(135, 1040, 79.3, 270, 360, 0, is_exterior=True)
    f3.add_door(294, 1040, 79.3, 180, 270, 180, is_exterior=True)

    f3.add_window(350, 935, 350, 1025, label="127")
    f3.add_window(413, 920, 636, 920, label="223 (3x75)")
    f3.add_door(413, 920, 75, 270, 360, 0, is_exterior=True)

    # West wall openings
    f3.add_window(0, 465, 0, 535)
    f3.add_window(0, 330, 0, 410, label="80")
    f3.add_window(0, 195, 0, 272, label="77")
    f3.add_door(0, 195, 77, 0, 90, 90, is_exterior=True)

    # Bedroom South glazed assembly
    f3.add_window(437, 120, 662, 120, label="225")
    f3.add_door(437, 120, 75, 0, 90, 0, is_exterior=True)

    # Internal Doors
    f3.add_door(230, 300, 74, 90, 180, 90, thickness=10)
    f3.add_door(360, 290, 90, 90, 180, 180, thickness=10)
    f3.add_door(377, 465, 80, 270, 360, 270, thickness=12)

    # Stairs
    f3.add_stairs(377, 500, 260, 75, num_treads=9, direction="right", label="INTERNAL STAIRS")
    f3.add_stairs(20, 120, 330, 85, num_treads=10, direction="left", label="STAIRS")

    # Room Labels
    f3.add_text_label("FLOOR 3 - MAIN LEVEL", 350, 1110, z=0.05, size=28.0)
    f3.add_text_label("KITCHEN", 175, 780)
    f3.add_text_label("LIVING ROOM", 525, 710)
    f3.add_text_label("BALCONY", 525, 980, size=18.0)
    f3.add_text_label("BALCONY", -60, 372, size=18.0, rotation_z=90.0)
    f3.add_text_label("BATH", 115, 365, size=20.0)
    f3.add_text_label("BEDROOM", 538, 310)
    f3.add_text_label("BALCONY", 538, 60, size=18.0)
    f3.add_text_label("OPENING 155", 77, 565, size=14.0, mat_key="dim")

    f3.build_geometry()
    return f3


# ==============================================================================
# ATTIC FLOOR 4 - UPPER LEVEL PLAN DEFINITION
# ==============================================================================
def build_floor_4_3d(mats):
    offset = (0.0, 0.0, WALL_HEIGHT + SLAB_THICK) if STACK_FLOORS else (10.5, 0.0, 0.0)
    f4 = FloorPlanBuilder("Floor_4_Attic_Level", mats, root_offset=offset)

    # Usable Interior Floor Slab
    f4.add_slab_polygon(
        "Interior_Slab",
        [(0, 120), (700, 120), (700, 918), (360, 918), (360, 1040), (220, 1040), (220, 570), (180, 570), (180, 210), (0, 210)],
    )

    # Cross-hatched Roof Void / Unusable Area on the West side
    f4.add_slab_polygon(
        "Roof_Void_Area",
        [(0, 210), (0, 1040), (220, 1040), (220, 570), (180, 570), (180, 210)],
        z_bottom=-SLAB_THICK,
        z_top=0.04,
        mat_key="void",
    )

    # Balconies
    f4.add_balcony("NE_Balcony", 360, 918, 340, 122, open_edges=("N", "E"))
    f4.add_balcony("SE_Balcony", 360, 0, 340, 120, open_edges=("S", "E", "W"))

    # Structural & Internal Walls
    f4.add_wall(220, 1040, 360, 1040, 15)    # North wall left of NE Balcony
    f4.add_wall(360, 1040, 360, 918, 15)     # NE Balcony West wall (122)
    f4.add_wall(360, 918, 700, 918, 15)      # NE Balcony South wall (340)
    f4.add_wall(700, 918, 700, 120, 15)      # East exterior wall
    f4.add_wall(220, 1040, 220, 570, 15)     # Attic room West wall (330)
    f4.add_wall(220, 570, 360, 570, 10)      # Hallway divider
    f4.add_wall(360, 500, 700, 500, 12)      # Attic Bedroom North wall (340)
    f4.add_wall(360, 500, 360, 120, 12)      # Attic Bedroom West wall
    f4.add_wall(360, 120, 700, 120, 15)      # Attic Bedroom South wall
    f4.add_wall(0, 120, 360, 120, 15)        # South stairwell wall
    f4.add_wall(0, 1040, 0, 120, 8)          # West perimeter boundary
    f4.add_wall(180, 230, 360, 230, 10)      # Stairwell landing partition wall

    # Windows & Glazed Assemblies
    f4.add_window(434, 918, 626, 918, label="192")
    f4.add_door(434, 918, 75, 270, 360, 0, is_exterior=True)

    f4.add_window(437, 120, 662, 120, label="225")
    f4.add_door(437, 120, 75, 0, 90, 0, is_exterior=True)

    # 120 cm Double Utility Door on the 330 wall (y=920..1040)
    f4.add_door(220, 1040, 60, 270, 360, 270, thickness=15)
    f4.add_door(220, 920, 60, 0, 90, 90, thickness=15)

    # Attic Bedroom Door & Main Stair Landing Door
    f4.add_door(360, 460, 80, 270, 360, 270, thickness=12)
    f4.add_door(340, 230, 85, 90, 180, 180, thickness=10)

    # Stairs
    f4.add_stairs(360, 500, 270, 70, num_treads=9, direction="right", label="INTERNAL STAIRS")
    f4.add_stairs(20, 120, 310, 85, num_treads=9, direction="left", label="MAIN STAIRS")

    # Room Labels
    f4.add_text_label("ATTIC FLOOR 4 - UPPER LEVEL", 350, 1110, z=0.05, size=28.0)
    f4.add_text_label("ROOF VOID / UNUSABLE", 100, 650, size=18.0, rotation_z=90.0)
    f4.add_text_label("ATTIC MAIN ROOM", 460, 740)
    f4.add_text_label("BALCONY", 530, 980, size=18.0)
    f4.add_text_label("ATTIC ROOM / BEDROOM", 530, 310, size=20.0)
    f4.add_text_label("BALCONY", 530, 60, size=18.0)

    f4.build_geometry()
    return f4


# ==============================================================================
# LIGHTING & CAMERAS
# ==============================================================================
def setup_lighting_and_cameras():
    env_col = get_or_create_collection("Lighting_And_Cameras")

    # Sun Light
    sun_data = bpy.data.lights.new(name="Sun_Light", type="SUN")
    sun_data.energy = 3.5
    sun_data.angle = math.radians(5.0)
    sun_obj = bpy.data.objects.new(name="Sun_Light", object_data=sun_data)
    sun_obj.location = (8.0, -6.0, 15.0)
    sun_obj.rotation_euler = (math.radians(38.0), math.radians(18.0), math.radians(25.0))
    link_to_collection(sun_obj, env_col)

    # Perspective Overview Camera
    cam_data = bpy.data.cameras.new(name="Camera_Perspective")
    cam_data.lens = 35.0
    cam_obj = bpy.data.objects.new(name="Camera_Perspective", object_data=cam_data)
    if STACK_FLOORS:
        cam_obj.location = (3.2, -7.5, 11.5)
        cam_obj.rotation_euler = (math.radians(42.0), 0.0, 0.0)
    else:
        cam_obj.location = (8.5, -8.5, 16.5)
        cam_obj.rotation_euler = (math.radians(40.0), 0.0, 0.0)
    link_to_collection(cam_obj, env_col)
    bpy.context.scene.camera = cam_obj

    # Top-Down Orthographic CAD Camera
    ortho_data = bpy.data.cameras.new(name="Camera_Top_CAD")
    ortho_data.type = "ORTHO"
    ortho_data.ortho_scale = 13.0 if STACK_FLOORS else 21.0
    ortho_obj = bpy.data.objects.new(name="Camera_Top_CAD", object_data=ortho_data)
    ortho_obj.location = (3.2 if STACK_FLOORS else 8.5, 5.2, 18.0)
    ortho_obj.rotation_euler = (0.0, 0.0, 0.0)
    link_to_collection(ortho_obj, env_col)

    # Bright architectural background
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.95, 0.96, 0.98, 1.0)
        bg.inputs[1].default_value = 0.8


def main():
    clear_scene()
    mats = create_materials()
    build_floor_3_3d(mats)
    build_floor_4_3d(mats)
    setup_lighting_and_cameras()
    print("3D Architectural Floor Plans generated successfully!")


if __name__ == "__main__":
    main()