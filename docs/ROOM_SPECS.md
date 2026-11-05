# ROOM_SPECS.md — Architectural Room Dimensions & Furniture Plug-in Guide

This document is the **single source of truth for all room dimensions, wall boundaries, ceiling heights, door/window clearances, and coordinate systems** across the Markovo 3D CAD project.

Use this reference when designing room furniture in external CAD software (such as **SketchUp**, **Rhino**, **Fusion 360**) or in isolated Python modules under `scripts/furniture/`.

---

## 1. Global Coordinate Systems & Rules

- **2D Plan Coordinates**: Defined in **centimeters** (`CM = 0.01 m`).
  - $+X$ runs West $\rightarrow$ East.
  - $+Y$ runs South $\rightarrow$ North.
- **Vertical Level ($Z$)**: Defined in **meters**.
  - Floor slab finished surface: $Z = 0.00\text{ m}$.
  - Floor slab bottom: $Z = -0.15\text{ m}$ (slab thickness: $15\text{ cm}$).
  - Ceiling height (Floor 3): $Z = 2.80\text{ m}$ (flat).
  - Ceiling height (Floor 4 Attic): Sloped roof pitch:
    $$Z_{\text{attic}}(x) = 1.40\text{ m} + 1.40 \times \left(\frac{x}{700}\right)$$
    - At outer facade knee wall ($X = 0\text{ cm}$): $Z = 1.40\text{ m}$.
    - At internal party wall ($X = 700\text{ cm}$): $Z = 2.80\text{ m}$.
- **Exporting Room Shells to SketchUp**:
  Every room file in `scripts/furniture/` supports exporting the empty room shell with walls, windows, and door openings directly into **COLLADA (`.dae`)**:
  ```bash
  /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/<room>.py -- --export-shell
  ```
  Import the resulting `.dae` into SketchUp via **File $\rightarrow$ Import $\rightarrow$ COLLADA Files (`*.dae`)** to model furniture directly inside the actual walls.

---

## 2. Floor 3 (Main Level) Rooms

### Room 1: Kitchen
- **Inner Net Dimensions**: $350\text{ cm}$ (width, X) $\times 490\text{ cm}$ (depth, Y).
- **Floor Area**: $17.15\text{ m}^2$.
- **Floor Finish**: Clay Terracotta Tiles (`"clay_tiles"`).
- **Ceiling Height**: $2.80\text{ m}$ (flat).
- **Boundary Polygon (cm)**:
  `[(0, 550), (350, 550), (350, 1040), (0, 1040)]`
- **Wall Openings & Clearances**:
  - **North Wall ($Y = 1040$)**: Window from $X = 56$ to $294$ ($238\text{ cm}$ wide, sill $0.90\text{ m}$, top $2.40\text{ m}$).
  - **South Opening ($Y = 550$)**: Open passage to hallway from $X = 0$ to $155$ ($155\text{ cm}$ clear walk zone). Utility stub wall extends from $X = 155$ to $230$.
  - **West Wall ($X = 0$)**: Exterior solid facade wall ($15\text{ cm}$ thick).
- **Default Furniture Run**:
  - Straight linear cabinetry run against West wall: Origin $(X=7.5, Y=560)$, runs North $+Y$ to $Y=1000$ ($440\text{ cm}$ total length).

---

### Room 2: Living Room
- **Inner Net Dimensions**: $350\text{ cm}$ (width, X: $350 \rightarrow 700$) $\times 420\text{ cm}$ (length, Y: $500 \rightarrow 920$).
- **Floor Area**: $14.70\text{ m}^2$.
- **Floor Finish**: Clay Terracotta Tiles (`"clay_tiles"`).
- **Ceiling Height**: $2.80\text{ m}$ (flat).
- **Boundary Polygon (cm)**:
  `[(350, 500), (700, 500), (700, 920), (350, 920)]`
- **Wall Openings & Clearances**:
  - **North Wall ($Y = 920$)**:
    - Balcony door: $X = 413$, width $75\text{ cm}$ (swings North into balcony).
    - Window assembly: $X = 413 \rightarrow 636$ ($223\text{ cm}$ wide, 3 segments).
  - **West Wall ($X = 350$)**:
    - Dividing window to balcony: $Y = 935 \rightarrow 1025$ ($127\text{ cm}$ wide).
    - Fully open to kitchen / hallway circulation: $Y = 500 \rightarrow 920$.
  - **South Wall ($Y = 500$)**:
    - Internal stairs ascending to Floor 4 Attic: $X = 377 \rightarrow 637$, width $75\text{ cm}$, 9 treads.
    - Partition wall separating from bedroom: $X = 377 \rightarrow 700$ ($12\text{ cm}$ thick).
  - **East Wall ($X = 700$)**: Solid building party wall ($420\text{ cm}$ uninterrupted).
