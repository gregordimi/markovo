"""
==============================================================================
MARKOVO RESIDENTIAL ARCHITECTURAL 3D CAD / BIM MODEL GENERATOR
==============================================================================

Refactored Modular Architecture:
- `cad_markovo.config`: Dimensions, units (CM), vertical heights, layout modes
- `cad_markovo.materials`: PBR & procedural materials:
    * Clay Terracotta Tiles (Kitchen & Living Room)
    * Parallel Parquet Light Coniferous Wood (Bedroom & Attic)
    * Cement Mosaic ("мозайка") for Stairs & Landings
    * White uPVC (External Windows & Balcony Doors)
    * Solid Parapet Walls (matching building walls) + Stone Coping on Terraces
- `cad_markovo.geometry`: 3D CAD mesh generators & architectural assemblies
- `cad_markovo.builder`: FloorPlanBuilder engine with clean opening cutouts
- `cad_markovo.floor3`: Floor 3 (Main Level) specification
- `cad_markovo.floor4`: Floor 4 (Attic Level) specification
- `cad_markovo.scene`: Scene cleanup, lighting rig, cameras, and render helper

Usage:
  Interactive (Blender GUI):
    Open this script in Blender's Text Editor and click 'Run Script' (Alt+P).

  Headless / CLI:
    blender -b --python scripts/blender_floor_plans.py
    blender -b --python scripts/blender_floor_plans.py -- --render
    blender -b --python scripts/blender_floor_plans.py -- --stack --render
==============================================================================
"""

import sys
import os
import site
import importlib
from pathlib import Path

# Ensure user site-packages are on sys.path for Blender Python
_user_site = site.getusersitepackages()
if _user_site and _user_site not in sys.path:
    sys.path.append(_user_site)

# ------------------------------------------------------------------------------
# Robust Path Resolution & Auto-Reloading for Blender Scripting
# ------------------------------------------------------------------------------
def _resolve_script_dir() -> Path:
    """Finds the directory containing this script whether run from CLI or Blender GUI."""
    try:
        return Path(__file__).resolve().parent
    except NameError:
        # Running inside Blender Text Editor where __file__ might be undefined
        import bpy
        space = getattr(getattr(bpy.context, "space_data", None), "text", None)
        if space and space.filepath:
            return Path(space.filepath).resolve().parent
        return Path.cwd() / "scripts"


SCRIPT_DIR = _resolve_script_dir()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# Import modular package
import cad_markovo
from cad_markovo import config, materials, geometry, kitchen, builder, floor3, floor4, scene, cad_export
import furniture
from furniture import kitchen as furniture_kitchen

# Hot-reload all submodules when running iteratively inside Blender's Text Editor
importlib.reload(config)
importlib.reload(materials)
importlib.reload(geometry)
importlib.reload(furniture_kitchen)
importlib.reload(furniture)
importlib.reload(kitchen)
importlib.reload(builder)
importlib.reload(floor3)
importlib.reload(floor4)
importlib.reload(scene)
importlib.reload(cad_export)
importlib.reload(cad_markovo)


# ==============================================================================
# RUNTIME CONFIGURATION
# ==============================================================================
# Set STACK_FLOORS = True to stack Floor 4 directly above Floor 3 in 3D,
# or False to display them side-by-side (matching the 2-panel architectural plot).
STACK_FLOORS = False

# Render and Export configurations
RENDER_DIR = SCRIPT_DIR.parent / "renders"
RENDER_VIEWS = []
EXPORT_BLUEPRINT = False
EXPORT_WIREFRAME = False
EXPORT_DXF = False
EXPORT_SVG = False

CAMERA_ALIAS_MAP = {
    "perspective": "Camera_Perspective",
    "cad": "Camera_Top_CAD",
    "top": "Camera_Top_CAD",
    "cad_top": "Camera_Top_CAD",
    "kitchen": "Camera_Kitchen_Inside",
    "kitchen_inside": "Camera_Kitchen_Inside",
    "kitchen_overview": "Camera_Kitchen_Overview",
    "kitchen_eye": "Camera_Kitchen_Eye",
    "bathroom": "Camera_Bathroom_Overview",
    "bathroom_overview": "Camera_Bathroom_Overview",
    "living_room": "Camera_Living_Room_Overview",
    "living": "Camera_Living_Room_Overview",
    "bedroom": "Camera_Bedroom_Overview",
    "stairs": "Camera_Main_Stairs_Overview",
    "attic_office": "Camera_Attic_Office",
    "attic_bedroom": "Camera_Attic_Bedroom",
}

