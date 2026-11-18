#!/usr/bin/env python3
"""
Filtarr — parametric storage cases for pour-over paper filters.

Generates print-ready STLs for two-piece, dust-proof boxes that hold flat
filter papers, for every paper in the PAPERS registry. The box follows the
paper's outline ("shape"): a wedge for flat cone papers (Case), a flat-bottom
fan for Kalita-style papers (TrapezoidCase) or a circle for paper discs such
as AeroPress (RoundCase). Every paper comes in four case designs:

  * friction        — "chocolate box" full-cover telescoping lid, snug fit
                      (round boxes: a twist-off lid without grip notches)
  * magnet-skirt    — same telescoping lid with a loose glide fit, closed by
                      6 x 3 mm disc magnets in outward wall lobes (4 pairs;
                      round boxes 3, 120° apart)
  * magnet-flat     — flat lay-on lid with a small alignment lip; the magnet
                      pairs live in enlarged corners, MAG-BOX style — one
                      per convex corner (wedge 3, fan and combo 4; round
                      boxes 3 bulges, 120° apart)
  * magnet-pedestal — magnet-flat shell + easy paper picking: a full-height
                      finger bay bulges outward mid-arc and the papers rest
                      on a pedestal floor whose edge stops short of the arc
                      wall, so single sheets are pinched from below via the
                      bay — the rim stays closed (dust-proof) and the box
                      grows PEDESTAL_H taller to keep full stack headroom

Each design's lid also comes in an engraved version (ENGRAVE_TEXT on the
top face), giving 8 printable variants per paper from 12 STLs (bases are
shared between the plain and engraved variants):

  <folder>/stl/<paper>-case-<design>-base.stl
  <folder>/stl/<paper>-case-<design>-lid.stl
  <folder>/stl/<paper>-case-<design>-lid-engraved.stl

A PAPERS entry can also combine two papers in one box ("combines" ->
ComboCase, an asymmetric keyhole). It additionally exports dividers, so both
papers fit at once — a loose plate or a table on legs, users print one:
<folder>/stl/<paper>-case-divider.stl, -divider-table.stl and (the pedestal
design's own) -divider-table-pedestal.stl.

Also writes one self-contained interactive 3D preview per paper (inlined
three.js + base64 STLs, works offline from file://).

Usage:
  pip install -r requirements.txt
  python3 generate.py [tolerance overrides]

Printer-fit tolerances and shell thicknesses are CLI flags (defaults in
SHARED DESIGN PARAMETERS), so they can be tuned per printer without editing
code — via make: `make generate GEN_ARGS="--clear-friction 0.32"`. Flags:
--clear-friction, --clear-magnet, --lip-clear, --pocket-d, --pocket-depth,
--wall-t, --floor-t, --skirt-t, --chamfer-bottom, --chamfer-side-wall,
--divider-t, --divider-clear, --divider-leg-h, --notch-w, --notch-h, --arc-notch-w, --arc-notch-h, --arc-notch-gap,
--arc-notch-chamfer, --scoop-w, --scoop-above-floor.

To add a new paper, add one PAPERS entry — see HOWTO.md.
All dimensions are millimetres / degrees.
"""

import argparse
import base64
import json
import math
import os

import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import LineString, Polygon, Point, box as shp_box
from shapely.ops import nearest_points, unary_union

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
# designs   optional: subset of DESIGNS to generate (default: all four)
# depth     optional: interior depth override, mm (default DEPTH). Size it so a
#           loose 100-pack drops in without squeezing: smooth Hario paper
#           stacks ~32 mm/100, creped CAFEC paper ≈ its pouch thickness
#           (40-50 mm/100) — see the README capacity notes.
# shape     optional: outline family, default "wedge" (a flat folded cone
#           paper: side / angle / tab_extra above). make_case() picks the Case
#           class from CASE_CLASSES by it; "trapezoid" (flat-bottom fan papers)
#           and "round" (paper discs) take their own keys instead of
#           side / angle, documented here:
#   "trapezoid" — a flat-bottom fan paper (Kalita 101/102/103 style) folded
#           flat is a truncated sector: two straight sides meeting in a
#           VIRTUAL apex, a straight bottom (crimp seam) edge across them and
#           a top arc concentric with that apex. width / height / bottom
#           describe a REFERENCE sheet of the size (typically its largest);
#           fan_solve() derives angle / arc radius / apex distance from it,
#           and that angle (+ ANGLE_SLACK) is the box's. The box is then
#           sized so EVERY listed sheet fits pushed home — the widest bottom
#           sets the bottom wall, the farthest-reaching sheet the arc, the
#           shortest the pedestal moat — and tools/verify.py seats each one:
#     width     top chord c, mm (corner to corner across the arc)
#     height    centre-line height h, mm (bottom edge to arc, on the bisector)
#     bottom    bottom (crimp seam) edge b, mm
#     variants  optional: ((width, height, bottom), ...) the other real sheets
#               the box must hold (other brands; a variant may be larger than
#               the reference in one dimension) — add sheets here instead of
#               taking per-dimension maxima: the angle depends on all three
#     tab_extra 0.0 (fan papers have no hanging tab); never side / angle
#               (rejected)
#   "round" — flat paper discs (RoundCase); side / angle / tab_extra are
#           rejected if present:
#     diameter  the largest disc to hold, mm (interior Ø = diameter +
#               2·DISC_SLACK). Size it to the biggest real sheet, not the spec.
#     stack_h   optional: preview ghost stack height, mm — a typical pack
#               (default PREVIEW_STACK_H, never above depth − 4)
# combines  INSTEAD of side/angle/tab_extra: the slugs of two papers that one
#           box should hold (-> ComboCase). Their wedges are overlaid against
#           one shared straight wall — an asymmetric keyhole — and each keeps
#           its own slack formula, so both fit exactly like in their own box.
#           depth defaults to the deeper of the two. Adds divider STLs.
# engrave_rot  optional: engraving rotation, deg (default -90 = upright when
#           the wedge tip / the box's -X end points at the reader; 0 =
#           baseline along +X)

PAPERS = {
    "deep27": {
        "display": "CAFEC Deep 27",
        "folder": "deep27",
        "side": 155.0,      # user-measured; photo-verified
        "angle": 42.0,      # 27° cone -> 180*sin(13.5°) = 42.02°
        "tab_extra": 0.0,   # Deep 27 papers have no hanging tab
        "depth": 47.0,      # 100-pack free stack ≈ 40 mm (pouch) + headroom
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
        "depth": 47.0,      # 100-pack free stack ≈ 40 mm (pouch) + headroom
    },
    "v60-cafec-02": {
        "display": "CAFEC cone cup 4 (V60-02 size, tabless)",
        "folder": "v60",
        "side": 127.0,      # retail dims ~121 x 127 mm
        "angle": 90.0,
        "tab_extra": 0.0,
        "depth": 54.0,      # 100-pack free stack ≈ 50 mm (pouch) + headroom
    },
    # Kalita flat-bottom fan papers (TrapezoidCase). width x height x bottom
    # is a reference sheet (sets the box angle); the box is sized so every
    # listed sheet fits — reference + "variants", some larger in one
    # dimension — and verify.py seats each one. Depth 58: never squeezed —
    # FP bags 45/50 mm, NK 40/45, Kalita's boxed 100-sheet line ≈ 58 mm
    # inside (with the flat lids' 2.5 mm lip: 55.5 mm along the walls).
    "kalita-101": {
        "display": "Kalita 101 (FP101 / NK101)",
        "folder": "kalita",
        "shape": "trapezoid",
        "width": 138.0,     # top chord: retail 13.4-13.5 cm
        "height": 80.0,     # centre height: retail 8 cm (40P box caps ~79)
        "bottom": 53.0,     # crimped bottom edge: retail 50 (one source)
        "variants": ((134.0, 80.0, 45.0), (134.0, 80.0, 50.0),
                     (134.0, 80.0, 55.0)),
        "tab_extra": 0.0,
        "depth": 58.0,
    },
    "kalita-102": {
        "display": "Kalita 102 (FP102 / NK102)",
        "folder": "kalita",
        "shape": "trapezoid",
        "width": 165.0,     # retail 16 x 10 cm (Askul 102-size 16.5 x 10.2)
        "height": 105.0,    # Kalita sheets 100-103; 105 = Melitta 1x2's height,
                            # so that sheet keeps the full RADIAL_SLACK too
        "bottom": 53.0,     # retail 50, Toyo 102 53; render trace ~45
        "variants": ((160.0, 100.0, 44.0), (160.0, 100.0, 50.0),
                     (160.0, 105.0, 47.0),    # Melitta 1x2
                     (165.0, 103.0, 54.0)),   # Brooks 102 (1 mm wider bottom)
        "tab_extra": 0.0,
        "depth": 58.0,
    },
    "kalita-103": {
        "display": "Kalita 103 (FP103 / NK103)",
        "folder": "kalita",
        "shape": "trapezoid",
        "width": 195.0,     # retail 19.3 x 12.7 cm; Kalita boxes cap ~195
        "height": 130.0,
        "bottom": 56.0,     # no Kalita figure (Toyo 103: 53)
        "variants": ((193.0, 127.0, 47.0), (193.0, 127.0, 53.0),
                     (200.0, 130.0, 56.0)),   # last: generic 103-size
        "tab_extra": 0.0,
        "depth": 58.0,
    },
    # One box for two papers (see ComboCase). References the entries above
    # instead of repeating their numbers, so it follows any re-measurement.
    # Holds a full 100-pack of either paper, or part packs of both with a
    # divider (loose plate or table) between them.
    "combo": {
        "display": "Combo — CAFEC Deep 27 + V60 01",
        "folder": "combo",
        "combines": ("deep27", "v60-01"),
        "engrave_rot": 0.0,  # baseline along the long shared wall: upright
                             # when that flat wall faces the reader
    },
    # AeroPress paper discs — round boxes (RoundCase). One sheet is ~0.12 mm
    # (stacks measure 0.111-0.129 mm/sheet); the depth holds the WORST pack
    # height plus the flat lids' 2.5 mm alignment lip, which in a close round
    # bore comes down over the disc edges, plus margin (never squeezed).
    "aeropress": {
        "display": "AeroPress Standard (Original / Clear / Go / Premium)",
        "folder": "aeropress",
        "shape": "round",
        "diameter": 65.0,   # spec Ø63.5 (2.5"); listings go up to Ø65. Also
                            # Premium / Go Plus, and the Ø61-63.5 metal discs
        "depth": 55.0,      # 350-pack: 44 mm typical, 50 worst case
        "stack_h": 44.0,    # preview ghost: a typical 350-pack
    },
    "aeropress-xl": {
        "display": "AeroPress XL",
        "folder": "aeropress",
        "shape": "round",
        "diameter": 75.0,   # spec Ø73.7 (2.9"), measured up to Ø74
        "depth": 35.0,      # 200-pack: 25 mm typical, 29 worst case
        "stack_h": 25.0,    # preview ghost: a typical 200-pack
    },
}

# --------------------------------------------------------------------------
# SHARED DESIGN PARAMETERS
# --------------------------------------------------------------------------

ANGLE_SLACK = 3.0        # extra wedge angle so papers never wedge tight
RADIAL_SLACK = 3.5       # extra length beyond the paper side
INNER_ROUND = 4.0        # fillet radius of the interior corners

# Shell thicknesses — "stable, not bulletproof" (print feedback 2026-07-20:
# 2.4 shells felt tank-like). 2.0 = 5 perimeters with a 0.4 nozzle / 10 layers
# at 0.2 mm; ~58 % of the 2.4 bending stiffness (t³), still rigid for a paper
# box. CLI-overridable (--wall-t / --floor-t) for personal taste.
WALL_T = 2.0             # base wall thickness
FLOOR_T = 2.0            # base floor thickness
DEPTH = 42.0             # default interior depth (fits 100 smooth Hario papers,
                         # measured stack ~32 mm); creped papers override per-paper

# Telescoping designs (friction / magnet-skirt)
SKIRT_T = 1.6            # lid skirt wall thickness — 4 perimeters; a closed
                         # hoop ring, and braced by the base wall when closed,
                         # so it can run thinner than the free-standing walls
PLINTH = 3.0             # base rim left exposed below the closed lid (grip)
LID_T_FRICTION = 2.0     # lid top plate thickness, friction design
LID_T_MAGNET = 4.6       # magnet-lid plate at the rim & pockets — can't shrink:
                         # 3.2 mm pocket + 1.4 mm roof (7 layers); any thinner
                         # and the magnet pairs touch (hard clack, chip risk)
LID_CORE_T = 2.0         # magnet lids are recessed from below to this over the
                         # cavity (= LID_T_FRICTION; engraving leaves 1.4) —
                         # sheds ~45 % lid weight; full thickness stays over
                         # the rim (dust contact), lip root and pockets
# Printer-fit tolerances — CLI-overridable (apply_tolerance_args), listed in
# the previews' "Tolerances" row and in README -> Printing
CLEAR_FRICTION = 0.28    # lid-to-base clearance per side, friction design
CLEAR_MAGNET = 0.50      # loose glide fit — the magnets do the holding

# Finger scoop cut into the wide-end wall (friction / magnet-skirt bases;
# covered by the skirt when closed, so it stays dust-proof).
# SCOOP_ABOVE_FLOOR positions the friction scoop only: the magnet-skirt
# scoop bottom is derived as back-notch top + ARC_NOTCH_GAP (see below), so
# that scoop is shorter and always clears the notch.
SCOOP_W = 36.0
SCOOP_R = 14.0           # corner radius of the scoop
SCOOP_ABOVE_FLOOR = 8.0  # scoop bottom height above the interior floor

# Grip notches at the bottom edge of the telescoping lids
NOTCH_W = 22.0
NOTCH_H = 10.0
NOTCH_R = 6.0
NOTCH_FRAC = 0.36        # notch position along the straight sides, × R_INT
# Third notch mid-arc, magnet-skirt lid only (use feedback 2026-08-01: with
# four magnet pairs — 25-30 N, right at weak-user pinch strength — the two
# side pinches aren't enough to break the lid free): a thumb push-up ledge at
# the back. Fingers pinch the side notches, the thumb pushes this edge up,
# peeling the arc magnet pair first ("push until it clicks free, then lift" —
# the 0.50 glide fit binds after ~2° of tilt, already enough to break a Ø6x3
# pair). Sized from ANSUR thumb breadth (18.6 F/P5 – 26.4 M/P95): the thumb
# bears on the FLAT ledge W − 2r, so the radius stays smaller than NOTCH_R —
# 24/r4 = 16 mm flat, more than either 22/r6 or 26/r6 would give. The scoop
# behind is a through-cut, so notch and scoop must never overlap (dust
# slit): on this design the scoop bottom is DERIVED as notch top +
# ARC_NOTCH_GAP — the scoop rides above the notch by construction (preview
# feedback 2026-08-01: v1 instead squeezed the notch under a full-depth
# scoop, leaving a cramped 6 mm window and a 1 mm sliver between the two
# openings).
ARC_NOTCH_W = 24.0
ARC_NOTCH_H = 10.0       # window height above the plinth (= NOTCH_H)
ARC_NOTCH_R = 4.0        # smaller corner radius = longer flat thumb ledge
ARC_NOTCH_GAP = 6.0      # solid wall band between notch top and scoop bottom
ARC_NOTCH_CHAMFER = 1.0  # ceiling ramp: outer-face edge sits this far below
                         # the top, rising to it at the inner face — the
                         # thumb meets a ramp, not a 1.6 mm knife edge

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
CORNER_BLEND_R = 6.0     # smoothing radius blending bulges / the bay into walls
PRY_W = 20.0             # pry slot under the lid edge, mid-arc
PRY_H = 2.2

