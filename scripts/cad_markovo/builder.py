"""
FloorPlanBuilder Engine.

Coordinates collection management, wall slicing with precise door/window
lintel and sill openings, room slab generation with distinct floor finishes,
terrace solid parapets with stone coping, and 3D joinery assemblies.
"""

import math
from typing import Dict, List, Tuple
import bpy
from mathutils import Vector

from .config import (
    CM,
    WALL_HEIGHT,
    SLAB_THICK,
    DOOR_HEIGHT,
    WIN_SILL,
    WIN_TOP,
)
from .geometry import (
    wall_quad,
    link_to_collection,
    create_prism_from_quad,
    create_extruded_polygon,
    create_window_3d,
    create_door_3d,
    create_stairs_3d,
    create_terrace_parapet_and_coping,
    create_text_label_3d,
)


def get_or_create_collection(name: str, parent: bpy.types.Collection = None) -> bpy.types.Collection:
    """Gets an existing collection or creates a new one and links it to the hierarchy."""
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    if parent is None:
        bpy.context.scene.collection.children.link(col)
    else:
        parent.children.link(col)
    return col


class FloorPlanBuilder:
    """
    High-level parametric builder for architectural floor plans.
    """

    def __init__(self, name: str, mats: Dict[str, bpy.types.Material], root_offset: Tuple[float, float, float] = (0.0, 0.0, 0.0)):
        self.name = name
        self.mats = mats
        self.col = get_or_create_collection(name)

        # Root empty object for floor translation, rotation, and stacking
        self.root = bpy.data.objects.new(f"{name}_Root", None)
        self.root.empty_display_type = "PLAIN_AXES"
        self.root.empty_display_size = 0.5
        self.root.location = Vector(root_offset)
        link_to_collection(self.root, self.col)

        self.walls: List[dict] = []
        self.windows: List[dict] = []
        self.doors: List[dict] = []
        self.rooms: List[dict] = []
        self.terraces: List[dict] = []
        self.stairs: List[dict] = []
        self.labels: List[dict] = []
        self.custom_prisms: List[dict] = []

    def add_wall(self, x1: float, y1: float, x2: float, y2: float, thickness: float = 15.0):
        """Adds a structural or partition wall."""
        self.walls.append({
            "x1": float(x1), "y1": float(y1),
            "x2": float(x2), "y2": float(y2),
            "thickness": float(thickness),
        })

    def add_window(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        thickness: float = 15.0,
        label: str = None,
        sill: float = WIN_SILL,
        top: float = WIN_TOP,
    ):
        """Adds a window opening and White uPVC glazed assembly."""
        self.windows.append({
            "x1": float(x1), "y1": float(y1),
            "x2": float(x2), "y2": float(y2),
            "thickness": float(thickness),
            "label": label,
            "sill": sill,
            "top": top,
        })

    def add_door(
        self,
        hx: float,
        hy: float,
        radius: float,
        start_angle: float,
        end_angle: float,
        wall_angle: float,
        thickness: float = 15.0,
        is_exterior: bool = False,
    ):
        """
        Adds a door opening and swing door assembly.
        Exterior doors use White uPVC. Interior doors use warm natural wood.
        """
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

    def add_room(
        self,
        name: str,
        poly_2d: list,
        mat_key: str = "clay_tiles",
        z_bottom: float = -SLAB_THICK,
        z_top: float = 0.0,
    ):
        """Adds a room floor slab with a specific floor material finish."""
        self.rooms.append({
            "name": name,
            "poly": poly_2d,
            "mat_key": mat_key,
            "z_bottom": z_bottom,
            "z_top": z_top,
        })

    def add_terrace(
        self,
        name: str,
        x: float,
        y: float,
        w: float,
        h: float,
        open_edges: tuple = ("N", "E", "S", "W"),
        mat_key: str = "balcony",
    ):
        """
        Adds a terrace/balcony.
        Solid masonry parapet walls are built using the SAME material as the walls,
        topped with architectural stone terrace coping on all exposed edges.
        Glass is completely omitted.
        """
        self.terraces.append({
            "name": name,
            "x": float(x), "y": float(y),
            "w": float(w), "h": float(h),
            "open_edges": open_edges,
            "mat_key": mat_key,
        })

    def add_stairs(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        num_treads: int = 10,
        direction: str = "right",
        label: str = "STAIRS",
    ):
        """Adds stairs finished with Cement Mosaic ("мозайка")."""
        self.stairs.append({
            "x": float(x), "y": float(y),
            "w": float(w), "h": float(h),
            "num_treads": num_treads,
            "direction": direction,
            "label": label,
        })

    def add_label(
        self,
        text_str: str,
        x: float,
        y: float,
        z: float = 0.02,
        size: float = 22.0,
        rotation_z: float = 0.0,
        mat_key: str = "text",
    ):
        """Adds a 3D architectural text label."""
        self.labels.append({
            "text": text_str,
            "x": float(x), "y": float(y),
            "z": float(z), "size": float(size),
            "rotation_z": float(rotation_z),
            "mat_key": mat_key,
        })

    def add_custom_prism(
        self,
        name: str,
        corners_2d: list,
        z_bottom: float,
        z_top: float,
        mat_key: str = "shaft",
    ):
        """Adds a custom prism (such as a plumbing shaft or structural pier)."""
        self.custom_prisms.append({
            "name": name,
            "corners": corners_2d,
            "z_bottom": z_bottom,
            "z_top": z_top,
            "mat_key": mat_key,
        })

    # --------------------------------------------------------------------------
    # Building Routines
    # --------------------------------------------------------------------------
    def _build_walls_with_cutouts(self):
        """Constructs all solid walls, door lintels, window sills, and window lintels."""
        for w_idx, w in enumerate(self.walls):
            x1, y1, x2, y2, thick = w["x1"], w["y1"], w["x2"], w["y2"], w["thickness"]
            dx, dy = x2 - x1, y2 - y1
            L = math.hypot(dx, dy)
            if L < 1e-3:
                continue
            ux, uy = dx / L, dy / L
            nx, ny = -uy, ux

            wall_doors = []
            wall_wins = []
            cut_points = {0.0, L}

            # Detect collinear doors
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

            # Detect collinear windows
            for win in self.windows:
                dist1 = abs((win["x1"] - x1) * nx + (win["y1"] - y1) * ny)
                dist2 = abs((win["x2"] - x1) * nx + (win["y2"] - y1) * ny)
                if dist1 < 2.5 and dist2 < 2.5:
                    s1 = (win["x1"] - x1) * ux + (win["y1"] - y1) * uy
                    s2 = (win["x2"] - x1) * ux + (win["y2"] - y1) * uy
                    a, b = max(0.0, min(s1, s2)), min(L, max(s1, s2))
                    if b - a > 1.0:
                        wall_wins.append((a, b, win.get("sill", WIN_SILL), win.get("top", WIN_TOP)))
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
                matched_win = next((w_info for w_info in wall_wins if w_info[0] <= mid <= w_info[1]), None)

                if has_door:
                    # Lintel above door
                    create_prism_from_quad(
                        f"{self.name}_Wall_{w_idx}_LintelD_{s_idx}",
                        quad,
                        DOOR_HEIGHT,
                        WALL_HEIGHT,
                        self.mats["wall"],
                        self.col,
                        self.root,
                    )
                elif matched_win is not None:
                    # Sill below window + Lintel above window
                    w_sill, w_top = matched_win[2], matched_win[3]
                    create_prism_from_quad(
                        f"{self.name}_Wall_{w_idx}_SillW_{s_idx}",
                        quad,
                        0.0,
                        w_sill,
                        self.mats["wall"],
                        self.col,
                        self.root,
                    )
                    create_prism_from_quad(
                        f"{self.name}_Wall_{w_idx}_LintelW_{s_idx}",
                        quad,
                        w_top,
                        WALL_HEIGHT,
                        self.mats["wall"],
                        self.col,
                        self.root,
                    )
                else:
                    # Solid full-height wall segment
                    create_prism_from_quad(
                        f"{self.name}_Wall_{w_idx}_Solid_{s_idx}",
                        quad,
                        0.0,
                        WALL_HEIGHT,
                        self.mats["wall"],
                        self.col,
                        self.root,
                    )

    def _build_windows(self):
        """Builds all 3D window assemblies using White uPVC and double glazing."""
        win_counter = 0
        for win in self.windows:
            x1, y1, x2, y2 = win["x1"], win["y1"], win["x2"], win["y2"]
            dx, dy = x2 - x1, y2 - y1
            L = math.hypot(dx, dy)
            if L < 1e-3:
                continue
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
                    create_window_3d(
                        name_prefix=self.name,
                        idx=win_counter,
                        x1=x1 + ux * a,
                        y1=y1 + uy * a,
                        x2=x1 + ux * b,
                        y2=y1 + uy * b,
                        thickness=win["thickness"],
                        z_sill=win.get("sill", WIN_SILL),
                        z_top=win.get("top", WIN_TOP),
                        pvc_mat=self.mats["pvc_white"],
                        glass_mat=self.mats["glass"],
                        col=self.col,
                        parent=self.root,
                    )

    def _build_doors(self):
        """Builds all 3D doors. Exterior doors use White uPVC; interior doors use wood."""
        for d_idx, d in enumerate(self.doors):
            create_door_3d(
                name_prefix=self.name,
                idx=d_idx + 1,
                hx=d["hx"],
                hy=d["hy"],
                x2=d["x2"],
                y2=d["y2"],
                radius=d["radius"],
                start_angle=d["start_angle"],
                end_angle=d["end_angle"],
                wall_angle=d["wall_angle"],
                thickness=d["thickness"],
                is_exterior=d["is_exterior"],
                pvc_mat=self.mats["pvc_white"],
                wood_mat=self.mats["door_wood"],
                door_frame_mat=self.mats["door_frame"],
                col=self.col,
                parent=self.root,
            )

    def _build_rooms(self):
        """Builds room floor slabs with designated floor finishes (Clay Tiles, Parquet, etc.)."""
        for r in self.rooms:
            mat = self.mats.get(r["mat_key"], self.mats["slab"])
            create_extruded_polygon(
                f"{self.name}_Room_{r['name']}",
                r["poly"],
                r["z_bottom"],
                r["z_top"],
                mat,
                self.col,
                self.root,
            )

    def _build_terraces(self):
        """
        Builds terrace floor slabs, solid parapet walls matching the wall material,
        and stone terrace coping along all open edges.
        """
        for t in self.terraces:
            x, y, w, h = t["x"], t["y"], t["w"], t["h"]
            poly = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]

            # Balcony floor slab
            slab_mat = self.mats.get(t["mat_key"], self.mats["balcony"])
            create_extruded_polygon(
                f"{self.name}_{t['name']}_Slab",
                poly,
                -SLAB_THICK,
                0.0,
                slab_mat,
                self.col,
                self.root,
            )

            # Edge segments for open perimeter
            edge_map = {
                "S": (x, y, x + w, y),
                "E": (x + w, y, x + w, y + h),
                "N": (x + w, y + h, x, y + h),
                "W": (x, y + h, x, y),
            }

            for edge_key in t["open_edges"]:
                ex1, ey1, ex2, ey2 = edge_map[edge_key]
                create_terrace_parapet_and_coping(
                    name_prefix=f"{self.name}_{t['name']}",
                    edge_key=edge_key,
                    x1=ex1, y1=ey1,
                    x2=ex2, y2=ey2,
                    wall_mat=self.mats["wall"],
                    coping_mat=self.mats["terrace_coping"],
                    col=self.col,
                    parent=self.root,
                )

    def _build_stairs(self):
        """Builds all stairs with Cement Mosaic finish."""
        for s in self.stairs:
            create_stairs_3d(
                name_prefix=self.name,
                x=s["x"], y=s["y"],
                w=s["w"], h=s["h"],
                num_treads=s["num_treads"],
                direction=s["direction"],
                label=s["label"],
                mosaic_mat=self.mats["cement_mosaic"],
                text_mat=self.mats["text"],
                col=self.col,
                parent=self.root,
            )

    def _build_labels(self):
        """Builds 3D text labels."""
        for lbl in self.labels:
            mat = self.mats.get(lbl["mat_key"], self.mats["text"])
            create_text_label_3d(
                name_prefix=self.name,
                text_str=lbl["text"],
                x=lbl["x"], y=lbl["y"],
                z=lbl["z"],
                size=lbl["size"],
                rotation_z=lbl["rotation_z"],
                mat=mat,
                col=self.col,
                parent=self.root,
            )

    def _build_custom_prisms(self):
        """Builds shafts and structural columns."""
        for p in self.custom_prisms:
            mat = self.mats.get(p["mat_key"], self.mats["shaft"])
            create_prism_from_quad(
                f"{self.name}_{p['name']}",
                p["corners"],
                p["z_bottom"],
                p["z_top"],
                mat,
                self.col,
                self.root,
            )

    def build_geometry(self):
        """Constructs all floor components in clean dependency order."""
        self._build_walls_with_cutouts()
        self._build_windows()
        self._build_doors()
        self._build_rooms()
        self._build_terraces()
        self._build_stairs()
        self._build_custom_prisms()
        self._build_labels()
