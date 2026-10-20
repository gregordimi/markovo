"""
PBR & Procedural Material Library for Markovo 3D Architectural CAD.

Includes:
- White uPVC for external windows and exterior doors
- Clay terracotta tiles for Kitchen and Living Room
- Parallel parquet light coniferous wood for Bedroom and Attic
- Cement mosaic / terrazzo for Stairs and stair landings
- Solid wall material matching terraces and structural walls
- Architectural stone terrace coping
- Glazing, interior wood doors, slabs, shafts, and text materials
"""

from pathlib import Path
import bpy


def make_pbr_material(
    name: str,
    rgba: tuple,
    roughness: float = 0.5,
    metallic: float = 0.0,
    transmission: float = 0.0,
) -> bpy.types.Material:
    """Creates a standard Principled BSDF material compatible with Blender 3.x, 4.x, and 5.x."""
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = rgba

    if hasattr(mat, "use_nodes"):
        try:
            mat.use_nodes = True
        except Exception:
            pass

    tree = mat.node_tree
    if tree:
        bsdf = tree.nodes.get("Principled BSDF")
        if bsdf:
            if "Base Color" in bsdf.inputs:
                bsdf.inputs["Base Color"].default_value = rgba
            if "Roughness" in bsdf.inputs:
                bsdf.inputs["Roughness"].default_value = roughness
            if "Metallic" in bsdf.inputs:
                bsdf.inputs["Metallic"].default_value = metallic
            if "Alpha" in bsdf.inputs:
                bsdf.inputs["Alpha"].default_value = rgba[3]
            if transmission > 0:
                if "Transmission Weight" in bsdf.inputs:
                    bsdf.inputs["Transmission Weight"].default_value = transmission
                elif "Transmission" in bsdf.inputs:
                    bsdf.inputs["Transmission"].default_value = transmission

    # Glass and semi-transparent alpha handling
    if rgba[3] < 1.0 or transmission > 0:
        if hasattr(mat, "blend_method"):
            mat.blend_method = "BLEND"
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"

    return mat


def load_polyhaven_tiles_material(name: str = "Clay_Tiles_Mat") -> bpy.types.Material:
    """
    Loads Poly Haven's 'brown_floor_tiles' scanned PBR material from the assets/ folder.
    Configures viewport diffuse preview color and ensures valid texture paths.
    Falls back gracefully to procedural `create_clay_tiles_material()` if the asset is missing.
    """
    repo_root = Path(__file__).resolve().parents[2]
    candidate_paths = [
        repo_root / "assets" / "brown_floor_tiles_4k.blend" / "brown_floor_tiles_4k.blend",
        repo_root / "assets" / "brown_floor_tiles_4k.blend",
        repo_root / "assets" / "brown_floor_tiles.blend",
    ]

    blend_file = None
    for p in candidate_paths:
        if p.is_file():
            blend_file = p
            break

    if not blend_file:
        print("[Materials] Poly Haven blend file not found in assets/. Falling back to procedural cotto tiles.")
        return create_clay_tiles_material(name=name)

    try:
        with bpy.data.libraries.load(str(blend_file), link=False) as (data_from, data_to):
            if "brown_floor_tiles" in data_from.materials:
                data_to.materials = ["brown_floor_tiles"]
            elif data_from.materials:
                data_to.materials = [data_from.materials[0]]

        loaded_mat = bpy.data.materials.get("brown_floor_tiles")
        if not loaded_mat:
            print("[Materials] 'brown_floor_tiles' material not found in library. Falling back to procedural.")
            return create_clay_tiles_material(name=name)

        # Set rich warm terracotta viewport diffuse color
        loaded_mat.diffuse_color = (0.58, 0.32, 0.18, 1.0)
        loaded_mat.name = name

        # Mark as asset so it appears in Blender's Asset Browser
        try:
            if not getattr(loaded_mat, "asset_data", None):
                loaded_mat.asset_mark()
        except Exception:
            pass

        # Verify and fix texture image paths if needed
        textures_dir = blend_file.parent / "textures"
        if loaded_mat.node_tree:
            for node in loaded_mat.node_tree.nodes:
                if node.type == "TEX_IMAGE" and node.image:
                    img_path = Path(bpy.path.abspath(node.image.filepath))
                    if not img_path.exists():
                        local_match = textures_dir / Path(node.image.filepath).name
                        if local_match.exists():
                            node.image.filepath = str(local_match)
                            node.image.reload()

        return loaded_mat

    except Exception as e:
        print(f"[Materials] Warning: Failed to load Poly Haven material ({e}). Falling back to procedural.")
        return create_clay_tiles_material(name=name)


