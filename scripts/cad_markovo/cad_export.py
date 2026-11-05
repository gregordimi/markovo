"""
CAD and Vector Blueprint Exporter for Markovo 3D Floor Plans.

Provides:
- AutoCAD DXF (R2018) export via `ezdxf` with standardized CAD layers & lineweights
- Scalable 2D Vector Blueprint export via `drawsvg`
"""

import math
from pathlib import Path
from typing import List, Tuple
import ezdxf
from ezdxf import colors
import drawsvg as draw

from .config import CM
from .geometry import wall_quad
from .builder import FloorPlanBuilder


def export_to_dxf(floor_builders: List[FloorPlanBuilder], filepath: str):
    """
    Exports floor plans to an authentic layered AutoCAD DXF (R2018) file.
    Standardized CAD Layers:
      - A-WALL: Solid walls (thick line, color 7)
      - A-DOOR: Swing doors & arcs (color 1, red)
      - A-GLAZ: Glazed windows & mullions (color 4, cyan)
      - A-FLOR: Room floor slab boundaries (color 8, dark gray)
      - A-KITCH: Kitchen cabinetry, carcasses, sink & hob (color 3, green)
      - A-BALC: Balcony parapets and stone coping (color 6, magenta)
      - A-DIMS: CAD dimension strings & ticks (color 5, blue)
      - A-TEXT: Room stamps, dimensions, and area text (color 2, yellow)
    """
    doc = ezdxf.new("R2018", setup=True)
    msp = doc.modelspace()

    # Setup layers with lineweights (in 1/100 mm)
    layer_defs = [
        ("A-WALL", colors.WHITE, 50),
        ("A-DOOR", colors.RED, 25),
        ("A-GLAZ", colors.CYAN, 25),
        ("A-FLOR", colors.GRAY, 13),
        ("A-KITCH", colors.GREEN, 25),
        ("A-BALC", colors.MAGENTA, 35),
        ("A-DIMS", colors.BLUE, 18),
        ("A-TEXT", colors.YELLOW, 18),
    ]
    for name, color, weight in layer_defs:
        if name not in doc.layers:
            doc.layers.new(name, dxfattribs={"color": color, "lineweight": weight})

    for b in floor_builders:
        # Root translation offset
        ox = b.root.location.x / CM
        oy = b.root.location.y / CM

        # 1. Floor Slabs
        for r in b.rooms:
            pts = [(x + ox, y + oy) for x, y in r["poly"]]
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "A-FLOR"})

        # 2. Walls (Quads)
        for w in b.walls:
            q = wall_quad(w["x1"] + ox, w["y1"] + oy, w["x2"] + ox, w["y2"] + oy, w["thickness"])
            msp.add_lwpolyline(q, close=True, dxfattribs={"layer": "A-WALL"})

        # 3. Windows
        for win in b.windows:
            wx1, wy1 = win["x1"] + ox, win["y1"] + oy
            wx2, wy2 = win["x2"] + ox, win["y2"] + oy
            wq = wall_quad(wx1, wy1, wx2, wy2, win.get("thickness", 15.0))
            msp.add_lwpolyline(wq, close=True, dxfattribs={"layer": "A-GLAZ"})
            # Centerline glazing
            msp.add_line((wx1, wy1), (wx2, wy2), dxfattribs={"layer": "A-GLAZ"})

        # 4. Doors
        for d in b.doors:
            hx, hy = d["hx"] + ox, d["hy"] + oy
            radius = d["radius"]
            sa, ea = d["start_angle"], d["end_angle"]
            # Swing arc
            msp.add_arc(
                center=(hx, hy),
                radius=radius,
                start_angle=sa,
                end_angle=ea,
                dxfattribs={"layer": "A-DOOR"},
            )
            # Hinge to leaf edge
            rad_leaf = math.radians(sa)
            msp.add_line(
                (hx, hy),
                (hx + radius * math.cos(rad_leaf), hy + radius * math.sin(rad_leaf)),
                dxfattribs={"layer": "A-DOOR"},
            )

        # 5. Terraces / Balconies
        for t in b.terraces:
            tx, ty, tw, th = t["x"] + ox, t["y"] + oy, t["w"], t["h"]
            t_poly = [(tx, ty), (tx + tw, ty), (tx + tw, ty + th), (tx, ty + th)]
            msp.add_lwpolyline(t_poly, close=True, dxfattribs={"layer": "A-BALC"})

        # 6. Dimensions
        for d in b.dimensions:
            p1 = (d["p1"][0] + ox, d["p1"][1] + oy)
            p2 = (d["p2"][0] + ox, d["p2"][1] + oy)
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            L = math.hypot(dx, dy)
            if L < 1.0:
                continue
            ux, uy = dx / L, dy / L
            nx, ny = (-uy, ux) if d["side"] == "left" else (uy, -ux)
            offset = d["offset_cm"]

            d1 = (p1[0] + nx * offset, p1[1] + ny * offset)
            d2 = (p2[0] + nx * offset, p2[1] + ny * offset)

            # Parallel dimension line & witness lines
            msp.add_line(d1, d2, dxfattribs={"layer": "A-DIMS"})
            msp.add_line(p1, (d1[0] + nx * 5, d1[1] + ny * 5), dxfattribs={"layer": "A-DIMS"})
            msp.add_line(p2, (d2[0] + nx * 5, d2[1] + ny * 5), dxfattribs={"layer": "A-DIMS"})

            # 45 degree ticks
            tlen = 7.0
            tux, tuy = (ux + nx) * 0.7071 * tlen, (uy + ny) * 0.7071 * tlen
            msp.add_line((d1[0] - tux, d1[1] - tuy), (d1[0] + tux, d1[1] + tuy), dxfattribs={"layer": "A-DIMS"})
            msp.add_line((d2[0] - tux, d2[1] - tuy), (d2[0] + tux, d2[1] + tuy), dxfattribs={"layer": "A-DIMS"})

            # Dimension text
            tx = 0.5 * (d1[0] + d2[0]) + nx * 7.0
            ty = 0.5 * (d1[1] + d2[1]) + ny * 7.0
            rot_deg = math.degrees(math.atan2(uy, ux))
            if 90.0 < rot_deg <= 270.0:
                rot_deg -= 180.0
            elif -270.0 <= rot_deg < -90.0:
                rot_deg += 180.0
            msp.add_text(
                f"{round(L)}",
                dxfattribs={"layer": "A-TEXT", "height": 14.0, "rotation": rot_deg},
            ).set_placement((tx, ty), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)

        # 7. Room Stamps (shapely area and centroid)
        import shapely.geometry
        for r in b.rooms:
            if r.get("mat_key") == "void":
                continue
            poly = shapely.geometry.Polygon(r["poly"])
            area_m2 = round(poly.area * 0.0001, 2)
            minx, miny, maxx, maxy = poly.bounds
            width_m = round((maxx - minx) * 0.01, 2)
            depth_m = round((maxy - miny) * 0.01, 2)
            cx, cy = poly.centroid.x + ox, poly.centroid.y + oy

            clean_name = r["name"].upper().replace("_", " ")
            stamp_text = f"{clean_name}\\P{width_m:.2f} x {depth_m:.2f} m\\P{area_m2:.2f} m²"
            mtext = msp.add_mtext(
                stamp_text,
                dxfattribs={"layer": "A-TEXT", "char_height": 12.0},
            )
            mtext.set_location(insert=(cx, cy), attachment_point=ezdxf.enums.MTextEntityAlignment.MIDDLE_CENTER)

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(filepath)
    print(f"[CAD Export] Saved AutoCAD DXF (R2018) to: {filepath}")


