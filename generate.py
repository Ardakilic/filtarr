#!/usr/bin/env python3
"""
Filtarr — parametric storage cases for pour-over paper filters.

Generates print-ready STLs for two-piece, dust-proof wedge boxes that hold
flat cone filter papers, for every paper in the PAPERS registry and in three
case designs:

  * friction     — "chocolate box" full-cover telescoping lid, snug fit
  * magnet-skirt — same telescoping lid with a loose glide fit, closed by
                   4 pairs of 6 x 3 mm disc magnets in outward wall lobes
  * magnet-flat  — flat lay-on lid with a small alignment lip; 3 magnet
                   pairs live in enlarged corners (apex + both wide-end
                   corners), MAG-BOX style

Each design's lid also comes in an engraved version (ENGRAVE_TEXT on the
top face), giving 6 printable variants per paper from 9 STLs (bases are
shared between the plain and engraved variants):

  <folder>/stl/<paper>-case-<design>-base.stl
  <folder>/stl/<paper>-case-<design>-lid.stl
  <folder>/stl/<paper>-case-<design>-lid-engraved.stl

Also writes one self-contained interactive 3D preview per paper (inlined
three.js + base64 STLs, works offline from file://).

Usage:
  pip install -r requirements.txt
  python3 generate.py

To add a new paper, add one PAPERS entry — see HOWTO.md.
All dimensions are millimetres / degrees.
"""

import base64
import json
import math
import os

import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import Polygon, Point, box as shp_box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------------
# PAPERS — one entry per supported filter paper (see HOWTO.md)
# --------------------------------------------------------------------------
# side      longest flat edge from the tip, mm (usually the crimped seam edge)
# angle     wedge angle of the flat folded paper, deg.  For a cone dripper
#           with full apex angle A the flat paper is 180*sin(A/2) degrees.
# tab_extra extra radial clearance, mm, for the round hanging tab some brands
#           put on the arc edge (position varies by brand — radial clearance
#           covers every position, so one box fits all brands)
# designs   optional: subset of DESIGNS to generate (default: all three)

PAPERS = {
    "deep27": {
        "display": "CAFEC Deep 27",
        "folder": "deep27",
        "side": 155.0,      # user-measured; photo-verified
        "angle": 42.0,      # 27° cone -> 180*sin(13.5°) = 42.02°
        "tab_extra": 0.0,   # Deep 27 papers have no hanging tab
    },
    "v60-01": {
        "display": "V60 size 01 (Hario / CAFEC)",
        "folder": "v60",
        "side": 107.0,      # Hario spec 100x100; sheets measure up to 105x107
        "angle": 90.0,      # 60° cone -> 180*sin(30°) = 90°
        "tab_extra": 6.0,   # Hario tab protrudes ~5-7 mm from the arc, next to
                            # the seam corner; CAFEC cone papers have no tab
    },
    "v60-02": {
        "display": "V60 size 02 (Hario / CAFEC)",
        "folder": "v60",
        "side": 128.0,      # Hario spec 125x125; sheets measure up to 125x128
        "angle": 90.0,
        "tab_extra": 7.0,
    },
    # CAFEC cone papers have no hanging tab and run a few mm smaller than
    # Hario — these tabless cases are noticeably more compact (smaller beds)
    "v60-cafec-01": {
        "display": "CAFEC cone cup 1 (V60-01 size, tabless)",
        "folder": "v60",
        "side": 106.0,      # retail dims ~101 x 106 mm
        "angle": 90.0,
        "tab_extra": 0.0,
        "designs": ("friction",),
    },
    "v60-cafec-02": {
        "display": "CAFEC cone cup 4 (V60-02 size, tabless)",
        "folder": "v60",
        "side": 127.0,      # retail dims ~121 x 127 mm
        "angle": 90.0,
        "tab_extra": 0.0,
        "designs": ("friction",),
    },
}

# --------------------------------------------------------------------------
# SHARED DESIGN PARAMETERS
# --------------------------------------------------------------------------

ANGLE_SLACK = 3.0        # extra wedge angle so papers never wedge tight
RADIAL_SLACK = 3.5       # extra length beyond the paper side
INNER_ROUND = 4.0        # fillet radius of the interior corners

