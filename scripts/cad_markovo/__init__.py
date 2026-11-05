"""
Markovo 3D Architectural CAD Package.

Modular BIM/CAD modeling package for Blender:
- config: architectural dimensions, heights, and global settings
- materials: PBR and procedural material library
- geometry: 3D CAD mesh generators and primitives
- kitchen: kitchen joinery runs (plywood carcasses, inset fronts, worktop, sink, hob)
- builder: FloorPlanBuilder class for opening cutouts and collection hierarchies
- floor3: Floor 3 (Main Level) specification
- floor4: Floor 4 (Attic Level) specification
- scene: scene clearing, lighting, cameras, and rendering
"""

import site
import sys

_user_site = site.getusersitepackages()
if _user_site and _user_site not in sys.path:
    sys.path.append(_user_site)

from . import config
from . import materials
from . import geometry
from . import kitchen
from . import builder
from . import floor3
from . import floor4
from . import scene
from . import cad_export

__all__ = [
    "config",
    "materials",
    "geometry",
    "kitchen",
    "builder",
    "floor3",
    "floor4",
    "scene",
    "cad_export",
]