def create_clay_tiles_material(name: str = "Clay_Tiles_Mat") -> bpy.types.Material:
    """
    Creates artisanal Mediterranean terracotta/cotto floor tiles matched to the reference photo.
    Square tiles (~31x31 cm) with natural cloudy mottling across the surface and dark cement grout.
    """
    mat = bpy.data.materials.new(name=name)
    # Viewport color: rich warm burnt terracotta
    mat.diffuse_color = (0.64, 0.34, 0.18, 1.0)

    if hasattr(mat, "use_nodes"):
        try:
            mat.use_nodes = True
        except Exception:
            pass

    tree = mat.node_tree
    if not tree:
        return mat

    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    # Output node
    out_node = nodes.new("ShaderNodeOutputMaterial")
    out_node.location = (650, 0)

    # Principled BSDF
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (350, 0)
    bsdf.inputs["Roughness"].default_value = 0.65  # Natural matte fired cotto finish
    bsdf.inputs["Metallic"].default_value = 0.0

    # Texture Coordinate & Mapping
    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-650, 0)

    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-450, 0)
    mapping.inputs["Scale"].default_value = (3.2, 3.2, 3.2)  # ~31x31 cm square tiles

    # Brick Texture for square cotto tiles
    brick = nodes.new("ShaderNodeTexBrick")
    brick.location = (-200, 100)
    brick.inputs["Color1"].default_value = (0.66, 0.36, 0.20, 1.0)  # Primary warm terracotta
    brick.inputs["Color2"].default_value = (0.54, 0.28, 0.15, 1.0)  # Slightly darker baked clay
    brick.inputs["Mortar"].default_value = (0.42, 0.38, 0.35, 1.0)  # Darker grey-brown cement grout
    brick.inputs["Mortar Size"].default_value = 0.012               # Clean ~4 mm grout joint
    brick.inputs["Mortar Smooth"].default_value = 0.1
    brick.inputs["Bias"].default_value = 0.05
    brick.inputs["Brick Width"].default_value = 1.0                 # Square tile ratio
    brick.inputs["Row Height"].default_value = 1.0

    # Noise texture for artisanal fired-clay cloudy mottling (as seen in photo)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-200, -150)
    noise.inputs["Scale"].default_value = 14.0
    noise.inputs["Detail"].default_value = 3.5
    noise.inputs["Roughness"].default_value = 0.6

    # Mix cloudy mottling over the brick tiles
    mix = nodes.new("ShaderNodeMix")
    mix.location = (100, 0)
    mix.data_type = "RGBA"
    mix.blend_type = "OVERLAY"
    mix.inputs["Factor"].default_value = 0.24

    # Connect nodes
    links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], brick.inputs["Vector"])
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

    links.new(brick.outputs["Color"], mix.inputs[6])
    links.new(noise.outputs["Color"], mix.inputs[7])
    links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], out_node.inputs["Surface"])

    return mat