WALL_T = 2.4             # base wall thickness
FLOOR_T = 2.4            # base floor thickness
DEPTH = 42.0             # interior depth (≈ a full 100-pack with headroom)

# Telescoping designs (friction / magnet-skirt)
SKIRT_T = 2.0            # lid skirt wall thickness
PLINTH = 3.0             # base rim left exposed below the closed lid (grip)
LID_T_FRICTION = 2.4     # lid top plate thickness, friction design
LID_T_MAGNET = 4.6       # thicker plate: hides the magnet pockets
CLEAR_FRICTION = 0.28    # lid-to-base clearance per side, friction design
CLEAR_MAGNET = 0.50      # loose glide fit — the magnets do the holding

# Finger scoop cut into the wide-end wall (friction / magnet-skirt bases;
# covered by the skirt when closed, so it stays dust-proof)
SCOOP_W = 36.0
SCOOP_R = 14.0           # corner radius of the scoop
SCOOP_ABOVE_FLOOR = 8.0  # scoop bottom height above the interior floor

# Grip notches at the bottom edge of the telescoping lids
NOTCH_W = 22.0
NOTCH_H = 10.0
NOTCH_R = 6.0
NOTCH_FRAC = 0.36        # notch position along the straight sides, × R_INT

# Magnets: 6 mm diameter x 3 mm thick discs, glued into blind pockets
POCKET_D = 6.4           # pocket diameter (0.4 mm glue/fit allowance)
POCKET_DEPTH = 3.2       # pocket depth (magnet sits ~0.2 mm recessed)

# magnet-skirt design: outward lobes on the base wall host the pockets
LOBE_R = 5.0             # radius of the wall lobes
MAG_OFFSET = 5.5         # magnet centre distance outside the interior face
MAG_ARC_ANGLES = (13.0, -13.0)  # two magnets on the wide-end arc
MAG_SIDE_FRAC = 0.60     # straight-side magnet position, × R_INT

# magnet-flat design: flat lay-on lid, magnets in 3 enlarged corners
LIP_CLEAR = 0.5          # alignment lip clearance to the interior wall
LIP_T = 1.8              # alignment lip thickness
LIP_H = 2.5              # how far the lip descends into the opening
CORNER_BLEND_R = 6.0     # smoothing radius blending corner bulges into walls
PRY_W = 20.0             # pry slot under the lid edge, mid-arc
PRY_H = 2.2

# Engraving (lid top face). Upright when the tip of the wedge points at you.
ENGRAVE_TEXT = "Filtarr"
ENGRAVE_WIDTH = 60.0     # total width of the text block
ENGRAVE_DEPTH = 0.6      # 3 layers at 0.2 mm
ENGRAVE_POS_FRAC = 0.70  # text centre along the bisector, × R_INT
# Bold preferred for engraving legibility; Liberation Sans is the
# metric-compatible Arial substitute in the Docker build image
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

# Ghost paper stack shown in the preview only
PREVIEW_STACK_H = 26.0

QS = 24  # quad segments for shapely buffers (arc smoothness)
DESIGNS = ("friction", "magnet-skirt", "magnet-flat")

# --------------------------------------------------------------------------
# STATELESS MESH HELPERS
# --------------------------------------------------------------------------


def sector_poly(angle_deg, radius, steps_per_deg=2.0):
    """Pie-slice polygon, apex at origin, opening along +X, symmetric in Y."""
    n = max(8, int(angle_deg * steps_per_deg))
    ang = np.radians(np.linspace(-angle_deg / 2.0, angle_deg / 2.0, n + 1))
    pts = [(0.0, 0.0)] + [(radius * math.cos(a), radius * math.sin(a)) for a in ang]
    return Polygon(pts)


def prism(poly, z0, z1):
    m = trimesh.creation.extrude_polygon(poly, z1 - z0)
    m.apply_translation([0.0, 0.0, z0])
    return m


def diff(solid, *cutters):
    return trimesh.boolean.difference([solid, *cutters], check_volume=False)


