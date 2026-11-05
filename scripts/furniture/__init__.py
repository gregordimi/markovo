"""
Markovo Furniture Module.

Provides isolated, standalone furniture and joinery packages for individual rooms:
- kitchen: Birch plywood carcasses, olive inset fronts, solid wood worktop, sink, hob, oven, fridge.
"""

from . import (
    kitchen,
    living_room,
    bedroom,
    bathroom,
    utility,
    attic_office,
    attic_bedroom,
)

__all__ = [
    "kitchen",
    "living_room",
    "bedroom",
    "bathroom",
    "utility",
    "attic_office",
    "attic_bedroom",
]

