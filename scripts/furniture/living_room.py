"""
==============================================================================
MARKOVO FURNITURE — LIVING ROOM
==============================================================================

Self-contained module defining the living room furniture, spatial clearances,
and room shell for Floor 3 (Main Level).

Dimensions & Boundaries:
  - Plan footprint: X in [350, 700] cm, Y in [500, 920] cm (Width: 3.50 m, Length: 4.20 m)
  - Floor Area: 14.70 m²
  - Ceiling Height: 2.80 m (flat)
  - Openings:
    * North: Balcony door (x=413, w=75) + 3-segment window (x=413..636)
    * West: Balcony window (y=935..1025) + open walk zone to kitchen (y=500..920)
    * South: Internal stairs (x=377..637) going to Floor 4 Attic
    * East: Solid building party wall (4.20 m)

CLI Usage:
  1. Interactive Blender GUI:
     /Applications/Blender.app/Contents/MacOS/Blender --python scripts/furniture/living_room.py

  2. Render studio preview to PNG:
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/living_room.py -- --render

  3. Export empty room shell to SketchUp (.dae) for designing in external apps:
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/living_room.py -- --export-shell

  4. Export room + furniture to SketchUp (.dae):
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/living_room.py -- --sketchup
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

# Room Boundary
ROOM_NAME = "Living_Room"
FLOOR_LEVEL = "Floor_3"
ROOM_X_MIN = 350.0  # cm
ROOM_X_MAX = 700.0  # cm
ROOM_Y_MIN = 500.0  # cm
ROOM_Y_MAX = 920.0  # cm
ROOM_WIDTH = ROOM_X_MAX - ROOM_X_MIN    # 350 cm (3.50 m)
ROOM_LENGTH = ROOM_Y_MAX - ROOM_Y_MIN  # 420 cm (4.20 m)
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

    # 1. Terracotta floor tiles
    floor = get_or_create_material("Mat_Terracotta_Floor")
    bsdf = floor.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.76, 0.44, 0.30, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.45
    mats["floor"] = floor

    # 2. Wall plaster (Off-white warm)
    wall = get_or_create_material("Mat_Wall_Plaster")
    bsdf = wall.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.93, 0.92, 0.90, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.70
    mats["wall"] = wall

    # 3. Sofa fabric (Warm charcoal grey)
    fabric = get_or_create_material("Mat_Sofa_Fabric")
    bsdf = fabric.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.20, 0.22, 0.24, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.85
    mats["fabric"] = fabric

    # 4. Natural Oak Wood (Coffee table, TV media console)
    wood = get_or_create_material("Mat_Oak_Wood")
    bsdf = wood.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.75, 0.58, 0.38, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.35
    mats["wood"] = wood

    # 5. Black Metal (Legs, TV frame)
    metal = get_or_create_material("Mat_Black_Metal")
    bsdf = metal.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.05, 0.05, 0.05, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.25
        bsdf.inputs["Metallic"].default_value = 0.85
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
    """Builds the living room architectural shell (floor slab, walls with window/door cutouts)."""
    root = bpy.data.objects.new("Living_Room_Shell", None)
    col.objects.link(root)
    if parent:
        root.parent = parent

    fl = mats["floor"]
    w = mats["wall"]

    # 1. Floor slab
    _create_box("LR_Floor_Slab", ROOM_X_MIN, ROOM_X_MAX, ROOM_Y_MIN, ROOM_Y_MAX, -0.15, 0.0, fl, col, root)

    # 2. East Party Wall (x=700..715, y=500..920, z=0..2.80)
    _create_box("LR_Wall_East_Party", ROOM_X_MAX, ROOM_X_MAX + 15, ROOM_Y_MIN, ROOM_Y_MAX, 0.0, CEILING_HEIGHT, w, col, root)

    # 3. North Balcony Wall (y=920..935, with window & door openings)
    # Lintel above window/door (z=2.10..2.80)
    _create_box("LR_Wall_North_Lintel", ROOM_X_MIN, ROOM_X_MAX, ROOM_Y_MAX, ROOM_Y_MAX + 15, 2.10, CEILING_HEIGHT, w, col, root)
    # West wall pier (x=350..413)
    _create_box("LR_Wall_North_Pier_W", ROOM_X_MIN, 413, ROOM_Y_MAX, ROOM_Y_MAX + 15, 0.0, 2.10, w, col, root)
    # Sill below window (x=413..636, z=0..0.90)
    _create_box("LR_Wall_North_Sill", 413, 636, ROOM_Y_MAX, ROOM_Y_MAX + 15, 0.0, 0.90, w, col, root)
    # East wall pier (x=636..700)
    _create_box("LR_Wall_North_Pier_E", 636, ROOM_X_MAX, ROOM_Y_MAX, ROOM_Y_MAX + 15, 0.0, 2.10, w, col, root)

    # 4. South Wall to Bedroom (y=488..500, x=377..700)
    _create_box("LR_Wall_South_Bedroom", 377, ROOM_X_MAX, ROOM_Y_MIN - 12, ROOM_Y_MIN, 0.0, CEILING_HEIGHT, w, col, root)

    return root


def build_living_room_furniture(col: Any, mats: Dict[str, Any], parent: Any = None) -> bpy.types.Object:
    """Builds standard living room furniture (3-seater sofa, coffee table, media unit, 65" TV)."""
    root = bpy.data.objects.new("Living_Room_Furniture", None)
    col.objects.link(root)
    if parent:
        root.parent = parent

    fabric = mats["fabric"]
    wood = mats["wood"]
    metal = mats["metal"]

    # 1. 3-Seater Sofa facing East (Placed against open kitchen zone: x=410..500, y=620..840)
    # Base cushion (depth 90cm, length 220cm, height 42cm)
    _create_box("Sofa_Seat_Base", 420, 510, 620, 840, 0.0, 0.42, fabric, col, root)
    # Backrest (thickness 20cm, height 80cm) along West side of sofa
    _create_box("Sofa_Backrest", 400, 420, 620, 840, 0.0, 0.80, fabric, col, root)
    # Armrests (North & South)
    _create_box("Sofa_Armrest_S", 400, 510, 600, 620, 0.0, 0.62, fabric, col, root)
    _create_box("Sofa_Armrest_N", 400, 510, 840, 860, 0.0, 0.62, fabric, col, root)

    # 2. Coffee Table (Solid Oak with black steel frame, 110 x 60 cm, height 40cm)
    # Placed in front of sofa: x=540..600, y=675..785
    _create_box("Coffee_Table_Top", 540, 600, 675, 785, 0.36, 0.40, wood, col, root)
    _create_box("Coffee_Table_Leg_SW", 542, 546, 677, 681, 0.0, 0.36, metal, col, root)
    _create_box("Coffee_Table_Leg_SE", 594, 598, 677, 681, 0.0, 0.36, metal, col, root)
    _create_box("Coffee_Table_Leg_NW", 542, 546, 779, 783, 0.0, 0.36, metal, col, root)
    _create_box("Coffee_Table_Leg_NE", 594, 598, 779, 783, 0.0, 0.36, metal, col, root)

    # 3. TV Media Console (Low credenza along East party wall: x=655..695, y=630..830)
    # Length 200cm, depth 40cm, height 48cm
    _create_box("TV_Media_Cabinet", 655, 695, 630, 830, 0.08, 0.48, wood, col, root)
    _create_box("TV_Cabinet_Legs", 657, 693, 635, 825, 0.0, 0.08, metal, col, root)

    # 4. Wall-Mounted 65" OLED TV (Mounted on East wall at eye level z=1.05..1.85)
    # Width 145cm, height 83cm, depth 5cm
    _create_box("TV_Screen", 692, 697, 658, 802, 1.05, 1.88, metal, col, root)

    return root


def setup_studio(parent_obj: Any):
    col = bpy.data.collections.new("Studio_Rig")
    bpy.context.scene.collection.children.link(col)

    # Key Softbox
    key = bpy.data.lights.new("LR_Key", "AREA")
    key.energy = 280.0
    key.size = 4.0
    key_obj = bpy.data.objects.new("LR_Key", key)
    key_obj.location = (4.8, 6.8, 3.5)
    key_obj.rotation_euler = (math.radians(35.0), math.radians(10.0), math.radians(45.0))
    col.objects.link(key_obj)

    # Camera framed inside living room looking North-East towards TV and balcony
    cam_data = bpy.data.cameras.new("LR_Camera")
    cam_data.lens = 22.0
    cam_obj = bpy.data.objects.new("LR_Camera", cam_data)
    cam_obj.location = (3.8, 5.2, 1.65)
    target = Vector((5.6, 7.3, 1.10))
    cam_obj.rotation_euler = (target - cam_obj.location).to_track_quat("-Z", "Y").to_euler()
    col.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj


def export_collada_dae(filepath: str, include_furniture: bool = True):
    """Exports room shell and/or furniture into COLLADA (.dae) for SketchUp."""
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

    prefixes = ("LR_", "Sofa_", "Coffee_", "TV_") if include_furniture else ("LR_",)
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

    # 1. Reset
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for b in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.collections):
        for block in list(b):
            b.remove(block)

    mats = create_materials()
    col = bpy.context.scene.collection

    # 2. Build room shell
    print("[1/3] Building architectural room shell...")
    shell = build_room_shell(col, mats)

    # 3. Build furniture
    if not is_shell_only:
        print("[2/3] Constructing living room furniture (sofa, coffee table, TV console)...")
        furn = build_living_room_furniture(col, mats, parent=shell)
    else:
        print("[2/3] Skipping furniture (--export-shell requested)...")

    # 4. Studio setup
    print("[3/3] Setting up interior studio lighting and camera...")
    setup_studio(shell)

    # Export COLLADA DAE if requested
    if is_shell_only:
        out_dae = export_collada_dae("renders/room_living_room_shell.dae", include_furniture=False)
        print(f"\n[SketchUp] Exported empty room shell to: {out_dae}")
        print("           Open in SketchUp via: File > Import > COLLADA Files (*.dae)")
    elif is_sketchup:
        out_dae = export_collada_dae("renders/room_living_room_furniture.dae", include_furniture=True)
        print(f"\n[SketchUp] Exported room + furniture to: {out_dae}")

    # Render preview
    if is_render:
        out_png = Path("renders/living_room_preview.png").resolve()
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