ALL_CAMERAS = [
    "Camera_Perspective",
    "Camera_Top_CAD",
    "Camera_Kitchen_Inside",
    "Camera_Kitchen_Overview",
    "Camera_Kitchen_Eye",
    "Camera_Bathroom_Overview",
    "Camera_Living_Room_Overview",
    "Camera_Bedroom_Overview",
    "Camera_Main_Stairs_Overview",
    "Camera_Attic_Office",
    "Camera_Attic_Bedroom",
]


def parse_cli_args():
    """Parses optional CLI arguments passed after '--' in Blender CLI."""
    global STACK_FLOORS, RENDER_VIEWS, EXPORT_BLUEPRINT, EXPORT_WIREFRAME, EXPORT_DXF, EXPORT_SVG
    if "--" not in sys.argv:
        return

    args = sys.argv[sys.argv.index("--") + 1 :]
    if "--stack" in args:
        STACK_FLOORS = True
        print("[CLI] Stacking floors vertically in 3D.")
    if "--side-by-side" in args:
        STACK_FLOORS = False
        print("[CLI] Displaying floors side-by-side.")

    if "--render" in args:
        RENDER_VIEWS.extend(["Camera_Perspective", "Camera_Top_CAD"])

    if "--blueprint" in args:
        EXPORT_BLUEPRINT = True
        print("[CLI] Technical CAD blueprint rendering enabled.")

    if "--wireframe" in args:
        EXPORT_WIREFRAME = True
        print("[CLI] Technical wireframe rendering enabled.")

    if "--dxf" in args:
        EXPORT_DXF = True
        print("[CLI] AutoCAD DXF export enabled.")

    if "--svg" in args:
        EXPORT_SVG = True
        print("[CLI] 2D Vector SVG blueprint export enabled.")

    if "--all" in args:
        RENDER_VIEWS.extend(ALL_CAMERAS)
        EXPORT_BLUEPRINT = True
        EXPORT_WIREFRAME = True
        EXPORT_DXF = True
        EXPORT_SVG = True
        print("[CLI] Full export suite enabled (all views, blueprint, wireframe, DXF, SVG).")

    # View parsing: --view kitchen,bathroom or --view all
    for idx, arg in enumerate(args):
        if arg == "--view" and idx + 1 < len(args):
            v_val = args[idx + 1].strip().lower()
            if v_val == "all":
                RENDER_VIEWS = list(ALL_CAMERAS)
            else:
                for token in v_val.split(","):
                    token = token.strip()
                    cam_name = CAMERA_ALIAS_MAP.get(token, token)
                    if cam_name not in RENDER_VIEWS:
                        RENDER_VIEWS.append(cam_name)
            print(f"[CLI] Targeted camera views: {RENDER_VIEWS}")

    if "--help" in args or "-h" in args:
        print("""
Markovo 3D Floor Plans CLI Options:
  --stack         : Stack Floor 4 on top of Floor 3 in 3D
  --side-by-side  : Place Floor 3 and Floor 4 side-by-side (default)
  --render        : Render default perspective and CAD top views
  --view <name>   : Render specific camera views (e.g. --view kitchen,bathroom or --view all)
                    Options: kitchen, kitchen_eye, bathroom, living_room, bedroom, stairs,
                             attic_office, attic_bedroom, perspective, cad, all
  --blueprint     : Render instant Workbench architectural blueprint (white on navy)
  --wireframe     : Render instant Workbench wireframe CAD view
  --dxf           : Export authentic AutoCAD .dxf file with CAD layers & dimensions
  --svg           : Export 2D vector SVG architectural blueprint sheets
  --all           : Run complete render & export pipeline
  -h, --help      : Show this help message
""")


