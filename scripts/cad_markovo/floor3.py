"""
Floor 3 (Main Level) Plan Definition and Architectural Specification.

Finishes:
- Kitchen & Living Room: Clay Terracotta Tiles
- Bedroom: Parallel Parquet Light Coniferous Wood
- Stairs & Landing: Cement Mosaic ("мозайка")
- Windows & Exterior Balcony Doors: White uPVC
- Terraces: Solid walls matching building wall material + Stone Coping (No glass)
"""

from typing import Dict
import bpy
from .config import WALL_HEIGHT
from .builder import FloorPlanBuilder


def build_floor_3(mats: Dict[str, bpy.types.Material], offset=(0.0, 0.0, 0.0)) -> FloorPlanBuilder:
    """Builds Floor 3 - Main Level with all architectural elements and requested materials."""
    f3 = FloorPlanBuilder("Floor_3_Main_Level", mats, root_offset=offset)

    # --------------------------------------------------------------------------
    # 1. Room Floor Slabs with Specific Finishes
    # --------------------------------------------------------------------------
    # Kitchen: Clay Terracotta Tiles
    f3.add_room(
        name="Kitchen",
        poly_2d=[(0, 550), (350, 550), (350, 920), (350, 1040), (0, 1040)],
        mat_key="clay_tiles",
    )

    # Living Room: Clay Terracotta Tiles
    f3.add_room(
        name="Living_Room",
        poly_2d=[(350, 500), (700, 500), (700, 920), (350, 920)],
        mat_key="clay_tiles",
    )

    # Hallway & Circulation: Clay Terracotta Tiles
    f3.add_room(
        name="Hallway",
        poly_2d=[(230, 290), (377, 290), (377, 500), (350, 500), (350, 550), (230, 550)],
        mat_key="clay_tiles",
    )

    # Bath: Ceramic Floor Tile
    f3.add_room(
        name="Bathroom",
        poly_2d=[(0, 290), (230, 290), (230, 450), (0, 450)],
        mat_key="bath_tiles",
    )

    # Utility: Clay / Floor Tile
    f3.add_room(
        name="Utility",
        poly_2d=[(0, 450), (230, 450), (230, 550), (0, 550)],
        mat_key="clay_tiles",
    )

    # Bedroom: Parallel Parquet Light Coniferous Wood
    f3.add_room(
        name="Bedroom",
        poly_2d=[(377, 120), (700, 120), (700, 500), (377, 500)],
        mat_key="parquet_light_wood",
    )

    # Stairwell Landing: Cement Mosaic
    f3.add_room(
        name="Stair_Landing",
        poly_2d=[(0, 120), (377, 120), (377, 290), (0, 290)],
        mat_key="cement_mosaic",
    )

    # --------------------------------------------------------------------------
    # 2. Terraces: Solid Parapet Wall (Wall Material) + Terrace Coping (No Glass)
    # --------------------------------------------------------------------------
    f3.add_terrace("NE_Balcony", 350, 920, 350, 120, open_edges=("N", "E"))
    f3.add_terrace("SE_Balcony", 377, 0, 323, 120, open_edges=("S", "E", "W"))
    f3.add_terrace("West_Balcony", -120, 195, 120, 355, open_edges=("N", "W", "S"))

    # --------------------------------------------------------------------------
    # 3. Structural & Exterior Walls (15 cm)
    # --------------------------------------------------------------------------
    f3.add_wall(0, 1040, 350, 1040, 15)      # Kitchen North wall
    f3.add_wall(350, 1040, 350, 920, 15)     # Balcony divider West
    f3.add_wall(350, 920, 700, 920, 15)      # Living Room North wall
    f3.add_wall(700, 920, 700, 120, 15)      # East exterior wall
    f3.add_wall(0, 1040, 0, 120, 15)         # West exterior wall
    f3.add_wall(0, 120, 377, 120, 15)        # South stairwell wall
    f3.add_wall(377, 120, 700, 120, 15)      # Bedroom South wall

    # --------------------------------------------------------------------------
    # 4. Internal Partitions
    # --------------------------------------------------------------------------
    f3.add_wall(155, 550, 230, 550, 10)      # Utility stub (leaves 155 cm opening)
    f3.add_wall(230, 550, 230, 290, 10)      # Utility + Bath East wall
    f3.add_wall(0, 450, 230, 450, 10)        # Bath North wall
    f3.add_wall(0, 290, 377, 290, 10)        # Bath South + Hallway entry wall
    f3.add_wall(377, 500, 700, 500, 12)      # Bedroom North wall
    f3.add_wall(377, 500, 377, 120, 12)      # Bedroom West wall

    # --------------------------------------------------------------------------
    # 5. Plumbing & Ventilation Shaft
    # --------------------------------------------------------------------------
    f3.add_custom_prism(
        name="Bath_Shaft_50x50",
        corners_2d=[(0, 400), (50, 400), (50, 450), (0, 450)],
        z_bottom=0.0,
        z_top=WALL_HEIGHT,
        mat_key="shaft",
    )

    # --------------------------------------------------------------------------
    # 6. Windows & Glazed Assemblies (White uPVC Frames & Mullions)
    # --------------------------------------------------------------------------
    # Kitchen North glazed assembly
    f3.add_window(56, 1040, 294, 1040, label="238 (3x79.3)")
    f3.add_door(135, 1040, 79.3, 270, 360, 0, is_exterior=True)
    f3.add_door(294, 1040, 79.3, 180, 270, 180, is_exterior=True)

    # Balcony divider & Living Room North assembly
    f3.add_window(350, 935, 350, 1025, label="127")
    f3.add_window(413, 920, 636, 920, label="223 (3x75)")
    f3.add_door(413, 920, 75, 270, 360, 0, is_exterior=True)

    # West wall openings
    f3.add_window(0, 465, 0, 535)
    f3.add_window(0, 330, 0, 410, label="80")
    f3.add_window(0, 195, 0, 272, label="77")
    f3.add_door(0, 195, 77, 0, 90, 90, is_exterior=True)

    # Bedroom South glazed assembly
    f3.add_window(437, 120, 662, 120, label="225")
    f3.add_door(437, 120, 75, 0, 90, 0, is_exterior=True)

    # --------------------------------------------------------------------------
    # 7. Internal Doors (Warm Wood Leaves)
    # --------------------------------------------------------------------------
    f3.add_door(230, 300, 74, 90, 180, 90, thickness=10, is_exterior=False)
    f3.add_door(360, 290, 90, 90, 180, 180, thickness=10, is_exterior=False)
    f3.add_door(377, 465, 80, 270, 360, 270, thickness=12, is_exterior=False)

    # --------------------------------------------------------------------------
    # 8. Stairs (Cement Mosaic Finish)
    # --------------------------------------------------------------------------
    f3.add_stairs(377, 500, 260, 75, num_treads=9, direction="right", label="INTERNAL STAIRS")
    f3.add_stairs(20, 120, 330, 85, num_treads=10, direction="left", label="STAIRS")

    # --------------------------------------------------------------------------
    # 9. Architectural Room Labels
    # --------------------------------------------------------------------------
    f3.add_label("FLOOR 3 - MAIN LEVEL", 350, 1110, z=0.05, size=28.0)
    f3.add_label("KITCHEN", 175, 780)
    f3.add_label("LIVING ROOM", 525, 710)
    f3.add_label("BALCONY", 525, 980, size=18.0)
    f3.add_label("BALCONY", -60, 372, size=18.0, rotation_z=90.0)
    f3.add_label("BATH", 115, 365, size=20.0)
    f3.add_label("BEDROOM", 538, 310)
    f3.add_label("BALCONY", 538, 60, size=18.0)
    f3.add_label("OPENING 155", 77, 565, size=14.0, mat_key="dim")

    f3.build_geometry()
    return f3