- **Design Recommendations**:
  - TV Media console against East party wall ($X = 700$).
  - 3-seater sofa / sectional facing East with coffee table.
  - Dining table / breakfast zone near kitchen transition ($X \approx 360..450, Y \approx 650..800$).
  - Keep clear passage to internal stairs ($X \approx 377..450, Y \approx 500..580$).

---

### Room 3: Bedroom (Floor 3)
- **Inner Net Dimensions**: $323\text{ cm}$ (width, X: $377 \rightarrow 700$) $\times 380\text{ cm}$ (length, Y: $120 \rightarrow 500$).
- **Floor Area**: $12.27\text{ m}^2$.
- **Floor Finish**: Parallel Parquet Light Coniferous Wood (`"parquet_light_wood"`).
- **Ceiling Height**: $2.80\text{ m}$ (flat).
- **Boundary Polygon (cm)**:
  `[(377, 120), (700, 120), (700, 500), (377, 500)]`
- **Wall Openings & Clearances**:
  - **South Wall ($Y = 120$)**:
    - South balcony door: $X = 437$, width $75\text{ cm}$ (swings South into balcony).
    - Window assembly: $X = 437 \rightarrow 662$ ($225\text{ cm}$ wide).
  - **West Wall ($X = 377$)**:
    - Entry door from hallway: $Y = 465$, width $80\text{ cm}$ (swings East into room along North wall).
  - **North Wall ($Y = 500$)**: Solid partition wall to living room ($323\text{ cm}$).
  - **East Wall ($X = 700$)**: Solid building party wall ($380\text{ cm}$).
- **Design Recommendations**:
  - Double bed ($160 \times 200\text{ cm}$ or $180 \times 200\text{ cm}$) centered against North wall ($Y = 500$) or East wall ($X = 700$).
  - Nightstands on both sides of bed ($45 \times 40\text{ cm}$).
  - Full-height wardrobe closet ($200..240\text{ cm}$ wide, $60\text{ cm}$ deep) along West wall ($X = 377, Y = 140..380$).
  - Ensure $80\text{ cm}$ walk clearance in front of entry door and balcony door.

---

### Room 4: Bathroom (Floor 3)
- **Inner Net Dimensions**: $230\text{ cm}$ (width, X: $0 \rightarrow 230$) $\times 160\text{ cm}$ (length, Y: $290 \rightarrow 450$).
- **Floor Area**: $3.68\text{ m}^2$.
- **Floor Finish**: Ceramic Bath Floor Tiles (`"bath_tiles"`).
- **Ceiling Height**: $2.80\text{ m}$ (flat).
- **Boundary Polygon (cm)**:
  `[(0, 290), (230, 290), (230, 450), (0, 450)]`
- **Wall Openings & Obstacles**:
  - **South Wall ($Y = 290$)**:
    - Entry door: at $X = 230, Y = 300$, width $74\text{ cm}$ (swings inside towards East wall).
  - **North Wall ($Y = 450$)**: Partition wall separating from utility room.
  - **Plumbing & Ventilation Shaft**:
    - Fixed $50 \times 50\text{ cm}$ vertical masonry shaft located in NW corner:
      `X in [0, 50], Y in [400, 450]` (cannot place furniture inside this footprint).
  - **West Wall ($X = 0$)**:
    - High bathroom window: $Y = 330 \rightarrow 410$ ($80\text{ cm}$ wide, high sill at $1.40\text{ m}$).
- **Design Recommendations**:
  - Walk-in shower enclosure ($120 \times 80\text{ cm}$) along North wall next to shaft.
  - Vanity sink unit with mirror cabinet ($80 \times 50\text{ cm}$) against East or North wall.
  - Wall-hung WC with concealed cistern frame ($40 \times 55\text{ cm}$) backed against plumbing shaft or East wall.

---

### Room 5: Utility Room (Floor 3)
- **Inner Net Dimensions**: $230\text{ cm}$ (width, X: $0 \rightarrow 230$) $\times 100\text{ cm}$ (depth, Y: $450 \rightarrow 550$).
- **Floor Area**: $2.30\text{ m}^2$.
- **Floor Finish**: Clay Terracotta Tiles (`"clay_tiles"`).
- **Ceiling Height**: $2.80\text{ m}$ (flat).
- **Boundary Polygon (cm)**:
  `[(0, 450), (230, 450), (230, 550), (0, 550)]`
