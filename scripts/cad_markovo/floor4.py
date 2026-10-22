"""
Floor 4 (Attic Level) Plan Definition and Architectural Specification.

Finishes:
- Attic Rooms (Bedroom, Office, Circulation): Parallel Parquet Light Coniferous Wood
- Utility Room: Cross-Hatched Roof Void
- Stairs & Landing: Cement Mosaic / Architectural Concrete
- Windows & Exterior Balcony Doors: White uPVC
- Terraces: Solid walls matching building wall material + Stone Coping (No glass)
"""

from typing import Dict
import bpy
from .config import SLAB_THICK, get_floor_4_offset
from .builder import FloorPlanBuilder


def attic_z(x: float) -> float:
    """
    Computes wall top height (in meters) following the roof pitch.
    Party wall (x=700): 2.80 m (full ceiling height).
    Outer facade knee wall (x=0): 1.40 m.
    """
    t = max(0.0, min(1.0, x / 700.0))
    return round(1.40 + 1.40 * t, 3)


def build_floor_4(
    mats: Dict[str, bpy.types.Material],
    offset=None,
    stack: bool = None,
) -> FloorPlanBuilder:
    """Builds Floor 4 - Attic Level with raked walls and specified room layout."""
    if offset is None:
        offset = get_floor_4_offset(stack)

    f4 = FloorPlanBuilder("Floor_4_Attic_Level", mats, root_offset=offset)

    # --------------------------------------------------------------------------
    # 1. Usable Attic Rooms with Light Coniferous Wood Parallel Parquet
    # --------------------------------------------------------------------------
    # Attic Office (formerly Attic Bedroom / Attic Room)
    f4.add_room(
        name="Attic_Office",
        poly_2d=[(360, 120), (700, 120), (700, 500), (360, 500)],
        mat_key="parquet_light_wood",
    )

    # Attic Bedroom (formerly Attic Main Room)
    # Decomposed into 3 convex quads leaving [377, 637] x [500, 575] open for the stairs
    f4.add_room(
        name="Attic_Bedroom_Main",
        poly_2d=[(360, 575), (700, 575), (700, 918), (360, 918)],
        mat_key="parquet_light_wood",
    )
    f4.add_room(
        name="Attic_Bedroom_West",
        poly_2d=[(220, 570), (360, 570), (360, 1040), (220, 1040)],
        mat_key="parquet_light_wood",
    )
    f4.add_room(
        name="Attic_Bedroom_Stair_Landing",
        poly_2d=[(637, 500), (700, 500), (700, 575), (637, 575)],
        mat_key="parquet_light_wood",
    )

    # Stair Landing (where main stairs enter - concrete floor, NO TILES)
    f4.add_room(
        name="Stair_Landing",
        poly_2d=[(0, 120), (360, 120), (360, 210), (0, 210)],
        mat_key="concrete_floor",
    )

    # Utility Room under sloped ceiling (void finish, NOT connected to rooms, NO TILES)
    f4.add_room(
        name="Attic_Utility_Room",
        poly_2d=[(0, 210), (0, 1040), (220, 1040), (220, 570), (180, 570), (180, 210)],
        mat_key="void",
        z_bottom=-SLAB_THICK,
        z_top=0.04,
    )

    # --------------------------------------------------------------------------
    # 2. Terraces: Solid Parapet Wall (Wall Material) + Terrace Coping (No Glass)
    # --------------------------------------------------------------------------
    f4.add_terrace("Attic_Bedroom_Balcony", 360, 918, 340, 122, open_edges=("N", "E"))
    f4.add_terrace("Attic_Office_Balcony", 360, 0, 340, 120, open_edges=("S", "E", "W"))

    # --------------------------------------------------------------------------
    # 3. Structural & Internal Walls with Raked Tops Indicating Roof Slope
    # --------------------------------------------------------------------------
    # Attic Bedroom walls
    f4.add_wall(220, 1040, 360, 1040, 15, z_top=(attic_z(220), attic_z(360)), id="wall_attic_bedroom_kitchen_side", room="Attic_Bedroom")
    f4.add_wall(360, 1040, 360, 918, 15, z_top=attic_z(360), id="wall_attic_balcony_divider", room="Attic_Bedroom")
    f4.add_wall(360, 918, 700, 918, 15, z_top=(attic_z(360), attic_z(700)), id="wall_attic_bedroom_balcony", room="Attic_Bedroom")
    f4.add_wall(700, 918, 700, 120, 15, z_top=attic_z(700), id="wall_attic_party_side", room="Attic_Bedroom")
    # Wall along x=220 separating bedroom from utility room (solid, NO doors)
    f4.add_wall(220, 1040, 220, 570, 15, z_top=attic_z(220), id="wall_attic_main_330", room="Attic_Bedroom")

    # Wall separating 4th floor hallway and the Attic Bedroom (y=570, x=220..360)
    f4.add_wall(220, 570, 360, 570, 10, z_top=(attic_z(220), attic_z(360)), id="wall_attic_hallway_bedroom_divider", room="Attic_Hallway")

    # Walls closing hallway from utility room
    f4.add_wall(180, 570, 220, 570, 10, z_top=(attic_z(180), attic_z(220)), id="wall_attic_hallway_utility_divider", room="Attic_Hallway")
    f4.add_wall(180, 230, 180, 570, 10, z_top=attic_z(180), id="wall_attic_utility_hallway_divider", room="Attic_Hallway")

    # Wall closing hallway from stairs & private bedroom
    f4.add_wall(360, 500, 360, 575, 12, z_top=attic_z(360), id="wall_attic_hallway_stair_closure", room="Attic_Bedroom")

    # Wall behind the open stairs (closing the stair opening from the Attic Bedroom)
    f4.add_wall(360, 575, 637, 575, 12, z_top=(attic_z(360), attic_z(637)), id="wall_attic_stairs_back", room="Attic_Bedroom")

    # Attic Office divider & perimeter walls
    f4.add_wall(360, 500, 700, 500, 12, z_top=(attic_z(360), attic_z(700)), id="wall_attic_office_bedroom_divider", room="Attic_Office")
    f4.add_wall(360, 500, 360, 120, 12, z_top=attic_z(360), id="wall_attic_office_hallway", room="Attic_Office")
    f4.add_wall(360, 120, 700, 120, 15, z_top=(attic_z(360), attic_z(700)), id="wall_attic_office_balcony", room="Attic_Office")

    # Stair Landing outer wall & partition
    f4.add_wall(0, 120, 360, 120, 15, z_top=(attic_z(0), attic_z(360)), id="wall_stairwell_landing_outer", room="Stair_Landing")
    f4.add_wall(180, 230, 360, 230, 10, z_top=(attic_z(180), attic_z(360)), id="wall_stairwell_landing_partition", room="Stair_Landing")

    # Outer perimeter knee wall along x=0
    f4.add_wall(0, 1040, 0, 120, 15, z_top=attic_z(0), id="wall_roof_void_perimeter", room="Attic_Utility_Room")

    # --------------------------------------------------------------------------
    # 4. Windows & Glazed Assemblies (White uPVC Frames & Mullions)
    # --------------------------------------------------------------------------
    # Attic Bedroom Balcony assembly
    f4.add_window(
        434, 918, 626, 918,
        label="192",
        id="attic_bedroom_window",
        room="Attic_Bedroom",
    )
    f4.add_door(
        434, 918, 75, 270, 360, 0,
        is_exterior=True,
        id="attic_bedroom_balcony_door",
        room="Attic_Bedroom",
    )

    # Attic Office Balcony assembly
    f4.add_window(
        437, 120, 662, 120,
        label="225",
        id="attic_office_window",
        room="Attic_Office",
    )
    f4.add_door(
        437, 120, 75, 0, 90, 0,
        is_exterior=True,
        id="attic_office_balcony_door",
        room="Attic_Office",
    )

    # --------------------------------------------------------------------------
    # 5. Internal Doors (Wood Leaves)
    # --------------------------------------------------------------------------
    # Attic Office Door from Hallway
    f4.add_door(
        360, 460, 80, 270, 360, 270,
        thickness=12,
        is_exterior=False,
        id="attic_office_door",
        room="Attic_Office",
    )

    # Main Stair Landing Door into Attic Hallway
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
    f4.add_label("UTILITY ROOM", 100, 650, z=0.06, size=18.0, rotation_z=90.0)
    f4.add_label("ATTIC BEDROOM", 460, 740)
    f4.add_label("BALCONY", 530, 980, size=18.0)
    f4.add_label("ATTIC OFFICE", 530, 310, size=20.0)
    f4.add_label("BALCONY", 530, 60, size=18.0)

    f4.build_geometry()
    return f4