def slot_cutter(width, z0, z1, corner_r, centre_xy, normal_deg, span):
    """Rounded-corner slot prism.

    The profile lives in the (tangent, z) plane and is extruded `span` mm
    along the horizontal outward normal, centred on `centre_xy`.
    """
    prof = (
        shp_box(-width / 2.0, z0, width / 2.0, z1)
        .buffer(-corner_r, quad_segs=16)
        .buffer(corner_r, quad_segs=16)
    )
    m = trimesh.creation.extrude_polygon(prof, span)
    m.apply_translation([0.0, 0.0, -span / 2.0])
    nd = math.radians(normal_deg)
    n = np.array([math.cos(nd), math.sin(nd), 0.0])
    up = np.array([0.0, 0.0, 1.0])
    t = np.cross(up, n)  # right-handed: local x -> tangent, y -> up, z -> normal
    tf = np.eye(4)
    tf[:3, 0], tf[:3, 1], tf[:3, 2] = t, up, n
    tf[:3, 3] = [centre_xy[0], centre_xy[1], 0.0]
    m.apply_transform(tf)
    return m


def pocket_cutters(centres, z0, z1):
    """Vertical magnet-pocket cutters spanning exactly z0..z1."""
    cutters = []
    for cx, cy in centres:
        c = trimesh.creation.cylinder(radius=POCKET_D / 2.0,
                                      height=z1 - z0, sections=48)
        c.apply_translation([cx, cy, (z0 + z1) / 2.0])
        cutters.append(c)
    return cutters


def print_orientation_lid(lid):
    """Flip the lid so its top face lies on the print bed."""
    m = lid.copy()
    m.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
    m.apply_translation([0.0, 0.0, -m.bounds[0][2]])
    return m


# --------------------------------------------------------------------------
# CASE — all per-paper geometry, built in "closed box" world coordinates
# (wedge apex at the origin, opening along +X, z=0 at the table)
# --------------------------------------------------------------------------


