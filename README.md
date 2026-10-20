# Markovo 3D Architectural CAD / BIM

A parametric 3D architectural CAD generator and renderer for a multi-level residential building in Markovo, built with Blender's Python API (`bpy` / `bmesh`).

---

## Features

- **Procedural PBR Materials**:
  - **Clay Terracotta Tiles**: Mediterranean baked clay floor tiles with cement grout in the Kitchen and Living Room.
  - **Parallel Parquet Light Coniferous Wood**: Scandinavian blonde pine/fir strip parquet in the Bedroom and Attic.
  - **Cement Mosaic ("Мозайка")**: Traditional terrazzo with mineral aggregate chips on all stairs and landings.
  - **White uPVC**: Clean architectural profiles for all external windows and balcony doors.
  - **Terraces**: Solid masonry parapet walls matching building walls, topped with stone coping (no glass).
- **Precision Parametric Openings**: Automated collinear lintel and sill cutouts for windows and doors without brittle CSG Boolean modifiers.
- **Dual Visual Modes**: Side-by-side 2-panel CAD layout or full 3D vertical stacking (`--stack`).
- **Cycles Raytracing**: Studio lighting rig with sun, fill, and background sky with CPU rendering.
- **Blender GUI Hot-Reloading**: Seamless iterative script development inside Blender's Text Editor (`Alt+P`).

---

## Quick Start

### 1. Run Headless Scene Generation
```bash
blender -b --python scripts/blender_floor_plans.py
```

### 2. Render Perspective and Orthographic CAD Views
```bash
blender -b --python scripts/blender_floor_plans.py -- --render
```
Outputs are saved to `renders/`:
- `markovo_floor_plans_perspective.png`
- `markovo_floor_plans_cad_top.png`

### 3. Stack Floors Vertically in 3D
```bash
blender -b --python scripts/blender_floor_plans.py -- --stack --render
```

### 4. Interactive Blender GUI
1. Open Blender.
2. Load [`scripts/blender_floor_plans.py`](file:///Users/gdimitrov/projects/markovo/scripts/blender_floor_plans.py) into the Text Editor.
3. Press **Alt+P** (Run Script).

---

## Documentation

- **[Agentic Instructions & Architecture Guide](file:///Users/gdimitrov/projects/markovo/docs/AGENT_INSTRUCTIONS.md)**: System architecture, coordinate systems, room/wall definitions, and guidelines for AI agents.
- **[Materials & Shader Guide](file:///Users/gdimitrov/projects/markovo/docs/MATERIALS_GUIDE.md)**: Deep dive into procedural node networks, parameters, color tuning, and custom material recipes.
- **[Agent Cheatsheet](file:///Users/gdimitrov/projects/markovo/AGENTS.md)**: Fast reference for AI coding assistants.