- **Wall Openings**:
  - **North Wall ($Y = 550$)**: Utility stub wall extends from $X = 155$ to $230$ ($75\text{ cm}$ wide), leaving open walk passage from $X = 0$ to $155$.
  - **South Wall ($Y = 450$)**: Partition wall to bathroom.
  - **West Wall ($X = 0$)**: Window from $Y = 465$ to $535$ ($70\text{ cm}$ wide).
- **Design Recommendations**:
  - Stacked washer and heat-pump dryer ($60 \times 60\text{ cm}$) against East wall ($X = 230$).
  - Vertical storage pantry / broom cabinet ($60 \times 40\text{ cm}$) for cleaning supplies.
  - Electric water heater / boiler tank.

---

## 3. Floor 4 (Attic Level) Rooms

### Room 6: Attic Office
- **Inner Net Dimensions**: $340\text{ cm}$ (width, X: $360 \rightarrow 700$) $\times 380\text{ cm}$ (length, Y: $120 \rightarrow 500$).
- **Floor Area**: $12.92\text{ m}^2$.
- **Floor Finish**: Parallel Parquet Light Coniferous Wood (`"parquet_light_wood"`).
- **Ceiling Height**: Slopes from West ($Z \approx 2.12\text{ m}$ at $X = 360$) to East ($Z = 2.80\text{ m}$ at $X = 700$).
- **Boundary Polygon (cm)**:
  `[(360, 120), (700, 120), (700, 500), (360, 500)]`
- **Wall Openings**:
  - **South Wall ($Y = 120$)**: Balcony door ($X = 437$, width $75\text{ cm}$) and window opening to South terrace.
  - **West Wall ($X = 360$)**: Partition wall with entry door from landing.
  - **North Wall ($Y = 500$)**: Partition wall to stairwell.
- **Design Recommendations**:
  - Executive work desk ($160 \times 80\text{ cm}$) with ergonomic chair.
  - Bookshelf / credenza unit along North or East wall (where ceiling is tall: $Z = 2.80\text{ m}$).
  - Lounge armchair / reading corner near balcony window.

---

### Room 7: Attic Bedroom
- **Inner Net Dimensions**:
  - Main area: $340\text{ cm}$ (width, X: $360 \rightarrow 700$) $\times 343\text{ cm}$ (length, Y: $575 \rightarrow 918$).
  - West alcove: $140\text{ cm}$ (width, X: $220 \rightarrow 360$) $\times 470\text{ cm}$ (length, Y: $570 \rightarrow 1040$).
  - Stair void: Opening at $X \in [377, 637], Y \in [500, 575]$ where the internal stairs emerge.
- **Floor Area**: $\approx 24.5\text{ m}^2$.
- **Floor Finish**: Parallel Parquet Light Coniferous Wood (`"parquet_light_wood"`).
- **Ceiling Height**:
  - At West wall ($X = 220$): $Z = 1.84\text{ m}$.
  - At mid-line ($X = 360$): $Z = 2.12\text{ m}$.
  - At East party wall ($X = 700$): $Z = 2.80\text{ m}$.
- **Wall Openings**:
  - **North Wall ($Y = 918$)**: Balcony door and window opening to North Attic Terrace.
  - **West Wall ($X = 220$)**: Solid knee wall separating from unheated roof utility void.
- **Design Recommendations**:
  - Double bed ($160 \times 200\text{ cm}$) under sloped roof or against East wall.
  - Low-profile knee-wall storage drawers / built-in cabinetry along West knee wall ($X = 220$).
  - Stair safety balustrade / handrail around the stair opening ($X \in [377, 637], Y = 575$).

---

## 4. How to Use the Modular Furniture System

Each room module in `scripts/furniture/` is a **runnable, self-contained Python script**:

```bash
# 1. Open the room furniture in interactive Blender GUI:
/Applications/Blender.app/Contents/MacOS/Blender --python scripts/furniture/living_room.py

# 2. Render an isolated studio preview to PNG:
/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/living_room.py -- --render

# 3. Export empty room shell to SketchUp COLLADA (.dae) to model in external apps:
/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/living_room.py -- --export-shell

# 4. Export furniture + room to SketchUp COLLADA (.dae):
/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/furniture/living_room.py -- --sketchup
```