# magnet-pedestal design: magnet-flat shell + easy paper picking. A finger bay
# bulges outward mid-arc (full height, rim stays closed -> still dust-proof)
# and the pedestal the papers rest on stops MOAT_W (+ tab_extra) short of the
# arc wall — every brand's paper edge overhangs the moat, so one sheet can be
# pinched from below via the bay, down to the very last paper. The interior is
# deepened by PEDESTAL_H so the 100-pack keeps full headroom (never squeezed).
BAY_W = 34.0             # bay opening width along the wide-end arc
BAY_D = 12.0             # bay depth outward beyond the interior wall
PEDESTAL_H = 8.0         # pedestal height — enough to get a fingertip under
MOAT_W = 15.0            # pedestal setback from the arc wall (+ tab_extra)
# Two 45° chamfers soften the pedestal's abrupt section changes, which
# telegraph shrink witness lines through the shell (print feedback; researched
# sizing: such transitions need 1.5-3 mm — sub-mm only fixes elephant-foot —
# and they fade rather than vanish, an FDM limit). Both are CLI flags; 0 = off.
PEDESTAL_CHAMFER_BOTTOM = 2.0  # at the pedestal's foot, in the moat: softens
                               # the line on the base's UNDERSIDE. Papers rest
                               # on the pedestal top 8 mm above — never touched.
PEDESTAL_CHAMFER_WALL = 1.2    # cove where the pedestal TOP meets the side
                               # walls/apex: softens the ring where the slab's
                               # solid section ends + kills the sharp interior
                               # corner. Kept small on purpose: papers can sit
                               # within ~1 mm of the walls near the tip, so a
                               # bigger cove would prop their edges up.

# Combo cases (PAPERS "combines"): a loose divider plate lets both papers
# share the cavity. Recommended order: the SHORT/WIDE paper's stack on the
# floor, the plate, the long/narrow paper on top. Measured statics (55 g/m2
# x 2 plies, 31 g plate, worst case over the push range): that order keeps
# +9 / +6 / +3 mm of tipping margin at 25 / 50 / 100 top sheets over genuine
# 107 mm V60 sheets, while the reverse order tips from about half a pack
# (+3 / -0.5 / -3 mm). Undersized lower sheets (R ~ 100 mm clones, CAFEC
# cup 1) make the recommended order marginal too (-1 mm at 50, -4 mm at 100)
# — sliding the lower stack outward, toward the horn, restores the margin.
# The finger hole sits in the zone only the wide paper covers, so it stays
# reachable under the top stack. Thickness and wall gap are CLI flags
# (--divider-t, --divider-clear).
DIVIDER_T = 1.6           # plate thickness (8 layers) — stiff enough to lift
DIVIDER_CLEAR = 1.0       # gap to the cavity walls, per side (drops in freely)
DIVIDER_HOLE_D = 22.0     # finger hole diameter — two holes, one in each
                          # paper's own zone, so whichever stack lies on top
                          # one hole stays uncovered ("pull from either side")
DIVIDER_HOLE_FRAC = 0.62  # wide-paper hole centre, × its R_INT, mid its arc;
                          # the other sits mid-horn on the long paper's bisector
DIVIDER_HOLE_LAND = 8.0   # minimum plate material around a hole
# Table divider — the alternative to the loose plate: the same top on legs,
# so the upper stack never rests on the lower one. The order is forced by
# where legs can stand: the long/narrow paper lies on the floor (its sweep
# wedge stays free of posts), the short/wide paper on the table. Round posts
# stand in the zone only the wide paper covers, two arc-segment feet hug the
# far arc beyond the long paper's edge. The pedestal design gets its own
# table: its far feet reach down into the moat (PEDESTAL_H longer).
DIVIDER_LEG_H = 22.0      # clear height under the table top (--divider-leg-h)
DIVIDER_POST_D = 8.0      # round post diameter
DIVIDER_POST_GAP = 2.0    # posts stay this far outside the long paper's wedge
DIVIDER_POST_INSET = 3.0  # pedestal: post inset from the plinth edge (clears
                          # the wall cove, never overhangs the moat)
DIVIDER_FOOT_T = 3.2      # far-arc feet: radial thickness (8 perimeters)
DIVIDER_FOOT_W = 16.0     # far-arc feet: tangential length
DIVIDER_FAR_PLAY = 3.0    # radial play the far feet must leave the long paper

# Engraving (lid top face). Upright when the tip of the wedge points at you
# (per-paper "engrave_rot" overrides the direction).
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
PREVIEW_COMBO_STACK_H = (16.0, 20.0)  # combo: stack under / on the divider

QS = 24  # quad segments for shapely buffers (arc smoothness)
DESIGNS = ("friction", "magnet-skirt", "magnet-flat", "magnet-pedestal")

# --------------------------------------------------------------------------
# STATELESS MESH HELPERS
# --------------------------------------------------------------------------


def sector_poly(angle_deg, radius, steps_per_deg=2.0):
    """Pie-slice polygon, apex at origin, opening along +X, symmetric in Y."""
    n = max(8, int(angle_deg * steps_per_deg))
    ang = np.radians(np.linspace(-angle_deg / 2.0, angle_deg / 2.0, n + 1))
    pts = [(0.0, 0.0)] + [(radius * math.cos(a), radius * math.sin(a)) for a in ang]
    return Polygon(pts)


def polar(r, deg):
    a = math.radians(deg)
    return (r * math.cos(a), r * math.sin(a))


def paper_outline(side, angle, tab_extra, apex_tip_x):
    """Flat paper footprint on the +X bisector (preview ghost), tip nudged
    just clear of the filleted apex."""
    poly = sector_poly(angle, side)
    if tab_extra > 0.0:
        poly = poly.union(Point(side - 2.0, 0.0).buffer(7.5, quad_segs=QS))
    return affinity.translate(poly, xoff=apex_tip_x + 1.5)


def prism(poly, z0, z1):
    m = trimesh.creation.extrude_polygon(poly, z1 - z0)
    m.apply_translation([0.0, 0.0, z0])
    return m


def poly_parts(geom):
    """Polygons of a (possibly Multi-) polygon, skipping empties."""
    parts = list(geom.geoms) if hasattr(geom, "geoms") else [geom]
    return [p for p in parts if p.geom_type == "Polygon" and not p.is_empty]


def diff(solid, *cutters):
    return trimesh.boolean.difference([solid, *cutters], check_volume=False)


def clean_union(mesh, tol=1e-5):
    """Manifold.simplify() pass over a unioned mesh: collapses the sub-µm
    slivers that near-coincident faces leave behind (the pedestal plinth
    unioned against cavity walls whose corner fillets are discretised
    differently) — in memory they are zero-volume shells, but in a float32
    STL their vertices merge into non-manifold edges. Moves no surface by
    more than tol. Used by the newer shapes only: running it on the legacy
    papers would rewrite their published STL bytes."""
    import manifold3d
    m = manifold3d.Manifold(manifold3d.Mesh(
        vert_properties=np.asarray(mesh.vertices, dtype=np.float32),
        tri_verts=np.asarray(mesh.faces, dtype=np.uint32))).simplify(tol)
    out = m.to_mesh()
    return trimesh.Trimesh(vertices=out.vert_properties[:, :3],
                           faces=out.tri_verts, process=True)


def slot_cutter(width, z0, z1, corner_r, centre_xy, normal_deg, span):
    """Rounded-corner slot prism.

    The profile lives in the (tangent, z) plane and is extruded `span` mm
    along the horizontal outward normal, centred on `centre_xy`.
    """
    # a corner_r >= half the profile's short side would erode the box to an
    # empty polygon and surface as an opaque trimesh error far from the cause
    # (hit when --floor-t overrides shrank the arc notch profile): clamp it
    corner_r = min(corner_r, width / 2.0 - 0.25, (z1 - z0) / 2.0 - 0.25)
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


class ArcFrame:
    """Where the mid-arc grips go (scoop, back notch, pry slot, finger bay):
    an arc wall of radius r whose bisector points along deg. xy(r) is the
    point on that bisector at radius r; tangent = up x outward normal."""

    def __init__(self, r, deg):
        self.r = r
        self.deg = deg

    def xy(self, r):
        return polar(r, self.deg)

    @property
    def tangent(self):
        a = math.radians(self.deg)
        return (-math.sin(a), math.cos(a), 0.0)


class BisectorFrame(ArcFrame):
    """A plain wedge's arc frame, straight along +X — spelled out in exact
    literals instead of cos/sin of 0 (keeps published STLs bit-identical)."""

    tangent = (0.0, 1.0, 0.0)

    def __init__(self, r):
        super().__init__(r, 0.0)

    def xy(self, r):
        return (r, 0.0)


# --------------------------------------------------------------------------
# CASE — all per-paper geometry, built in "closed box" world coordinates
# (wedge apex at the origin, opening along +X, z=0 at the table)
# --------------------------------------------------------------------------