class Case:
    def __init__(self, slug):
        cfg = PAPERS[slug]
        self.slug = slug
        self.cfg = cfg
        self.side = cfg["side"]
        self.angle = cfg["angle"]
        self.int_angle = self.angle + ANGLE_SLACK
        self.half = self.int_angle / 2.0
        # after filleting, the interior apex tip sits this far from the origin
        self.apex_tip_x = INNER_ROUND * (1.0 / math.sin(math.radians(self.half)) - 1.0)
        self.r_int = self.side + self.apex_tip_x + RADIAL_SLACK + cfg["tab_extra"]
        self.base_h = FLOOR_T + DEPTH
        self.engrave_x = ENGRAVE_POS_FRAC * self.r_int

        self.interior = (
            sector_poly(self.int_angle, self.r_int)
            .buffer(-INNER_ROUND, quad_segs=QS)
            .buffer(INNER_ROUND, quad_segs=QS)
        )
        self.ext_plain = self.interior.buffer(WALL_T, quad_segs=QS)

        self.magnets_skirt = self._skirt_magnet_centres()
        self.magnets_flat = self._flat_magnet_centres()

        self.ext_skirt = unary_union(
            [self.ext_plain]
            + [Point(c).buffer(LOBE_R, quad_segs=QS) for c in self.magnets_skirt]
        )
        # corner bulges blended smooth with a morphological closing (dilate+erode)
        self.ext_flat = (
            unary_union(
                [self.ext_plain]
                + [Point(c).buffer(POCKET_D / 2.0 + 1.6, quad_segs=QS)
                   for c in self.magnets_flat]
            )
            .buffer(CORNER_BLEND_R, quad_segs=QS)
            .buffer(-CORNER_BLEND_R, quad_segs=QS)
        )

    # -- magnet layouts ------------------------------------------------------

    def _skirt_magnet_centres(self):
        """magnet-skirt: 2 on the wide-end arc + 1 per straight side."""
        out = []
        for a in MAG_ARC_ANGLES:
            r = math.radians(a)
            out.append(((self.r_int + MAG_OFFSET) * math.cos(r),
                        (self.r_int + MAG_OFFSET) * math.sin(r)))
        side_r = MAG_SIDE_FRAC * self.r_int
        for side in (+1, -1):
            edge = math.radians(side * self.half)
            nrm = edge + side * math.pi / 2.0
            px = side_r * math.cos(edge) + MAG_OFFSET * math.cos(nrm)
            py = side_r * math.sin(edge) + MAG_OFFSET * math.sin(nrm)
            out.append((px, py))
        return out

    def _step_out(self, start_xy, dir_deg, clearance):
        """March from start_xy along dir_deg until clear of the interior."""
        d = math.radians(dir_deg)
        v = np.array([math.cos(d), math.sin(d)])
        p = np.array(start_xy, dtype=float)
        while Point(p).distance(self.interior) < clearance:
            p += v * 0.1
        return (float(p[0]), float(p[1]))

    def _flat_magnet_centres(self):
        """magnet-flat: apex + both wide-end corners."""
        clr = POCKET_D / 2.0 + 1.3
        pts = [self._step_out((self.apex_tip_x, 0.0), 180.0, clr)]
        for side in (+1, -1):
            corner = (self.r_int * math.cos(math.radians(side * self.half)),
                      self.r_int * math.sin(math.radians(side * self.half)))
            pts.append(self._step_out(corner, side * (self.half + 45.0), clr))
        return pts

    # -- cutters ---------------------------------------------------------------

    def scoop_cutter(self):
        return slot_cutter(SCOOP_W, FLOOR_T + SCOOP_ABOVE_FLOOR,
                           self.base_h + 40.0, SCOOP_R,
                           (self.r_int, 0.0), 0.0, 60.0)

    def notch_cutters(self):
        """Grip notches at the bottom edge of the telescoping lids."""
        out = []
        notch_r = NOTCH_FRAC * self.r_int
        for side in (+1, -1):
            edge = math.radians(side * self.half)
            nrm_deg = math.degrees(edge) + side * 90.0
            px = notch_r * math.cos(edge)
            py = notch_r * math.sin(edge)
            out.append(
                slot_cutter(NOTCH_W, PLINTH - 6.0, PLINTH + NOTCH_H, NOTCH_R,
                            (px, py), nrm_deg, 24.0))
        return out

    def pry_cutter(self):
        """Shallow slot under the flat lid's edge, mid-arc: thumbnail pry point."""
        return slot_cutter(PRY_W, self.base_h - PRY_H, self.base_h + 5.0, 2.0,
                           (self.r_int, 0.0), 0.0, 30.0)

    # -- engraving ---------------------------------------------------------------

    def text_geometry(self):
        """ENGRAVE_TEXT on the lid top, upright when the wedge tip points at
        the reader."""
        from matplotlib.font_manager import FontProperties
        from matplotlib.textpath import TextPath

        fp = FontProperties(family=["sans-serif"])
        for cand in FONT_CANDIDATES:
            if os.path.exists(cand):
                fp = FontProperties(fname=cand)
                break

        tp = TextPath((0, 0), ENGRAVE_TEXT, size=40, prop=fp)
        geom = None
        for ring in tp.to_polygons():
            if len(ring) < 3:
                continue
            p = Polygon(ring)
            if not p.is_valid:
                p = p.buffer(0)
            if p.is_empty:
                continue
            geom = p if geom is None else geom.symmetric_difference(p)

        minx, miny, maxx, maxy = geom.bounds
        s = ENGRAVE_WIDTH / (maxx - minx)
        geom = affinity.scale(geom, xfact=s, yfact=s, origin=(0, 0))
        minx, miny, maxx, maxy = geom.bounds
        geom = affinity.translate(geom, -(minx + maxx) / 2.0, -(miny + maxy) / 2.0)
        # local (reading, up) -> world: text up-vector = +X, so the text is
        # upright when the apex (wedge tip) points toward the reader
        geom = affinity.rotate(geom, -90, origin=(0, 0))
        return affinity.translate(geom, self.engrave_x, 0.0)

    def engrave_cutters(self, plate_top):
        geom = self.text_geometry()
        parts = list(geom.geoms) if hasattr(geom, "geoms") else [geom]
        return [prism(g, plate_top - ENGRAVE_DEPTH, plate_top + 1.0)
                for g in parts if g.geom_type == "Polygon" and not g.is_empty]

    # -- parts ---------------------------------------------------------------

    def build_base(self, design):
        if design == "friction":
            solid = prism(self.ext_plain, 0.0, self.base_h)
            cutters = [self.scoop_cutter()]
        elif design == "magnet-skirt":
            solid = prism(self.ext_skirt, 0.0, self.base_h)
            cutters = [self.scoop_cutter()] + pocket_cutters(
                self.magnets_skirt, self.base_h - POCKET_DEPTH, self.base_h + 1.0)
        else:  # magnet-flat: no through-scoop (the whole top opens), pry slot instead
            solid = prism(self.ext_flat, 0.0, self.base_h)
            cutters = [self.pry_cutter()] + pocket_cutters(
                self.magnets_flat, self.base_h - POCKET_DEPTH, self.base_h + 1.0)
        cutters.append(prism(self.interior, FLOOR_T, self.base_h + 1.0))
        return diff(solid, *cutters)

    def build_lid(self, design, engraved=False):
        if design == "friction":
            inner = self.ext_plain.buffer(CLEAR_FRICTION, quad_segs=QS)
            plate_t = LID_T_FRICTION
        elif design == "magnet-skirt":
            inner = self.ext_skirt.buffer(CLEAR_MAGNET, quad_segs=QS)
            plate_t = LID_T_MAGNET
        else:
            plate_t = LID_T_MAGNET

        if design == "magnet-flat":
            plate = prism(self.ext_flat, self.base_h, self.base_h + plate_t)
            lip = prism(
                self.interior.buffer(-LIP_CLEAR, quad_segs=QS).difference(
                    self.interior.buffer(-(LIP_CLEAR + LIP_T), quad_segs=QS)),
                self.base_h - LIP_H, self.base_h + 0.5)
            solid = trimesh.boolean.union([plate, lip], check_volume=False)
            cutters = pocket_cutters(self.magnets_flat, self.base_h - 1.0,
                                     self.base_h + POCKET_DEPTH)
        else:
            outer = inner.buffer(SKIRT_T, quad_segs=QS)
            solid = prism(outer, PLINTH, self.base_h + plate_t)
            cutters = [prism(inner, PLINTH - 1.0, self.base_h)] + self.notch_cutters()
            if design == "magnet-skirt":
                # pockets rise into the lid plate from its underside
                cutters += pocket_cutters(self.magnets_skirt, self.base_h - 1.0,
                                          self.base_h + POCKET_DEPTH)
        if engraved:
            cutters += self.engrave_cutters(self.base_h + plate_t)
        return diff(solid, *cutters)

    # -- preview-only ghosts --------------------------------------------------

    def paper_ghost(self):
        poly = sector_poly(self.angle, self.side)
        if self.cfg["tab_extra"] > 0.0:
            poly = poly.union(Point(self.side - 2.0, 0.0).buffer(7.5, quad_segs=QS))
        poly = affinity.translate(poly, xoff=self.apex_tip_x + 1.5)
        return prism(poly, FLOOR_T + 0.3, FLOOR_T + 0.3 + PREVIEW_STACK_H)

    def magnet_ghosts(self, centres):
        base_m, lid_m = [], []
        for cx, cy in centres:
            for bucket, z in ((base_m, self.base_h - POCKET_DEPTH + 0.1),
                              (lid_m, self.base_h + 0.1)):
                c = trimesh.creation.cylinder(radius=3.0, height=3.0, sections=48)
                c.apply_translation([cx, cy, z + 1.5])
                bucket.append(c)
        return trimesh.util.concatenate(base_m), trimesh.util.concatenate(lid_m)

    # -- output naming ---------------------------------------------------------

    @property
    def designs(self):
        return tuple(self.cfg.get("designs", DESIGNS))

    @property
    def out_dir(self):
        return os.path.join(HERE, self.cfg["folder"])

    @property
    def short(self):
        """Slug without the folder prefix: 'v60-cafec-01' -> 'cafec-01'."""
        prefix = self.cfg["folder"] + "-"
        return self.slug[len(prefix):] if self.slug.startswith(prefix) else self.slug

    @property
    def preview_name(self):
        if self.cfg["folder"] == self.slug:
            return "preview.html"
        return f"preview-{self.short}.html"


