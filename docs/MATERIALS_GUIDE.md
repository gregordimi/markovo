# Markovo Architectural Materials Guide

This guide provides an in-depth reference for the procedural and PBR shader materials implemented in [`scripts/cad_markovo/materials.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/materials.py).

---

## 1. Material Architecture Overview

All materials in the project are designed with dual compatibility:
1. **Viewport Solid & Workbench Display**: Every material has its `diffuse_color` set to an appropriate RGBA tuple so it displays clearly in Blender's Solid Viewport shading mode.
2. **Procedural PBR Shading (Cycles & Eevee)**: Full node networks connected to `ShaderNodeBsdfPrincipled` (Principled BSDF) outputting to `ShaderNodeOutputMaterial`.

---

## 2. Core Shader Functions

### 2.1 `make_pbr_material(name, rgba, roughness, metallic, transmission)`
A clean factory helper for standard non-textured PBR surfaces (e.g. walls, stone coping, glass, uPVC).

```python
def make_pbr_material(
    name: str,
    rgba: tuple,
    roughness: float = 0.5,
    metallic: float = 0.0,
    transmission: float = 0.0,
) -> bpy.types.Material
```

- Handles Blender 3.x, 4.x, and 5.x Principled BSDF input name variations (`Transmission Weight` vs `Transmission`).
- Automatically enables alpha blending (`blend_method = "BLEND"`) when `rgba[3] < 1.0` or `transmission > 0`.

---

### 2.2 `create_clay_tiles_material(name="Clay_Tiles_Mat")`
Generates artisanal Mediterranean terracotta/cotto floor tiles precisely matched to the user's reference photo. Features square tiles (~31x31 cm) with soft cloudy artisanal mottling and dark grey-brown cement grout lines.

#### Shader Node Graph:
```
                                         ┌──► [Brick Texture (Square Tiles)] ──┐
[TexCoord (Object)] ──► [Mapping (3.2)] ─┤                                     ├──► [Mix (Overlay 0.24)] ──► [Principled BSDF]
                                         └──► [Noise Texture (Cloudy Mottling)]┘
```

#### Key Parameters & How to Tune Them:
| Parameter | Location in Code | Default Value | Description / Tuning Guidance |
| :--- | :--- | :--- | :--- |
| **Tile Scale** | `mapping.inputs["Scale"]` | `(3.2, 3.2, 3.2)` | Controls tile size ($\sim 31 \times 31\text{ cm}$). Increase to `4.0` for smaller tiles or decrease to `2.5` for larger tiles. |
| **Color 1** | `brick.inputs["Color1"]` | `(0.66, 0.36, 0.20, 1.0)` | Primary warm terracotta tone. |
| **Color 2** | `brick.inputs["Color2"]` | `(0.54, 0.28, 0.15, 1.0)` | Darker baked clay variation between adjacent tiles. |
| **Mortar Color** | `brick.inputs["Mortar"]` | `(0.42, 0.38, 0.35, 1.0)` | Dark grey-brown cement grout line. |
| **Mortar Size** | `brick.inputs["Mortar Size"]` | `0.012` | Clean $\approx 4\text{ mm}$ grout joint. |
| **Mottling Scale** | `noise.inputs["Scale"]` | `14.0` | Cloudy organic surface mottling across tiles. |
| **Mottling Factor**| `mix.inputs["Factor"]` | `0.24` | Blend strength of cloudy mottling. |
| **Roughness** | `bsdf.inputs["Roughness"]` | `0.65` | Natural matte fired cotto finish. |

---

### 2.3 `create_parquet_light_wood_material(name="Parquet_Coniferous_Light_Mat")`
Generates continuous parallel coniferous pine floorboards ("дюшеме") matched to the user's reference photo. Features narrow continuous parallel planks (~11 cm wide), warm amber/honey pine wood tones, longitudinal grain, and scattered natural darker knots.

#### Shader Node Graph:
```
                                        ┌──► [Brick Texture (Parallel Planks)] ─┐
                                        │                                       ├──► [Mix (Grain)] ──┐
[TexCoord (Object)] ──► [Mapping (1.0)] ┼──► [Wave Texture (Ring Grain)] ───────┘                    ├──► [Mix (Knots)] ──► [Principled BSDF]
                                        │                                                            │
                                        └──► [Voronoi (Knots)] ──► [ColorRamp (Knot Rings)] ─────────┘
```

#### Key Parameters & How to Tune Them:
| Parameter | Location in Code | Default Value | Description / Tuning Guidance |
| :--- | :--- | :--- | :--- |
| **Plank Length** | `brick.inputs["Brick Width"]` | `4.5` | Continuous longitudinal boards ($4.5\text{ m}$). |
| **Plank Width** | `brick.inputs["Row Height"]` | `0.11` | Width of parallel floorboards ($11\text{ cm}$). |
| **Color 1** | `brick.inputs["Color1"]` | `(0.82, 0.58, 0.26, 1.0)` | Warm golden amber pine tone. |
| **Color 2** | `brick.inputs["Color2"]` | `(0.74, 0.48, 0.20, 1.0)` | Deeper honey pine tone. |
| **Mortar / Seam** | `brick.inputs["Mortar"]` | `(0.32, 0.18, 0.08, 1.0)` | Dark seam / V-groove shadow between boards. |
| **Knot Frequency** | `voronoi.inputs["Scale"]` | `5.5` | Density of scattered knots on boards. |
| **Knot Color** | `ramp.elements[0]` | `(0.28, 0.14, 0.05, 1.0)` | Dark core of natural pine knots. |
| **Grain Frequency** | `wave.inputs["Scale"]` | `24.0` | Directional coniferous ring grain density. |
| **Surface Finish** | `bsdf.inputs["Roughness"]` | `0.34` | Varnished wood floor sheen. |

---

### 2.4 `create_cement_mosaic_material(name="Cement_Mosaic_Stairs_Mat")`
Generates traditional Mediterranean / Balkan cement mosaic ("мозайка") / terrazzo for stairs and stairwell landings. Features a polished cement matrix with embedded chips of basalt, white marble, and quartz.

#### Shader Node Graph:
```
[TexCoord (Object)] ──► [Voronoi Texture (Scale 40)] ──► [ColorRamp (Constant)] ──► [Principled BSDF] ──► [Material Output]
```

#### Key Parameters & How to Tune Them:
| Parameter | Location in Code | Default Value | Description / Tuning Guidance |
| :--- | :--- | :--- | :--- |
| **Aggregate Size** | `voronoi.inputs["Scale"]` | `40.0` | Chip granularity. Increase to `60.0` for finer chips, or decrease to `25.0` for larger stone chunks. |
| **Randomness** | `voronoi.inputs["Randomness"]` | `0.95` | Irregularity of natural crushed stone chips. |
| **Matrix Base Color** | `ramp.elements[0]` at `0.00` | `(0.76, 0.76, 0.75, 1.0)` | Mid-light architectural Portland cement grey. |
| **White Marble Chips** | `ramp.elements[1]` at `0.35` | `(0.92, 0.92, 0.90, 1.0)` | Calcite / Carrara white marble inclusions. |
| **Basalt Chips** | `ramp.elements[2]` at `0.65` | `(0.35, 0.35, 0.36, 1.0)` | Dark mineral / basalt aggregate chips. |
| **Limestone Chips** | `ramp.elements[3]` at `0.85` | `(0.72, 0.65, 0.58, 1.0)` | Warm ochre / dolomite quartz flecks. |
| **Surface Sheen** | `bsdf.inputs["Roughness"]` | `0.35` | Smooth diamond-ground polished terrazzo sheen. |

---

### 2.5 `door_wood` & 8-Panel Door Geometry
Interior doors are modeled after the reference photo with:
- **8 Recessed/Raised Molded Panels**: 2 columns $\times$ 4 rows of panels with profiled border bevels.
- **Door Frame**: Stiles ($10\text{ cm}$), top rail ($12\text{ cm}$), bottom kick rail ($18\text{ cm}$), and 3 intermediate cross rails.
- **Material**: Rich warm chestnut/honey pine wood (`(0.46, 0.28, 0.14, 1.0)`, `roughness = 0.38`).
- **Hardware**: Brushed silver lever handle and vertical escutcheon plate at $z = 1.00\text{ m}$ (`Door_Handle_Mat`, `metallic = 0.92`, `roughness = 0.22`).

---

### 2.6 `pvc_white` (White uPVC Joinery)
Used for all external window frames, vertical mullions, and exterior balcony doors.

```python
"pvc_white": make_pbr_material(
    "PVC_White_Mat",
    (0.95, 0.95, 0.95, 1.0),
    roughness=0.25,
    metallic=0.0,
)
```
- **Base Color**: Clean architectural white (`0.95, 0.95, 0.95`).
- **Roughness**: `0.25` for smooth extruded plastic sheen with crisp specular highlights.

---

### 2.6 `wall` & `terrace_coping` (Parapets & Coping)
- **Wall Parapet**: Uses the **exact same material** as the building walls (`"wall"` $\rightarrow$ `Wall_Mat`, `(0.29, 0.29, 0.29, 1.0)`).
- **Terrace Coping**: Uses `"terrace_coping"` $\rightarrow$ `Terrace_Coping_Mat`, `(0.86, 0.85, 0.82, 1.0)`, `roughness=0.5`. Forms the capping stone resting on top of the parapet wall with a $2.5\text{ cm}$ overhang on both sides.

---

## 3. Step-by-Step Customization Recipes

### Recipe A: Switching Parquet from Blonde Pine to Rich Dark Oak
In `create_parquet_light_wood_material()`:
```python
# Replace Color1 and Color2 with rich smoked oak tones:
brick.inputs["Color1"].default_value = (0.42, 0.28, 0.16, 1.0)  # Medium walnut / oak
brick.inputs["Color2"].default_value = (0.34, 0.22, 0.12, 1.0)  # Dark grain
bsdf.inputs["Roughness"].default_value = 0.45                    # Matte oil finish
```

### Recipe B: Changing Window Frames from White uPVC to Anthracite Grey (RAL 7016)
In `create_materials()`:
```python
"pvc_white": make_pbr_material(
    "PVC_Anthracite_Mat",
    (0.22, 0.23, 0.25, 1.0),  # RAL 7016 Anthracite Grey
    roughness=0.32,
    metallic=0.0,
),
```

### Recipe C: Changing Kitchen Tiles from Terracotta to Gray Slate Tiles
In `create_clay_tiles_material()`:
```python
brick.inputs["Color1"].default_value = (0.45, 0.46, 0.48, 1.0)  # Slate gray
brick.inputs["Color2"].default_value = (0.35, 0.36, 0.38, 1.0)  # Darker graphite
brick.inputs["Mortar"].default_value = (0.25, 0.25, 0.26, 1.0)  # Charcoal grout
```

### Recipe D: Adding a New Floor Material (e.g. Marble)
1. Add the builder function in `materials.py`:
   ```python
   def create_marble_material(name="Marble_Carrara_Mat"):
       return make_pbr_material(name, (0.92, 0.93, 0.94, 1.0), roughness=0.18)
   ```
2. Register it in `create_materials()`:
   ```python
   "marble": create_marble_material(),
   ```
3. Use it in `floor3.py` or `floor4.py`:
   ```python
   f3.add_room("Bathroom", [(0, 290), (230, 290), (230, 450), (0, 450)], mat_key="marble")
   ```
