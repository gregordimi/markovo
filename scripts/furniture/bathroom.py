"""
==============================================================================
MARKOVO FURNITURE — BATHROOM (FLOOR 3)
==============================================================================

Self-contained module defining the bathroom sanitary fixtures, spatial clearances,
and room shell for Floor 3 (Main Level).

Dimensions & Boundaries:
  - Plan footprint: X in [0, 230] cm, Y in [290, 450] cm (Width: 2.30 m, Length: 1.60 m)
  - Floor Area: 3.68 m²
  - Ceiling Height: 2.80 m (flat)
  - Obstacles & Openings:
    * NW Corner: Fixed 50x50 cm vertical plumbing shaft (x in [0, 50], y in [400, 450])
    * West Wall: High bathroom window (y in [330, 410], w=80 cm, sill at 1.40 m)
    * South Wall: Entry door at x=230, y=300 (w=74 cm, thickness 10 cm)
    * North Wall: Solid partition wall to utility room (10 cm thick)

CLI Usage:
  1. Interactive Blender GUI:
     /Applications/Blender.app/Contents/MacOS/Blender --python scripts/furniture/bathroom.py

  2. Render studio preview to PNG:
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/bathroom.py -- --render

  3. Export empty room shell to SketchUp (.dae):
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/bathroom.py -- --export-shell

  4. Export room + sanitary fixtures to SketchUp (.dae):
     /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/bathroom.py -- --sketchup
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

ROOM_NAME = "Bathroom"
FLOOR_LEVEL = "Floor_3"
ROOM_X_MIN = 0.0    # cm
ROOM_X_MAX = 230.0  # cm
ROOM_Y_MIN = 290.0  # cm
ROOM_Y_MAX = 450.0  # cm
ROOM_WIDTH = ROOM_X_MAX - ROOM_X_MIN    # 230 cm (2.30 m)
ROOM_LENGTH = ROOM_Y_MAX - ROOM_Y_MIN  # 160 cm (1.60 m)
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

    # 1. Floor tile (Dark Slate Grey Porcelain)
    fl = get_or_create_material("Mat_Bath_Floor_Slate")
    bsdf = fl.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.22, 0.23, 0.25, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.35
    mats["floor"] = fl

    # 2. Wall tile (Warm White Calacatta Marble style)
    w = get_or_create_material("Mat_Bath_Wall_Marble")
    bsdf = w.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.94, 0.94, 0.93, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.25
    mats["wall"] = w

    # 3. White Ceramic (Toilet bowl, Basin sink)
    ceramic = get_or_create_material("Mat_Sanitary_Ceramic")
    bsdf = ceramic.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.97, 0.97, 0.97, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.10
    mats["ceramic"] = ceramic

    # 4. Chrome Metal (Taps, shower head, valves)
    chrome = get_or_create_material("Mat_Bath_Chrome")
    bsdf = chrome.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.85, 0.86, 0.88, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.95
        bsdf.inputs["Roughness"].default_value = 0.15
    mats["chrome"] = chrome

    # 5. Shower Glass (Clear safety glass)
    glass = get_or_create_material("Mat_Shower_Glass")
    bsdf = glass.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.90, 0.95, 0.95, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.05
        if "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = 0.92
        elif "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = 0.92
    mats["glass"] = glass

    # 6. Vanity Cabinet Wood (Smoked Oak)
    wood = get_or_create_material("Mat_Vanity_Wood")
    bsdf = wood.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.40, 0.30, 0.22, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.40
    mats["wood"] = wood

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
    """Builds the bathroom architectural shell with plumbing shaft, window, and door opening."""
    root = bpy.data.objects.new("Bathroom_Shell", None)
    col.objects.link(root)
    if parent:
        root.parent = parent

    fl = mats["floor"]
    w = mats["wall"]

    # Floor slab
    _create_box("Bath_Floor_Slab", ROOM_X_MIN, ROOM_X_MAX, ROOM_Y_MIN, ROOM_Y_MAX, -0.15, 0.0, fl, col, root)

    # 1. Plumbing Shaft (x=0..50, y=400..450, z=0..2.80)
    _create_box("Bath_Plumbing_Shaft", 0, 50, 400, 450, 0.0, CEILING_HEIGHT, w, col, root)

    # 2. North Wall to Utility (y=450..460, x=50..230)
    _create_box("Bath_Wall_North_Utility", 50, ROOM_X_MAX, ROOM_Y_MAX, ROOM_Y_MAX + 10, 0.0, CEILING_HEIGHT, w, col, root)

    # 3. East Wall to Hallway (x=230..240, y=290..450)
    _create_box("Bath_Wall_East_Hallway", ROOM_X_MAX, ROOM_X_MAX + 10, ROOM_Y_MIN, ROOM_Y_MAX, 0.0, CEILING_HEIGHT, w, col, root)

    # 4. South Wall (y=280..290, with door opening at x=230, y=300..374)
    # Lintel above door (x=156..230, z=2.10..2.80)
    _create_box("Bath_Wall_South_Lintel", 156, ROOM_X_MAX, ROOM_Y_MIN - 10, ROOM_Y_MIN, 2.10, CEILING_HEIGHT, w, col, root)
    # South wall solid segment (x=0..156, z=0..2.80)
    _create_box("Bath_Wall_South_Solid", 0, 156, ROOM_Y_MIN - 10, ROOM_Y_MIN, 0.0, CEILING_HEIGHT, w, col, root)

    # 5. West Facade Wall (x=-15..0, y=290..450, with window at y=330..410)
    _create_box("Bath_Wall_West_Low", -15, 0, ROOM_Y_MIN, 330, 0.0, CEILING_HEIGHT, w, col, root)
    _create_box("Bath_Wall_West_Sill", -15, 0, 330, 410, 0.0, 1.40, w, col, root)
    _create_box("Bath_Wall_West_Lintel", -15, 0, 330, 410, 2.10, CEILING_HEIGHT, w, col, root)
    _create_box("Bath_Wall_West_High", -15, 0, 410, ROOM_Y_MAX, 0.0, CEILING_HEIGHT, w, col, root)

    return root


def build_bathroom_furniture(col: Any, mats: Dict[str, Any], parent: Any = None) -> bpy.types.Object:
    """Builds standard bathroom sanitary fixtures (Walk-in Shower, Vanity Sink, Wall-hung WC)."""
    root = bpy.data.objects.new("Bathroom_Sanitary", None)
    col.objects.link(root)
    if parent:
        root.parent = parent

    ceramic = mats["ceramic"]
    chrome = mats["chrome"]
    glass = mats["glass"]
    wood = mats["wood"]

    # 1. Walk-in Shower Enclosure (120 x 85 cm along North wall: x=50..170, y=365..450)
    # Shower low profile tray (height 4cm)
    _create_box("Shower_Tray", 50, 170, 365, 450, 0.0, 0.04, ceramic, col, root)
    # Fixed glass screen (8mm tempered glass, height 2.00m, length 120cm along South edge of shower zone)
    _create_box("Shower_Glass_Screen", 50, 150, 365, 366, 0.04, 2.05, glass, col, root)
    # Rain shower head & vertical pipe (mounted on East wall of shower: x=168)
    _create_box("Shower_Riser_Pipe", 168, 170, 405, 408, 1.10, 2.15, chrome, col, root)
    _create_box("Shower_Head", 155, 170, 400, 415, 2.15, 2.18, chrome, col, root)

    # 2. Vanity Sink Cabinet with Mirror (Width 80cm: x=0..80, y=290..340, along South wall)
    # Wood floating vanity cabinet (height 50cm, suspended 30cm above floor)
    _create_box("Vanity_Cabinet", 5, 85, 292, 342, 0.35, 0.85, wood, col, root)
    # Ceramic basin on top
    _create_box("Vanity_Basin", 10, 80, 295, 339, 0.85, 0.88, ceramic, col, root)
    # Mixer tap
    _create_box("Vanity_Tap", 42, 48, 298, 305, 0.88, 1.05, chrome, col, root)
    # Mirror cabinet on wall (80 x 75 cm, z=1.15..1.90)
    _create_box("Vanity_Mirror", 5, 85, 290, 295, 1.15, 1.90, glass, col, root)

    # 3. Wall-Hung WC with Concealed Cistern Box (Placed against East wall: x=175..230, y=295..345)
    # Cistern box (depth 18cm, height 1.15m)
    _create_box("WC_Cistern_Box", 212, 230, 295, 345, 0.0, 1.15, mats["wall"], col, root)
    # Toilet bowl (ceramic, length 52cm, width 36cm, height 40cm, wall-hung)
    _create_box("WC_Bowl", 162, 212, 305, 341, 0.15, 0.45, ceramic, col, root)
    # Flush plate (chrome)
    _create_box("WC_Flush_Plate", 211, 212, 310, 330, 0.95, 1.08, chrome, col, root)

    return root


def setup_studio(parent_obj: Any):
    col = bpy.data.collections.new("Studio_Rig")
    bpy.context.scene.collection.children.link(col)

    key = bpy.data.lights.new("Bath_Key", "AREA")
    key.energy = 160.0
    key.size = 2.0
    key_obj = bpy.data.objects.new("Bath_Key", key)
    key_obj.location = (1.15, 3.70, 2.70)
    col.objects.link(key_obj)

    cam_data = bpy.data.cameras.new("Bath_Camera")
    cam_data.lens = 18.0
    cam_obj = bpy.data.objects.new("Bath_Camera", cam_data)
    cam_obj.location = (2.10, 3.10, 1.70)
    target = Vector((0.70, 3.90, 0.90))
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

    prefixes = ("Bath_", "Shower_", "Vanity_", "WC_") if include_furniture else ("Bath_",)
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

    print("[1/3] Building architectural room shell with plumbing shaft...")
    shell = build_room_shell(col, mats)

    if not is_shell_only:
        print("[2/3] Constructing bathroom sanitary fixtures (shower, vanity, WC)...")
        furn = build_bathroom_furniture(col, mats, parent=shell)
    else:
        print("[2/3] Skipping fixtures (--export-shell requested)...")

    print("[3/3] Setting up interior studio lighting and camera...")
    setup_studio(shell)

    if is_shell_only:
        out_dae = export_collada_dae("renders/room_bathroom_shell.dae", include_furniture=False)
        print(f"\n[SketchUp] Exported empty room shell to: {out_dae}")
    elif is_sketchup:
        out_dae = export_collada_dae("renders/room_bathroom_furniture.dae", include_furniture=True)
        print(f"\n[SketchUp] Exported room + fixtures to: {out_dae}")

    if is_render:
        out_png = Path("renders/bathroom_preview.png").resolve()
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

