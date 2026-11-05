# AGENTS.md — Agent Instructions for Markovo 3D CAD

This file contains operating instructions for AI coding assistants working in the `markovo` repository.

> **Detailed Guides**:
> - Comprehensive architecture & development instructions: [`docs/AGENT_INSTRUCTIONS.md`](file:///Users/gdimitrov/projects/markovo/docs/AGENT_INSTRUCTIONS.md)
> - Material shader nodes, parameters, and tuning recipes: [`docs/MATERIALS_GUIDE.md`](file:///Users/gdimitrov/projects/markovo/docs/MATERIALS_GUIDE.md)

---

## 1. Quick Commands

| Task | Command |
| :--- | :--- |
| **Verify Scene Build (Headless)** | `/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/blender_floor_plans.py` |
| **Render Perspective & CAD to PNG** | `/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/blender_floor_plans.py -- --render` |
| **Stack Floors in 3D & Render** | `/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/blender_floor_plans.py -- --stack --render` |
| **Render Targeted Room Views** | `/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/blender_floor_plans.py -- --view kitchen,bathroom` |
| **Render CAD Blueprint & Wireframe** | `/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/blender_floor_plans.py -- --blueprint --wireframe` |
| **Export AutoCAD DXF & Vector SVG** | `/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/blender_floor_plans.py -- --dxf --svg` |
| **Develop Kitchen Furniture in Isolation** | `/Applications/Blender.app/Contents/MacOS/Blender --python scripts/furniture/kitchen.py` |
| **Render Isolated Kitchen Furniture** | `/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/kitchen.py -- --render` |
| **Export Room Shell to SketchUp (.dae)** | `/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/<room>.py -- --export-shell` |
| **Room Dimensions & Clearances Spec** | See [`docs/ROOM_SPECS.md`](file:///Users/gdimitrov/projects/markovo/docs/ROOM_SPECS.md) |

---

## 2. Architecture Quick Reference

- **Entry Point**: [`scripts/blender_floor_plans.py`](file:///Users/gdimitrov/projects/markovo/scripts/blender_floor_plans.py)
- **Room Specs Guide**: [`docs/ROOM_SPECS.md`](file:///Users/gdimitrov/projects/markovo/docs/ROOM_SPECS.md) (Exact inner room dimensions, wall boundaries, ceiling heights, door/window openings).
- **Modular Furniture**: [`scripts/furniture/`](file:///Users/gdimitrov/projects/markovo/scripts/furniture)
  - [`kitchen.py`](file:///Users/gdimitrov/projects/markovo/scripts/furniture/kitchen.py): Kitchen cabinetry, inset fronts, and appliances.
  - [`living_room.py`](file:///Users/gdimitrov/projects/markovo/scripts/furniture/living_room.py): Living room sofa, coffee table, media unit, 65" TV.
  - [`bedroom.py`](file:///Users/gdimitrov/projects/markovo/scripts/furniture/bedroom.py): Double bed 160x200, nightstands, wardrobe closet.
  - [`bathroom.py`](file:///Users/gdimitrov/projects/markovo/scripts/furniture/bathroom.py): Walk-in shower, floating vanity sink, wall-hung WC, plumbing shaft.
  - [`utility.py`](file:///Users/gdimitrov/projects/markovo/scripts/furniture/utility.py): Stacked washer/dryer, laundry tall cupboard, boiler.
  - [`attic_office.py`](file:///Users/gdimitrov/projects/markovo/scripts/furniture/attic_office.py): Executive desk, ergonomic chair, tall library bookshelf.
  - [`attic_bedroom.py`](file:///Users/gdimitrov/projects/markovo/scripts/furniture/attic_bedroom.py): Attic master bed, nightstands, low knee-wall storage, stair balustrade.
- **Core CAD Package**: [`scripts/cad_markovo/`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo)
  - [`config.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/config.py): Units (`CM = 0.01`), vertical dimensions, layout flags.
  - [`materials.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/materials.py): Material shaders & factory (`create_materials()`).
  - [`geometry.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/geometry.py): 3D CAD primitives, windows, doors, stairs, terrace walls & coping, dimension strings, and shapely room stamps.
  - [`kitchen.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/kitchen.py): Clean adapter forwarding to `furniture.kitchen`.
  - [`builder.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/builder.py): [`FloorPlanBuilder`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/builder.py#L40) class with automatic collinear lintel/sill cutouts, perimeter dimensions, and area stamps.
  - [`cad_export.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/cad_export.py): Authentic AutoCAD `.dxf` (R2018) export with CAD layers & scalable vector SVG blueprints.
  - [`floor3.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/floor3.py): Floor 3 (Main Level) specification.
  - [`floor4.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/floor4.py): Floor 4 (Attic Level) specification.
  - [`scene.py`](file:///Users/gdimitrov/projects/markovo/scripts/cad_markovo/scene.py): Scene cleanup, studio lighting, multi-camera framing (room presets), Cycles & Workbench blueprint renderers.

---

## 3. Strict Architectural Rules

1. **Units & Coordinate Systems**:
   - Input 2D coordinates are in **centimeters** (`CM = 0.01`).
   - Vertical dimensions ($z$) are in **meters**.
   - Floor slab top: $z = 0.0\text{ m}$, slab bottom: $z = -0.15\text{ m}$. Ceiling: $z = 2.80\text{ m}$.
2. **Materials Assignments**:
   - **External Windows & Exterior Balcony Doors**: Always use White uPVC (`"pvc_white"`).
   - **Kitchen & Living Room Floors**: Always use Clay Terracotta Tiles (`"clay_tiles"`).
   - **Bedroom & Attic Floors**: Always use Parallel Parquet Light Coniferous Wood (`"parquet_light_wood"`).
   - **Stairs & Landings**: Always use Cement Mosaic / Terrazzo ("мозайка") (`"cement_mosaic"`).
   - **Terraces**: Solid masonry parapet walls using the exact same material as the walls (`"wall"`), topped with stone coping (`"terrace_coping"`) with an overhang. **Never add glass to terraces**.
   - **Interior Doors**: Warm natural wood (`"door_wood"`).
3. **Cutouts & Geometry**:
   - Do NOT use CSG Boolean modifiers. Use `FloorPlanBuilder`'s interval slicing.
   - When building custom polygons in `bmesh`, ensure reverse winding on bottom faces (`verts_btm[::-1]`) and call `bmesh.ops.recalc_face_normals(bm, faces=bm.faces)`.
4. **Testing Before Completion**:
   - Always run the headless script to verify no exceptions.
   - If visual changes are made, run `--render` and inspect output images in [`renders/`](file:///Users/gdimitrov/projects/markovo/renders) using `view_file`.
5. **Explain Questions First**:
   - When the user asks a question (e.g. "why is it like this?"), explain the reason and ask for permission before modifying code or configurations.
6. **Preserve Fast Default Shading & Preferences**:
   - Never force `shading.type = 'MATERIAL'` in scripts or edit Blender preferences. Keep default `SOLID` mode for fast ($< 1.5\text{ s}$) startup. Viewport PBR textures are viewed on demand by pressing `Z` $\rightarrow$ `Material Preview`.