def export_to_svg(
    floor_builder: FloorPlanBuilder,
    filepath: str,
    view_width: float = 850.0,
    view_height: float = 1200.0,
    margin: float = 60.0,
    style: str = "blueprint",
):
    """
    Exports a standalone, razor-sharp architectural vector floor plan sheet via drawsvg.
    Styles:
      'blueprint': navy blue background with crisp white / cyan linework
      'white': technical drafting paper with dark ink lines
    """
    import shapely.geometry

    b = floor_builder
    # Compute bounds from all rooms and walls
    all_x, all_y = [], []
    for r in b.rooms:
        for x, y in r["poly"]:
            all_x.append(x)
            all_y.append(y)
    for w in b.walls:
        all_x.extend([w["x1"], w["x2"]])
        all_y.extend([w["y1"], w["y2"]])

    min_x = min(all_x) - 80 if all_x else -50
    max_x = max(all_x) + 80 if all_x else 800
    min_y = min(all_y) - 80 if all_y else -50
    max_y = max(all_y) + 120 if all_y else 1150

    model_w = max_x - min_x
    model_h = max_y - min_y

    # SVG Canvas setup
    scale = min((view_width - 2 * margin) / model_w, (view_height - 2 * margin) / model_h)
    dwg = draw.Drawing(view_width, view_height, origin=(0, 0))

    # Palette
    if style == "blueprint":
        bg_col = "#0B1D3A"
        wall_fill = "#132D54"
        wall_stroke = "#FFFFFF"
        door_col = "#5CE1E6"
        win_col = "#4DEEEA"
        dim_col = "#7FB3D5"
        text_col = "#FFFFFF"
        terrace_stroke = "#E5E8E8"
    else:
        bg_col = "#FDFEFE"
        wall_fill = "#D5D8DC"
        wall_stroke = "#17202A"
        door_col = "#C0392B"
        win_col = "#2980B9"
        dim_col = "#1B4F72"
        text_col = "#111111"
        terrace_stroke = "#7F8C8D"

    # Background
    dwg.append(draw.Rectangle(0, 0, view_width, view_height, fill=bg_col))

    def to_svg(x: float, y: float) -> Tuple[float, float]:
        """Maps CAD plan coordinates (x right, y up in cm) to SVG canvas coordinates."""
        sx = margin + (x - min_x) * scale
        sy = view_height - margin - (y - min_y) * scale
        return sx, sy

    # 1. Floor Slabs
    for r in b.rooms:
        if r.get("mat_key") == "void":
            continue
        pts = [to_svg(x, y) for x, y in r["poly"]]
        flat_pts = [coord for pt in pts for coord in pt]
        dwg.append(draw.Lines(*flat_pts, close=True, fill=wall_fill, fill_opacity=0.35, stroke="none"))

    # 2. Terraces / Balconies
    for t in b.terraces:
        x, y, w, h = t["x"], t["y"], t["w"], t["h"]
        poly = [to_svg(x, y), to_svg(x + w, y), to_svg(x + w, y + h), to_svg(x, y + h)]
        flat_pts = [c for pt in poly for c in pt]
        dwg.append(draw.Lines(*flat_pts, close=True, fill="none", stroke=terrace_stroke, stroke_width=2.0, stroke_dasharray="6,4"))

    # 3. Walls
    for w in b.walls:
        q = wall_quad(w["x1"], w["y1"], w["x2"], w["y2"], w["thickness"])
        svg_q = [to_svg(x, y) for x, y in q]
        flat_pts = [c for pt in svg_q for c in pt]
        dwg.append(draw.Lines(*flat_pts, close=True, fill=wall_fill, stroke=wall_stroke, stroke_width=2.5))

    # 4. Windows
    for win in b.windows:
        wx1, wy1 = to_svg(win["x1"], win["y1"])
        wx2, wy2 = to_svg(win["x2"], win["y2"])
        dwg.append(draw.Line(wx1, wy1, wx2, wy2, stroke=win_col, stroke_width=3.5))

    # 5. Doors
    for d in b.doors:
        hx, hy = to_svg(d["hx"], d["hy"])
        r_px = d["radius"] * scale
        dwg.append(draw.Circle(hx, hy, 3.0, fill=door_col))

    # 6. Dimensions
    for d in b.dimensions:
        p1 = d["p1"]
        p2 = d["p2"]
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        L = math.hypot(dx, dy)
        if L < 1.0:
            continue
        ux, uy = dx / L, dy / L
        nx, ny = (-uy, ux) if d["side"] == "left" else (uy, -ux)
        offset = d["offset_cm"]

        d1 = (p1[0] + nx * offset, p1[1] + ny * offset)
        d2 = (p2[0] + nx * offset, p2[1] + ny * offset)

        s_d1 = to_svg(*d1)
        s_d2 = to_svg(*d2)
        s_p1 = to_svg(*p1)
        s_p2 = to_svg(*p2)

        dwg.append(draw.Line(s_d1[0], s_d1[1], s_d2[0], s_d2[1], stroke=dim_col, stroke_width=1.5))
        dwg.append(draw.Line(s_p1[0], s_p1[1], s_d1[0], s_d1[1], stroke=dim_col, stroke_width=1.0, stroke_opacity=0.7))
        dwg.append(draw.Line(s_p2[0], s_p2[1], s_d2[0], s_d2[1], stroke=dim_col, stroke_width=1.0, stroke_opacity=0.7))

        # Centered dimension text
        tx = 0.5 * (s_d1[0] + s_d2[0])
        ty = 0.5 * (s_d1[1] + s_d2[1]) - 6.0
        dwg.append(draw.Text(f"{round(L)}", font_size=12, x=tx, y=ty, text_anchor="middle", fill=dim_col, font_family="monospace"))

    # 7. Room Stamps
    for r in b.rooms:
        if r.get("mat_key") == "void":
            continue
        poly = shapely.geometry.Polygon(r["poly"])
        area_m2 = round(poly.area * 0.0001, 2)
        minx, miny, maxx, maxy = poly.bounds
        width_m = round((maxx - minx) * 0.01, 2)
        depth_m = round((maxy - miny) * 0.01, 2)
        cx, cy = to_svg(poly.centroid.x, poly.centroid.y)

        clean_name = r["name"].upper().replace("_", " ")
        dwg.append(draw.Text(clean_name, font_size=13, x=cx, y=cy - 10, text_anchor="middle", fill=text_col, font_weight="bold", font_family="sans-serif"))
        dwg.append(draw.Text(f"{width_m:.2f} × {depth_m:.2f} m", font_size=10, x=cx, y=cy + 4, text_anchor="middle", fill=text_col, font_family="sans-serif", fill_opacity=0.85))
        dwg.append(draw.Text(f"{area_m2:.2f} m²", font_size=10, x=cx, y=cy + 17, text_anchor="middle", fill=text_col, font_family="sans-serif", fill_opacity=0.85))

    # Title Banner
    dwg.append(draw.Text(b.name.upper().replace("_", " "), font_size=16, x=margin, y=margin * 0.6, fill=text_col, font_weight="bold", font_family="sans-serif"))

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    dwg.save_svg(filepath)
    print(f"[CAD Export] Saved 2D Vector Blueprint SVG to: {filepath}")
