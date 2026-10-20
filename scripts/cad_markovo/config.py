"""
Architectural constants, units, dimensions, and configuration flags
for Markovo residential building 3D BIM/CAD floor plans.
"""

# Unit Conversion: Centimeters to Blender Meters
CM = 0.01  # 100 cm = 1.0 meter

# ------------------------------------------------------------------------------
# Architectural Vertical Dimensions (in Blender meters)
# ------------------------------------------------------------------------------
WALL_HEIGHT = 280.0 * CM          # 2.80 m ceiling height
SLAB_THICK = 15.0 * CM            # 0.15 m floor slab thickness
DOOR_HEIGHT = 210.0 * CM          # 2.10 m standard door height
WIN_SILL = 90.0 * CM              # 0.90 m window sill height
WIN_TOP = 210.0 * CM              # 2.10 m window head / lintel height

# ------------------------------------------------------------------------------
# Terrace / Balcony Parapet & Coping Dimensions
# ------------------------------------------------------------------------------
TERRACE_PARAPET_HEIGHT = 95.0 * CM     # 0.95 m solid masonry parapet wall
TERRACE_COPING_THICKNESS = 5.0 * CM   # 0.05 m stone / architectural coping cap
TERRACE_TOTAL_HEIGHT = TERRACE_PARAPET_HEIGHT + TERRACE_COPING_THICKNESS  # 1.00 m total
TERRACE_WALL_THICKNESS = 15.0         # 15.0 cm wall thickness (in cm)
TERRACE_COPING_OVERHANG = 2.5         # 2.5 cm overhang on both inner and outer edge (cm)
TERRACE_COPING_WIDTH = TERRACE_WALL_THICKNESS + 2.0 * TERRACE_COPING_OVERHANG  # 20.0 cm

# ------------------------------------------------------------------------------
# Frame & Leaf Dimensions
# ------------------------------------------------------------------------------
FRAME_THICKNESS_CM = 4.0          # 4 cm PVC/wood frame profile
DOOR_LEAF_THICKNESS_CM = 4.0      # 4 cm door leaf thickness
GLASS_THICKNESS_CM = 2.5          # 2.5 cm insulated double-glazing unit
DOOR_OPEN_RATIO = 0.45            # Swing open angle ratio (0.0=closed, 1.0=90 deg)

# ------------------------------------------------------------------------------
# Multi-Floor Layout Options
# ------------------------------------------------------------------------------
# Set STACK_FLOORS = True to stack Floor 4 directly on top of Floor 3 in 3D,
# or False to display them side-by-side for architectural plan review.
STACK_FLOORS = False

FLOOR_4_SIDE_OFFSET = (10.5, 0.0, 0.0)
FLOOR_4_STACK_OFFSET = (0.0, 0.0, WALL_HEIGHT + SLAB_THICK)


def get_floor_4_offset(stack: bool = None) -> tuple:
    """Returns the (x, y, z) offset vector for Floor 4 based on stacking mode."""
    use_stack = STACK_FLOORS if stack is None else stack
    return FLOOR_4_STACK_OFFSET if use_stack else FLOOR_4_SIDE_OFFSET