def create_parquet_light_wood_material(name: str = "Parquet_Coniferous_Light_Mat") -> bpy.types.Material:
    """
    Creates parallel coniferous pine plank flooring ("дюшеме") matched to the reference photo.
    Features continuous parallel planks (~11 cm wide), warm amber/honey pine tones,
    directional wood grain, and scattered natural darker knots.
    """
    mat = bpy.data.materials.new(name=name)
    # Viewport color: rich warm amber pine wood
    mat.diffuse_color = (0.80, 0.54, 0.24, 1.0)

    if hasattr(mat, "use_nodes"):
        try:
            mat.use_nodes = True
        except Exception:
            pass

    tree = mat.node_tree
    if not tree:
        return mat

    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    out_node = nodes.new("ShaderNodeOutputMaterial")
    out_node.location = (800, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (500, 0)
    bsdf.inputs["Roughness"].default_value = 0.34  # Varnished wood floor sheen
    bsdf.inputs["Metallic"].default_value = 0.0

    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-850, 0)

    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-650, 0)
    mapping.inputs["Scale"].default_value = (1.0, 1.0, 1.0)

    # 1. Parallel floorboards using Brick Texture (narrow height, long width)
    brick = nodes.new("ShaderNodeTexBrick")
    brick.location = (-350, 150)
    brick.inputs["Color1"].default_value = (0.82, 0.58, 0.26, 1.0)  # Warm golden pine
    brick.inputs["Color2"].default_value = (0.74, 0.48, 0.20, 1.0)  # Amber pine
    brick.inputs["Mortar"].default_value = (0.32, 0.18, 0.08, 1.0)  # Dark groove between boards
    brick.inputs["Mortar Size"].default_value = 0.005               # Fine tongue-and-groove seam
    brick.inputs["Mortar Smooth"].default_value = 0.05
    brick.inputs["Brick Width"].default_value = 4.5                 # Long continuous boards
    brick.inputs["Row Height"].default_value = 0.11                 # 11 cm board width

    # 2. Longitudinal annual ring wood grain
    wave = nodes.new("ShaderNodeTexWave")
    wave.location = (-350, -100)
    wave.wave_type = "BANDS"
    wave.bands_direction = "X"
    wave.inputs["Scale"].default_value = 24.0
    wave.inputs["Distortion"].default_value = 2.2
    wave.inputs["Detail"].default_value = 3.5

    # 3. Scattered round natural pine knots (Voronoi + ColorRamp)
    voronoi = nodes.new("ShaderNodeTexVoronoi")
    voronoi.location = (-350, -350)
    voronoi.inputs["Scale"].default_value = 5.5
    voronoi.inputs["Randomness"].default_value = 0.9

    cramp = nodes.new("ShaderNodeValToRGB")
    cramp.location = (-100, -350)
    ramp = cramp.color_ramp
    ramp.elements[0].position = 0.0
    ramp.elements[0].color = (0.28, 0.14, 0.05, 1.0)  # Dark knot center
    elem1 = ramp.elements.new(0.08)
    elem1.color = (0.55, 0.32, 0.14, 1.0)             # Knot halo ring
    elem2 = ramp.elements.new(0.12)
    elem2.color = (1.0, 1.0, 1.0, 1.0)                # Clear wood

    # Mix grain with boards
    mix_grain = nodes.new("ShaderNodeMix")
    mix_grain.location = (-50, 50)
    mix_grain.data_type = "RGBA"
    mix_grain.blend_type = "MULTIPLY"
    mix_grain.inputs["Factor"].default_value = 0.16

    # Multiply scattered knots into the wood
    mix_knots = nodes.new("ShaderNodeMix")
    mix_knots.location = (200, 0)
    mix_knots.data_type = "RGBA"
    mix_knots.blend_type = "MULTIPLY"
    mix_knots.inputs["Factor"].default_value = 0.85

    # Wire up
    links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], brick.inputs["Vector"])
    links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
    links.new(mapping.outputs["Vector"], voronoi.inputs["Vector"])

    links.new(brick.outputs["Color"], mix_grain.inputs[6])
    links.new(wave.outputs["Color"], mix_grain.inputs[7])

    links.new(mix_grain.outputs[2], mix_knots.inputs[6])
    links.new(voronoi.outputs["Distance"], cramp.inputs["Fac"])
    links.new(cramp.outputs["Color"], mix_knots.inputs[7])

    links.new(mix_knots.outputs[2], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], out_node.inputs["Surface"])

    return mat


def create_cement_mosaic_material(name: str = "Cement_Mosaic_Stairs_Mat") -> bpy.types.Material:
    """
    Creates cement mosaic / terrazzo ("мозайка") for Stairs & stairwell landings.
    Cement matrix with speckled aggregate mineral chips (basalt, marble, limestone).
    """
    mat = bpy.data.materials.new(name=name)
    # Viewport color: polished architectural cement mosaic
    mat.diffuse_color = (0.75, 0.74, 0.72, 1.0)

    if hasattr(mat, "use_nodes"):
        try:
            mat.use_nodes = True
        except Exception:
            pass

    tree = mat.node_tree
    if not tree:
        return mat

    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    out_node = nodes.new("ShaderNodeOutputMaterial")
    out_node.location = (600, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (300, 0)
    bsdf.inputs["Roughness"].default_value = 0.35  # Polished terrazzo sheen
    bsdf.inputs["Metallic"].default_value = 0.0

    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-600, 0)

    # Voronoi texture for random aggregate mineral chips
    voronoi = nodes.new("ShaderNodeTexVoronoi")
    voronoi.location = (-350, 0)
    voronoi.feature = "F1"
    voronoi.inputs["Scale"].default_value = 40.0  # Crisp mosaic chip size
    voronoi.inputs["Randomness"].default_value = 0.95

    # ColorRamp to map Voronoi cells to terrazzo palette:
    # Cement gray matrix, white calcite chips, dark basalt chips, ochre marble chips
    cramp = nodes.new("ShaderNodeValToRGB")
    cramp.location = (-100, 0)
    ramp = cramp.color_ramp
    ramp.color_mode = "RGB"
    ramp.interpolation = "CONSTANT"

    # Define color stops for authentic terrazzo
    ramp.elements[0].position = 0.0
    ramp.elements[0].color = (0.76, 0.76, 0.75, 1.0)   # Cement matrix

    elem1 = ramp.elements.new(0.35)
    elem1.color = (0.92, 0.92, 0.90, 1.0)              # White marble chip

    elem2 = ramp.elements.new(0.65)
    elem2.color = (0.35, 0.35, 0.36, 1.0)              # Dark basalt chip

    elem3 = ramp.elements.new(0.85)
    elem3.color = (0.72, 0.65, 0.58, 1.0)              # Limestone / quartz chip

    # Links
    links.new(tex_coord.outputs["Object"], voronoi.inputs["Vector"])
    links.new(voronoi.outputs["Distance"], cramp.inputs["Fac"])
    links.new(cramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], out_node.inputs["Surface"])

    return mat


