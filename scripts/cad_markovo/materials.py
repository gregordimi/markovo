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


def create_clay_tiles_material(name: str = "Clay_Tiles_Mat") -> bpy.types.Material:
    """
    Creates rich Mediterranean/Cotto clay tiles for Kitchen & Living Room floors.
    Uses procedural Brick texture with warm terracotta tones and subtle cement grout.
    """
    mat = bpy.data.materials.new(name=name)
    # Viewport color: warm terracotta clay
    mat.diffuse_color = (0.72, 0.36, 0.20, 1.0)

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
    out_node.location = (500, 0)

    # Principled BSDF
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (200, 0)
    bsdf.inputs["Roughness"].default_value = 0.68
    bsdf.inputs["Metallic"].default_value = 0.0

    # Texture Coordinate & Mapping
    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-600, 0)

    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-400, 0)
    mapping.inputs["Scale"].default_value = (3.0, 3.0, 3.0)  # ~33x33 cm tiles

    # Brick Texture for square clay tiles
    brick = nodes.new("ShaderNodeTexBrick")
    brick.location = (-150, 0)
    brick.inputs["Color1"].default_value = (0.74, 0.38, 0.22, 1.0)  # Primary terracotta
    brick.inputs["Color2"].default_value = (0.66, 0.31, 0.16, 1.0)  # Darker baked clay
    brick.inputs["Mortar"].default_value = (0.80, 0.78, 0.74, 1.0)  # Light cement grout
    brick.inputs["Mortar Size"].default_value = 0.015               # Clean grout line
    brick.inputs["Mortar Smooth"].default_value = 0.1
    brick.inputs["Bias"].default_value = 0.1
    brick.inputs["Brick Width"].default_value = 1.0                # Square tile ratio
    brick.inputs["Row Height"].default_value = 1.0

    # Links
    links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], brick.inputs["Vector"])
    links.new(brick.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], out_node.inputs["Surface"])

    return mat


def create_parquet_light_wood_material(name: str = "Parquet_Coniferous_Light_Mat") -> bpy.types.Material:
    """
    Creates parallel parquet light coniferous wood flooring for Bedroom & Attic.
    Warm pale honey/blonde Scandinavian pine & spruce tones with parallel board strip pattern.
    """
    mat = bpy.data.materials.new(name=name)
    # Viewport color: pale coniferous blonde wood
    mat.diffuse_color = (0.83, 0.71, 0.53, 1.0)

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
    bsdf.inputs["Roughness"].default_value = 0.38  # Satin lacquer finish
    bsdf.inputs["Metallic"].default_value = 0.0

    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-700, 0)

    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-500, 0)
    mapping.inputs["Scale"].default_value = (1.0, 1.0, 1.0)

    # Brick node configured as long parallel strip parquet boards
    brick = nodes.new("ShaderNodeTexBrick")
    brick.location = (-250, 50)
    # Coniferous blonde pine / spruce wood tones
    brick.inputs["Color1"].default_value = (0.85, 0.74, 0.57, 1.0)  # Light golden pine
    brick.inputs["Color2"].default_value = (0.78, 0.65, 0.47, 1.0)  # Warm honey fir
    brick.inputs["Mortar"].default_value = (0.42, 0.32, 0.20, 1.0)  # Fine bevel / shadow groove
    brick.inputs["Mortar Size"].default_value = 0.006               # Fine parquet board joint
    brick.inputs["Mortar Smooth"].default_value = 0.05
    brick.inputs["Brick Width"].default_value = 0.85                # ~85 cm long plank
    brick.inputs["Row Height"].default_value = 0.12                 # ~12 cm wide strip

    # Subtle coniferous wood grain using wave texture
    wave = nodes.new("ShaderNodeTexWave")
    wave.location = (-250, -250)
    wave.wave_type = "BANDS"
    wave.bands_direction = "X"
    wave.inputs["Scale"].default_value = 18.0
    wave.inputs["Distortion"].default_value = 1.8
    wave.inputs["Detail"].default_value = 3.0

    # Mix grain with parquet boards
    mix = nodes.new("ShaderNodeMix")
    mix.location = (50, 0)
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.18

    # Wire up nodes
    links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], brick.inputs["Vector"])
    links.new(mapping.outputs["Vector"], wave.inputs["Vector"])

    links.new(brick.outputs["Color"], mix.inputs[6])      # Color A
    links.new(wave.outputs["Color"], mix.inputs[7])       # Color B
    links.new(mix.outputs[2], bsdf.inputs["Base Color"])
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
    return {
        # Walls & Enclosures
        "wall": make_pbr_material("Wall_Mat", (0.29, 0.29, 0.29, 1.0), roughness=0.7),
        "wall_cap": make_pbr_material("Wall_Cap_Mat", (0.12, 0.12, 0.12, 1.0), roughness=0.6),

        # Terrace Coping (Architectural stone cap resting on top of terrace parapet walls)
        "terrace_coping": make_pbr_material("Terrace_Coping_Mat", (0.86, 0.85, 0.82, 1.0), roughness=0.5),

        # Floor Finishes
        "clay_tiles": create_clay_tiles_material("Clay_Tiles_Mat"),
        "parquet_light_wood": create_parquet_light_wood_material("Parquet_Light_Wood_Mat"),
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

        # Interior Joinery: Warm wood leaves & dark frames for interior doors
        "door_wood": make_pbr_material("Door_Wood_Mat", (0.45, 0.32, 0.22, 1.0), roughness=0.45),
        "door_frame": make_pbr_material("Door_Frame_Mat", (0.18, 0.18, 0.18, 1.0), roughness=0.4),

        # Annotation & Presentation
        "text": make_pbr_material("Text_Mat", (0.08, 0.08, 0.08, 1.0), roughness=0.4),
        "dim": make_pbr_material("Dim_Mat", (0.0, 0.33, 0.65, 1.0), roughness=0.4),
    }