# --------------------------------------------------------------------------
# BUILD + EXPORT
# --------------------------------------------------------------------------


def main():
    cases = []
    for slug in PAPERS:
        case = Case(slug)
        cases.append(case)
        print(f"\n=== {case.cfg['display']} ({slug}) — "
              f"interior {case.r_int - case.apex_tip_x:.0f} mm x "
              f"{case.int_angle:.0f}°, {DEPTH:.0f} mm deep ===")
        stl_dir = os.path.join(case.out_dir, "stl")
        os.makedirs(stl_dir, exist_ok=True)

        parts_world = {}
        for design in case.designs:
            parts_world[f"{design}-base"] = case.build_base(design)
            parts_world[f"{design}-lid"] = case.build_lid(design)
            parts_world[f"{design}-lid-engraved"] = case.build_lid(design, engraved=True)

        for name, mesh in parts_world.items():
            assert mesh.is_watertight, f"{slug} {name} is not watertight!"
            out = mesh if name.endswith("base") else print_orientation_lid(mesh)
            path = os.path.join(stl_dir, f"{case.slug}-case-{name}.stl")
            out.export(path)
            ext = out.bounds[1] - out.bounds[0]
            print(f"  {os.path.basename(path):52s} "
                  f"{ext[0]:6.1f} x {ext[1]:6.1f} x {ext[2]:5.1f} mm  "
                  f"{mesh.volume / 1000.0:6.1f} cm3")

        build_preview(case, parts_world)

    build_index(cases)
    print("\ndone.")


