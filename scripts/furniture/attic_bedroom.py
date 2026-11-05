"""
==============================================================================
MARKOVO FURNITURE — ATTIC BEDROOM (FLOOR 4)
==============================================================================

Self-contained module defining the attic bedroom furniture, sloped ceiling
clearances, knee-wall storage, stair balustrade, and room shell for Floor 4 (Attic Level).

Dimensions & Boundaries:
  - Plan footprint:
    * Main Area: X in [360, 700] cm, Y in [575, 918] cm (Width: 3.40 m, Length: 3.43 m)
    * West Alcove: X in [220, 360] cm, Y in [570, 1040] cm (Width: 1.40 m, Length: 4.70 m)
    * Stair Void Opening: X in [377, 637] cm, Y in [500, 575] cm
  - Floor Area: ~24.5 m²
  - Ceiling: Sloping roof pitch rising from West knee wall (z ≈ 1.84 m at x=220) to East (z = 2.80 m at x=700)
  - Openings:
    * North Wall: Balcony door and window opening to North Attic Terrace (y=918)
    * West Wall: Knee wall (x=220) separating from unheated roof void
    * East Wall: Solid building party wall (full 2.80 m height)

CLI Usage:
  1. Interactive Blender GUI:
     /Applications/Blender.app/Contents/MacOS/Blender --python scripts/furniture/attic_bedroom.py

  2. Render studio preview to PNG:
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/attic_bedroom.py -- --render

  3. Export empty room shell to SketchUp (.dae):
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/attic_bedroom.py -- --export-shell

  4. Export room + furniture to SketchUp (.dae):
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/attic_bedroom.py -- --sketchup
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

ROOM_NAME = "Attic_Bedroom"
FLOOR_LEVEL = "Floor_4"
ROOM_X_MIN = 220.0  # cm
ROOM_X_MAX = 700.0  # cm
ROOM_Y_MIN = 570.0  # cm
ROOM_Y_MAX = 1040.0 # cm


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

    fl = get_or_create_material("Mat_Attic_Parquet_Wood")
    bsdf = fl.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.78, 0.65, 0.46, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.35
    mats["floor"] = fl

    w = get_or_create_material("Mat_Attic_Plaster")
    bsdf = w.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.94, 0.93, 0.91, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.70
    mats["wall"] = w

    linen = get_or_create_material("Mat_Attic_Bed_Linen")
    bsdf = linen.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.86, 0.85, 0.82, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.90
    mats["linen"] = linen

    wood = get_or_create_material("Mat_Attic_Oak_Joinery")
    bsdf = wood.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.72, 0.55, 0.36, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.40
    mats["wood"] = wood

    metal = get_or_create_material("Mat_Attic_Balustrade_Metal")
    bsdf = metal.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.15, 0.15, 0.15, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.90
        bsdf.inputs["Roughness"].default_value = 0.25
    mats["metal"] = metal

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
    """Builds the attic bedroom shell (floor slab, sloping walls, balcony openings, knee wall)."""
    root = bpy.data.objects.new("Attic_Bedroom_Shell", None)
    col.objects.link(root)
    if parent:
        root.parent = parent

    fl = mats["floor"]
    w = mats["wall"]

    # Floor slab (main area + alcove)
    _create_box("AB_Floor_Main", 360, ROOM_X_MAX, 570, 918, -0.15, 0.0, fl, col, root)
    _create_box("AB_Floor_Alcove", ROOM_X_MIN, 360, 570, ROOM_Y_MAX, -0.15, 0.0, fl, col, root)

    # 1. East Party Wall (x=700..715, y=570..918, z=0..2.80)
    _create_box("AB_Wall_East_Party", ROOM_X_MAX, ROOM_X_MAX + 15, 570, 918, 0.0, attic_z(ROOM_X_MAX), w, col, root)

    # 2. West Knee Wall (x=205..220, y=570..1040, z=0..1.84)
    _create_box("AB_Wall_West_Knee", ROOM_X_MIN - 15, ROOM_X_MIN, 570, ROOM_Y_MAX, 0.0, attic_z(ROOM_X_MIN), w, col, root)

    # 3. North Facade Wall (Alcove: y=1040..1055, x=220..360)
    _create_box("AB_Wall_North_Alcove", ROOM_X_MIN, 360, ROOM_Y_MAX, ROOM_Y_MAX + 15, 0.0, attic_z(290), w, col, root)

    # 4. North Terrace Wall (Main area: y=918..933, x=360..700, with balcony door & window)
    _create_box("AB_Wall_North_Door_Pier", 360, 435, 918, 933, 0.0, 2.05, w, col, root)
    _create_box("AB_Wall_North_Sill", 510, 660, 918, 933, 0.0, 0.90, w, col, root)
    _create_box("AB_Wall_North_Pier_E", 660, ROOM_X_MAX, 918, 933, 0.0, 2.05, w, col, root)
    _create_box("AB_Wall_North_Lintel", 360, ROOM_X_MAX, 918, 933, 2.05, attic_z(530), w, col, root)

    # 5. Balcony divider wall (x=360, y=918..1040)
    _create_box("AB_Wall_Balcony_Divider", 360, 375, 918, ROOM_Y_MAX, 0.0, attic_z(360), w, col, root)

    return root


def build_attic_bedroom_furniture(col: Any, mats: Dict[str, Any], parent: Any = None, include_balustrade: bool = True) -> bpy.types.Object:
    """Builds attic bedroom furniture (Double Bed, Nightstands, Knee-Wall Storage, Stair Balustrade)."""
    root = bpy.data.objects.new("Attic_Bedroom_Furniture", None)
    col.objects.link(root)
    if parent:
        root.parent = parent

    linen = mats["linen"]
    wood = mats["wood"]
    metal = mats["metal"]

    # 1. Double Bed (160 x 200 cm, headboard against East wall where ceiling is 2.80m: x=500..700, y=660..820)
    # Headboard along East wall (x=692..700, y=650..830, z=0..1.10)
    _create_box("AB_Bed_Headboard", 692, 700, 650, 830, 0.0, 1.10, wood, col, root)
    # Bedframe (length 200cm: x=495..695, width 160cm: y=660..820, height 35cm)
    _create_box("AB_Bed_Frame", 495, 695, 660, 820, 0.0, 0.35, wood, col, root)
    # Mattress
    _create_box("AB_Bed_Mattress", 495, 691, 664, 816, 0.35, 0.54, linen, col, root)
    # Pillows
    _create_box("AB_Bed_Pillow_1", 640, 685, 668, 734, 0.54, 0.64, linen, col, root)
    _create_box("AB_Bed_Pillow_2", 640, 685, 742, 808, 0.54, 0.64, linen, col, root)

    # 2. Nightstands
    _create_box("AB_Nightstand_S", 655, 695, 600, 645, 0.0, 0.48, wood, col, root)
    _create_box("AB_Nightstand_N", 655, 695, 835, 880, 0.0, 0.48, wood, col, root)

    # 3. Built-in Knee-Wall Storage Unit (Under sloped ceiling along West wall x=220: Length 360cm: y=600..960, Depth 55cm, Height 90cm)
    _create_box("AB_Knee_Storage_Top", 220, 275, 600, 960, 0.86, 0.90, wood, col, root)
    _create_box("AB_Knee_Storage_Carcass", 220, 275, 600, 960, 0.0, 0.86, mats["wall"], col, root)

    # 4. Stairwell Safety Railing / Balustrade around stair void (x in [377, 637], y=575)
    if include_balustrade:
        # Handrail (length 260cm, height 95cm)
        _create_box("AB_Stair_Handrail", 377, 637, 573, 577, 0.90, 0.95, wood, col, root)
        # Balusters (spindles spaced every 20cm)
        for sx in range(380, 635, 20):
            _create_box(f"AB_Baluster_{sx}", sx, sx + 2, 574, 576, 0.0, 0.90, metal, col, root)

    return root


def setup_studio(parent_obj: Any):
    col = bpy.data.collections.new("Studio_Rig")
    bpy.context.scene.collection.children.link(col)

    key = bpy.data.lights.new("AB_Key", "AREA")
    key.energy = 260.0
    key.size = 4.0
    key_obj = bpy.data.objects.new("AB_Key", key)
    key_obj.location = (4.8, 7.5, 3.2)
    col.objects.link(key_obj)

    cam_data = bpy.data.cameras.new("AB_Camera")
    cam_data.lens = 20.0
    cam_obj = bpy.data.objects.new("AB_Camera", cam_data)
    cam_obj.location = (3.4, 6.1, 1.70)
    target = Vector((5.6, 7.5, 0.90))
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

    prefixes = ("AB_",) if include_furniture else ("AB_Floor_", "AB_Wall_")
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
    print(f"  MARKOVO FURNITURE — {ROOM_NAME.upper()}")
    print("=" * 70)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for b in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.collections):
        for block in list(b):
            b.remove(block)

    mats = create_materials()
    col = bpy.context.scene.collection

    print("[1/3] Building architectural room shell with knee wall & sloped ceiling...")
    shell = build_room_shell(col, mats)

    if not is_shell_only:
        print("[2/3] Constructing attic bedroom furniture (bed, nightstands, knee storage, balustrade)...")
        furn = build_attic_bedroom_furniture(col, mats, parent=shell)
    else:
        print("[2/3] Skipping furniture (--export-shell requested)...")

    print("[3/3] Setting up interior studio lighting and camera...")
    setup_studio(shell)

    if is_shell_only:
        out_dae = export_collada_dae("renders/room_attic_bedroom_shell.dae", include_furniture=False)
        print(f"\n[SketchUp] Exported empty room shell to: {out_dae}")
    elif is_sketchup:
        out_dae = export_collada_dae("renders/room_attic_bedroom_furniture.dae", include_furniture=True)
        print(f"\n[SketchUp] Exported room + furniture to: {out_dae}")

    if is_render:
        out_png = Path("renders/attic_bedroom_preview.png").resolve()
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