class Case:
    extras = ()              # extra printable parts (see ComboCase)

    def __init__(self, slug):
        self.slug = slug
        self.cfg = PAPERS[slug]
        self._derive_paper_geometry()
        self.base_h = FLOOR_T + self.depth
        self.engrave_rot = self.cfg.get("engrave_rot", -90)
        self._derive_outlines()

    def _derive_paper_geometry(self):
        """Paper -> r_int, depth, interior outline and engraving centre (the
        hook ComboCase replaces; everything else follows from these)."""
        cfg = self.cfg
        self.side = cfg["side"]
        self.angle = cfg["angle"]
        self.int_angle = self.angle + ANGLE_SLACK
        self.half = self.int_angle / 2.0
        # after filleting, the interior apex tip sits this far from the origin
        self.apex_tip_x = INNER_ROUND * (1.0 / math.sin(math.radians(self.half)) - 1.0)
        self.r_int = self.side + self.apex_tip_x + RADIAL_SLACK + cfg["tab_extra"]
        self.depth = cfg.get("depth", DEPTH)
        self.engrave_x = ENGRAVE_POS_FRAC * self.r_int
        self.engrave_xy = (self.engrave_x, 0.0)
        # arc walls that carry a scoop (+ the magnet-skirt back notch); the
        # first one also hosts the flat lids' pry slot. r_int is its radius.
        self.grip_arcs = [BisectorFrame(self.r_int)]

        self.interior = (
            sector_poly(self.int_angle, self.r_int)
            .buffer(-INNER_ROUND, quad_segs=QS)
            .buffer(INNER_ROUND, quad_segs=QS)
        )

    def _derive_outlines(self):
        """Everything that follows from self.interior + the magnet layouts."""
        self.ext_plain = self.interior.buffer(WALL_T, quad_segs=QS)

        self.magnets_skirt = self._skirt_magnet_centres()
        self.magnets_flat = self._flat_magnet_centres()

        # lobes get the same closing as the flat-lid corner bulges: the concave
        # cusps where a raw circle meets the wall are filled with smooth
        # gussets (print feedback: unblended lobes felt like pipes glued on)
        self.ext_skirt = (
            unary_union(
                [self.ext_plain]
                + [Point(c).buffer(LOBE_R, quad_segs=QS)
                   for c in self.magnets_skirt]
            )
            .buffer(CORNER_BLEND_R, quad_segs=QS)
            .buffer(-CORNER_BLEND_R, quad_segs=QS)
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

        # magnet-pedestal: the interior gains the outward finger bay mid-arc
        # (the wall follows at constant thickness, so the rim stays closed) and
        # the pedestal floor stops MOAT_W + tab_extra short of the arc wall,
        # guaranteeing the same paper-edge overhang for tabbed and tabless brands
        self.base_h_ped = self.base_h + PEDESTAL_H
        ped = self.interior
        for bay in self._bays():
            ped = ped.union(bay)
        self.interior_ped = (
            ped
            .buffer(CORNER_BLEND_R, quad_segs=QS)
            .buffer(-CORNER_BLEND_R, quad_segs=QS)
        )
        self.ext_ped = (
            unary_union(
                [self.interior_ped.buffer(WALL_T, quad_segs=QS)]
                + [Point(c).buffer(POCKET_D / 2.0 + 1.6, quad_segs=QS)
                   for c in self.magnets_flat]
            )
            .buffer(CORNER_BLEND_R, quad_segs=QS)
            .buffer(-CORNER_BLEND_R, quad_segs=QS)
        )
        self.plinth = self._plinth()

    def _bay(self, r_arc):
        """Finger-bay footprint straddling an arc wall of radius r_arc, on +X."""
        return (
            shp_box(r_arc - 6.0, -BAY_W / 2.0,
                    r_arc + BAY_D, BAY_W / 2.0)
            .buffer(-CORNER_BLEND_R, quad_segs=QS)
            .buffer(CORNER_BLEND_R, quad_segs=QS)
        )

    def _bays(self):
        return [self._bay(self.r_int)]

    def _plinth(self):
        return (
            self.interior.intersection(
                Point(0.0, 0.0).buffer(
                    self.r_int - MOAT_W - self.cfg.get("tab_extra", 0.0),
                    quad_segs=QS))
            .buffer(-2.0, quad_segs=QS)
            .buffer(2.0, quad_segs=QS)
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

    def _step_out(self, start_xy, dir_deg, clearance, max_steps=10000):
        """March from start_xy along dir_deg until clear of the interior.
        A heading that never leaves the interior (wrong sign, start on the
        far side) raises after max_steps (1 m) instead of hanging."""
        d = math.radians(dir_deg)
        v = np.array([math.cos(d), math.sin(d)])
        p = np.array(start_xy, dtype=float)
        steps = 0
        while Point(p).distance(self.interior) < clearance:
            if steps >= max_steps:
                raise ValueError(
                    f"{self.slug}: _step_out from ({start_xy[0]:.2f}, "
                    f"{start_xy[1]:.2f}) heading {dir_deg:g}° never clears "
                    f"the interior by {clearance:g} mm in {max_steps} steps")
            p += v * 0.1
            steps += 1
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

    # Per-shape sizing hooks. PROPERTIES on purpose, read at call time:
    # apply_printer_args() rebinds the module globals after import, so a class
    # attribute would freeze the defaults. Subclasses override them (e.g. a
    # small round box: narrower scoop / engraving).

    @property
    def arc_notch_top(self):
        return PLINTH + ARC_NOTCH_H

    @property
    def scoop_w(self):
        """Finger-scoop width at every grip arc."""
        return SCOOP_W

    @property
    def friction_scoop_bottom(self):
        """Friction-design scoop bottom (z); the magnet-skirt one derives
        from the back notch instead (build_base)."""
        return FLOOR_T + SCOOP_ABOVE_FLOOR

    @property
    def engrave_width(self):
        """Total width of the engraved text block."""
        return ENGRAVE_WIDTH

    @property
    def pedestal_cove(self):
        """Width (= height) of the 45° wall cove on the pedestal top."""
        return PEDESTAL_CHAMFER_WALL

    def scoop_cutters(self, bottom):
        return [slot_cutter(self.scoop_w, bottom, self.base_h + 40.0, SCOOP_R,
                            arc.xy(arc.r), arc.deg, 60.0)
                for arc in self.grip_arcs]

    def _side_notch_frames(self):
        """(centre on the interior wall face, outward normal deg) per notch."""
        out = []
        notch_r = NOTCH_FRAC * self.r_int
        for side in (+1, -1):
            edge = math.radians(side * self.half)
            nrm_deg = math.degrees(edge) + side * 90.0
            px = notch_r * math.cos(edge)
            py = notch_r * math.sin(edge)
            out.append(((px, py), nrm_deg))
        return out

    def notch_cutters(self, arc_notch=False):
        """Grip notches at the bottom edge of the telescoping lids."""
        out = [
            slot_cutter(NOTCH_W, PLINTH - 6.0, PLINTH + NOTCH_H, NOTCH_R,
                        xy, nrm_deg, 24.0)
            for xy, nrm_deg in self._side_notch_frames()]
        if arc_notch:
            # mid-arc thumb ledge — magnet-skirt only, deliberately: the
            # friction lid has no magnet pairs to peel and opens by
            # pinch-and-wiggle from its two side notches. Two cutters: a
            # straight slot to z_top - chamfer, then a tilted copy whose top
            # face ramps from z_top at the skirt's inner face down-and-out
            # (in the lid's print orientation the ramp faces up — no
            # overhang). The scoop bottom sits ARC_NOTCH_GAP above z_top by
            # construction (build_base), so the ramp's ~0.4 mm flank rise
            # from pivoting about the mid-arc chord never nears the void.
            # Guard: a too-wide --arc-notch-w would open the window straight
            # into the arc-lobe magnet channels while every mesh stays
            # watertight, so nothing downstream would catch it.
            chan = self.ext_skirt.buffer(CLEAR_MAGNET, quad_segs=QS).difference(
                self.ext_plain.buffer(CLEAR_MAGNET, quad_segs=QS))
            z_top = self.arc_notch_top
            for arc in self.grip_arcs:
                fp = affinity.rotate(
                    shp_box(arc.r - 15.0, -ARC_NOTCH_W / 2.0,
                            arc.r + 15.0, ARC_NOTCH_W / 2.0),
                    arc.deg, origin=(0, 0))
                clr = fp.distance(chan)
                if clr < 1.5:
                    raise ValueError(
                        f"{self.slug}: --arc-notch-w {ARC_NOTCH_W:g} leaves "
                        f"only {clr:.2f} mm to the arc magnet channel "
                        "(need >= 1.5) — narrow the back notch")
                out.append(
                    slot_cutter(ARC_NOTCH_W, PLINTH - 6.0,
                                z_top - ARC_NOTCH_CHAMFER, ARC_NOTCH_R,
                                arc.xy(arc.r), arc.deg, 30.0))
                ramp = slot_cutter(ARC_NOTCH_W, PLINTH - 6.0, z_top,
                                   ARC_NOTCH_R, arc.xy(arc.r), arc.deg, 30.0)
                ramp.apply_transform(trimesh.transformations.rotation_matrix(
                    math.atan2(ARC_NOTCH_CHAMFER, SKIRT_T), arc.tangent,
                    [*arc.xy(arc.r + WALL_T + CLEAR_MAGNET), z_top]))
                out.append(ramp)
        return out

    def lid_notch_cutters(self, design):
        """Grip-notch cutters of one telescoping design's lid (build_lid):
        the side notches, plus the back thumb notch on magnet-skirt. A
        subclass may return fewer (e.g. a twist-off round friction lid: [])."""
        return self.notch_cutters(arc_notch=(design == "magnet-skirt"))

    def pry_cutter(self, cx, top):
        """Shallow slot under a flat lid's edge, mid-arc: thumbnail pry point
        (the lid's lip still backs it, so no dust path opens up)."""
        arc = self.grip_arcs[0]
        return slot_cutter(PRY_W, top - PRY_H, top + 5.0, 2.0,
                           arc.xy(cx), arc.deg, 30.0)

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
        s = self.engrave_width / (maxx - minx)
        geom = affinity.scale(geom, xfact=s, yfact=s, origin=(0, 0))
        minx, miny, maxx, maxy = geom.bounds
        geom = affinity.translate(geom, -(minx + maxx) / 2.0, -(miny + maxy) / 2.0)
        # local (reading, up) -> world: by default (engrave_rot -90) the text
        # up-vector = +X, so the text is upright when the apex (wedge tip)
        # points toward the reader
        geom = affinity.rotate(geom, self.engrave_rot, origin=(0, 0))
        return affinity.translate(geom, *self.engrave_xy)

    def engrave_cutters(self, plate_top):
        geom = self.text_geometry()
        parts = list(geom.geoms) if hasattr(geom, "geoms") else [geom]
        return [prism(g, plate_top - ENGRAVE_DEPTH, plate_top + 1.0)
                for g in parts if g.geom_type == "Polygon" and not g.is_empty]

    # -- parts ---------------------------------------------------------------

    def build_base(self, design):
        if design == "friction":
            solid = prism(self.ext_plain, 0.0, self.base_h)
            cutters = self.scoop_cutters(self.friction_scoop_bottom)
        elif design == "magnet-skirt":
            solid = prism(self.ext_skirt, 0.0, self.base_h)
            # shorter scoop, riding above the back notch: a solid wall band
            # of ARC_NOTCH_GAP separates the two openings
            cutters = self.scoop_cutters(
                self.arc_notch_top + ARC_NOTCH_GAP) + pocket_cutters(
                self.magnets_skirt, self.base_h - POCKET_DEPTH, self.base_h + 1.0)
        elif design == "magnet-flat":  # no through-scoop (the whole top opens)
            solid = prism(self.ext_flat, 0.0, self.base_h)
            cutters = [self.pry_cutter(self.r_int, self.base_h)] + pocket_cutters(
                self.magnets_flat, self.base_h - POCKET_DEPTH, self.base_h + 1.0)
        else:  # magnet-pedestal: papers picked via the finger bay + moat
            solid = prism(self.ext_ped, 0.0, self.base_h_ped)
            cutters = [self.pry_cutter(self.r_int + BAY_D, self.base_h_ped)]
            cutters += pocket_cutters(self.magnets_flat,
                                      self.base_h_ped - POCKET_DEPTH,
                                      self.base_h_ped + 1.0)
            cutters.append(prism(self.interior_ped, FLOOR_T,
                                 self.base_h_ped + 1.0))
            tray = diff(solid, *cutters)
            # pedestal added after the cavity cut; the moat keeps floor level
            parts = [tray, prism(self.plinth, FLOOR_T - 1.0,
                                 FLOOR_T + PEDESTAL_H)]
            # Both chamfers are 0.2 mm staircases (what the slicer would emit
            # for a smooth 45° face anyway), so printability is untouched.
            if PEDESTAL_CHAMFER_BOTTOM > 0.0:
                # foot chamfer in the moat: the floor->plinth section change
                # becomes gradual instead of a one-layer step. Clipped to the
                # cavity: along the straight sides the plinth boundary
                # coincides with the interior walls, and an unclipped buffer
                # would poke through them (visible outside) once > WALL_T.
                c = PEDESTAL_CHAMFER_BOTTOM
                n = max(1, math.ceil(c / 0.2))
                h = c / n
                for k in range(n):
                    ring = (self.plinth.buffer(c - k * h, quad_segs=QS)
                            .intersection(self.interior_ped))
                    parts += [prism(p, FLOOR_T - 0.5, FLOOR_T + (k + 1) * h)
                              for p in poly_parts(ring)]
            if self.pedestal_cove > 0.0:
                # cove where the pedestal top meets the side walls/apex —
                # smooths the ring where the slab's solid section ends and
                # opens up the sharp interior corner. Clipped to the plinth
                # footprint so nothing overhangs the moat/bay unsupported.
                s = self.pedestal_cove
                n = max(1, math.ceil(s / 0.2))
                h = s / n
                ped_top = FLOOR_T + PEDESTAL_H
                for k in range(n):
                    band = (self.interior_ped.difference(
                                self.interior_ped.buffer(-(s - k * h),
                                                         quad_segs=QS))
                            .intersection(self.plinth))
                    parts += [prism(p, ped_top - 0.5, ped_top + (k + 1) * h)
                              for p in poly_parts(band)]
            return trimesh.boolean.union(parts, check_volume=False)
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

        if design in ("magnet-flat", "magnet-pedestal"):
            outline, cavity, top = (
                (self.ext_flat, self.interior, self.base_h)
                if design == "magnet-flat"
                else (self.ext_ped, self.interior_ped, self.base_h_ped))
            plate = prism(outline, top, top + plate_t)
            lip = prism(
                cavity.buffer(-LIP_CLEAR, quad_segs=QS).difference(
                    cavity.buffer(-(LIP_CLEAR + LIP_T), quad_segs=QS)),
                top - LIP_H, top + 0.5)
            solid = trimesh.boolean.union([plate, lip], check_volume=False)
            cutters = pocket_cutters(self.magnets_flat, top - 1.0,
                                     top + POCKET_DEPTH)
            # lightening recess: thin the underside to LID_CORE_T over the
            # cavity; rim contact, lip root and magnet pockets stay full
            core = cavity.buffer(-(LIP_CLEAR + LIP_T + 2.0), quad_segs=QS)
            cutters.append(prism(core, top - 1.0, top + plate_t - LID_CORE_T))
        else:
            top = self.base_h
            outer = inner.buffer(SKIRT_T, quad_segs=QS)
            solid = prism(outer, PLINTH, top + plate_t)
            cutters = ([prism(inner, PLINTH - 1.0, top)]
                       + self.lid_notch_cutters(design))
            if design == "magnet-skirt":
                # pockets rise into the lid plate from its underside
                cutters += pocket_cutters(self.magnets_skirt, top - 1.0,
                                          top + POCKET_DEPTH)
                # same lightening recess as the flat lids (plate is LID_T_MAGNET)
                core = self.interior.buffer(-2.0, quad_segs=QS)
                cutters.append(prism(core, top - 1.0,
                                     top + plate_t - LID_CORE_T))
        if engraved:
            cutters += self.engrave_cutters(top + plate_t)
        return diff(solid, *cutters)

    def build_extra(self, name):
        """Extra part listed in `extras`, in print orientation."""
        raise ValueError(f"{self.slug}: no extra part {name!r}")

    def extras_for(self, design):
        """The extras that go with one design (ComboCase: its dividers)."""
        return list(self.extras)

    # -- shared guards (a subclass's _check() calls the ones that apply) ------
    # Each catches a failure that would otherwise pass SILENTLY — the meshes
    # stay watertight while a pocket opens into the cavity, a notch holes the
    # lid plate or the text runs off the lid. They only read the outlines, so
    # calling them never changes a generated byte. The plain wedge does not
    # call them (its layout predates them and is pinned by the hash gate).

    def _fail(self, msg):
        raise ValueError(f"{self.slug}: {msg}")

    @staticmethod
    def _is_simple(poly):
        """One valid polygon without holes."""
        return (poly.geom_type == "Polygon" and poly.is_valid
                and not poly.interiors)

    def _guard_pockets(self, min_skin=0.4):
        """Every magnet pocket lies inside its design's exterior with at least
        min_skin (0.4 = one perimeter) of wall to the cavity and outside."""
        for design, centres, ext, cavity in (
                ("magnet-skirt", self.magnets_skirt, self.ext_skirt,
                 self.interior),
                ("magnet-flat", self.magnets_flat, self.ext_flat,
                 self.interior),
                ("magnet-pedestal", self.magnets_flat, self.ext_ped,
                 self.interior_ped)):
            if design not in self.designs:  # a PAPERS "designs" subset
                continue
            for c in centres:
                pocket = Point(c).buffer(POCKET_D / 2.0, quad_segs=QS)
                if not ext.contains(pocket):
                    self._fail(f"{design} pocket at ({c[0]:.1f}, {c[1]:.1f}) "
                               "breaks out of the wall")
                skin = min(pocket.distance(cavity),
                           pocket.distance(ext.boundary))
                if skin < min_skin:  # less than one perimeter round the magnet
                    self._fail(f"{design} pocket at ({c[0]:.1f}, {c[1]:.1f}) "
                               f"leaves only {skin:.2f} mm of wall "
                               f"(need >= {min_skin:g})")

    def _guard_side_notches_straight(self, tol=0.05):
        """Every side-notch window sits on STRAIGHT wall, inside and out:
        clear of rounded corners, shoulders and any lobe blend."""
        for (px, py), nrm_deg in self._side_notch_frames():
            tx, ty = polar(1.0, nrm_deg + 90.0)
            ox, oy = polar(WALL_T, nrm_deg)
            for t in (-NOTCH_W / 2.0, 0.0, NOTCH_W / 2.0):
                q = (px + t * tx, py + t * ty)
                off = max(
                    Point(q).distance(self.interior.boundary),
                    Point(q[0] + ox, q[1] + oy).distance(
                        self.ext_skirt.boundary))
                if off > tol:
                    self._fail(f"grip notch at ({px:.1f}, {py:.1f}) is "
                               f"{off:.2f} mm off its straight wall")

    def _guard_grip_arcs_on_wall(self, tol=0.05):
        """Scoop / back-notch / bay windows sit on plain arc wall at every
        grip arc (no corner or shoulder within their half-width)."""
        for arc in self.grip_arcs:
            half_w = max(self.scoop_w, ARC_NOTCH_W, BAY_W) / 2.0 / arc.r
            for da in (-half_w, 0.0, half_w):
                q = polar(arc.r, arc.deg + math.degrees(da))
                off = Point(q).distance(self.interior.boundary)
                if off > tol:
                    self._fail(f"mid-arc grips at {arc.deg:.1f}° run "
                               f"{off:.2f} mm off their arc wall (corner or "
                               "shoulder too close)")

    def _guard_text_fits(self, margin=4.0):
        """The engraving's bounding box lies on the lid core (interior less
        margin) and clear of every magnet pocket."""
        text = shp_box(*self.text_geometry().bounds)
        if not text.within(self.interior.buffer(-margin, quad_segs=QS)):
            self._fail("engraving runs off the lid core")
        for c in self.magnets_skirt + self.magnets_flat:
            if text.distance(Point(c)) < POCKET_D / 2.0 + 2.0:
                self._fail("engraving collides with a magnet pocket")

    # -- preview-only ghosts --------------------------------------------------

    def paper_ghost(self, lift=0.0):
        """Ghost paper stack; `lift` raises it onto the pedestal design's floor."""
        poly = paper_outline(self.side, self.angle, self.cfg["tab_extra"],
                             self.apex_tip_x)
        return prism(poly, FLOOR_T + lift + 0.3,
                     FLOOR_T + lift + 0.3 + PREVIEW_STACK_H)

    # Preview "contents" scenes: name / label / ghost part names. One scene
    # shows as a plain on/off checkbox; ComboCase offers several to pick from.
    scenes = [{"name": "papers", "label": "Ghost paper stack",
               "parts": ["papers"]}]
    default_scene = "papers"

    def ghosts(self, design):
        """Preview-only ghost parts of one design (name / color / opacity /
        mesh); the scenes above pick which of them show."""
        lift = PEDESTAL_H if design == "magnet-pedestal" else 0.0
        return [{"name": "papers", "color": "#efe3c8", "opacity": 0.55,
                 "mesh": self.paper_ghost(lift)}]

    def magnet_ghosts(self, centres, top=None):
        top = self.base_h if top is None else top
        base_m, lid_m = [], []
        for cx, cy in centres:
            for bucket, z in ((base_m, top - POCKET_DEPTH + 0.1),
                              (lid_m, top + 0.1)):
                c = trimesh.creation.cylinder(radius=3.0, height=3.0, sections=48)
                c.apply_translation([cx, cy, z + 1.5])
                bucket.append(c)
        return trimesh.util.concatenate(base_m), trimesh.util.concatenate(lid_m)

    # -- wording (console, preview Dimensions panel, index card) -----------------

    @property
    def short_name(self):
        """Display name without the brand list: 'V60 size 01 (Hario / CAFEC)'
        -> 'V60 size 01'."""
        return self.cfg["display"].split(" (")[0]

    @property
    def paper_txt(self):
        return f"{self.side:.0f} mm side, {self.angle:.0f}° wedge"

    @property
    def interior_txt(self):
        return (f"{self.r_int - self.apex_tip_x:.0f} mm x "
                f"{self.int_angle:.0f}°")

    @property
    def geo_txt(self):
        tab_txt = (f"{self.cfg['tab_extra']:.0f} mm tab clearance"
                   if self.cfg["tab_extra"] else "no tab")
        return (f"{self.side:.0f} mm side · {self.angle:.0f}° wedge ·\n"
                f"       {tab_txt}")

    @property
    def grip_txt(self):
        """Preview "Grip" row (shown when the paper has magnet-skirt): the
        telescoping lids' notches — side notches on both, the back thumb
        notch on magnet-skirt."""
        return (f"side notches {NOTCH_W:.1f} x {NOTCH_H:.1f} mm; "
                f"skirt back notch {ARC_NOTCH_W:.1f} x "
                f"{ARC_NOTCH_H:.1f} mm, {ARC_NOTCH_GAP:.1f} mm band "
                f"to its scoop")

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
# SHAPE REGISTRY — PAPERS "shape" (default "wedge") -> Case class. make_case()
# dispatches on it; "combines" entries always build a ComboCase. A new shape
# class registers with ONE line right after its class:
#     CASE_CLASSES["<shape>"] = <ShapeCase>
# --------------------------------------------------------------------------

CASE_CLASSES = {"wedge": Case}


# --------------------------------------------------------------------------
# TRAPEZOID CASE — flat-bottom fan papers (PAPERS "shape": "trapezoid")
# --------------------------------------------------------------------------
# A fan paper folded flat is a truncated sector (see PAPERS "trapezoid"). The
# box keeps the wedge's frame — the paper's VIRTUAL apex at the origin,
# opening along +X, arc concentric with it — and just cuts the apex off with
# a flat bottom wall, so every mid-arc feature (scoop, back thumb notch, pry
# slot, finger bay, moat) and the corner-magnet stepping run unchanged.

TRAP_SIDE_CLEAR = 2.0    # pushed home, a sheet's bottom corners keep this gap
                         # (mm, square to the wall) to the side walls — the
                         # naive "bottom wall RADIAL_SLACK behind the sheet"
                         # left ~0 there and the stack would wedge in the
                         # corners. The angle slack widens it toward the arc.
TRAP_WALL_MARGIN = 2.0   # plain straight wall kept between a side-notch
                         # window and the bottom-corner fillet / the blend of
                         # the side magnet lobe (magnet-skirt)


def fan_solve(width, height, bottom):
    """Flat fan paper (top chord c, centre height h, bottom edge b) ->
    (angle_deg, R, d): full angle between the straight sides, top-arc radius
    and bottom-edge distance, both from the virtual apex.

    Solves c/(2 sin t) - b/(2 tan t) = h for the half angle t by bisection
    (fixed iteration count -> deterministic). The left side falls steadily
    from +inf to sqrt(c² - b²)/2 on (0, acos(b/c)); the narrow root there is
    the paper (a second, blunt root past acos(b/c) is not a fan sheet)."""
    c, h, b = float(width), float(height), float(bottom)
    if not 0.0 < b < c or h <= math.sqrt(c * c - b * b) / 2.0:
        raise ValueError(
            f"no flat fan sheet is {c:g} wide x {h:g} high with a {b:g} mm "
            f"bottom (need bottom < width and height > "
            f"{math.sqrt(max(c * c - b * b, 0.0)) / 2.0:.1f})")
    lo, hi = 1e-9, math.acos(b / c)
    for _ in range(200):
        t = 0.5 * (lo + hi)
        if (c - b * math.cos(t)) / (2.0 * math.sin(t)) > h:
            lo = t
        else:
            hi = t
    t = 0.5 * (lo + hi)
    return 2.0 * math.degrees(t), c / (2.0 * math.sin(t)), b / (2.0 * math.tan(t))


def fan_outline(angle_deg, radius, bottom_x, steps_per_deg=2.0):
    """Flat fan sheet, virtual apex at the origin, opening along +X: the
    sector clipped by its straight bottom edge at x = bottom_x."""
    return sector_poly(angle_deg, radius, steps_per_deg).intersection(
        shp_box(bottom_x, -radius, radius + 1.0, radius))


class TrapezoidCase(Case):
    """Flat-bottom fan papers (Kalita 101/102/103): a wedge box whose apex is
    cut off by a flat bottom wall the sheets' crimped bottom edge rests on.

    Interior = the reference sheet's angle + ANGLE_SLACK about the virtual
    apex, clipped at x_bottom and filleted INNER_ROUND, sized over EVERY
    registry sheet (reference + variants): x_bottom is set by the WIDEST
    bottom edge and the bottom-corner gap (TRAP_SIDE_CLEAR), not by a fixed
    slack behind the sheet — pushed home, each bottom edge rests on the
    flat bottom wall with its corners clear of the side walls and fillets;
    r_int leaves RADIAL_SLACK beyond the farthest pushed-home arc, and the
    pedestal plinth stops MOAT_W - RADIAL_SLACK short of the SHORTEST one.

    Grips: two side notches clamped onto the plain straight run of the side
    walls (never in a fillet); magnet-skirt 4 pairs (2 on the arc as on the
    wedge + 1 per side, beyond its notch); magnet-flat / pedestal 4 pairs,
    one per convex corner (both bottom corners + both arc corners). Never
    sets side / angle / apex_tip_x, so no wedge formula runs on it unnoticed.
    """

    def __init__(self, slug):
        super().__init__(slug)
        self._check()

    def _derive_paper_geometry(self):
        cfg = self.cfg
        # never side / angle (like the round case): a wedge formula reached
        # by mistake must crash instead of building junk
        stray = [k for k in ("side", "angle") if k in cfg]
        if stray:
            raise ValueError(
                f"{self.slug}: a trapezoid paper takes 'width' / 'height' / "
                "'bottom', not " + " / ".join(stray))
        # the REFERENCE sheet sets the box angle; the box is sized so that
        # every listed sheet (reference + variants) fits pushed home
        self.sheet = (cfg["width"], cfg["height"], cfg["bottom"])
        self.sheets = [self.sheet] + [tuple(v) for v in cfg.get("variants", ())]
        self.fans = []
        for c, hh, b in self.sheets:
            try:
                self.fans.append(fan_solve(c, hh, b))
            except ValueError as e:
                raise ValueError(f"{self.slug}: {e}") from None
        self.fan_angle, self.fan_r, self.fan_d = self.fans[0]
        self.int_angle = self.fan_angle + ANGLE_SLACK
        self.int_half = self.int_angle / 2.0
        h = math.radians(self.int_half)
        # the obtuse bottom corner's fillet runs this far along each wall;
        # every sheet's corner must land on the flat bottom wall before it
        self.fillet_run = INNER_ROUND * math.tan((math.pi / 2.0 - h) / 2.0)
        self.side_gap = max(TRAP_SIDE_CLEAR, self.fillet_run * math.cos(h))
        # the WIDEST bottom edge sets the bottom wall: its corners keep
        # side_gap square to the side walls, and the flat wall left between
        # them and the fillets is corner_run (every narrower sheet: more)
        self.bottom_max = max(b for _, _, b in self.sheets)
        self.x_bottom = ((self.bottom_max / 2.0 + self.side_gap / math.cos(h))
                         / math.tan(h))
        self.corner_run = self.side_gap / math.cos(h) - self.fillet_run
        # where the reference sheet's virtual apex sits pushed home (bottom
        # edge on the bottom wall) — the analogue of a wedge's apex_tip_x
        self.home_dx = self.x_bottom - self.fan_d
        # pushed home, each sheet's arc is concentric with its own virtual
        # apex at x_bottom - d: on the bisector it reaches x_bottom + h; its
        # point farthest from the box's apex is that bisector point while
        # the sheet's apex sits in front of the box's (else its arc corner)
        self.sheet_reach = [self.x_bottom + hh for _, hh, _ in self.sheets]
        far = []
        for angle, radius, d in self.fans:
            s = self.x_bottom - d
            if s >= 0.0:
                far.append(s + radius)
            else:
                far.append(math.sqrt(
                    s * s + 2.0 * s * radius * math.cos(math.radians(angle / 2.0))
                    + radius * radius))
        self.r_int = max(far) + RADIAL_SLACK + cfg.get("tab_extra", 0.0)
        # pedestal: the SHORTEST sheet's pushed-home arc edge still overhangs
        # the moat by MOAT_W - RADIAL_SLACK at the bay (cf. tab_extra
        # widening the moat on the V60 boxes) — the taller ones overhang more
        self.plinth_r = min(self.sheet_reach) + RADIAL_SLACK - MOAT_W
        self.depth = cfg.get("depth", DEPTH)
        self.grip_arcs = [BisectorFrame(self.r_int)]
        self.interior = (
            sector_poly(self.int_angle, self.r_int)
            .intersection(shp_box(self.x_bottom, -self.r_int,
                                  self.r_int + 1.0, self.r_int))
            .buffer(-INNER_ROUND, quad_segs=QS)
            .buffer(INNER_ROUND, quad_segs=QS)
        )
        self.engrave_xy = (self.interior.centroid.x, 0.0)

    # -- straight side walls -----------------------------------------------------

    def _side_frame(self, rho, side):
        """Point rho mm from the virtual apex along the +1 / -1 side wall's
        interior face, and that wall's outward normal (deg)."""
        return (polar(rho, side * self.int_half),
                side * (self.int_half + 90.0))

    @property
    def side_run(self):
        """(rho_lo, rho_hi): the plain straight part of each side wall,
        measured from the virtual apex — between the two corner fillets."""
        rho_b = self.x_bottom / math.cos(math.radians(self.int_half))
        return rho_b + self.fillet_run, self.r_int - INNER_ROUND

    @property
    def notch_rho(self):
        """Side-notch centre: NOTCH_FRAC as on the wedge, clamped so the
        window keeps TRAP_WALL_MARGIN of plain wall to both fillets."""
        lo, hi = self.side_run
        half = NOTCH_W / 2.0 + TRAP_WALL_MARGIN
        return min(max(NOTCH_FRAC * self.r_int, lo + half), hi - half)

    @property
    def lobe_reach(self):
        """How far a magnet lobe's blended footprint can run along the wall
        from its centre (lobe + the CORNER_BLEND_R closing — an upper
        bound)."""
        return LOBE_R + CORNER_BLEND_R

    @property
    def side_magnet_rho(self):
        """Side magnet: MAG_SIDE_FRAC as on the wedge, clamped beyond the
        notch window (TRAP_WALL_MARGIN of plain wall before the lobe blend)
        and short of the arc-corner fillet."""
        lo, hi = self.side_run
        return min(max(MAG_SIDE_FRAC * self.r_int,
                       self.notch_rho + NOTCH_W / 2.0 + TRAP_WALL_MARGIN
                       + self.lobe_reach),
                   hi - TRAP_WALL_MARGIN - self.lobe_reach)

    def _side_notch_frames(self):
        return [self._side_frame(self.notch_rho, side) for side in (+1, -1)]

    def _plinth(self):
        """Pedestal plinth: as the wedge's, but its radius comes from the
        SHORTEST registry sheet (plinth_r), so every sheet's pushed-home arc
        edge overhangs the moat by at least MOAT_W - RADIAL_SLACK."""
        return (
            self.interior.intersection(
                Point(0.0, 0.0).buffer(self.plinth_r, quad_segs=QS))
            .buffer(-2.0, quad_segs=QS)
            .buffer(2.0, quad_segs=QS)
        )

    def build_base(self, design):
        base = super().build_base(design)
        # the pedestal's union leaves zero-volume slivers at the bottom-
        # corner fillets that turn non-manifold in the float32 STL
        return clean_union(base) if design == "magnet-pedestal" else base

    def home_sheet(self, i, gap=0.0):
        """Registry sheet i (0 = reference) pushed home: centred on the
        bisector, its bottom edge `gap` mm off the bottom wall."""
        angle, radius, d = self.fans[i]
        return affinity.translate(fan_outline(angle, radius, d),
                                  xoff=self.x_bottom - d + gap)

    # -- magnet layouts ----------------------------------------------------------

    def _skirt_magnet_centres(self):
        """magnet-skirt: 2 on the arc (wedge angles) + 1 per straight side."""
        out = [polar(self.r_int + MAG_OFFSET, a) for a in MAG_ARC_ANGLES]
        for side in (+1, -1):
            (px, py), nrm = self._side_frame(self.side_magnet_rho, side)
            ox, oy = polar(MAG_OFFSET, nrm)
            out.append((px + ox, py + oy))
        return out

    def _flat_magnet_centres(self):
        """magnet-flat / pedestal: one pair per convex corner — both bottom
        corners, then both arc corners — stepped out along the bisector of
        the two outward normals that meet there."""
        clr = POCKET_D / 2.0 + 1.3
        y_b = self.x_bottom * math.tan(math.radians(self.int_half))
        out = [self._step_out((self.x_bottom, side * y_b),
                              side * (135.0 + self.int_half / 2.0), clr)
               for side in (+1, -1)]
        out += [self._step_out(polar(self.r_int, side * self.int_half),
                               side * (self.int_half + 45.0), clr)
                for side in (+1, -1)]
        return out

    # -- guards --------------------------------------------------------------------

    def _check(self):
        """Each of these would otherwise pass silently: the meshes stay
        watertight while a sheet wedges in a corner, a notch window bites
        into a fillet or a lobe, or a pocket opens into the scoop."""
        fail = self._fail
        if not self._is_simple(self.interior):
            fail("the interior is not one simple polygon")
        # EVERY registry sheet, pushed home (a hair off the bottom wall),
        # fits, and both its bottom corners land on the FLAT bottom wall —
        # measured on the interior polygon: the wall left between a corner
        # and the fillet must be >= corner_run (what the widest bottom keeps
        # by construction) - 0.05; a corner past the flat run sits on a
        # fillet and the stack would ride up it / wedge
        x0 = self.interior.bounds[0]
        flat_y = [y for x, y in self.interior.exterior.coords
                  if x < x0 + 1e-6]
        flat = LineString([(x0, min(flat_y)), (x0, max(flat_y))])
        wall = self.interior.exterior.difference(flat.buffer(1e-6))
        for i, (c, hh, b) in enumerate(self.sheets):
            name = f"the {c:g} x {hh:g} x {b:g} sheet"
            for side in (+1, -1):
                y = side * b / 2.0
                run = Point(self.x_bottom + 0.02, y).distance(wall)
                if not min(flat_y) < y < max(flat_y):
                    fail(f"{name}'s bottom corners land on the corner "
                         "fillets")
                if run < self.corner_run - 0.05:
                    fail(f"{name}'s bottom corner keeps only {run:.2f} mm of "
                         "flat bottom wall before the corner fillet (need "
                         f">= {self.corner_run:.2f})")
            if not self.interior.contains(self.home_sheet(i, 0.02)):
                fail(f"{name} does not fit pushed home")
        # the reference sheet (it sets the angle) keeps >= side_gap to every
        # wall above the corner zone
        sheet = self.home_sheet(0, 0.02)
        upper = sheet.buffer(self.side_gap - 0.05, quad_segs=QS).difference(
            shp_box(0.0, -self.r_int, self.x_bottom + INNER_ROUND,
                    self.r_int))
        if not upper.within(self.interior):
            fail(f"the reference sheet pushed home does not keep "
                 f"{self.side_gap:.2f} mm to the side walls")
        # side walls: notch window, then the magnet lobe, on plain straight
        # wall with TRAP_WALL_MARGIN between them and to both fillets (the
        # 101's straight side is only ~67 mm long)
        lo, hi = self.side_run
        rn, rm, reach = self.notch_rho, self.side_magnet_rho, self.lobe_reach
        eps = 1e-6
        if (rn - NOTCH_W / 2.0 < lo + TRAP_WALL_MARGIN - eps
                or rn + NOTCH_W / 2.0 > hi - TRAP_WALL_MARGIN + eps):
            fail(f"a {NOTCH_W:g} mm grip notch does not fit on the "
                 f"{hi - lo:.1f} mm straight side wall")
        if (rm - reach < rn + NOTCH_W / 2.0 + TRAP_WALL_MARGIN - eps
                or rm + reach > hi - TRAP_WALL_MARGIN + eps):
            fail(f"the side magnet lobe does not fit beside the {NOTCH_W:g} "
                 f"mm grip notch on the {hi - lo:.1f} mm straight side wall")
        # measured: the notch window through base wall + skirt stays clear
        # of the lobe blend. 0.05 = the straight-wall tolerance of the
        # notch checks: the lobes' closing re-discretises the corner arcs and
        # tilts the plain run by a few hundredths (e.g. 0.04 at --wall-t 3)
        blend = self.ext_skirt.difference(
            self.ext_plain.buffer(0.05, quad_segs=QS))
        span = WALL_T + max(CLEAR_FRICTION, CLEAR_MAGNET) + SKIRT_T + 1.0
        for (px, py), nrm in self._side_notch_frames():
            window = affinity.translate(affinity.rotate(
                shp_box(-1.0, -NOTCH_W / 2.0, span, NOTCH_W / 2.0), nrm,
                origin=(0, 0)), px, py)
            if window.distance(blend) < 1.0:
                fail(f"grip notch at ({px:.1f}, {py:.1f}) runs into the side "
                     "magnet lobe")
        self._guard_pockets()
        self._guard_side_notches_straight()
        self._guard_grip_arcs_on_wall()
        # arc lobes: on plain arc wall (clear of the arc-corner fillets) and
        # their pockets clear of the scoop slot through the wall
        arc = self.grip_arcs[0]
        plain_deg = self.int_half - math.degrees(
            (INNER_ROUND + reach) / arc.r)
        scoop = shp_box(arc.r - 30.0, -self.scoop_w / 2.0,
                        arc.r + 30.0, self.scoop_w / 2.0)
        for a, c in zip(MAG_ARC_ANGLES, self.magnets_skirt):
            if abs(a) > plain_deg:
                fail(f"the arc magnet lobe at {a:g}° runs into an arc corner")
            if Point(c).buffer(POCKET_D / 2.0, quad_segs=QS).distance(
                    scoop) < 1.0:
                fail(f"--scoop-w {self.scoop_w:g} opens into the arc magnet "
                     f"pocket at {a:g}°")
        self._guard_text_fits()

    # -- preview-only ghost -----------------------------------------------------

    def paper_ghost(self, lift=0.0):
        """The reference sheet's stack, pushed home (1 mm off the bottom wall
        so the faces don't fight in the preview)."""
        poly = self.home_sheet(0, 1.0)
        return prism(poly, FLOOR_T + lift + 0.3,
                     FLOOR_T + lift + 0.3 + PREVIEW_STACK_H)

    # -- wording -----------------------------------------------------------------

    @property
    def paper_txt(self):
        c, h, b = self.sheet
        return (f"{c:.0f} x {h:.0f} mm fan, {b:.0f} mm flat bottom, "
                f"{self.fan_angle:.0f}°")

    @property
    def interior_txt(self):
        flat = 2.0 * self.x_bottom * math.tan(math.radians(self.int_half))
        return (f"{self.r_int - self.x_bottom:.0f} mm x "
                f"{self.int_angle:.0f}° (flat bottom {flat:.0f} mm)")

    @property
    def geo_txt(self):
        c, h, b = self.sheet
        return (f"{c:.0f} x {h:.0f} mm fan · {b:.0f} mm flat bottom ·\n"
                f"       {self.fan_angle:.0f}° · no tab")


CASE_CLASSES["trapezoid"] = TrapezoidCase


# --------------------------------------------------------------------------
# COMBO CASE — one box for two papers (PAPERS "combines")
# --------------------------------------------------------------------------


class ComboCase(Case):
    """Asymmetric keyhole: two papers' wedges overlaid against ONE shared wall.

    World frame: apex at the origin, the shared long wall runs along +X
    (θ = 0) and both sectors open counter-clockwise from it —

      far   the LONG, narrow paper:  θ 0 -> its int_angle, R = r_int (far arc)
      fan   the SHORT, wide paper:   θ 0 -> its int_angle, R = fan.r_int

    so the outline reads: long wall -> far arc -> horn wall (back down the
    θ = far.int_angle ray) -> re-entrant shoulder -> exposed fan arc -> fan
    wall -> apex. Each sector is a plain Case of its own paper, so both fit
    exactly like in their dedicated boxes ("never squeezed"), and whatever one
    paper leaves empty is finger room for picking the other.

    Mid-arc features (scoop, back notch, pry slot, first finger bay) ride the
    far arc; the grip notches sit on the two walls that form the apex; magnet
    counts stay at 4 skirt pairs (already strong) / one flat pair per convex
    corner; the engraving follows the long wall (PAPERS "engrave_rot").
    """

    def __init__(self, slug):
        super().__init__(slug)
        self._derive_table()
        self._check()

    def _derive_paper_geometry(self):
        # a combo has no side/angle/half of its own: those stay undefined on
        # purpose, so a single-wedge formula can't run on it unnoticed
        cfg = self.cfg
        names = cfg["combines"]
        if (isinstance(names, str) or len(names) != 2 or len(set(names)) != 2
                or any(n not in PAPERS or "combines" in PAPERS[n]
                       for n in names)):
            raise ValueError(
                f"{self.slug}: 'combines' must name exactly two different "
                f"plain PAPERS entries (got {names!r})")
        # the keyhole overlays two WEDGES (side / angle / apex_tip_x); any
        # other shape would be read as a wedge, or crash far from the cause
        odd = [n for n in names if PAPERS[n].get("shape", "wedge") != "wedge"]
        if odd:
            raise ValueError(
                f"{self.slug}: 'combines' members must be wedge papers, but "
                + ", ".join(f"{n} is shape {PAPERS[n]['shape']!r}"
                            for n in odd))
        self.far, self.fan = self.sectors = sorted(
            (Case(s) for s in names), key=lambda c: -c.r_int)
        if not self.far.int_angle < self.fan.int_angle:
            raise ValueError(
                f"{self.slug}: the longer paper ({self.far.slug}) must also "
                f"be the narrower one, but {self.fan.slug} is not wider — "
                "the longer paper's own box already holds both")
        self.r_int = self.far.r_int
        # grips mid far arc AND mid exposed fan arc ("just like the other
        # end"): both get a scoop, a magnet-skirt back notch and a finger bay
        self.grip_arcs = [
            ArcFrame(self.far.r_int, self.far.half),
            ArcFrame(self.fan.r_int,
                     (self.far.int_angle + self.fan.int_angle) / 2.0)]
        # the two straight walls that form the apex: (sector whose r_int
        # scales positions along the wall, wall direction, outward normal)
        self.walls = ((self.far, 0.0, -90.0),
                      (self.fan, self.fan.int_angle, self.fan.int_angle + 90.0))
        self.depth = cfg.get("depth", max(c.depth for c in self.sectors))

        self.interior = (
            unary_union([
                affinity.rotate(sector_poly(c.int_angle, c.r_int), c.half,
                                origin=(0, 0))
                for c in self.sectors])
            .buffer(-INNER_ROUND, quad_segs=QS)
            .buffer(INNER_ROUND, quad_segs=QS)
            # the opening leaves the shoulder sharp — a wall corner poking
            # into the cavity. This closing rounds it, so paper edges and the
            # telescoping lids can't catch (base outer groove r =
            # CORNER_BLEND_R - WALL_T, lid channels stay smooth)
            .buffer(CORNER_BLEND_R, quad_segs=QS)
            .buffer(-CORNER_BLEND_R, quad_segs=QS)
        )
        centre = self.interior.centroid
        self.engrave_xy = (centre.x, centre.y)
        self.divider_outline = self.interior.buffer(-DIVIDER_CLEAR, quad_segs=QS)
        far_arc, fan_arc = self.grip_arcs
        self.divider_holes = [
            Point(xy).buffer(DIVIDER_HOLE_D / 2.0, quad_segs=QS)
            for xy in (fan_arc.xy(DIVIDER_HOLE_FRAC * self.fan.r_int),
                       far_arc.xy((self.fan.r_int + self.far.r_int) / 2.0))]

    # -- layouts -------------------------------------------------------------------

    def _skirt_magnet_centres(self):
        """magnet-skirt: 2 on the far arc + 1 on each wall that forms the apex."""
        far_arc = self.grip_arcs[0]
        out = [polar(far_arc.r + MAG_OFFSET, far_arc.deg + a)
               for a in MAG_ARC_ANGLES]
        for sec, wall_deg, nrm_deg in self.walls:
            px, py = polar(MAG_SIDE_FRAC * sec.r_int, wall_deg)
            ox, oy = polar(MAG_OFFSET, nrm_deg)
            out.append((px + ox, py + oy))
        return out

    def _flat_magnet_centres(self):
        """magnet-flat/pedestal: one pair per convex corner, stepped out along
        the bisector of the two outward normals that meet there."""
        clr = POCKET_D / 2.0 + 1.3
        fa, fn = self.far.int_angle, self.fan.int_angle
        corners = (
            (polar(self.fan.apex_tip_x, fn / 2.0), fn / 2.0 + 180.0),  # apex
            (polar(self.r_int, 0.0), -45.0),             # long wall / far arc
            (polar(self.r_int, fa), fa + 45.0),          # horn tip
            (polar(self.fan.r_int, fn), fn + 45.0),      # fan arc / fan wall
        )
        return [self._step_out(xy, heading, clr) for xy, heading in corners]

    def _side_notch_frames(self):
        # NOTCH_FRAC of the FAN radius on both apex walls: the same pinch
        # span as the wide paper's own box — plus a third notch mid-way along
        # the horn's flat inner wall, next to the shoulder
        r = NOTCH_FRAC * self.fan.r_int
        horn_deg = self.far.int_angle
        return [(polar(r, wall_deg), nrm_deg)
                for _, wall_deg, nrm_deg in self.walls] + [
            (polar((self.fan.r_int + self.far.r_int) / 2.0, horn_deg),
             horn_deg + 90.0)]

    def _bays(self):
        # one finger bay per paper: mid far arc + mid exposed fan arc
        return [affinity.rotate(self._bay(arc.r), arc.deg, origin=(0, 0))
                for arc in self.grip_arcs]

    def _plinth(self):
        """Stepped pedestal: each paper's arc edge overhangs its own moat. The
        far paper's plinth only spans its own wedge, so the fan moat stays
        open from the shoulder round to the fan wall; the fan paper's arc edge
        inside the far wedge simply rests on the far plinth."""
        def disc(sec):
            # the moat is measured from the paper's PUSHED-HOME arc edge: the
            # shared apex is the fan's (blunter), so the narrower paper slides
            # deeper than in its own box and its edge retreats by the
            # difference — without this its overhang at the bay would shrink
            slide = sec.apex_tip_x - self.fan.apex_tip_x
            return Point(0.0, 0.0).buffer(
                sec.r_int - MOAT_W - sec.cfg["tab_extra"] - slide,
                quad_segs=QS)
        wedge = affinity.rotate(
            sector_poly(self.far.int_angle, self.r_int), self.far.half,
            origin=(0, 0))
        return (
            self.interior.intersection(
                disc(self.fan).union(wedge.intersection(disc(self.far))))
            .buffer(-2.0, quad_segs=QS)
            .buffer(2.0, quad_segs=QS)
            # round the concave junction where the fan moat meets the step
            .buffer(CORNER_BLEND_R, quad_segs=QS)
            .buffer(-CORNER_BLEND_R, quad_segs=QS)
            .intersection(self.interior)
        )

    # -- dividers: loose plate OR table (users print one) --------------------------

    @property
    def extras(self):
        names = ["divider"]
        if any(d != "magnet-pedestal" for d in self.designs):
            names.append("divider-table")
        if "magnet-pedestal" in self.designs:
            names.append("divider-table-pedestal")
        return tuple(names)

    def extras_for(self, design):
        return ["divider", "divider-table-pedestal"
                if design == "magnet-pedestal" else "divider-table"]

    # heading of the extras in the preview's print panel
    extras_title = "Optional divider, both papers at once — print one"

    def extra_note(self, name):
        lower, upper = ((self.fan, self.far) if name == "divider"
                        else (self.far, self.fan))
        return (f"{'loose plate' if name == 'divider' else 'table on legs'}"
                f" — {lower.short_name} below, {upper.short_name} on top")

    def _home(self, sec):
        """How far from the origin a paper's tip stops when pushed home into
        the shared apex along its own bisector."""
        ray = LineString([(0.0, 0.0), polar(4.0 * INNER_ROUND, sec.half)])
        return Point(0.0, 0.0).distance(ray.intersection(self.interior))

    def _derive_table(self):
        """Leg layout of the table divider, from the sector list: three round
        posts in the zone only the fan paper covers (nearest the apex — vital
        for the support hull — the fan-top corner and the shoulder) + two
        arc-segment feet hugging the far arc next to its corners. Posts are
        (xy, drop) — drop = how far the leg reaches below the floor the table
        stands on. The pedestal table stands on the plinth; its far feet and
        its fan-top post reach PEDESTAL_H down into the moats."""
        post_r = DIVIDER_POST_D / 2.0
        far_wedge = affinity.rotate(
            sector_poly(self.far.int_angle, 2.0 * self.r_int), self.far.half,
            origin=(0, 0))
        # where a post CENTRE may go: under the top, off the finger holes,
        # outside the wedge the long paper sweeps on the floor
        zone = (
            self.divider_outline.buffer(-post_r, quad_segs=QS)
            .difference(far_wedge.buffer(DIVIDER_POST_GAP + post_r,
                                         quad_segs=QS))
            .difference(unary_union(self.divider_holes).buffer(
                post_r + DIVIDER_POST_GAP, quad_segs=QS)))
        on_plinth = zone.intersection(self.plinth.buffer(
            -(DIVIDER_POST_INSET + post_r), quad_segs=QS))
        targets = ((0.0, 0.0),
                   polar(self.fan.r_int, self.fan.int_angle),
                   polar(self.fan.r_int, self.far.int_angle))

        def nearest(z):
            return [nearest_points(z, Point(t))[0].coords[0] for t in targets]

        std, ped = nearest(zone), nearest(on_plinth)
        # pedestal: apex and shoulder posts stand on the plinth (the standard
        # shoulder spot would land on the plinth-foot chamfer at the moat's
        # dead end), but the fan-top post keeps the standard XY and stands in
        # the fan moat — on the plinth it would pull the support hull in and
        # a light press on the fan-top corner would tip the table
        self.table_posts = {
            False: [(xy, 0.0) for xy in std],
            True: [(ped[0], 0.0), (std[1], PEDESTAL_H), (ped[2], 0.0)]}

        r_out = self.far.r_int - DIVIDER_CLEAR
        r_mid = r_out - DIVIDER_FOOT_T / 2.0
        half_w = math.degrees(DIVIDER_FOOT_W / 2.0 / r_mid)
        off_corner = math.degrees((INNER_ROUND + 2.0) / r_mid)
        self.table_feet = []
        for mid in (off_corner + half_w,
                    self.far.int_angle - off_corner - half_w):
            ang = np.radians(np.linspace(mid - half_w, mid + half_w, 17))
            ring = Polygon(
                [((r_out + 1.0) * math.cos(a), (r_out + 1.0) * math.sin(a))
                 for a in ang]
                + [((r_out - DIVIDER_FOOT_T) * math.cos(a),
                    (r_out - DIVIDER_FOOT_T) * math.sin(a))
                   for a in ang[::-1]])
            # rounded inner corners; the outer face stays flush with the top
            self.table_feet.append(
                ring.buffer(-1.2, quad_segs=QS).buffer(1.2, quad_segs=QS)
                .intersection(self.divider_outline))

    def build_divider(self):
        """Loose plate between the two stacks (prints flat, as modelled)."""
        return prism(
            self.divider_outline.difference(unary_union(self.divider_holes)),
            0.0, DIVIDER_T)

    def build_table(self, pedestal=False):
        """Table divider, standing: z = 0 is the floor the posts stand on —
        the plinth top for the pedestal design, whose far feet reach
        PEDESTAL_H further down into the moat."""
        top = DIVIDER_LEG_H
        plate = self.build_divider()
        plate.apply_translation([0.0, 0.0, top])
        # legs run half-way into the top: a real overlap for the union
        legs = [prism(Point(xy).buffer(DIVIDER_POST_D / 2.0, quad_segs=QS),
                      -drop, top + DIVIDER_T / 2.0)
                for xy, drop in self.table_posts[pedestal]]
        legs += [prism(foot, -PEDESTAL_H if pedestal else 0.0,
                       top + DIVIDER_T / 2.0)
                 for foot in self.table_feet]
        return trimesh.boolean.union([plate] + legs, check_volume=False)

    def build_extra(self, name):
        if name == "divider":
            return self.build_divider()
        # tables print upside down: top on the bed, legs up — no bridging
        return print_orientation_lid(
            self.build_table(pedestal=name.endswith("-pedestal")))

    # -- guards --------------------------------------------------------------------

    def _check(self):
        """Every failure here would otherwise pass silently: the meshes stay
        watertight while a pocket opens into the cavity, a notch holes the
        lid plate or the text runs off the lid."""
        fail = self._fail

        if not self._is_simple(self.interior):
            fail("the combined interior is not one simple polygon")
        if (not self._is_simple(self.plinth)
                or self.plinth.area < 0.4 * self.interior.area
                or self.plinth.difference(self.interior).area > 1e-6):
            fail("the stepped pedestal plinth is degenerate")
        self._guard_pockets()
        # side-notch windows on STRAIGHT wall: clear of the rounded shoulder,
        # the corner fillets and any lobe blend
        self._guard_side_notches_straight()
        self._guard_grip_arcs_on_wall()

        # dividers: one hole per paper zone — whichever stack lies on top,
        # the other hole stays uncovered
        far_wedge = affinity.rotate(
            sector_poly(self.far.int_angle, 2.0 * self.r_int), self.far.half,
            origin=(0, 0))
        fan_disc = Point(0.0, 0.0).buffer(self.fan.r_int, quad_segs=QS)
        land = self.divider_outline.buffer(-DIVIDER_HOLE_LAND, quad_segs=QS)
        fan_hole, horn_hole = self.divider_holes
        if (not fan_hole.within(land) or not horn_hole.within(land)
                or not fan_hole.disjoint(far_wedge)
                or not horn_hole.disjoint(fan_disc)):
            fail("a divider finger hole leaves its paper's own zone or has "
                 f"less than {DIVIDER_HOLE_LAND:g} mm of plate around it")
        if DIVIDER_LEG_H + DIVIDER_T > self.depth - 10.0:
            fail(f"--divider-leg-h {DIVIDER_LEG_H:g} leaves less than 10 mm "
                 "above the table")
        post_r = DIVIDER_POST_D / 2.0
        bays = unary_union([
            affinity.rotate(
                shp_box(arc.r - 20.0, -BAY_W / 2.0, arc.r + 20.0, BAY_W / 2.0),
                arc.deg, origin=(0, 0))
            for arc in self.grip_arcs])
        for pedestal, posts in self.table_posts.items():
            if min(Point(a).distance(Point(b))
                   for i, (a, _) in enumerate(posts)
                   for b, _ in posts[i + 1:]) < 2.0 * DIVIDER_POST_D:
                fail("table posts collapse onto each other")
            for xy, drop in posts:
                post = Point(xy).buffer(post_r, quad_segs=QS)
                if (not post.within(self.divider_outline.buffer(0.01))
                        or post.distance(far_wedge) < DIVIDER_POST_GAP - 0.01):
                    fail(f"table post at ({xy[0]:.1f}, {xy[1]:.1f}) leaves "
                         "the top outline or enters the long paper's wedge")
                if pedestal and drop == 0.0 and not post.within(
                        self.plinth.buffer(-DIVIDER_POST_INSET + 0.01,
                                           quad_segs=QS)):
                    fail(f"pedestal table post at ({xy[0]:.1f}, {xy[1]:.1f}) "
                         "does not stand fully on the plinth")
                # a moat post needs flat moat floor under its whole foot
                if drop > 0.0 and (
                        post.distance(self.plinth)
                        < PEDESTAL_CHAMFER_BOTTOM + 1.0
                        or post.distance(bays) < 3.0):
                    fail(f"pedestal table post at ({xy[0]:.1f}, {xy[1]:.1f}) "
                         "fouls the plinth-foot chamfer or a finger bay")
        play = (self.far.r_int - DIVIDER_CLEAR - DIVIDER_FOOT_T
                - (self.far.side + self._home(self.far)))
        if play < DIVIDER_FAR_PLAY:
            fail(f"table feet leave the long paper only {play:.2f} mm of "
                 f"radial play (need >= {DIVIDER_FAR_PLAY:g})")
        far_arc = self.grip_arcs[0]
        window = affinity.rotate(
            shp_box(far_arc.r - 20.0, -max(self.scoop_w, BAY_W) / 2.0,
                    far_arc.r + 20.0, max(self.scoop_w, BAY_W) / 2.0),
            far_arc.deg, origin=(0, 0))
        for foot in self.table_feet:
            if (foot.geom_type != "Polygon" or foot.distance(window) < 3.0
                    or foot.distance(self.plinth)
                    < PEDESTAL_CHAMFER_BOTTOM + 1.0):
                fail("a table foot fouls the far scoop / finger bay or the "
                     "pedestal's foot chamfer")
        self._guard_text_fits()

    # -- preview-only ghosts --------------------------------------------------

    def paper_ghost(self, lift=0.0):
        raise NotImplementedError(
            f"{self.slug}: a combo holds two papers — use ghosts()")

    @property
    def scenes(self):
        far, fan = self.far, self.fan
        return [
            {"name": far.slug, "label": f"{far.short_name} only",
             "parts": [f"full-{far.slug}"]},
            {"name": fan.slug, "label": f"{fan.short_name} only",
             "parts": [f"full-{fan.slug}"]},
            {"name": "plate", "label": "Both — loose plate",
             "parts": ["plate-lower", "plate", "plate-upper"]},
            {"name": "table", "label": "Both — table divider",
             "parts": ["table-lower", "table", "table-upper"]},
        ]

    default_scene = "table"

    def ghosts(self, design):
        """Every usage mode's contents for one design: a full pack of either
        paper; fan paper / loose plate / far paper; far paper / table / fan
        paper. The pedestal design lifts them onto its plinth and gets its
        own table."""
        pedestal = design == "magnet-pedestal"
        floor = FLOOR_T + (PEDESTAL_H if pedestal else 0.0)
        colors = {self.fan.slug: "#efe3c8", self.far.slug: "#e0c894"}

        def stack(name, sec, z, h):
            # both tips push home into the shared (fan) apex
            poly = affinity.rotate(
                paper_outline(sec.side, sec.angle, sec.cfg["tab_extra"],
                              self.fan.apex_tip_x),
                sec.half, origin=(0, 0))
            return {"name": name, "color": colors[sec.slug], "opacity": 0.55,
                    "mesh": prism(poly, z, z + h)}

        def solid(name, mesh, z):
            mesh.apply_translation([0.0, 0.0, z])
            return {"name": name, "color": "#7d8794", "mesh": mesh}

        under, on = PREVIEW_COMBO_STACK_H
        plate_z = floor + 0.3 + under + 0.3
        table_top = floor + DIVIDER_LEG_H + DIVIDER_T
        return [
            stack(f"full-{self.far.slug}", self.far, floor + 0.3,
                  PREVIEW_STACK_H),
            stack(f"full-{self.fan.slug}", self.fan, floor + 0.3,
                  PREVIEW_STACK_H),
            stack("plate-lower", self.fan, floor + 0.3, under),
            solid("plate", self.build_divider(), plate_z),
            stack("plate-upper", self.far, plate_z + DIVIDER_T + 0.3, on),
            stack("table-lower", self.far, floor + 0.3, DIVIDER_LEG_H - 2.0),
            solid("table", self.build_table(pedestal), floor),
            stack("table-upper", self.fan, table_top + 0.3,
                  self.depth - DIVIDER_LEG_H - DIVIDER_T - 5.0),
        ]

    # -- wording -----------------------------------------------------------------

    @property
    def paper_txt(self):
        return " + ".join(f"{c.short_name}: {c.paper_txt}"
                          for c in self.sectors)

    @property
    def interior_txt(self):
        return (" + ".join(c.interior_txt for c in self.sectors)
                + " keyhole (one shared wall)")

    @property
    def geo_txt(self):
        return (" + ".join(f"{c.side:.0f} mm · {c.angle:.0f}°"
                           for c in self.sectors)
                + " wedges,\n       one shared wall · plate or table divider")


# --------------------------------------------------------------------------
# ROUND CASE — flat paper discs (PAPERS "shape": "round")
# --------------------------------------------------------------------------
# Centre at the origin, the mid-arc grips (scoop, back thumb notch, pry slot,
# finger bay) on +X like every other case, so the shared builders run as-is.
# The absolute sizes tuned on 150 mm wedges don't fit a ~70 mm circle, hence
# the round layout below. A future nested-cup variant (Kalita Wave / basket
# filters) can subclass RoundCase and override sheet_outline / paper_ghost.

DISC_SLACK = 1.0          # radial slack round the discs (Ø65 -> Ø67 bore): a
                          # flat disc can't wedge, 1 mm all round is plenty
ROUND_SEGMENTS = 720      # interior = regular 720-gon (2 vertices / degree)
                          # whose INSCRIBED radius is r_int — never undersized
ROUND_SCOOP_SCALE = 0.75  # scoop width = SCOOP_W x this: 27 mm by default (a
                          # 36 mm scoop would take 64° of a Ø67 wall); a
                          # --scoop-w override scales the same way
ROUND_ENGRAVE_FRAC = 1.4  # engraving width = this x r_int (47 / 54 mm),
                          # capped at ENGRAVE_WIDTH (60 runs off a Ø67 lid core)
# Layout round the circle, deg (0° = scoop + back thumb notch, +X). The two
# magnet-skirt side notches at ±120° and the thumb notch at 0° make a tripod
# grip: fingers hold the base through the side notches, the thumb pushes the
# back ledge up. The three lobes sit midway between the windows, 60° clear of
# each, so the ±60° pairs nearest the thumb peel first and the 180° pair is
# the hinge. Lobes and flat-lid bulges are 120°-symmetric: a lid put on
# turned by 120° still fits and snaps (glue all base magnets same pole up).
ROUND_NOTCH_DEG = 120.0
ROUND_SKIRT_MAG_DEGS = (60.0, 180.0, -60.0)
ROUND_FLAT_MAG_DEGS = (180.0, 60.0, -60.0)
ROUND_MIN_GAP = 3.0       # plain wall/skirt between any two of: side notches,
                          # back notch, scoop, magnet lobes (mm)
ROUND_MIN_BAND = 0.8      # solid band any skirt window must keep below the
                          # scoop (the --arc-notch-gap floor: else a dust slit)


def disc_poly(r, n=ROUND_SEGMENTS):
    """Regular n-gon about the origin whose INSCRIBED circle is r (so it
    never cuts inside the true circle). Edge midpoints sit at multiples of
    360/n degrees — on the axes and at ±60° / ±120° for n = 720."""
    rv = r / math.cos(math.pi / n)
    return Polygon([polar(rv, (k + 0.5) * 360.0 / n) for k in range(n)])


def slot_footprint(width, span, xy, normal_deg):
    """XY footprint of slot_cutter(width, ..., xy, normal_deg, span)."""
    fp = shp_box(-span / 2.0, -width / 2.0, span / 2.0, width / 2.0)
    fp = affinity.rotate(fp, normal_deg, origin=(0, 0))
    return affinity.translate(fp, *xy)


class RoundCase(Case):
    """Round box for stacks of flat paper discs (PAPERS "shape": "round").

    One BisectorFrame grip arc at r_int on +X, like a plain wedge, so scoop,
    back thumb notch + ramp, pry slot, lids, lip, recess and pockets come
    from the shared builders, and so does the finger bay. Own: the magnet /
    notch angles (ROUND_*), a D-shaped pedestal plinth (moat only in front
    of the bay — the floppy discs keep the most support), a narrower scoop
    and engraving, and a TWIST-OFF friction lid without grip notches (user
    decision: a round lid turns, so a notch could land over the scoop and
    open a dust slit).
    """

    def __init__(self, slug):
        super().__init__(slug)
        self._check()

    def _derive_paper_geometry(self):
        # no side / angle / half / apex_tip_x on purpose (like the combo): a
        # wedge formula reached by mistake crashes instead of building junk
        cfg = self.cfg
        wedge_keys = [k for k in ("side", "angle", "tab_extra") if k in cfg]
        if wedge_keys:
            raise ValueError(
                f"{self.slug}: a round paper takes 'diameter', not "
                + " / ".join(wedge_keys))
        self.diameter = float(cfg["diameter"])
        self.r_disc = self.diameter / 2.0
        self.r_int = self.r_disc + DISC_SLACK
        self.depth = cfg.get("depth", DEPTH)
        # no INNER_ROUND opening: a circle has no corners to fillet
        self.interior = disc_poly(self.r_int)
        self.engrave_xy = (0.0, 0.0)
        self.grip_arcs = [BisectorFrame(self.r_int)]

    # -- layouts -----------------------------------------------------------------

    def _skirt_magnet_centres(self):
        """magnet-skirt: 3 lobes midway between the three grip windows."""
        return [polar(self.r_int + MAG_OFFSET, a) for a in ROUND_SKIRT_MAG_DEGS]

    def _flat_magnet_centres(self):
        """magnet-flat/pedestal: 3 bulges at 120°, so the round lid snaps
        aligned in any of its three orientations (the pedestal lid is keyed
        by the bay). Same clearance _step_out would march to, on a circle."""
        clr = POCKET_D / 2.0 + 1.3
        return [polar(self.r_int + clr, a) for a in ROUND_FLAT_MAG_DEGS]

    def _side_notch_frames(self):
        """magnet-skirt lid only (the friction lid is twist-off): ±120°."""
        return [(polar(self.r_int, s * ROUND_NOTCH_DEG), s * ROUND_NOTCH_DEG)
                for s in (+1, -1)]

    # _bay / _bays: inherited. On the raw box the r6 inner fillets barely
    # reach into a small bore, but the CORNER_BLEND_R closing that builds
    # interior_ped fills the junction: the channel keeps 33.85 of BAY_W 34 mm
    # on Ø67 (measured; verify checks it), so no round-specific bay.

    def _plinth(self):
        """D-shaped pedestal: the whole disc rests on it except a MOAT_W
        segment in front of the bay. Pushed away from the bay (the worst
        case) a disc still overhangs the moat by MOAT_W − 2·DISC_SLACK."""
        r = self.r_int
        return (
            self.interior.intersection(
                shp_box(-2.0 * r, -2.0 * r, r - MOAT_W, 2.0 * r))
            .buffer(-2.0, quad_segs=QS)
            .buffer(2.0, quad_segs=QS)
        )

    # -- sizing hooks --------------------------------------------------------------

    @property
    def scoop_w(self):
        return ROUND_SCOOP_SCALE * SCOOP_W

    @property
    def engrave_width(self):
        return min(ENGRAVE_WIDTH, ROUND_ENGRAVE_FRAC * self.r_int)

    @property
    def pedestal_cove(self):
        """The wall cove runs all round the bore, under the disc edges: kept
        DISC_SLACK - 0.2 narrow (0.8 mm by default) so a centred disc of the
        largest size still lies flat on the plinth. --chamfer-side-wall
        still applies when it is smaller."""
        return min(PEDESTAL_CHAMFER_WALL, DISC_SLACK - 0.2)

    def build_base(self, design):
        base = super().build_base(design)
        # see TrapezoidCase.build_base: same pedestal-union slivers
        return clean_union(base) if design == "magnet-pedestal" else base

    def lid_notch_cutters(self, design):
        # twist-off friction lid: no notches at all (user decision)
        if design == "friction":
            return []
        return super().lid_notch_cutters(design)

    # -- guards ------------------------------------------------------------------

    def _check(self):
        """Layout guards — each catches a failure that would otherwise pass
        silently (the meshes stay watertight)."""
        fail = self._fail
        if not self._is_simple(self.interior):
            fail("the round interior is not one simple polygon")
        # only the designs this entry ships (PAPERS "designs" subset): a
        # small disc box restricted to friction must not trip the bay guard
        if "magnet-pedestal" in self.designs:
            if self.r_int < BAY_W / 2.0 + CORNER_BLEND_R + 1.0:
                fail(f"Ø{self.diameter:g} is too small for the {BAY_W:g} mm "
                     "finger bay")
            if (not self._is_simple(self.plinth)
                    or self.plinth.area < 0.4 * self.interior.area
                    or self.plinth.difference(self.interior).area > 1e-6):
                fail("the D-shaped pedestal plinth is degenerate")
        self._guard_pockets()
        if "magnet-skirt" in self.designs:
            self._guard_side_notches_round()
        self._guard_grip_arcs_on_wall()
        self._guard_round_layout()
        self._guard_text_fits()

    def _guard_side_notches_round(self, tol=0.05):
        """Each side-notch window sits on plain CIRCULAR wall, inside and
        out (clear of every lobe blend) — sampled along the circle, since a
        tangent line leaves an r≈34 circle by ~2 mm at ±12 mm."""
        for (px, py), nrm_deg in self._side_notch_frames():
            r = math.hypot(px, py)
            for t in (-NOTCH_W / 2.0 - 1.0, 0.0, NOTCH_W / 2.0 + 1.0):
                a = nrm_deg + math.degrees(t / r)
                off = max(
                    Point(polar(r, a)).distance(self.interior.boundary),
                    Point(polar(r + WALL_T, a)).distance(
                        self.ext_skirt.boundary))
                if off > tol:
                    self._fail(f"side notch at {nrm_deg:g}° is {off:.2f} mm "
                               "off its circular wall (a lobe blend runs "
                               "into it)")

    def _guard_round_layout(self):
        """Grip windows and magnet lobes share one small circle: every pair
        stays ROUND_MIN_GAP apart, measured on the wall + skirt hoop they cut,
        and no skirt window can reach the scoop (dust slit) — not even with
        the lid put on turned by 120° (lobes are 120°-symmetric). Every one
        of these is a magnet-skirt feature (lobes, side notches, back notch
        + ramp), so nothing to guard without that design."""
        if "magnet-skirt" not in self.designs:
            return
        fail = self._fail
        cm = CLEAR_MAGNET
        hoop = self.ext_skirt.buffer(cm + SKIRT_T, quad_segs=QS).difference(
            self.interior)
        chan = self.ext_skirt.buffer(cm, quad_segs=QS).difference(
            self.ext_plain.buffer(cm, quad_segs=QS))     # lid lobe channels
        lobes = self.ext_skirt.difference(self.ext_plain)  # base lobes
        arc = self.grip_arcs[0]
        side = [(f"side notch at {n:g}°",
                 slot_footprint(NOTCH_W, 24.0, xy, n).intersection(hoop))
                for xy, n in self._side_notch_frames()]
        back = slot_footprint(ARC_NOTCH_W, 30.0, arc.xy(arc.r),
                              arc.deg).intersection(hoop)
        scoop = slot_footprint(self.scoop_w, 60.0, arc.xy(arc.r),
                               arc.deg).intersection(hoop)
        pairs = [(name, w, "a magnet lobe", chan) for name, w in side]
        pairs += [(name, w, "the back notch", back) for name, w in side]
        pairs += [("the back notch", back, "a magnet lobe", chan),
                  ("the scoop", scoop, "a magnet lobe", lobes)]
        for a_name, a, b_name, b in pairs:
            gap = a.distance(b)
            if gap < ROUND_MIN_GAP:
                fail(f"{a_name} comes within {gap:.2f} mm of {b_name} (need "
                     f">= {ROUND_MIN_GAP:g}) — narrow it or shrink the pockets")
        scoop_bottom = self.arc_notch_top + ARC_NOTCH_GAP
        turned_band = scoop_bottom - (PLINTH + NOTCH_H)
        if turned_band < ROUND_MIN_BAND:
            fail(f"--notch-h {NOTCH_H:g}: a magnet-skirt lid put on turned by "
                 f"120° sets a side notch over the scoop with only "
                 f"{turned_band:.2f} mm of wall between them (need >= "
                 f"{ROUND_MIN_BAND:g})")
        # the back-notch ramp pivots about the straight tangent at the
        # bisector, but the skirt curves away from it: toward the window
        # flanks the skirt's inner face lies inside the pivot, where the
        # tilted ramp cutter climbs (audit D6). The scoop's rounded bottom
        # climbs too — compare both at every tangent offset t (both cutters
        # are planar prisms, so their profiles don't vary with the radius).
        z_top = self.arc_notch_top
        r_in = self.r_int + WALL_T + cm
        half, hs = ARC_NOTCH_W / 2.0, self.scoop_w / 2.0
        rr = min(ARC_NOTCH_R, half - 0.25,
                 (z_top - (PLINTH - 6.0)) / 2.0 - 0.25)
        rs = min(SCOOP_R, hs - 0.25)  # slot_cutter's clamps
        slope = ARC_NOTCH_CHAMFER / SKIRT_T

        def corner_lift(t, w2, r):  # how far a rounded corner sits off the edge
            c = t - (w2 - r)
            return r - math.sqrt(max(r ** 2 - c ** 2, 0.0)) if c > 0 else 0.0

        def band_at(t):  # scoop bottom − notch ceiling (skirt inner face)
            ceiling = ((r_in - math.sqrt(r_in ** 2 - t ** 2)) * slope
                       - corner_lift(t, half, rr))
            return ARC_NOTCH_GAP + corner_lift(t, hs, rs) - ceiling

        worst = min(band_at(t) for t in np.linspace(0.0, min(half, hs), 97))
        if worst < ROUND_MIN_BAND - 0.01:  # ~ the gap itself near the bisector
            fail(f"--arc-notch-gap {ARC_NOTCH_GAP:g}: on this round skirt the "
                 f"back-notch ramp climbs toward its flanks, leaving only "
                 f"{worst:.2f} mm below the scoop (need >= "
                 f"{ROUND_MIN_BAND:g})")

    # -- preview-only ghosts --------------------------------------------------

    scenes = [{"name": "papers", "label": "Ghost filter stack",
               "parts": ["papers"]}]

    @property
    def stack_h(self):
        """Preview ghost height: a typical pack (PAPERS "stack_h"), never
        above depth − 4 (the flat lids' lip reaches 2.5 mm down)."""
        return min(self.cfg.get("stack_h", PREVIEW_STACK_H), self.depth - 4.0)

    def sheet_outline(self):
        """One sheet's footprint, centred: 1 mm of play shows all round."""
        return disc_poly(self.r_disc, 180)

    def paper_ghost(self, lift=0.0):
        z0 = FLOOR_T + lift + 0.3
        return prism(self.sheet_outline(), z0, z0 + self.stack_h)

    # -- wording -----------------------------------------------------------------

    @property
    def paper_txt(self):
        return f"paper discs up to Ø{self.diameter:g} mm"

    @property
    def interior_txt(self):
        return f"Ø{2.0 * self.r_int:g} mm round"

    @property
    def geo_txt(self):
        return (f"discs up to Ø{self.diameter:g} mm · round box ·\n"
                f"       {DISC_SLACK:g} mm slack all round")

    @property
    def grip_txt(self):
        return (f"friction lid: twist-off (no notches); magnet-skirt lid: "
                f"side notches {NOTCH_W:.1f} x {NOTCH_H:.1f} mm at "
                f"±{ROUND_NOTCH_DEG:.0f}°, back notch {ARC_NOTCH_W:.1f} x "
                f"{ARC_NOTCH_H:.1f} mm, {ARC_NOTCH_GAP:.1f} mm band to its "
                f"{self.scoop_w:.1f} mm scoop")


CASE_CLASSES["round"] = RoundCase


def make_case(slug):
    """The Case for one PAPERS entry: ComboCase for "combines", else the
    class registered for its "shape" (default "wedge" -> Case)."""
    cfg = PAPERS[slug]
    if "combines" in cfg:
        return ComboCase(slug)
    shape = cfg.get("shape", "wedge")
    if shape not in CASE_CLASSES:
        raise ValueError(
            f"{slug}: unknown shape {shape!r} (known: "
            f"{', '.join(sorted(CASE_CLASSES))})")
    return CASE_CLASSES[shape](slug)


# --------------------------------------------------------------------------
# BUILD + EXPORT
# --------------------------------------------------------------------------


def apply_printer_args(argv=None):
    """Override the printer-fit tolerances and shell thicknesses from the
    command line, so parts can be tuned per printer/taste without editing code
    (make generate GEN_ARGS="...")."""
    global CLEAR_FRICTION, CLEAR_MAGNET, LIP_CLEAR, POCKET_D, POCKET_DEPTH
    global WALL_T, FLOOR_T, SKIRT_T
    global PEDESTAL_CHAMFER_BOTTOM, PEDESTAL_CHAMFER_WALL
    global DIVIDER_T, DIVIDER_CLEAR, DIVIDER_LEG_H
    global NOTCH_W, NOTCH_H, ARC_NOTCH_W, ARC_NOTCH_H, ARC_NOTCH_GAP
    global ARC_NOTCH_CHAMFER, SCOOP_W, SCOOP_ABOVE_FLOOR
    p = argparse.ArgumentParser(
        description="Generate all Filtarr STLs, previews and index.html.")
    p.add_argument("--clear-friction", type=float, default=CLEAR_FRICTION,
                   metavar="MM", help="friction lid clearance per side "
                   f"(default {CLEAR_FRICTION}; tune in ±0.04 steps)")
    p.add_argument("--clear-magnet", type=float, default=CLEAR_MAGNET,
                   metavar="MM", help="magnet-skirt lid glide clearance per "
                   f"side (default {CLEAR_MAGNET})")
    p.add_argument("--lip-clear", type=float, default=LIP_CLEAR,
                   metavar="MM", help="flat/pedestal lid alignment-lip "
                   f"clearance per side (default {LIP_CLEAR})")
    p.add_argument("--pocket-d", type=float, default=POCKET_D,
                   metavar="MM", help="magnet pocket diameter "
                   f"(default {POCKET_D}, for Ø6 mm discs)")
    p.add_argument("--pocket-depth", type=float, default=POCKET_DEPTH,
                   metavar="MM", help="magnet pocket depth "
                   f"(default {POCKET_DEPTH}, for 3 mm thick discs)")
    p.add_argument("--wall-t", type=float, default=WALL_T, metavar="MM",
                   help=f"base wall thickness (default {WALL_T}; "
                   "1.6 = ultralight, 2.4 = extra rigid)")
    p.add_argument("--floor-t", type=float, default=FLOOR_T, metavar="MM",
                   help=f"base floor thickness (default {FLOOR_T})")
    p.add_argument("--skirt-t", type=float, default=SKIRT_T, metavar="MM",
                   help=f"telescoping lid skirt thickness (default {SKIRT_T})")
    p.add_argument("--chamfer-bottom", type=float,
                   default=PEDESTAL_CHAMFER_BOTTOM, metavar="MM",
                   help="45° chamfer at the pedestal's foot (in the moat), "
                   "softens the shrink line on the base underside "
                   f"(default {PEDESTAL_CHAMFER_BOTTOM}; 0 disables)")
    p.add_argument("--chamfer-side-wall", type=float,
                   default=PEDESTAL_CHAMFER_WALL, metavar="MM",
                   help="45° cove where the pedestal top meets the side "
                   "walls/apex (default "
                   f"{PEDESTAL_CHAMFER_WALL}; 0 disables; keep small — "
                   "papers sit close to the walls near the tip)")
    p.add_argument("--divider-t", type=float, default=DIVIDER_T, metavar="MM",
                   help="combo divider plate thickness "
                   f"(default {DIVIDER_T})")
    p.add_argument("--divider-clear", type=float, default=DIVIDER_CLEAR,
                   metavar="MM", help="combo divider plate gap to the cavity "
                   f"walls, per side (default {DIVIDER_CLEAR})")
    p.add_argument("--divider-leg-h", type=float, default=DIVIDER_LEG_H,
                   metavar="MM", help="combo table divider: clear height "
                   "under the top = room for the lower stack "
                   f"(default {DIVIDER_LEG_H})")
    grip = p.add_argument_group("grip geometry (telescoping designs)")
    grip.add_argument("--notch-w", type=float, default=NOTCH_W, metavar="MM",
                      help=f"side grip notch width (default {NOTCH_W})")
    grip.add_argument("--notch-h", type=float, default=NOTCH_H, metavar="MM",
                      help="side grip notch height above the plinth "
                      f"(default {NOTCH_H})")
    grip.add_argument("--arc-notch-w", type=float, default=ARC_NOTCH_W,
                      metavar="MM", help="magnet-skirt back thumb notch "
                      f"width (default {ARC_NOTCH_W})")
    grip.add_argument("--arc-notch-h", type=float, default=ARC_NOTCH_H,
                      metavar="MM", help="back thumb notch height above the "
                      f"plinth (default {ARC_NOTCH_H})")
    grip.add_argument("--arc-notch-gap", type=float, default=ARC_NOTCH_GAP,
                      metavar="MM", help="solid wall band between the back "
                      "notch top and the magnet-skirt scoop bottom "
                      f"(default {ARC_NOTCH_GAP}; keep >= 1.5 so the dust "
                      "seal survives print variance)")
    grip.add_argument("--arc-notch-chamfer", type=float,
                      default=ARC_NOTCH_CHAMFER, metavar="MM",
                      help="back notch ceiling ramp depth "
                      f"(default {ARC_NOTCH_CHAMFER}; 0 = square edge)")
    grip.add_argument("--scoop-w", type=float, default=SCOOP_W, metavar="MM",
                      help=f"finger scoop width (default {SCOOP_W})")
    grip.add_argument("--scoop-above-floor", type=float,
                      default=SCOOP_ABOVE_FLOOR, metavar="MM",
                      help="friction-design scoop bottom above the interior "
                      f"floor (default {SCOOP_ABOVE_FLOOR}; the magnet-skirt "
                      "scoop bottom derives from the back notch instead)")
    a = p.parse_args(argv)
    if a.arc_notch_gap < 0.8:
        p.error("--arc-notch-gap below 0.8 mm would risk a dust slit "
                "between the back notch and the magnet-skirt scoop")
    CLEAR_FRICTION, CLEAR_MAGNET = a.clear_friction, a.clear_magnet
    LIP_CLEAR, POCKET_D, POCKET_DEPTH = a.lip_clear, a.pocket_d, a.pocket_depth
    WALL_T, FLOOR_T, SKIRT_T = a.wall_t, a.floor_t, a.skirt_t
    PEDESTAL_CHAMFER_BOTTOM = a.chamfer_bottom
    PEDESTAL_CHAMFER_WALL = a.chamfer_side_wall
    DIVIDER_T, DIVIDER_CLEAR = a.divider_t, a.divider_clear
    DIVIDER_LEG_H = a.divider_leg_h
    NOTCH_W, NOTCH_H = a.notch_w, a.notch_h
    ARC_NOTCH_W, ARC_NOTCH_H = a.arc_notch_w, a.arc_notch_h
    ARC_NOTCH_GAP, ARC_NOTCH_CHAMFER = a.arc_notch_gap, a.arc_notch_chamfer
    SCOOP_W, SCOOP_ABOVE_FLOOR = a.scoop_w, a.scoop_above_floor


def tolerance_summary():
    return (f"lid fit/side: friction {CLEAR_FRICTION:.2f}, skirt "
            f"{CLEAR_MAGNET:.2f}, flat lip {LIP_CLEAR:.2f} mm; magnet pockets "
            f"Ø{POCKET_D:.1f} x {POCKET_DEPTH:.1f} mm (Ø6x3 discs sit "
            f"{POCKET_DEPTH - 3.0:.1f} mm recessed)")


def shell_summary(cove=None):
    """cove: a case's pedestal_cove (default PEDESTAL_CHAMFER_WALL — the
    round boxes cap theirs)."""
    cove = PEDESTAL_CHAMFER_WALL if cove is None else cove
    s = (f"walls {WALL_T:.1f} / floor {FLOOR_T:.1f} / lid skirts "
         f"{SKIRT_T:.1f} mm; lid plates: friction {LID_T_FRICTION:.1f}, "
         f"magnet {LID_T_MAGNET:.1f} at rim & pockets / {LID_CORE_T:.1f} core")
    if PEDESTAL_CHAMFER_BOTTOM > 0.0 or cove > 0.0:
        s += (f"; pedestal chamfers: foot {PEDESTAL_CHAMFER_BOTTOM:.1f} / "
              f"wall cove {cove:.1f}")
    return s


def main():
    apply_printer_args()
    print(f"tolerances — {tolerance_summary()}")
    print(f"shell — {shell_summary()}")
    cases = []
    for slug in PAPERS:
        case = make_case(slug)
        cases.append(case)
        print(f"\n=== {case.cfg['display']} ({slug}) — "
              f"interior {case.interior_txt}, {case.depth:.0f} mm deep ===")
        stl_dir = os.path.join(case.out_dir, "stl")
        os.makedirs(stl_dir, exist_ok=True)

        parts_world = {}
        for design in case.designs:
            parts_world[f"{design}-base"] = case.build_base(design)
            parts_world[f"{design}-lid"] = case.build_lid(design)
            parts_world[f"{design}-lid-engraved"] = case.build_lid(design, engraved=True)

        # extras (combo dividers) come back in print orientation already
        extras = {name: case.build_extra(name) for name in case.extras}

        for name, mesh in {**parts_world, **extras}.items():
            assert mesh.is_watertight, f"{slug} {name} is not watertight!"
            upright = name.endswith("base") or name in extras
            out = mesh if upright else print_orientation_lid(mesh)
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
              "magnet-flat": "#4f7cb3", "magnet-pedestal": "#8a5fb3"}


def build_preview(case, parts_world):
    def ghost_parts(design):
        out = []
        for g in case.ghosts(design):
            part = {"name": g["name"], "attach": "base", "color": g["color"]}
            if g.get("opacity"):
                part["opacity"] = g["opacity"]
            part["stl"] = b64stl(g["mesh"])
            out.append(part)
        return out

    variants = {}
    for design in case.designs:
        parts = [
            {"name": "base", "attach": "base", "color": "#8a8f98",
             "stl": b64stl(parts_world[f"{design}-base"])},
            {"name": "lid", "attach": "lid", "color": LID_COLORS[design],
             "stl": b64stl(parts_world[f"{design}-lid"])},
            {"name": "lid-engraved", "attach": "lid", "color": LID_COLORS[design],
             "stl": b64stl(parts_world[f"{design}-lid-engraved"])},
        ] + ghost_parts(design)
        if design != "friction":
            centres = (case.magnets_skirt if design == "magnet-skirt"
                       else case.magnets_flat)
            mb, ml = case.magnet_ghosts(
                centres,
                case.base_h_ped if design == "magnet-pedestal" else None)
            parts += [
                {"name": "magnets", "attach": "base", "color": "#d7dade",
                 "metal": True, "stl": b64stl(mb)},
                {"name": "magnets-lid", "attach": "lid", "color": "#d7dade",
                 "metal": True, "stl": b64stl(ml)},
            ]
        variants[design] = parts

    has_magnets = any(d.startswith("magnet") for d in case.designs)
    has_pedestal = "magnet-pedestal" in case.designs
    heights = [f"{case.base_h + LID_T_FRICTION:.0f} mm (friction)"]
    if has_magnets:
        heights.append(f"{case.base_h + LID_T_MAGNET:.0f} mm (magnet)")
    if has_pedestal:
        heights.append(f"{case.base_h_ped + LID_T_MAGNET:.0f} mm (pedestal)")
    depth_txt = f"{case.depth:.0f} mm deep"
    if has_pedestal:
        depth_txt += f" ({case.depth + PEDESTAL_H:.0f} pedestal)"
    dims = {
        "paper": case.paper_txt,
        "interior": f"{case.interior_txt}, {depth_txt}",
        "closedH": " / ".join(heights),
    }
    mag_counts = {"magnet-skirt": 2 * len(case.magnets_skirt),
                  "magnet-flat": 2 * len(case.magnets_flat),
                  "magnet-pedestal": 2 * len(case.magnets_flat)}
    if has_magnets:
        dims["magnets"] = (f"Ø6x3 mm discs — skirt: "
                           f"{mag_counts['magnet-skirt']}, flat/pedestal: "
                           f"{mag_counts['magnet-flat']}; "
                           f"pockets {POCKET_D:.1f} x {POCKET_DEPTH:.1f} mm")
    if "divider" in case.extras:
        dims["divider"] = (f"optional, for both papers at once — loose "
                           f"{DIVIDER_T:.1f} mm plate ({DIVIDER_CLEAR:.1f} mm "
                           f"wall gap): {case.fan.short_name} below, "
                           f"{case.far.short_name} on top")
        dims["table"] = (f"or a table on {DIVIDER_LEG_H:.0f} mm legs: "
                         f"{case.far.short_name} below ({DIVIDER_LEG_H:.0f} "
                         f"mm), {case.fan.short_name} on top ("
                         f"{case.depth - DIVIDER_LEG_H - DIVIDER_T:.1f} mm)")
    dims["tolerances"] = (f"lid fit/side: friction {CLEAR_FRICTION:.2f}, "
                          f"skirt {CLEAR_MAGNET:.2f}, flat lip {LIP_CLEAR:.2f} mm"
                          + (f"; magnets sit {POCKET_DEPTH - 3.0:.1f} mm recessed"
                             if has_magnets else ""))
    dims["shell"] = shell_summary(case.pedestal_cove)
    if "magnet-skirt" in case.designs:
        dims["grip"] = case.grip_txt
    def print_entry(design):
        entry = {
            "base": f"stl/{case.slug}-case-{design}-base.stl",
            "lid": f"stl/{case.slug}-case-{design}-lid.stl",
            "lid_engraved": f"stl/{case.slug}-case-{design}-lid-engraved.stl",
            "magnets": (f"{mag_counts[design]}x Ø6x3 mm magnets + glue"
                        if design.startswith("magnet") else None),
        }
        # optional alternatives (combo dividers), under their own heading
        extras = [{"file": f"stl/{case.slug}-case-{name}.stl",
                   "note": case.extra_note(name)}
                  for name in case.extras_for(design)]
        if extras:
            entry["extras_title"] = case.extras_title
            entry["extras"] = extras
        return entry

    data = {
        "title": f"Filtarr — {case.cfg['display']}",
        "variants": variants,
        # contents scenes: which ghost parts (same names in every variant)
        # show together; a single scene is a plain on/off checkbox
        "scenes": case.scenes,
        "scene": case.default_scene,
        "dims": dims,
        "print": {design: print_entry(design) for design in case.designs},
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
        stls = "".join(
            f'<li><a href="{folder}/stl/{case.slug}-case-{name}.stl">'
            f"{case.slug}-case-{name}.stl</a></li>"
            for name in [f"{design}-{part}" for design in case.designs
                         for part in ("base", "lid", "lid-engraved")]
            + list(case.extras))
        cards.append(f"""
  <article>
    <a href="{renders}"><img loading="lazy" src="{renders}"
         alt="Renders of the {case.cfg['display']} cases"></a>
    <h2>{case.cfg['display']}</h2>
    <p class="geo">{case.geo_txt} · {case.depth:.0f} mm deep ·
       {len(case.designs)} design{'s' if len(case.designs) > 1 else ''}</p>
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