def b64stl(mesh):
    return base64.b64encode(mesh.export(file_type="stl")).decode()


LID_COLORS = {"friction": "#2f8f83", "magnet-skirt": "#b3634f",
              "magnet-flat": "#4f7cb3"}


def build_preview(case, parts_world):
    ghost_paper = b64stl(case.paper_ghost())
    variants = {}
    for design in case.designs:
        parts = [
            {"name": "base", "attach": "base", "color": "#8a8f98",
             "stl": b64stl(parts_world[f"{design}-base"])},
            {"name": "lid", "attach": "lid", "color": LID_COLORS[design],
             "stl": b64stl(parts_world[f"{design}-lid"])},
            {"name": "lid-engraved", "attach": "lid", "color": LID_COLORS[design],
             "stl": b64stl(parts_world[f"{design}-lid-engraved"])},
            {"name": "papers", "attach": "base", "color": "#efe3c8",
             "opacity": 0.55, "stl": ghost_paper},
        ]
        if design != "friction":
            centres = (case.magnets_skirt if design == "magnet-skirt"
                       else case.magnets_flat)
            mb, ml = case.magnet_ghosts(centres)
            parts += [
                {"name": "magnets", "attach": "base", "color": "#d7dade",
                 "metal": True, "stl": b64stl(mb)},
                {"name": "magnets-lid", "attach": "lid", "color": "#d7dade",
                 "metal": True, "stl": b64stl(ml)},
            ]
        variants[design] = parts

    has_magnets = any(d.startswith("magnet") for d in case.designs)
    heights = [f"{case.base_h + LID_T_FRICTION:.0f} mm (friction)"]
    if has_magnets:
        heights.append(f"{case.base_h + LID_T_MAGNET:.0f} mm (magnet)")
    dims = {
        "paper": f"{case.side:.0f} mm side, {case.angle:.0f}° wedge",
        "interior": f"{case.r_int - case.apex_tip_x:.0f} mm x "
                    f"{case.int_angle:.0f}°, {DEPTH:.0f} mm deep",
        "closedH": " / ".join(heights),
    }
    if has_magnets:
        dims["magnets"] = (f"Ø6x3 mm discs — skirt: 8, flat: 6; "
                           f"pockets {POCKET_D:.1f} x {POCKET_DEPTH:.1f} mm")
    mag_counts = {"magnet-skirt": 8, "magnet-flat": 6}
    data = {
        "title": f"Filtarr — {case.cfg['display']}",
        "variants": variants,
        "dims": dims,
        "print": {
            design: {
                "base": f"stl/{case.slug}-case-{design}-base.stl",
                "lid": f"stl/{case.slug}-case-{design}-lid.stl",
                "lid_engraved": f"stl/{case.slug}-case-{design}-lid-engraved.stl",
                "magnets": (f"{mag_counts[design]}x Ø6x3 mm magnets + glue"
                            if design in mag_counts else None),
            } for design in case.designs
        },
    }

    def b64file(name):
        with open(os.path.join(HERE, "vendor", name), "rb") as f:
            return base64.b64encode(f.read()).decode()

    with open(os.path.join(HERE, "preview_template.html")) as f:
        tpl = f.read()

    html = tpl.replace("/*__THREE_B64__*/", b64file("three.module.min.js"))
    html = html.replace("/*__THREE_CORE_B64__*/", b64file("three.core.min.js"))
    html = html.replace("/*__DATA__*/null", json.dumps(data))
    out = os.path.join(case.out_dir, case.preview_name)
    with open(out, "w") as f:
        f.write(html)
    print(f"  {os.path.relpath(out, HERE):52s} "
          f"({os.path.getsize(out) / 1e6:.1f} MB preview)")


