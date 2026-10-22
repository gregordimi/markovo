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
import importlib
from pathlib import Path

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
from cad_markovo import config, materials, geometry, builder, floor3, floor4, scene

# Hot-reload all submodules when running iteratively inside Blender's Text Editor
importlib.reload(config)
importlib.reload(materials)
importlib.reload(geometry)
importlib.reload(builder)
importlib.reload(floor3)
importlib.reload(floor4)
importlib.reload(scene)
importlib.reload(cad_markovo)


# ==============================================================================
# RUNTIME CONFIGURATION
# ==============================================================================
# Set STACK_FLOORS = True to stack Floor 4 directly above Floor 3 in 3D,
# or False to display them side-by-side (matching the 2-panel architectural plot).
STACK_FLOORS = False

# Set RENDER_IMAGES = True to automatically render still images to renders/
RENDER_IMAGES = False
RENDER_DIR = SCRIPT_DIR.parent / "renders"


def parse_cli_args():
    """Parses optional CLI arguments passed after '--' in Blender CLI."""
    global STACK_FLOORS, RENDER_IMAGES
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
        RENDER_IMAGES = True
        print(f"[CLI] Automatic rendering enabled. Output dir: {RENDER_DIR}")
    if "--help" in args or "-h" in args:
        print("""
Markovo 3D Floor Plans CLI Options:
  --stack         : Stack Floor 4 on top of Floor 3 in 3D
  --side-by-side  : Place Floor 3 and Floor 4 side-by-side (default)
  --render        : Render perspective and CAD views to renders/
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
    print(f"  Floor 3 Walls: {len(f3.walls)} | Windows: {len(f3.windows)} | Doors: {len(f3.doors)} | Terraces: {len(f3.terraces)}")
    print(f"  Floor 4 Walls: {len(f4.walls)} | Windows: {len(f4.windows)} | Doors: {len(f4.doors)} | Terraces: {len(f4.terraces)}")
    print("-" * 70)

    # Optional Rendering
    if RENDER_IMAGES:
        RENDER_DIR.mkdir(parents=True, exist_ok=True)
        persp_out = RENDER_DIR / ("markovo_stacked_perspective.png" if STACK_FLOORS else "markovo_floor_plans_perspective.png")
        ortho_out = RENDER_DIR / ("markovo_stacked_cad_top.png" if STACK_FLOORS else "markovo_floor_plans_cad_top.png")

        print(f"\n[Render] Rendering perspective overview to: {persp_out}")
        scene.render_to_file(persp_out, camera_name="Camera_Perspective", resolution=(1920, 1080))

        print(f"[Render] Rendering top-down CAD orthographic view to: {ortho_out}")
        scene.render_to_file(ortho_out, camera_name="Camera_Top_CAD", resolution=(1920, 1080))
        print("[Render] All renders completed successfully!")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()