def create_materials() -> dict:
    """Builds and returns the complete material dictionary for Markovo 3D floor plans."""
    mats = {
        # Walls & Enclosures
        "wall": make_pbr_material("Wall_Mat", (0.29, 0.29, 0.29, 1.0), roughness=0.7),
        "wall_cap": make_pbr_material("Wall_Cap_Mat", (0.12, 0.12, 0.12, 1.0), roughness=0.6),

        # Terrace Coping (Architectural stone cap resting on top of terrace parapet walls)
        "terrace_coping": make_pbr_material("Terrace_Coping_Mat", (0.86, 0.85, 0.82, 1.0), roughness=0.5),

        # Floor Finishes (Matched to user reference photos & Poly Haven scanned PBR)
        "clay_tiles": load_polyhaven_tiles_material("brown_floor_tiles"),
        "parquet_light_wood": create_parquet_light_wood_material("Parquet_Coniferous_Light_Mat"),
        "cement_mosaic": create_cement_mosaic_material("Cement_Mosaic_Stairs_Mat"),

        # Structural & Auxiliary Slabs
        "slab": make_pbr_material("Floor_Slab_Mat", (0.92, 0.91, 0.88, 1.0), roughness=0.6),
        "balcony": make_pbr_material("Balcony_Mat", (0.82, 0.82, 0.82, 1.0), roughness=0.7),
        "void": make_pbr_material("Roof_Void_Mat", (0.75, 0.75, 0.77, 1.0), roughness=0.85),
        "shaft": make_pbr_material("Shaft_Mat", (0.85, 0.85, 0.85, 1.0), roughness=0.5),
        "bath_tiles": make_pbr_material("Bath_Tiles_Mat", (0.88, 0.90, 0.92, 1.0), roughness=0.35),

        # Glazing & Windows
        "glass": make_pbr_material(
            "Window_Glass_Mat",
            (0.0, 0.55, 0.55, 0.35),
            roughness=0.06,
            transmission=0.88,
        ),

        # External Joinery: White uPVC for all exterior windows and exterior balcony doors
        "pvc_white": make_pbr_material(
            "PVC_White_Mat",
            (0.95, 0.95, 0.95, 1.0),
            roughness=0.25,
            metallic=0.0,
        ),

        # Interior Joinery: 8-Panel solid wood doors matched to photo + brushed silver hardware
        "door_wood": make_pbr_material(
            "Door_Wood_Mat",
            (0.46, 0.28, 0.14, 1.0),  # Warm chestnut / honey-brown natural pine/oak wood
            roughness=0.38,
            metallic=0.0,
        ),
        "door_frame": make_pbr_material("Door_Frame_Mat", (0.22, 0.16, 0.10, 1.0), roughness=0.4),
        "door_handle": make_pbr_material(
            "Door_Handle_Mat",
            (0.85, 0.85, 0.85, 1.0),  # Brushed silver / satin stainless steel lever handle
            roughness=0.22,
            metallic=0.92,
        ),

        # Annotation & Presentation
        "text": make_pbr_material("Text_Mat", (0.08, 0.08, 0.08, 1.0), roughness=0.4),
        "dim": make_pbr_material("Dim_Mat", (0.0, 0.33, 0.65, 1.0), roughness=0.4),
    }

    # Mark materials as assets so they appear in Blender's Asset Browser under Current File
    for mat in mats.values():
        if mat and hasattr(mat, "asset_mark") and not getattr(mat, "asset_data", None):
            try:
                mat.asset_mark()
            except Exception:
                pass

    return mats
