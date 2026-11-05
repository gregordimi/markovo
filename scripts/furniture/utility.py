"""
==============================================================================
MARKOVO FURNITURE — UTILITY ROOM (FLOOR 3)
==============================================================================

Self-contained module defining the laundry & utility appliances, storage joinery,
and room shell for Floor 3 (Main Level).

Dimensions & Boundaries:
  - Plan footprint: X in [0, 230] cm, Y in [450, 550] cm (Width: 2.30 m, Depth: 1.00 m)
  - Floor Area: 2.30 m²
  - Ceiling Height: 2.80 m (flat)
  - Openings:
    * North Wall: Stub wall (x in [155, 230], w=75 cm), open passage (x in [0, 155], w=155 cm)
    * West Wall: Window (y in [465, 535], w=70 cm)
    * South Wall: Partition wall to bathroom (10 cm thick)
    * East Wall: Wall to hallway circulation (10 cm thick)

CLI Usage:
  1. Interactive Blender GUI:
     /Applications/Blender.app/Contents/MacOS/Blender --python scripts/furniture/utility.py

  2. Render studio preview to PNG:
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/utility.py -- --render

  3. Export empty room shell to SketchUp (.dae):
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/utility.py -- --export-shell

  4. Export room + appliances to SketchUp (.dae):
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/utility.py -- --sketchup
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

ROOM_NAME = "Utility"
FLOOR_LEVEL = "Floor_3"
ROOM_X_MIN = 0.0    # cm
ROOM_X_MAX = 230.0  # cm
ROOM_Y_MIN = 450.0  # cm
ROOM_Y_MAX = 550.0  # cm
ROOM_WIDTH = ROOM_X_MAX - ROOM_X_MIN    # 230 cm (2.30 m)
ROOM_LENGTH = ROOM_Y_MAX - ROOM_Y_MIN  # 100 cm (1.00 m)
CEILING_HEIGHT = 2.80                  # 2.80 m


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

    fl = get_or_create_material("Mat_Utility_Tiles")
    bsdf = fl.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.76, 0.44, 0.30, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.45
    mats["floor"] = fl

    w = get_or_create_material("Mat_Utility_Wall")
    bsdf = w.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.93, 0.92, 0.90, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.70
    mats["wall"] = w

    appliance = get_or_create_material("Mat_Appliance_White")
    bsdf = appliance.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.95, 0.95, 0.95, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.15
    mats["appliance"] = appliance

    door = get_or_create_material("Mat_Appliance_Glass")
    bsdf = door.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.10, 0.12, 0.14, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.05
    mats["glass"] = door

    ply = get_or_create_material("Mat_Utility_Plywood")
    bsdf = ply.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.85, 0.75, 0.60, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.50
    mats["plywood"] = ply

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
    """Builds the utility room architectural shell with opening to kitchen passage and window."""
    root = bpy.data.objects.new("Utility_Shell", None)
    col.objects.link(root)
    if parent:
        root.parent = parent

    fl = mats["floor"]
    w = mats["wall"]

    # Floor slab
    _create_box("Util_Floor_Slab", ROOM_X_MIN, ROOM_X_MAX, ROOM_Y_MIN, ROOM_Y_MAX, -0.15, 0.0, fl, col, root)

    # South Wall to Bathroom (y=440..450, x=0..230)
    _create_box("Util_Wall_South_Bath", ROOM_X_MIN, ROOM_X_MAX, ROOM_Y_MIN - 10, ROOM_Y_MIN, 0.0, CEILING_HEIGHT, w, col, root)

    # East Wall to Hallway (x=230..240, y=450..550)
    _create_box("Util_Wall_East_Hallway", ROOM_X_MAX, ROOM_X_MAX + 10, ROOM_Y_MIN, ROOM_Y_MAX, 0.0, CEILING_HEIGHT, w, col, root)

    # North Wall (y=550..560, stub wall x=155..230, open passage x=0..155)
    _create_box("Util_Wall_North_Stub", 155, ROOM_X_MAX, ROOM_Y_MAX, ROOM_Y_MAX + 10, 0.0, CEILING_HEIGHT, w, col, root)

    # West Facade Wall (x=-15..0, y=450..550, with window at y=465..535)
    _create_box("Util_Wall_West_Low", -15, 0, ROOM_Y_MIN, 465, 0.0, CEILING_HEIGHT, w, col, root)
    _create_box("Util_Wall_West_Sill", -15, 0, 465, 535, 0.0, 1.00, w, col, root)
    _create_box("Util_Wall_West_Lintel", -15, 0, 465, 535, 2.10, CEILING_HEIGHT, w, col, root)
    _create_box("Util_Wall_West_High", -15, 0, 535, ROOM_Y_MAX, 0.0, CEILING_HEIGHT, w, col, root)

    return root


def build_utility_furniture(col: Any, mats: Dict[str, Any], parent: Any = None) -> bpy.types.Object:
    """Builds utility appliances (Stacked Washer/Dryer, Laundry Tall Cabinet, Boiler)."""
    root = bpy.data.objects.new("Utility_Appliances", None)
    col.objects.link(root)
    if parent:
        root.parent = parent

    app = mats["appliance"]
    glass = mats["glass"]
    ply = mats["plywood"]

    # 1. Stacked Washing Machine & Heat-Pump Dryer (60 x 60 cm against East wall: x=168..228, y=460..520)
    # Lower: Washing Machine (height 85cm)
    _create_box("Washer_Body", 168, 228, 460, 520, 0.0, 0.85, app, col, root)
    _create_box("Washer_Door", 166, 168, 475, 515, 0.25, 0.65, glass, col, root)
    # Upper: Heat-Pump Tumble Dryer (height 85cm: z=0.85..1.70)
    _create_box("Dryer_Body", 168, 228, 460, 520, 0.85, 1.70, app, col, root)
    _create_box("Dryer_Door", 166, 168, 475, 515, 1.05, 1.45, glass, col, root)

    # 2. Tall Utility Laundry / Broom Cabinet (Width 55cm: x=105..160, Depth 50cm: y=460..510, Height 2.10m)
    _create_box("Utility_Tall_Cabinet", 105, 160, 460, 510, 0.0, 2.10, ply, col, root)

    # 3. Wall-Hung Electric Water Heater / Boiler (Cylinder box x=40..90, y=460..505, z=1.40..2.30)
    _create_box("Boiler_Unit", 40, 90, 460, 505, 1.40, 2.30, app, col, root)

    return root


def setup_studio(parent_obj: Any):
    col = bpy.data.collections.new("Studio_Rig")
    bpy.context.scene.collection.children.link(col)

    key = bpy.data.lights.new("Util_Key", "AREA")
    key.energy = 140.0
    key.size = 2.0
    key_obj = bpy.data.objects.new("Util_Key", key)
    key_obj.location = (1.15, 5.0, 2.60)
    col.objects.link(key_obj)

    cam_data = bpy.data.cameras.new("Util_Camera")
    cam_data.lens = 18.0
    cam_obj = bpy.data.objects.new("Util_Camera", cam_data)
    cam_obj.location = (0.60, 5.90, 1.60)
    target = Vector((1.40, 4.85, 1.10))
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

    prefixes = ("Util_", "Washer_", "Dryer_", "Utility_", "Boiler_") if include_furniture else ("Util_",)
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

    print("[1/3] Building architectural room shell...")
    shell = build_room_shell(col, mats)

    if not is_shell_only:
        print("[2/3] Constructing utility appliances (washer, dryer, cabinet, boiler)...")
        furn = build_utility_furniture(col, mats, parent=shell)
    else:
        print("[2/3] Skipping appliances (--export-shell requested)...")

    print("[3/3] Setting up interior studio lighting and camera...")
    setup_studio(shell)

    if is_shell_only:
        out_dae = export_collada_dae("renders/room_utility_shell.dae", include_furniture=False)
        print(f"\n[SketchUp] Exported empty room shell to: {out_dae}")
    elif is_sketchup:
        out_dae = export_collada_dae("renders/room_utility_furniture.dae", include_furniture=True)
        print(f"\n[SketchUp] Exported room + appliances to: {out_dae}")

    if is_render:
        out_png = Path("renders/utility_preview.png").resolve()
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

