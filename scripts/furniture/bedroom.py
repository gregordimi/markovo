"""
==============================================================================
MARKOVO FURNITURE — BEDROOM (FLOOR 3)
==============================================================================

Self-contained module defining the bedroom furniture, spatial clearances,
and room shell for Floor 3 (Main Level).

Dimensions & Boundaries:
  - Plan footprint: X in [377, 700] cm, Y in [120, 500] cm (Width: 3.23 m, Length: 3.80 m)
  - Floor Area: 12.27 m²
  - Ceiling Height: 2.80 m (flat)
  - Openings:
    * South: Balcony door (x=437, w=75) + window (x=437..662)
    * West: Entry door from hallway (y=465, w=80, swings into room)
    * North: Solid wall to living room (3.23 m)
    * East: Solid building party wall (3.80 m)

CLI Usage:
  1. Interactive Blender GUI:
     /Applications/Blender.app/Contents/MacOS/Blender --python scripts/furniture/bedroom.py

  2. Render studio preview to PNG:
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/bedroom.py -- --render

  3. Export empty room shell to SketchUp (.dae):
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/bedroom.py -- --export-shell

  4. Export room + furniture to SketchUp (.dae):
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/bedroom.py -- --sketchup
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
ROOM_NAME = "Bedroom"
FLOOR_LEVEL = "Floor_3"
ROOM_X_MIN = 377.0  # cm
ROOM_X_MAX = 700.0  # cm
ROOM_Y_MIN = 120.0  # cm
ROOM_Y_MAX = 500.0  # cm
ROOM_WIDTH = ROOM_X_MAX - ROOM_X_MIN    # 323 cm (3.23 m)
ROOM_LENGTH = ROOM_Y_MAX - ROOM_Y_MIN  # 380 cm (3.80 m)
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

    # Parquet floor
    fl = get_or_create_material("Mat_Parquet_Wood")
    bsdf = fl.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.78, 0.65, 0.46, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.35
    mats["floor"] = fl

    # Wall
    w = get_or_create_material("Mat_Bedroom_Wall")
    bsdf = w.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.94, 0.93, 0.91, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.70
    mats["wall"] = w

    # Bed Linen / Headboard (Warm light linen)
    linen = get_or_create_material("Mat_Bed_Linen")
    bsdf = linen.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.88, 0.86, 0.82, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.90
    mats["linen"] = linen

    # Natural Wood (Bedframe & nightstands)
    wood = get_or_create_material("Mat_Bed_Oak")
    bsdf = wood.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.72, 0.55, 0.36, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.40
    mats["wood"] = wood

    # Wardrobe Lacquer (Warm matte white)
    lacquer = get_or_create_material("Mat_Wardrobe_White")
    bsdf = lacquer.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.92, 0.92, 0.90, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.30
    mats["wardrobe"] = lacquer

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
    """Builds the bedroom architectural shell (floor slab, walls with door/window openings)."""
    root = bpy.data.objects.new("Bedroom_Shell", None)
    col.objects.link(root)
    if parent:
        root.parent = parent

    fl = mats["floor"]
    w = mats["wall"]

    # Floor slab
    _create_box("BR_Floor_Slab", ROOM_X_MIN, ROOM_X_MAX, ROOM_Y_MIN, ROOM_Y_MAX, -0.15, 0.0, fl, col, root)

    # East Party Wall (x=700..715, y=120..500)
    _create_box("BR_Wall_East_Party", ROOM_X_MAX, ROOM_X_MAX + 15, ROOM_Y_MIN, ROOM_Y_MAX, 0.0, CEILING_HEIGHT, w, col, root)

    # North Wall to Living Room (y=500..512, x=377..700)
    _create_box("BR_Wall_North_Living", ROOM_X_MIN, ROOM_X_MAX, ROOM_Y_MAX, ROOM_Y_MAX + 12, 0.0, CEILING_HEIGHT, w, col, root)

    # West Wall to Hallway (x=365..377, y=120..500, with entry door at y=465..545)
    # Wall segment below door (y=120..465)
    _create_box("BR_Wall_West_Low", ROOM_X_MIN - 12, ROOM_X_MIN, ROOM_Y_MIN, 465, 0.0, CEILING_HEIGHT, w, col, root)
    # Lintel above door (y=465..500, z=2.10..2.80)
    _create_box("BR_Wall_West_Lintel", ROOM_X_MIN - 12, ROOM_X_MIN, 465, ROOM_Y_MAX, 2.10, CEILING_HEIGHT, w, col, root)

    # South Wall to Balcony (y=105..120, with window x=437..662 and door x=437, w=75)
    # Lintel across entire south wall (z=2.10..2.80)
    _create_box("BR_Wall_South_Lintel", ROOM_X_MIN, ROOM_X_MAX, ROOM_Y_MIN - 15, ROOM_Y_MIN, 2.10, CEILING_HEIGHT, w, col, root)
    # West wall pier (x=377..437)
    _create_box("BR_Wall_South_Pier_W", ROOM_X_MIN, 437, ROOM_Y_MIN - 15, ROOM_Y_MIN, 0.0, 2.10, w, col, root)
    # Sill below window (x=512..662, z=0..0.90)
    _create_box("BR_Wall_South_Sill", 512, 662, ROOM_Y_MIN - 15, ROOM_Y_MIN, 0.0, 0.90, w, col, root)
    # East wall pier (x=662..700)
    _create_box("BR_Wall_South_Pier_E", 662, ROOM_X_MAX, ROOM_Y_MIN - 15, ROOM_Y_MIN, 0.0, 2.10, w, col, root)

    return root


def build_bedroom_furniture(col: Any, mats: Dict[str, Any], parent: Any = None) -> bpy.types.Object:
    """Builds bedroom furniture (Double Bed 160x200, 2 Nightstands, 4-Door Wardrobe)."""
    root = bpy.data.objects.new("Bedroom_Furniture", None)
    col.objects.link(root)
    if parent:
        root.parent = parent

    linen = mats["linen"]
    wood = mats["wood"]
    wardrobe = mats["wardrobe"]

    # 1. Double Bed (160 x 200 cm, headboard against North wall y=500, centered at x=538)
    # Bedframe: x in [458, 618] (160 cm wide), y in [295, 495] (200 cm deep)
    _create_box("Bed_Frame", 458, 618, 295, 495, 0.0, 0.35, wood, col, root)
    # Mattress (slightly recessed inside frame, height 50cm)
    _create_box("Bed_Mattress", 462, 614, 299, 495, 0.35, 0.54, linen, col, root)
    # Pillows (2x, 70 x 45 cm)
    _create_box("Bed_Pillow_L", 468, 532, 445, 490, 0.54, 0.64, linen, col, root)
    _create_box("Bed_Pillow_R", 544, 608, 445, 490, 0.54, 0.64, linen, col, root)
    # Headboard (thickness 8cm, width 180cm, height 1.10m)
    _create_box("Bed_Headboard", 448, 628, 492, 500, 0.0, 1.10, wood, col, root)

    # 2. Nightstands (45 x 40 cm, height 48cm)
    # Left Nightstand (x=400..445, y=455..495)
    _create_box("Nightstand_Left", 400, 445, 455, 495, 0.0, 0.48, wood, col, root)
    # Right Nightstand (x=631..676, y=455..495)
    _create_box("Nightstand_Right", 631, 676, 455, 495, 0.0, 0.48, wood, col, root)

    # 3. Wardrobe Closet along West wall (Length 220cm: y=160..380, Depth 60cm: x=377..437, Height 240cm)
    _create_box("Wardrobe_Cabinet", 377, 437, 160, 380, 0.0, 2.40, wardrobe, col, root)

    return root


def setup_studio(parent_obj: Any):
    col = bpy.data.collections.new("Studio_Rig")
    bpy.context.scene.collection.children.link(col)

    # Key Area Light
    key = bpy.data.lights.new("BR_Key", "AREA")
    key.energy = 260.0
    key.size = 3.0
    key_obj = bpy.data.objects.new("BR_Key", key)
    key_obj.location = (5.5, 2.5, 2.6)
    key_target = Vector((5.4, 3.8, 0.7))
    key_obj.rotation_euler = (key_target - key_obj.location).to_track_quat("-Z", "Y").to_euler()
    col.objects.link(key_obj)

    # Fill Area Light
    fill = bpy.data.lights.new("BR_Fill", "AREA")
    fill.energy = 120.0
    fill.size = 2.5
    fill_obj = bpy.data.objects.new("BR_Fill", fill)
    fill_obj.location = (4.8, 1.8, 2.4)
    fill_target = Vector((5.4, 3.8, 0.7))
    fill_obj.rotation_euler = (fill_target - fill_obj.location).to_track_quat("-Z", "Y").to_euler()
    col.objects.link(fill_obj)

    # Camera positioned in SE corner, pointing diagonally NW towards the Bed & Wardrobe
    cam_data = bpy.data.cameras.new("BR_Camera")
    cam_data.lens = 20.0
    cam_obj = bpy.data.objects.new("BR_Camera", cam_data)
    cam_obj.location = (6.4, 1.6, 1.65)
    target = Vector((4.8, 3.8, 0.85))
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

    prefixes = ("BR_", "Bed_", "Nightstand_", "Wardrobe_") if include_furniture else ("BR_",)
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
        print("[2/3] Constructing bedroom furniture (double bed, nightstands, wardrobe)...")
        furn = build_bedroom_furniture(col, mats, parent=shell)
    else:
        print("[2/3] Skipping furniture (--export-shell requested)...")

    print("[3/3] Setting up interior studio lighting and camera...")
    setup_studio(shell)

    if is_shell_only:
        out_dae = export_collada_dae("renders/room_bedroom_shell.dae", include_furniture=False)
        print(f"\n[SketchUp] Exported empty room shell to: {out_dae}")
    elif is_sketchup:
        out_dae = export_collada_dae("renders/room_bedroom_furniture.dae", include_furniture=True)
        print(f"\n[SketchUp] Exported room + furniture to: {out_dae}")

    if is_render:
        out_png = Path("renders/bedroom_preview.png").resolve()
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