REPO_URL = "https://github.com/Ardakilic/filtarr"


def build_index(cases):
    """Landing page (index.html) linking every paper's preview, render sheet
    and STL downloads — published to GitHub Pages by the pages workflow."""
    cards = []
    for case in cases:
        folder = case.cfg["folder"]
        sfx = "" if folder == case.slug else "-" + case.short
        renders = f"{folder}/docs/renders{sfx}.png"
        tab_txt = (f"{case.cfg['tab_extra']:.0f} mm tab clearance"
                   if case.cfg["tab_extra"] else "no tab")
        stls = "".join(
            f'<li><a href="{folder}/stl/{case.slug}-case-{design}-{part}.stl">'
            f"{case.slug}-case-{design}-{part}.stl</a></li>"
            for design in case.designs
            for part in ("base", "lid", "lid-engraved"))
        cards.append(f"""
  <article>
    <a href="{renders}"><img loading="lazy" src="{renders}"
         alt="Renders of the {case.cfg['display']} cases"></a>
    <h2>{case.cfg['display']}</h2>
    <p class="geo">{case.side:.0f} mm side · {case.angle:.0f}° wedge ·
       {tab_txt} · {len(case.designs)} design{'s' if len(case.designs) > 1 else ''}</p>
    <p><a class="btn" href="{folder}/{case.preview_name}">Interactive 3D preview</a></p>
    <details><summary>STL downloads</summary><ul>{stls}</ul></details>
  </article>""")

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Filtarr — 3D-printable filter paper cases</title>
<style>
  :root {{ --bg: #14171c; --panel: #1e232b; --ink: #e8eaee; --muted: #9aa3b0;
           --accent: #35b8a5; --line: #313945; }}
  * {{ box-sizing: border-box; margin: 0; }}
  body {{ background: var(--bg); color: var(--ink); padding: 40px 20px;
          font: 15px/1.5 -apple-system, "Segoe UI", Roboto, sans-serif; }}
  main {{ max-width: 1080px; margin: 0 auto; }}
  h1 {{ font-size: 30px; }} h1 span {{ color: var(--accent); }}
  .tagline {{ color: var(--muted); margin: 6px 0 8px; }}
  .top a {{ color: var(--accent); }}
  .grid {{ display: grid; gap: 18px; margin-top: 28px;
           grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); }}
  article {{ background: var(--panel); border: 1px solid var(--line);
             border-radius: 14px; padding: 16px; }}
  article img {{ width: 100%; border-radius: 8px; background: #fff; }}
  article h2 {{ font-size: 17px; margin: 12px 0 4px; }}
  .geo {{ color: var(--muted); font-size: 13px; margin-bottom: 10px; }}
  .btn {{ display: inline-block; background: var(--accent); color: #08201c;
          font-weight: 600; text-decoration: none; padding: 8px 14px;
          border-radius: 8px; font-size: 14px; }}
  details {{ margin-top: 10px; font-size: 13px; color: var(--muted); }}
  details a {{ color: var(--ink); }}
  details li {{ margin: 3px 0 3px 18px; word-break: break-all; }}
  footer {{ color: var(--muted); font-size: 13px; margin-top: 32px; }}
  footer a {{ color: var(--accent); }}
</style>
</head>
<body>
<main>
  <div class="top">
    <h1><span>Filtarr</span> — filter paper cases</h1>
    <p class="tagline">3D-printable, dust-proof storage boxes for pour-over
      coffee filter papers. Parametric, open source.</p>
    <p><a href="{REPO_URL}">Source, docs &amp; printing guide on GitHub</a></p>
  </div>
  <div class="grid">{"".join(cards)}
  </div>
  <footer>Code: MIT · Models &amp; images: CC BY 4.0 ·
    <a href="{REPO_URL}">{REPO_URL.split('//')[1]}</a></footer>
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "index.html")
    with open(out, "w") as f:
        f.write(html)
    print(f"\n  index.html ({len(cases)} papers)")


if __name__ == "__main__":
    main()
