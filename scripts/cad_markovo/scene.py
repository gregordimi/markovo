"""
Scene management, architectural lighting, cameras, and rendering utilities.
"""

import math
from pathlib import Path
import bpy
from .builder import get_or_create_collection, link_to_collection


def clear_scene():
    """Removes all existing objects, meshes, materials, curves, lights, cameras, and collections."""
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


def setup_lighting_and_cameras(stack: bool = False):
    """Sets up an architectural lighting rig, perspective camera, and top-down CAD camera."""
    env_col = get_or_create_collection("Lighting_And_Cameras")

    # --------------------------------------------------------------------------
    # 1. Architectural Sun Light
    # --------------------------------------------------------------------------
    sun_data = bpy.data.lights.new(name="Sun_Light", type="SUN")
    sun_data.energy = 3.5
    sun_data.angle = math.radians(4.0)
    sun_obj = bpy.data.objects.new(name="Sun_Light", object_data=sun_data)
    sun_obj.location = (8.0, -6.0, 15.0)
    sun_obj.rotation_euler = (math.radians(38.0), math.radians(18.0), math.radians(25.0))
    link_to_collection(sun_obj, env_col)

    # --------------------------------------------------------------------------
    # 2. Subtle Fill Light for Soft Architectural Shadows
    # --------------------------------------------------------------------------
    fill_data = bpy.data.lights.new(name="Fill_Light", type="SUN")
    fill_data.energy = 1.0
    fill_data.angle = math.radians(15.0)
    fill_obj = bpy.data.objects.new(name="Fill_Light", object_data=fill_data)
    fill_obj.location = (-6.0, 8.0, 12.0)
    fill_obj.rotation_euler = (math.radians(-30.0), math.radians(-20.0), math.radians(140.0))
    link_to_collection(fill_obj, env_col)

    # --------------------------------------------------------------------------
    # 3. Perspective Overview Camera
    # --------------------------------------------------------------------------
    cam_data = bpy.data.cameras.new(name="Camera_Perspective")
    cam_data.lens = 32.0
    cam_obj = bpy.data.objects.new(name="Camera_Perspective", object_data=cam_data)
    if stack:
        cam_obj.location = (3.5, -8.0, 11.5)
        cam_obj.rotation_euler = (math.radians(42.0), 0.0, 0.0)
    else:
        cam_obj.location = (8.8, -9.2, 16.5)
        cam_obj.rotation_euler = (math.radians(38.0), 0.0, 0.0)
    link_to_collection(cam_obj, env_col)
    bpy.context.scene.camera = cam_obj

    # --------------------------------------------------------------------------
    # 4. Top-Down Orthographic CAD Camera
    # --------------------------------------------------------------------------
    ortho_data = bpy.data.cameras.new(name="Camera_Top_CAD")
    ortho_data.type = "ORTHO"
    ortho_data.ortho_scale = 13.0 if stack else 22.0
    ortho_obj = bpy.data.objects.new(name="Camera_Top_CAD", object_data=ortho_data)
    ortho_obj.location = (3.5 if stack else 8.8, 5.2, 20.0)
    ortho_obj.rotation_euler = (0.0, 0.0, 0.0)
    link_to_collection(ortho_obj, env_col)

    # --------------------------------------------------------------------------
    # 5. Clean Architectural Studio Background
    # --------------------------------------------------------------------------
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    if hasattr(world, "use_nodes"):
        try:
            world.use_nodes = True
        except Exception:
            pass

    if world.node_tree:
        bg = world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs[0].default_value = (0.95, 0.96, 0.98, 1.0)
            bg.inputs[1].default_value = 0.85


def setup_viewport_shading(shading_mode: str = "MATERIAL"):
    """
    Configures all 3D Viewport spaces to Material Preview mode (or specified mode).
    This ensures PBR materials, scanned image textures, and procedural shaders
    are immediately visible in the interactive Blender viewport instead of default monochrome Solid shading.
    """
    try:
        wm = getattr(bpy.context, "window_manager", None)
        if not wm:
            return
        for window in wm.windows:
            screen = getattr(window, "screen", None)
            if not screen:
                continue
            for area in screen.areas:
                if area.type == "VIEW_3D":
                    for space in area.spaces:
                        if space.type == "VIEW_3D":
                            space.shading.type = shading_mode
    except Exception as e:
        print(f"Notice: Could not set viewport shading ({e})")


def register_project_asset_library():
    """
    Registers the project's assets/ directory in Blender's Preferences
    as an Asset Library named 'Markovo Assets'. This allows materials and models to
    appear directly in the Asset Browser under the 'Markovo Assets' catalog.
    """
    try:
        prefs = bpy.context.preferences.filepaths.asset_libraries
        assets_dir = Path(__file__).resolve().parents[2] / "assets"
        if not assets_dir.exists():
            return

        # Check if already registered
        for lib in prefs:
            if Path(lib.path).resolve() == assets_dir.resolve():
                return
            if lib.name == "Markovo Assets":
                lib.path = str(assets_dir)
                return

        new_lib = prefs.new(name="Markovo Assets")
        new_lib.path = str(assets_dir)
        print(f"      - Registered 'Markovo Assets' library: {assets_dir}")
    except Exception as e:
        print(f"Notice: Could not register asset library in preferences ({e})")



def render_to_file(
    filepath: str,
    camera_name: str = "Camera_Perspective",
    resolution=(1920, 1080),
    samples: int = 32,
):
    """Renders the current scene from the specified camera to an image file using Cycles."""
    cam = bpy.data.objects.get(camera_name)
    if not cam:
        print(f"Warning: Camera {camera_name} not found.")
        return

    scene = bpy.context.scene
    scene.camera = cam
    scene.render.engine = "CYCLES"
    if hasattr(scene, "cycles"):
        scene.cycles.device = "CPU"
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True

    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.filepath = str(filepath)

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    print(f"Rendering view '{camera_name}' ({resolution[0]}x{resolution[1]}, {samples} samples) to {filepath}...")
    bpy.ops.render.render(write_still=True)
    print(f"Render complete: {filepath}")
