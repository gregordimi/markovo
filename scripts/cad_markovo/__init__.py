"""
Markovo 3D Architectural CAD Package.

Modular BIM/CAD modeling package for Blender:
- config: architectural dimensions, heights, and global settings
- materials: PBR and procedural material library
- geometry: 3D CAD mesh generators and primitives
- builder: FloorPlanBuilder class for opening cutouts and collection hierarchies
- floor3: Floor 3 (Main Level) specification
- floor4: Floor 4 (Attic Level) specification
- scene: scene clearing, lighting, cameras, and rendering
"""

from . import config
from . import materials
from . import geometry
from . import builder
from . import floor3
from . import floor4
from . import scene

__all__ = [
    "config",
    "materials",
    "geometry",
    "builder",
    "floor3",
    "floor4",
    "scene",
]
