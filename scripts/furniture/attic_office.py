"""
==============================================================================
MARKOVO FURNITURE — ATTIC OFFICE (FLOOR 4)
==============================================================================

Self-contained module defining the office workspace furniture, sloped ceiling
clearances, and room shell for Floor 4 (Attic Level).

Dimensions & Boundaries:
  - Plan footprint: X in [360, 700] cm, Y in [120, 500] cm (Width: 3.40 m, Length: 3.80 m)
  - Floor Area: 12.92 m²
  - Ceiling: Sloping roof pitch rising from West (z ≈ 2.12 m at x=360) to East (z = 2.80 m at x=700)
  - Openings:
    * South Wall: Balcony door (x=437, w=75) + window to South Terrace
    * West Wall: Entry door from 4th floor stair landing (x=360)
    * East Wall: Solid building party wall (3.80 m, full 2.80 m height)

CLI Usage:
  1. Interactive Blender GUI:
     /Applications/Blender.app/Contents/MacOS/Blender --python scripts/furniture/attic_office.py

  2. Render studio preview to PNG:
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/attic_office.py -- --render

  3. Export empty room shell to SketchUp (.dae):
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/attic_office.py -- --export-shell

  4. Export room + office furniture to SketchUp (.dae):
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/attic_office.py -- --sketchup
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

ROOM_NAME = "Attic_Office"
FLOOR_LEVEL = "Floor_4"
ROOM_X_MIN = 360.0  # cm
ROOM_X_MAX = 700.0  # cm
ROOM_Y_MIN = 120.0  # cm
ROOM_Y_MAX = 500.0  # cm
ROOM_WIDTH = ROOM_X_MAX - ROOM_X_MIN    # 340 cm (3.40 m)
ROOM_LENGTH = ROOM_Y_MAX - ROOM_Y_MIN  # 380 cm (3.80 m)


def attic_z(x_cm: float) -> float:
    t = max(0.0, min(1.0, x_cm / 700.0))
    return round(1.40 + 1.40 * t, 3)


def get_or_create_material(name: str):
    if not HAS_BLENDER:
        return None
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    return mat


def create_materials() -> Dict[str, Any]:
    if not HAS_BLENDER:
        return {}
    mats = {}

    fl = get_or_create_material("Mat_Attic_Parquet")
    bsdf = fl.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.78, 0.65, 0.46, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.35
    mats["floor"] = fl

    w = get_or_create_material("Mat_Attic_Wall")
    bsdf = w.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.94, 0.93, 0.91, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.70
    mats["wall"] = w

    desk = get_or_create_material("Mat_Desk_Walnut")
    bsdf = desk.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.45, 0.32, 0.22, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.35
    mats["desk"] = desk

    metal = get_or_create_material("Mat_Office_Steel")
    bsdf = metal.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.12, 0.12, 0.12, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.85
        bsdf.inputs["Roughness"].default_value = 0.25
    mats["metal"] = metal

    leather = get_or_create_material("Mat_Chair_Leather")
    bsdf = leather.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.22, 0.16, 0.12, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.60
    mats["leather"] = leather

    return mats


def _create_box(name: str, x0: float, x1: float, y0: float, y1: float, z0: float, z1: float,
                mat: Any, col: Any, parent: Any = None):
    mesh = bpy.data.meshes.new(name)
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
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    if mat:
        obj.data.materials.append(mat)
    col.objects.link(obj)
    if parent:
        obj.parent = parent
    return obj


def build_room_shell(col: Any, mats: Dict[str, Any], parent: Any = None) -> bpy.types.Object:
    """Builds the attic office shell with sloping ceiling and balcony door/window."""
    root = bpy.data.objects.new("Attic_Office_Shell", None)
    col.objects.link(root)
    if parent:
        root.parent = parent

    fl = mats["floor"]
    w = mats["wall"]

    z_west = attic_z(ROOM_X_MIN)  # ~2.12m
    z_east = attic_z(ROOM_X_MAX)  # 2.80m

    # Floor slab
    _create_box("Office_Floor_Slab", ROOM_X_MIN, ROOM_X_MAX, ROOM_Y_MIN, ROOM_Y_MAX, -0.15, 0.0, fl, col, root)

    # East Party Wall (x=700..715, full 2.80m height)
    _create_box("Office_Wall_East_Party", ROOM_X_MAX, ROOM_X_MAX + 15, ROOM_Y_MIN, ROOM_Y_MAX, 0.0, z_east, w, col, root)

    # West Wall to Landing (x=345..360, height 2.12m)
    _create_box("Office_Wall_West", ROOM_X_MIN - 15, ROOM_X_MIN, ROOM_Y_MIN, ROOM_Y_MAX, 0.0, z_west, w, col, root)

    # North Wall to Stairwell (y=500..512, x=360..700, raked top)
    _create_box("Office_Wall_North", ROOM_X_MIN, ROOM_X_MAX, ROOM_Y_MAX, ROOM_Y_MAX + 12, 0.0, (z_west + z_east) * 0.5, w, col, root)

    # South Wall to Balcony (y=105..120, with balcony door & window)
    _create_box("Office_Wall_South_Pier_W", ROOM_X_MIN, 437, ROOM_Y_MIN - 15, ROOM_Y_MIN, 0.0, 2.05, w, col, root)
    _create_box("Office_Wall_South_Sill", 512, 662, ROOM_Y_MIN - 15, ROOM_Y_MIN, 0.0, 0.90, w, col, root)
    _create_box("Office_Wall_South_Pier_E", 662, ROOM_X_MAX, ROOM_Y_MIN - 15, ROOM_Y_MIN, 0.0, 2.05, w, col, root)
    _create_box("Office_Wall_South_Lintel", ROOM_X_MIN, ROOM_X_MAX, ROOM_Y_MIN - 15, ROOM_Y_MIN, 2.05, (z_west + z_east) * 0.5, w, col, root)

    return root


def build_office_furniture(col: Any, mats: Dict[str, Any], parent: Any = None) -> bpy.types.Object:
    """Builds office furniture (Executive Desk, Ergonomic Chair, Bookshelf along tall East wall)."""
    root = bpy.data.objects.new("Office_Furniture", None)
    col.objects.link(root)
    if parent:
        root.parent = parent

    desk_mat = mats["desk"]
    metal = mats["metal"]
    leather = mats["leather"]

    # 1. Executive Work Desk (160 x 80 cm, height 75cm, placed facing South towards terrace: x=460..620, y=240..320)
    _create_box("Desk_Top", 460, 620, 240, 320, 0.72, 0.76, desk_mat, col, root)
    # Steel frame legs
    _create_box("Desk_Leg_SW", 464, 470, 244, 250, 0.0, 0.72, metal, col, root)
    _create_box("Desk_Leg_SE", 610, 616, 244, 250, 0.0, 0.72, metal, col, root)
    _create_box("Desk_Leg_NW", 464, 470, 310, 316, 0.0, 0.72, metal, col, root)
    _create_box("Desk_Leg_NE", 610, 616, 310, 316, 0.0, 0.72, metal, col, root)
    # Under-desk drawer pedestal (x=464..504, y=250..310, z=0.10..0.68)
    _create_box("Desk_Drawer_Pedestal", 464, 504, 250, 310, 0.10, 0.68, desk_mat, col, root)

    # 2. Ergonomic Office Chair (centered at desk: x=540, y=350)
    _create_box("Chair_Base_Star", 520, 560, 330, 370, 0.0, 0.08, metal, col, root)
    _create_box("Chair_Seat", 516, 564, 326, 374, 0.44, 0.52, leather, col, root)
    _create_box("Chair_Backrest", 518, 562, 368, 376, 0.52, 1.05, leather, col, root)

    # 3. Tall Bookshelf / Library Storage along tall East wall (Width 220cm: y=200..420, Depth 40cm: x=660..700, Height 2.40m)
    _create_box("Bookshelf_Cabinet", 660, 700, 200, 420, 0.0, 2.40, desk_mat, col, root)

    return root


def setup_studio(parent_obj: Any):
    col = bpy.data.collections.new("Studio_Rig")
    bpy.context.scene.collection.children.link(col)

    key = bpy.data.lights.new("Office_Key", "AREA")
    key.energy = 240.0
    key.size = 3.5
    key_obj = bpy.data.objects.new("Office_Key", key)
    key_obj.location = (5.3, 2.5, 3.2)
    col.objects.link(key_obj)

    cam_data = bpy.data.cameras.new("Office_Camera")
    cam_data.lens = 22.0
    cam_obj = bpy.data.objects.new("Office_Camera", cam_data)
    cam_obj.location = (4.1, 1.8, 1.65)
    target = Vector((5.4, 3.4, 0.85))
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

    prefixes = ("Office_", "Desk_", "Chair_", "Bookshelf_") if include_furniture else ("Office_",)
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

    print("[1/3] Building architectural room shell with sloping roof...")
    shell = build_room_shell(col, mats)

    if not is_shell_only:
        print("[2/3] Constructing office furniture (desk, ergonomic chair, bookshelf)...")
        furn = build_office_furniture(col, mats, parent=shell)
    else:
        print("[2/3] Skipping furniture (--export-shell requested)...")

    print("[3/3] Setting up interior studio lighting and camera...")
    setup_studio(shell)

    if is_shell_only:
        out_dae = export_collada_dae("renders/room_attic_office_shell.dae", include_furniture=False)
        print(f"\n[SketchUp] Exported empty room shell to: {out_dae}")
    elif is_sketchup:
        out_dae = export_collada_dae("renders/room_attic_office_furniture.dae", include_furniture=True)
        print(f"\n[SketchUp] Exported room + furniture to: {out_dae}")

    if is_render:
        out_png = Path("renders/attic_office_preview.png").resolve()
        out_png.parent.mkdir(parents=True, exist_ok=True)
        print(f"\n[Render] Rendering preview to: {out_png}")
        scene = bpy.context.scene
        scene.render.engine = "CYCLES"
        if hasattr(scene, "cycles"):
            scene.cycles.device = "CPU"
            scene.cycles.samples = 32
            scene.cycles.use_denoising = True
        scene.render.resolution_x = 1920
        scene.render.resolution_y = 1080
        scene.render.filepath = str(out_png)
        bpy.ops.render.render(write_still=True)
        print(f"[Render] Preview complete: {out_png}")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

