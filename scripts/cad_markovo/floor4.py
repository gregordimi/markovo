"""
Floor 4 (Attic Level) Plan Definition and Architectural Specification.

Finishes:
- Attic Rooms (Bedroom, Main Room, Circulation): Parallel Parquet Light Coniferous Wood
- Unusable Area: Cross-Hatched Roof Void
- Stairs & Landing: Cement Mosaic ("мозайка")
- Windows & Exterior Balcony Doors: White uPVC
- Terraces: Solid walls matching building wall material + Stone Coping (No glass)
"""

from typing import Dict
import bpy
from .config import SLAB_THICK, get_floor_4_offset
from .builder import FloorPlanBuilder


def build_floor_4(
    mats: Dict[str, bpy.types.Material],
    offset=None,
    stack: bool = None,
) -> FloorPlanBuilder:
    """Builds Floor 4 - Attic Level with all architectural elements and requested materials."""
    if offset is None:
        offset = get_floor_4_offset(stack)

    f4 = FloorPlanBuilder("Floor_4_Attic_Level", mats, root_offset=offset)

    # --------------------------------------------------------------------------
    # 1. Usable Attic Rooms with Light Coniferous Wood Parallel Parquet
    # --------------------------------------------------------------------------
    # Attic Bedroom: Light Coniferous Wood Parallel Parquet
    f4.add_room(
        name="Attic_Bedroom",
        poly_2d=[(360, 120), (700, 120), (700, 500), (360, 500)],
        mat_key="parquet_light_wood",
    )

    # Attic Main Room: Light Coniferous Wood Parallel Parquet
    f4.add_room(
        name="Attic_Main_Room",
        poly_2d=[
            (360, 500), (700, 500), (700, 918), (360, 918),
            (360, 1040), (220, 1040), (220, 570), (360, 570),
        ],
        mat_key="parquet_light_wood",
    )

    # Attic Hallway & Landing: Light Coniferous Wood Parallel Parquet
    f4.add_room(
        name="Attic_Hallway",
        poly_2d=[(180, 210), (360, 210), (360, 570), (220, 570), (180, 570)],
        mat_key="parquet_light_wood",
    )

    # Stairwell Landing: Architectural Concrete (Poly Haven concrete_floor_01)
    f4.add_room(
        name="Stair_Landing",
        poly_2d=[(0, 120), (360, 120), (360, 210), (0, 210)],
        mat_key="concrete_floor",
    )

    # Roof Void / Unusable Area
    f4.add_room(
        name="Roof_Void_Area",
        poly_2d=[(0, 210), (0, 1040), (220, 1040), (220, 570), (180, 570), (180, 210)],
        mat_key="void",
        z_bottom=-SLAB_THICK,
        z_top=0.04,
    )

    # --------------------------------------------------------------------------
    # 2. Terraces: Solid Parapet Wall (Wall Material) + Terrace Coping (No Glass)
    # --------------------------------------------------------------------------
    f4.add_terrace("Attic_Main_Balcony", 360, 918, 340, 122, open_edges=("N", "E"))
    f4.add_terrace("Attic_Bedroom_Balcony", 360, 0, 340, 120, open_edges=("S", "E", "W"))

    # --------------------------------------------------------------------------
    # 3. Structural & Internal Walls
    # --------------------------------------------------------------------------
    f4.add_wall(220, 1040, 360, 1040, 15, id="wall_attic_main_kitchen_side", room="Attic_Main_Room")
    f4.add_wall(360, 1040, 360, 918, 15, id="wall_attic_balcony_divider", room="Attic_Main_Room")
    f4.add_wall(360, 918, 700, 918, 15, id="wall_attic_main_balcony", room="Attic_Main_Room")
    f4.add_wall(700, 918, 700, 120, 15, id="wall_attic_party_side", room="Attic_Main_Room")
    f4.add_wall(220, 1040, 220, 570, 15, id="wall_attic_main_330", room="Attic_Main_Room")
    f4.add_wall(220, 570, 360, 570, 10, id="wall_attic_hallway_divider", room="Attic_Hallway")
    f4.add_wall(360, 500, 700, 500, 12, id="wall_attic_bedroom_divider", room="Attic_Bedroom")
    f4.add_wall(360, 500, 360, 120, 12, id="wall_attic_bedroom_hallway", room="Attic_Bedroom")
    f4.add_wall(360, 120, 700, 120, 15, id="wall_attic_bedroom_balcony", room="Attic_Bedroom")
    f4.add_wall(0, 120, 360, 120, 15, id="wall_stairwell_landing_outer", room="Stair_Landing")
    f4.add_wall(0, 1040, 0, 120, 8, id="wall_roof_void_perimeter", room="Roof_Void_Area")
    f4.add_wall(180, 230, 360, 230, 10, id="wall_stairwell_landing_partition", room="Stair_Landing")

    # --------------------------------------------------------------------------
    # 4. Windows & Glazed Assemblies (White uPVC Frames & Mullions)
    # --------------------------------------------------------------------------
    # Attic Main Room Balcony assembly
    f4.add_window(
        434, 918, 626, 918,
        label="192",
        id="attic_main_window",
        room="Attic_Main_Room",
    )
    f4.add_door(
        434, 918, 75, 270, 360, 0,
        is_exterior=True,
        id="attic_main_balcony_door",
        room="Attic_Main_Room",
    )

    # Attic Bedroom Balcony assembly
    f4.add_window(
        437, 120, 662, 120,
        label="225",
        id="attic_bedroom_window",
        room="Attic_Bedroom",
    )
    f4.add_door(
        437, 120, 75, 0, 90, 0,
        is_exterior=True,
        id="attic_bedroom_balcony_door",
        room="Attic_Bedroom",
    )

    # --------------------------------------------------------------------------
    # 5. Internal Doors (Wood Leaves) & Utility Doors
    # --------------------------------------------------------------------------
    # 120 cm Double Utility Door on 330 wall (x=220, y=920..1040)
    f4.add_door(
        220, 1040, 60, 270, 360, 270,
        thickness=15,
        is_exterior=False,
        id="attic_utility_door_left",
        room="Attic_Main_Room",
    )
    f4.add_door(
        220, 920, 60, 0, 90, 90,
        thickness=15,
        is_exterior=False,
        id="attic_utility_door_right",
        room="Attic_Main_Room",
    )

    # Attic Bedroom Door & Main Stair Landing Door
    f4.add_door(
        360, 460, 80, 270, 360, 270,
        thickness=12,
        is_exterior=False,
        id="attic_bedroom_door",
        room="Attic_Bedroom",
    )
    f4.add_door(
        340, 230, 85, 90, 180, 180,
        thickness=10,
        is_exterior=False,
        id="attic_landing_door",
        room="Attic_Hallway",
    )

    # --------------------------------------------------------------------------
    # 6. Architectural Room Labels
    # --------------------------------------------------------------------------
    f4.add_label("ATTIC FLOOR 4 - UPPER LEVEL", 350, 1110, z=0.05, size=28.0)
    f4.add_label("ROOF VOID / UNUSABLE", 100, 650, size=18.0, rotation_z=90.0)
    f4.add_label("ATTIC MAIN ROOM", 460, 740)
    f4.add_label("BALCONY", 530, 980, size=18.0)
    f4.add_label("ATTIC ROOM / BEDROOM", 530, 310, size=20.0)
    f4.add_label("BALCONY", 530, 60, size=18.0)

    f4.build_geometry()
    return f4