# ==============================================================================
# MAIN ORCHESTRATOR
# ==============================================================================
def main():
    parse_cli_args()

    print("\n" + "=" * 70)
    print("  MARKOVO 3D ARCHITECTURAL MODEL GENERATION")
    print("=" * 70)

    # 1. Clean previous scene
    print("[1/5] Clearing existing scene data and collections...")
    scene.clear_scene()

    # 2. Build Material Palette
    print("[2/5] Creating PBR and procedural architectural materials...")
    mats = materials.create_materials()
    print(f"      - Loaded {len(mats)} materials:")
    print("        * White uPVC (External Doors & Windows)")
    print("        * Poly Haven Terracotta Floor Tiles (Kitchen & Living Room)")
    print("        * Poly Haven Worn Wood Floor (Bedroom & Attic)")
    print("        * Poly Haven Concrete Floor 01 (Main Stairs & Landings)")
    print("        * Poly Haven White Maple Veneer (Internal Stairs)")
    print("        * Satin Aluminum Railing (Main Stairs)")
    print("        * Terrace Parapets (Matching Wall Material) + Stone Coping")

    # 3. Build Floor 3 (Main Level)
    print("[3/5] Constructing Floor 3 (Main Level)...")
    f3 = floor3.build_floor_3(mats, offset=(0.0, 0.0, 0.0))

    # 4. Build Floor 4 (Attic Level)
    print(f"[4/5] Constructing Floor 4 (Attic Level, stacked={STACK_FLOORS})...")
    f4 = floor4.build_floor_4(mats, stack=STACK_FLOORS)

    # 5. Lighting & Cameras
    print("[5/5] Setting up architectural studio lighting and cameras...")
    scene.setup_lighting_and_cameras(stack=STACK_FLOORS)

    print("\n" + "-" * 70)
    print("  3D Floor Plans successfully constructed!")
    print(f"  Floor 3 Walls: {len(f3.walls)} | Windows: {len(f3.windows)} | Doors: {len(f3.doors)} | Terraces: {len(f3.terraces)} | Dimensions: {len(f3.dim_col.objects)}")
    print(f"  Floor 4 Walls: {len(f4.walls)} | Windows: {len(f4.windows)} | Doors: {len(f4.doors)} | Terraces: {len(f4.terraces)} | Dimensions: {len(f4.dim_col.objects)}")
    print("-" * 70)

    RENDER_DIR.mkdir(parents=True, exist_ok=True)

    # A. AutoCAD DXF Export
    if EXPORT_DXF:
        dxf_path = RENDER_DIR / ("markovo_stacked.dxf" if STACK_FLOORS else "markovo_floor_plans.dxf")
        print(f"\n[CAD] Exporting AutoCAD DXF (R2018) to: {dxf_path}")
        cad_export.export_to_dxf([f3, f4], str(dxf_path))

    # B. 2D Vector SVG Export
    if EXPORT_SVG:
        svg_f3 = RENDER_DIR / "markovo_floor3_blueprint.svg"
        svg_f4 = RENDER_DIR / "markovo_floor4_blueprint.svg"
        print(f"\n[CAD] Exporting 2D Vector SVG blueprints to: {svg_f3.name}, {svg_f4.name}")
        cad_export.export_to_svg(f3, str(svg_f3), style="blueprint")
        cad_export.export_to_svg(f4, str(svg_f4), style="blueprint")

    # C. Technical Blueprint (Workbench)
    if EXPORT_BLUEPRINT:
        bp_out = RENDER_DIR / ("markovo_blueprint_stacked.png" if STACK_FLOORS else "markovo_blueprint_cad_top.png")
        print(f"\n[Workbench] Rendering technical CAD blueprint to: {bp_out}")
        scene.render_workbench_blueprint(bp_out, camera_name="Camera_Top_CAD", style="blueprint", resolution=(1920, 1080))

    # D. Technical Wireframe (Workbench)
    if EXPORT_WIREFRAME:
        wf_out = RENDER_DIR / ("markovo_wireframe_stacked.png" if STACK_FLOORS else "markovo_wireframe_cad_top.png")
        print(f"\n[Workbench] Rendering technical wireframe to: {wf_out}")
        scene.render_workbench_blueprint(wf_out, camera_name="Camera_Top_CAD", style="wireframe", resolution=(1920, 1080))

    # E. Targeted Camera Renders (Cycles)
    if RENDER_VIEWS:
        unique_views = list(dict.fromkeys(RENDER_VIEWS))
        print(f"\n[Render] Rendering {len(unique_views)} view(s) via Cycles CPU...")
        for cam_name in unique_views:
            clean_name = cam_name.lower().replace("camera_", "")
            view_out = RENDER_DIR / f"markovo_{clean_name}.png"
            scene.render_to_file(view_out, camera_name=cam_name, resolution=(1920, 1080))

    print("\n[Done] Pipeline execution finished successfully!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()