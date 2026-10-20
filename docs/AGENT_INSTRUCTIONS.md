# Markovo CAD — Agentic Instructions & Architecture Guide

This document defines the instructions, design principles, architecture, and developer workflows for AI agents (and human engineers) working on the **Markovo 3D Architectural CAD / BIM** project.

---

## 1. Project Overview

The project programmatically models and visualizes the 3D architectural floor plans for a residential building in Markovo. The model is built using Blender's Python API (`bpy` and `bmesh`) with precision 2D-to-3D parametric extrusion, clean collinear opening cutouts, procedural PBR materials, and camera/lighting rigs.

### Key Outputs:
- **Floor 3 (Main Level)**: Living room, kitchen, bedroom, bathroom, utility, stairwell landing, internal stairs, and 3 exterior balconies/terraces.
- **Floor 4 (Attic Level)**: Attic main room, attic bedroom, circulation, stairwell landing, internal stairs, unusable roof void, and 2 exterior balconies/terraces.
- **Renders**: High-resolution perspective and top-down CAD orthographic views saved to [`renders/`](file:///Users/gdimitrov/projects/markovo/renders).

---

## 2. Directory Structure & Module Responsibilities

The codebase is structured into a clean modular package under [`scripts/cad_markovo/`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo) orchestrated by [`scripts/blender_floor_plans.py`](file:///Users/gdimitrov/projects/markovo/scripts/blender_floor_plans.py):

```
markovo/
├── AGENTS.md                                # Root agentic cheatsheet
├── README.md                                # Human-facing project overview
├── .gitignore                               # Blender and render ignore rules
├── docs/
│   ├── AGENT_INSTRUCTIONS.md                # This comprehensive agent guide
│   └── MATERIALS_GUIDE.md                   # Deep-dive into materials & shader nodes
├── renders/                                 # Rendered CAD and perspective images
└── scripts/
    ├── blender_floor_plans.py               # Main CLI & Blender GUI orchestrator
    └── cad_markovo/                         # Core Python package
        ├── __init__.py                      # Package exports
        ├── config.py                        # Units, architectural heights, settings
        ├── materials.py                     # Procedural & PBR material library
        ├── geometry.py                      # 3D CAD mesh primitives & fixtures
        ├── builder.py                       # FloorPlanBuilder engine (cutouts & slabs)
        ├── floor3.py                        # Floor 3 (Main Level) declarative data
        ├── floor4.py                        # Floor 4 (Attic Level) declarative data
        └── scene.py                         # Scene clearing, lighting, cameras, Cycles
```

### Module Responsibilities:

| File | Primary Role |
| :--- | :--- |
| [`config.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/config.py) | Defines `CM = 0.01` conversion factor, vertical levels (`WALL_HEIGHT`, `SLAB_THICK`, `DOOR_HEIGHT`, `WIN_SILL`, `WIN_TOP`, `TERRACE_PARAPET_HEIGHT`, `TERRACE_COPING_THICKNESS`), and layout flags (`STACK_FLOORS`). |
| [`materials.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/materials.py) | Central material factory: procedural clay tiles, parallel light parquet, cement mosaic terrazzo, white uPVC, stone coping, and PBR shaders. |
| [`geometry.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/geometry.py) | Low-level mesh geometry: `create_prism_from_quad`, `create_extruded_polygon`, `wall_quad`, uPVC windows, doors with swing arcs, stairs, solid terrace parapets, and coping. |
| [`builder.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/builder.py) | [`FloorPlanBuilder`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/builder.py#L40) class: manages object collections, root empties, automated collinear wall opening cutouts, lintels, sills, and room finishes. |
| [`floor3.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/floor3.py) | Declarative floor specification for Floor 3 (rooms, walls, openings, stairs, balconies). |
| [`floor4.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/floor4.py) | Declarative floor specification for Floor 4 Attic. |
| [`scene.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/scene.py) | Scene reset, studio sun/fill lighting rig, cameras (Perspective & CAD Ortho), and Cycles CPU rendering. |
| [`blender_floor_plans.py`](file:///Users/gdimitrov/projects/markovo/scripts/blender_floor_plans.py) | Top-level runner, CLI argument parser (`--render`, `--stack`), and hot-reloader for Blender's internal Python environment. |

---

## 3. Coordinate Systems & Architectural Conventions

1. **Units**:
   - 2D horizontal coordinates $(x, y)$ in input definitions are in **centimeters** ($100\text{ cm} = 1.0\text{ m}$).
   - The global constant `CM = 0.01` converts centimeters to Blender meters.
   - 3D vertical bounds $(z_{\text{bottom}}, z_{\text{top}})$ are in **meters**.

2. **Standard Vertical Levels**:
   - Floor slab top / finished floor level: $z = 0.00\text{ m}$
   - Floor slab bottom: $z = -0.15\text{ m}$ (`-SLAB_THICK`)
   - Window sill: $z = 0.00\text{ m}$ to $0.90\text{ m}$ (`WIN_SILL`)
   - Window head / lintel: $z = 2.10\text{ m}$ (`WIN_TOP`) to $2.80\text{ m}$ (`WALL_HEIGHT`)
   - Door head lintel: $z = 2.10\text{ m}$ (`DOOR_HEIGHT`) to $2.80\text{ m}$ (`WALL_HEIGHT`)
   - Solid wall: $z = 0.00\text{ m}$ to $2.80\text{ m}$ (`WALL_HEIGHT`)
   - Terrace parapet wall: $z = 0.00\text{ m}$ to $0.95\text{ m}$ (`TERRACE_PARAPET_HEIGHT`)
   - Terrace stone coping: $z = 0.95\text{ m}$ to $1.00\text{ m}$ (`TERRACE_TOTAL_HEIGHT`) with $2.5\text{ cm}$ overhang on both sides ($20\text{ cm}$ wide).

3. **Multi-Floor Layout Options**:
   - `STACK_FLOORS = False`: Floor 3 at $(0, 0, 0)$ and Floor 4 at $(10.5, 0, 0)$ side-by-side for 2-panel CAD review.
   - `STACK_FLOORS = True`: Floor 4 stacked directly above Floor 3 at $(0, 0, \text{WALL\_HEIGHT} + \text{SLAB\_THICK})$.

---

## 4. Materials Architecture & How to Change Them

Materials are defined in [`scripts/cad_markovo/materials.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/materials.py) and registered in `create_materials() -> dict`.

### 4.1 Current Material Palette

| Material Key | Material Name | Type | Assigned Location |
| :--- | :--- | :--- | :--- |
| `"clay_tiles"` | `Clay_Tiles_Mat` | Procedural Brick Node | Kitchen, Living Room, Hallway, Utility |
| `"parquet_light_wood"` | `Parquet_Light_Wood_Mat` | Procedural Brick + Wave | Floor 3 Bedroom, Floor 4 Attic Rooms & Hallway |
| `"cement_mosaic"` | `Cement_Mosaic_Stairs_Mat` | Procedural Voronoi + Ramp | All Stairs (treads/risers) & Stair Landings |
| `"pvc_white"` | `PVC_White_Mat` | PBR Smooth Gloss | All External Windows (frames/mullions) & Balcony Doors |
| `"wall"` | `Wall_Mat` | PBR Architectural Gray | All Structural & Partition Walls, Terrace Parapet Walls |
| `"terrace_coping"` | `Terrace_Coping_Mat` | PBR Architectural Stone | Stone Coping on all Terrace Parapets |
| `"glass"` | `Window_Glass_Mat` | PBR Transmission Glass | Window & Balcony Door Double-Glazing Panes |
| `"door_wood"` | `Door_Wood_Mat` | PBR Natural Wood | Interior Door Leaves |
| `"door_frame"` | `Door_Frame_Mat` | PBR Dark Trim | Interior Door Frames & Heads |
| `"void"` | `Roof_Void_Mat` | PBR Neutral Void | Attic West Unusable Roof Void Area |
| `"bath_tiles"` | `Bath_Tiles_Mat` | PBR Semi-Gloss Ceramic | Bathroom Floor Slab |
| `"shaft"` | `Shaft_Mat` | PBR Plaster | Bathroom Plumbing/Ventilation Shaft |

---

### 4.2 How to Change Material Colors & Properties

#### A. Adjusting an existing PBR material (e.g. White uPVC or Wall):
Locate `create_materials()` in [`scripts/cad_markovo/materials.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/materials.py#L210):
```python
# To change White uPVC to Anthracite Grey (RAL 7016):
"pvc_white": make_pbr_material(
    "PVC_Anthracite_Mat",
    (0.22, 0.23, 0.25, 1.0),  # Dark charcoal/anthracite RGBA
    roughness=0.35,
    metallic=0.0,
),
```

#### B. Modifying Clay Terracotta Tiles:
In `create_clay_tiles_material()` ([`materials.py:53`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/materials.py#L53)):
- **Tile Color 1 & 2**: Change `brick.inputs["Color1"]` and `Color2`.
- **Grout Color & Width**: Change `brick.inputs["Mortar"]` (default: light cement `(0.80, 0.78, 0.74)`) and `brick.inputs["Mortar Size"]` (default: `0.015`).
- **Tile Dimensions / Scale**: Adjust `mapping.inputs["Scale"]` (default: `(3.0, 3.0, 3.0)` for $\sim 33 \times 33\text{ cm}$ tiles).

#### C. Modifying Parallel Parquet Light Coniferous Wood:
In `create_parquet_light_wood_material()` ([`materials.py:105`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/materials.py#L105)):
- **Plank Dimensions**: `brick.inputs["Brick Width"] = 0.85` ($85\text{ cm}$ length) and `brick.inputs["Row Height"] = 0.12` ($12\text{ cm}$ strip width).
- **Wood Tones**: Change `Color1` (golden pine) and `Color2` (warm honey fir). For darker oak, use `(0.48, 0.35, 0.22, 1.0)`.
- **Wood Grain Intensity**: Adjust `mix.inputs["Factor"]` (default: `0.18`).

#### D. Modifying Cement Mosaic ("Мозайка") for Stairs:
In `create_cement_mosaic_material()` ([`materials.py:170`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/materials.py#L170)):
- **Aggregate Chip Density / Size**: Change `voronoi.inputs["Scale"]` (default: `40.0`).
- **Chip Colors**: In `cramp.color_ramp`, adjust the stops:
  - Stop 0 (`0.00`): Cement gray matrix `(0.76, 0.76, 0.75)`.
  - Stop 1 (`0.35`): White marble / calcite chips `(0.92, 0.92, 0.90)`.
  - Stop 2 (`0.65`): Dark basalt chips `(0.35, 0.35, 0.36)`.
  - Stop 3 (`0.85`): Limestone / quartz chips `(0.72, 0.65, 0.58)`.
- **Finish / Polish**: Change `bsdf.inputs["Roughness"]` (default: `0.35` for polished terrazzo sheen).

---

### 4.3 How to Create and Register a New Material

1. In [`scripts/cad_markovo/materials.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/materials.py), define the function:
   ```python
   def create_marble_slab_material(name: str = "Marble_White_Mat") -> bpy.types.Material:
       mat = bpy.data.materials.new(name=name)
       mat.diffuse_color = (0.92, 0.92, 0.94, 1.0)
       # ... build node tree using make_pbr_material or custom nodes ...
       return mat
   ```
2. Add it to the dictionary returned by `create_materials()`:
   ```python
   "marble": create_marble_slab_material("Marble_White_Mat"),
   ```
3. Assign it to any room, terrace, stair, or component:
   ```python
   # In floor3.py or floor4.py:
   f3.add_room("Bathroom", [(0, 290), (230, 290), (230, 450), (0, 450)], mat_key="marble")
   ```

---

## 5. How to Modify Floor Plans

Floor plans are defined declaratively in [`scripts/cad_markovo/floor3.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/floor3.py) and [`scripts/cad_markovo/floor4.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/floor4.py).

### 5.1 Adding or Modifying a Room
```python
f3.add_room(
    name="Office",
    poly_2d=[(377, 120), (700, 120), (700, 300), (377, 300)],
    mat_key="parquet_light_wood",  # key from create_materials()
)
```

### 5.2 Adding or Modifying a Wall
```python
f3.add_wall(x1=377, y1=300, x2=700, y2=300, thickness=12.0)
```
*Note: Wall cutouts for any doors or windows overlapping this segment are computed automatically.*

### 5.3 Adding or Modifying Windows & Doors
- **Window** (White uPVC frame + glass):
  ```python
  f3.add_window(x1=437, y1=120, x2=662, y2=120, thickness=15.0, label="225")
  ```
- **Exterior Balcony Door** (White uPVC frame + leaf):
  ```python
  f3.add_door(hx=437, hy=120, radius=75.0, start_angle=0, end_angle=90, wall_angle=0, is_exterior=True)
  ```
- **Interior Door** (Warm natural wood leaf):
  ```python
  f3.add_door(hx=230, hy=300, radius=74.0, start_angle=90, end_angle=180, wall_angle=90, thickness=10.0, is_exterior=False)
  ```

### 5.4 Adding or Modifying a Terrace / Balcony
```python
f3.add_terrace(
    name="South_Terrace",
    x=377, y=0, w=323, h=120,
    open_edges=("S", "E", "W"),   # Open edges where solid parapet + coping are built
    mat_key="balcony",            # Balcony floor slab material
)
```
*Rule: Terraces automatically create solid masonry parapets (`wall` material) topped with stone coping (`terrace_coping` material with overhang) along all `open_edges`. No glass is created.*

### 5.5 Adding Stairs
```python
f3.add_stairs(
    x=377, y=500, w=260, h=75,
    num_treads=9,
    direction="right",             # "right" (climbing +X) or "left" (climbing -X)
    label="INTERNAL STAIRS",
)
```
*Rule: Stairs automatically use `cement_mosaic` for all treads and risers.*

---

## 6. Execution & Testing Instructions

### 6.1 Headless Scene Generation
To verify that scene generation executes without errors:
```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/blender_floor_plans.py
```
*(Should complete in $\sim 1.5$ seconds with exit code 0).*

### 6.2 Generating Test Renders
To render both perspective and top-down CAD views to [`renders/`](file:///Users/gdimitrov/projects/markovo/renders):
```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/blender_floor_plans.py -- --render
```
*Note: Rendering uses Cycles CPU with 32 samples and denoising, ensuring reliable execution across sandboxed or server environments.*

### 6.3 3D Stacked View Mode
To stack Floor 4 directly on top of Floor 3 in 3D:
```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/blender_floor_plans.py -- --stack --render
```

### 6.4 Interactive Blender GUI Workflow
When working inside Blender's 3D Viewport:
1. Open [`scripts/blender_floor_plans.py`](file:///Users/gdimitrov/projects/markovo/scripts/blender_floor_plans.py) in the **Text Editor**.
2. Press **Alt+P** (or click **Run Script**).
3. Any edits made to submodules in [`scripts/cad_markovo/`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo) are automatically reloaded via `importlib.reload()` on every run.

---

## 7. Critical Agent Coding Rules

1. **No Monolithic Bloat**: Keep data in `floor3.py` / `floor4.py`, primitives in `geometry.py`, and materials in `materials.py`. Never paste 500 lines of coordinates directly into `blender_floor_plans.py`.
2. **Normals & Winding Order**: When constructing custom meshes in `bmesh`, bottom face vertices must be reversed (`verts_btm[::-1]`) and `bmesh.ops.recalc_face_normals(bm, faces=bm.faces)` must be called before exporting to `bpy.data.meshes`.
3. **Avoid CSG Boolean Modifiers**: Wall opening cutouts must continue using the 2D collinear interval slicing in `builder.py`. CSG booleans in Blender often generate non-manifold geometry, duplicate coplanar faces, and rendering artifacts.
4. **No Glass on Terraces**: All terraces must have solid parapet walls using `mats["wall"]` and terrace coping using `mats["terrace_coping"]`. Never re-introduce glass balustrades to terraces unless explicitly requested.
5. **Exterior vs. Interior Joinery**:
   - Exterior windows and exterior doors $\rightarrow$ `pvc_white`
   - Interior doors $\rightarrow$ `door_wood` leaf and `door_frame` head
6. **Always Verify Renders**: Before reporting completion on visual or material modifications, execute a headless render and inspect the output images using `view_file` to verify lighting, colors, and UV alignment.
7. **Explain Questions First Before Modifying Code**: When the user asks an informational question (e.g. "why is it like this?"), explain the technical reason and ask for user confirmation before implementing code or configuration changes. Never proactively alter codebase files, viewport states, or preferences on a question.
8. **Preserve Fast Default Viewport & User Preferences**: Never force `shading.type = 'MATERIAL'` or mutate Blender user preferences (`userpref.blend`) in scripts. Blender defaults to `SOLID` mode to keep startup fast ($< 1.5\text{ s}$). Forcing Material Preview on startup causes Eevee Next shader compilation of 4K textures, freezing Blender for over a minute.

