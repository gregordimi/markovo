"""
Scene management, architectural lighting, cameras, and rendering utilities.
"""

import math
from pathlib import Path
from typing import List, Tuple
import bpy
from mathutils import Vector
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


def create_camera(
    name: str,
    location: Tuple[float, float, float],
    target: Tuple[float, float, float] = None,
    rotation_euler: Tuple[float, float, float] = None,
    lens: float = 28.0,
    ortho: bool = False,
    ortho_scale: float = 10.0,
    clip_start: float = 0.1,
    col: bpy.types.Collection = None,
) -> bpy.types.Object:
    """Creates a perspective or orthographic camera aimed at a target coordinate or Euler angle."""
    cam_data = bpy.data.cameras.new(name=name)
    if ortho:
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = ortho_scale
    else:
        cam_data.type = "PERSP"
        cam_data.lens = lens
    cam_data.clip_start = clip_start

    cam_obj = bpy.data.objects.new(name=name, object_data=cam_data)
    cam_obj.location = location

    if target is not None:
        loc_v = Vector(location)
        tgt_v = Vector(target)
        direction = tgt_v - loc_v
        if direction.length > 1e-6:
            cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    elif rotation_euler is not None:
        cam_obj.rotation_euler = rotation_euler

    if col:
        link_to_collection(cam_obj, col)
    return cam_obj


def setup_lighting_and_cameras(stack: bool = False):
    """Sets up an architectural lighting rig and full suite of macro and room-specific cameras."""
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
    # 3. Macro Perspective Overview Camera
    # --------------------------------------------------------------------------
    persp_loc = (3.5, -8.0, 11.5) if stack else (8.8, -9.2, 16.5)
    persp_rot = (math.radians(42.0), 0.0, 0.0) if stack else (math.radians(38.0), 0.0, 0.0)
    cam_persp = create_camera(
        "Camera_Perspective",
        location=persp_loc,
        rotation_euler=persp_rot,
        lens=32.0,
        col=env_col,
    )
    bpy.context.scene.camera = cam_persp

    # --------------------------------------------------------------------------
    # 4. Top-Down Orthographic CAD Camera
    # --------------------------------------------------------------------------
    cad_loc = (3.5 if stack else 8.8, 5.2, 20.0)
    create_camera(
        "Camera_Top_CAD",
        location=cad_loc,
        rotation_euler=(0.0, 0.0, 0.0),
        ortho=True,
        ortho_scale=13.0 if stack else 22.0,
        col=env_col,
    )

    # --------------------------------------------------------------------------
    # 5. Room-Specific Architectural Cameras (Floor 3)
    # --------------------------------------------------------------------------
    # Kitchen Inside View: standing directly inside the kitchen looking towards the long wall run
    create_camera(
        "Camera_Kitchen_Inside",
        location=(2.5, 7.8, 1.55),
        target=(0.075, 7.8, 0.95),
        lens=20.0,
        col=env_col,
    )

    # Kitchen Overview: standing at the kitchen entrance looking North along the linear run
    create_camera(
        "Camera_Kitchen_Overview",
        location=(2.2, 5.2, 1.65),
        target=(0.35, 8.0, 0.95),
        lens=22.0,
        col=env_col,
    )

    # Kitchen Eye-Level: standing near the north window looking South along the worktop & tall fridge
    create_camera(
        "Camera_Kitchen_Eye",
        location=(2.3, 9.8, 1.55),
        target=(0.35, 7.2, 0.95),
        lens=22.0,
        col=env_col,
    )

    # Bathroom Overview: elevated cutaway looking down into fixtures and tile layout
    create_camera(
        "Camera_Bathroom_Overview",
        location=(1.15, 1.6, 4.0),
        target=(1.15, 3.7, 0.7),
        lens=24.0,
        col=env_col,
    )

    # Living Room Overview: elevated view of living area, internal stair base, and balcony opening
    create_camera(
        "Camera_Living_Room_Overview",
        location=(2.6, 3.8, 4.2),
        target=(5.25, 7.1, 0.9),
        lens=24.0,
        col=env_col,
    )

    # Bedroom Overview (Floor 3)
    create_camera(
        "Camera_Bedroom_Overview",
        location=(2.6, -0.4, 3.8),
        target=(5.38, 3.1, 0.8),
        lens=24.0,
        col=env_col,
    )

    # Main Stairs & Railing Overview
    create_camera(
        "Camera_Main_Stairs_Overview",
        location=(1.8, -0.6, 3.6),
        target=(1.8, 1.6, 1.2),
        lens=28.0,
        col=env_col,
    )

    # --------------------------------------------------------------------------
    # 6. Room-Specific Architectural Cameras (Floor 4 Attic)
    # --------------------------------------------------------------------------
    ox, oy, oz = (0.0, 0.0, 2.95) if stack else (10.5, 0.0, 0.0)

    # Attic Office Overview
    create_camera(
        "Camera_Attic_Office",
        location=(ox + 2.6, oy - 0.4, oz + 3.8),
        target=(ox + 5.3, oy + 3.1, oz + 0.8),
        lens=24.0,
        col=env_col,
    )

    # Attic Bedroom & Sloped Ceiling Overview
    create_camera(
        "Camera_Attic_Bedroom",
        location=(ox + 2.6, oy + 4.2, oz + 4.0),
        target=(ox + 5.3, oy + 7.5, oz + 0.8),
        lens=24.0,
        col=env_col,
    )

    # --------------------------------------------------------------------------
    # 7. Clean Architectural Studio Background
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


def set_dimensions_visibility(visible: bool):
    """Toggles render visibility for dimension collections."""
    for col_name in ("Floor_3_Main_Level_Dimensions", "Floor_4_Attic_Level_Dimensions"):
        col = bpy.data.collections.get(col_name)
        if col:
            col.hide_render = not visible
            col.hide_viewport = not visible


def render_to_file(
    filepath: str,
    camera_name: str = "Camera_Perspective",
    resolution=(1920, 1080),
    samples: int = 32,
    show_dimensions: bool = None,
):
    """Renders the current scene from the specified camera to an image file using Cycles."""
    cam = bpy.data.objects.get(camera_name)
    if not cam:
        print(f"Warning: Camera '{camera_name}' not found.")
        return

    # By default, show dimensions for top CAD, hide for 3D perspective beauty shots
    if show_dimensions is None:
        show_dimensions = "Top_CAD" in camera_name or "CAD" in camera_name
    set_dimensions_visibility(show_dimensions)

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


def render_workbench_blueprint(
    filepath: str,
    camera_name: str = "Camera_Top_CAD",
    style: str = "blueprint",
    resolution=(1920, 1080),
    show_dimensions: bool = True,
):
    """
    Renders an instant technical blueprint or wireframe image using Blender's Workbench engine.
    Styles:
      'blueprint': classic dark navy architectural blueprint with white linework & cavity shading.
      'cad_white': clean technical paper with dark ink lines.
      'wireframe': full 3D wireframe topology.
    """
    cam = bpy.data.objects.get(camera_name)
    if not cam:
        print(f"Warning: Camera '{camera_name}' not found for Workbench render.")
        return

    set_dimensions_visibility(show_dimensions)

    scene = bpy.context.scene
    scene.camera = cam
    original_engine = scene.render.engine
    scene.render.engine = "BLENDER_WORKBENCH"

    shading = scene.display.shading
    shading.show_cavity = True
    shading.cavity_type = "BOTH"
    shading.cavity_ridge_factor = 2.0
    shading.cavity_valley_factor = 1.5

    if style == "blueprint":
        shading.type = "SOLID"
        shading.light = "FLAT"
        shading.color_type = "SINGLE"
        shading.single_color = (0.04, 0.12, 0.26)  # Deep architectural navy blue
        shading.show_object_outline = True
        shading.object_outline_color = (0.95, 0.96, 1.0)  # Crisp white outline
    elif style == "wireframe":
        shading.type = "WIREFRAME"
        shading.show_xray_wireframe = True
        shading.xray_alpha_wireframe = 0.8
    elif style == "cad_white":
        shading.type = "SOLID"
        shading.light = "FLAT"
        shading.color_type = "SINGLE"
        shading.single_color = (0.96, 0.96, 0.97)  # Clean drafting paper
        shading.show_object_outline = True
        shading.object_outline_color = (0.1, 0.1, 0.1)  # Technical black ink
    else:
        shading.type = "SOLID"

    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.filepath = str(filepath)

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    print(f"[Workbench] Rendering {style} '{camera_name}' ({resolution[0]}x{resolution[1]}) to {filepath}...")
    bpy.ops.render.render(write_still=True)
    print(f"[Workbench] Render complete: {filepath}")

    # Restore engine
    scene.render.engine = original_engine
