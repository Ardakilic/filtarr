#!/usr/bin/env python3
"""Verify every Filtarr part without a printer: builds each PAPERS entry x
design IN MEMORY (never touches the generated outputs) and measures the
finished meshes — ray casts, cross-sections, booleans — against the
constants in generate.py. Exits 1 on any failure.

Usage:  python3 tools/verify.py [--paper SLUG ...] [-v] [generate.py flags]

  --paper SLUG   only this paper (repeatable); default: all of PAPERS
  -v             also list every passing check with its measured value

Every fit/shell/grip override of generate.py is accepted, so a tuned build
can be verified the same way it is generated:
  make verify GEN_ARGS="--clear-friction 0.32"

Needs the ray-cast extras on top of requirements.txt — see
requirements-dev.txt (`make verify` installs them into a throwaway container).
"""

import argparse
import importlib.util
import math
import os
import sys
import time
import warnings

import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import (LineString, MultiPoint, Point, Polygon,
                              box as shp_box)
from shapely.ops import unary_union
from shapely.prepared import prep

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import generate as g  # noqa: E402  (has a __main__ guard — importing is free)

TOL = 0.01            # mm — fit dimensions must hit their constant this closely
MIN_SKIN = 0.4        # mm of wall around a magnet pocket: one perimeter (the
                      # same threshold as the guard in ComboCase._check)
# Hario's hanging tab, for the paper-fit check: ~15 mm wide on the arc edge
# right next to a seam corner; it protrudes by the paper's own tab_extra
TAB_W = 15.0
# table statics: PLA density and filter paper (55 g/m2, a folded filter is
# two plies); the table must carry a full upper pack with this much margin
PLA_G_MM3 = 1.24e-3
PAPER_G_MM2 = 55e-6 * 2
COM_MARGIN = 35.0     # mm from the centre of mass to the edge of the feet
HOLE_GAP = 2.0        # mm a divider hole keeps from every pose of the paper
                      # that must never cover it

# What every box must HAVE — a spec, hard-coded on purpose: everything else
# here is derived from generate.py, so a feature that silently drops out of
# its lists would just shrink the number of checks and still pass. Counted on
# generate's lists and, where a mesh can show it, on the meshes.
EXPECT = {
    "plain": {"side notches": 2, "grip arcs": 1, "finger bays": 1,
              "magnet-skirt pairs": 4, "flat/pedestal pairs": 3},
    "combo": {"side notches": 3, "grip arcs": 2, "finger bays": 2,
              "magnet-skirt pairs": 4, "flat/pedestal pairs": 4},
}


def expected_extras(case, design):
    """Plain papers ship no extras; a combo ships its loose plate + the
    design's own table."""
    if kind(case) == "plain":
        return []
    return ["divider", "divider-table-pedestal"
            if design == "magnet-pedestal" else "divider-table"]


# --------------------------------------------------------------------------
# measuring helpers
# --------------------------------------------------------------------------


def section(mesh, z):
    """XY cross-section of a mesh at height z as a shapely (Multi)Polygon, in
    world coordinates (identity to_2D), or None if the plane misses it."""
    sec = mesh.section(plane_origin=[0.0, 0.0, float(z)],
                       plane_normal=[0.0, 0.0, 1.0])
    if sec is None:
        return None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        planar, _ = sec.to_planar(to_2D=np.eye(4))
    polys = list(planar.polygons_full)
    return unary_union(polys) if polys else None


def hits(mesh, xy):
    """Ascending z of every surface a vertical line through xy crosses."""
    loc, _, _ = mesh.ray.intersects_location(
        np.array([[xy[0], xy[1], -1000.0]]), np.array([[0.0, 0.0, 1.0]]),
        multiple_hits=True)
    return sorted(set(round(float(z), 4) for z in loc[:, 2]))


def inside(mesh, points):
    return mesh.contains(np.asarray(points, dtype=float))


def overlap(a, b):
    """Volume two meshes share, mm3."""
    m = trimesh.boolean.intersection([a, b], check_volume=False)
    return 0.0 if m.is_empty else abs(m.volume)


def polys(geom):
    return [p for p in getattr(geom, "geoms", [geom])
            if p.geom_type == "Polygon"]


def ring_points(geom, step):
    """Points roughly `step` apart along the exterior ring(s)."""
    out = []
    for p in polys(geom):
        n = max(16, int(p.exterior.length / step))
        out += [p.exterior.interpolate(i / n, normalized=True)
                for i in range(n)]
    return out


def off_axis(arc, r, t=0.3):
    """Point at radius r on a grip arc's bisector, nudged t mm sideways so a
    vertical ray never runs down a mesh edge on the symmetry line."""
    x, y = arc.xy(r)
    return (x + t * arc.tangent[0], y + t * arc.tangent[1])


# --------------------------------------------------------------------------
# results
# --------------------------------------------------------------------------


class Report:
    """Collects (scope, check, ok, detail) rows for one paper."""

    def __init__(self):
        self.rows = []
        self.scope = None

    def check(self, name, ok, detail=""):
        self.rows.append((self.scope, name, bool(ok), detail))

    def near(self, name, value, want, tol=TOL, unit="mm"):
        self.check(name, abs(value - want) <= tol,
                   f"{value:.3f} {unit} (want {want:.3f})")

    def at_least(self, name, value, want, tol=TOL, unit="mm"):
        self.check(name, value >= want - tol,
                   f"{value:.3f} {unit} (need >= {want:.3f})")


class Design:
    """One design of one paper: its meshes + the outlines they were cut from."""

    def __init__(self, case, name):
        self.case, self.name = case, name
        self.pedestal = name == "magnet-pedestal"
        self.telescoping = name in ("friction", "magnet-skirt")
        self.magnets = name != "friction"
        self.base = case.build_base(name)
        self.lid = case.build_lid(name)
        self.lid_engraved = case.build_lid(name, engraved=True)
        self.top = case.base_h_ped if self.pedestal else case.base_h
        self.floor = g.FLOOR_T + (g.PEDESTAL_H if self.pedestal else 0.0)
        self.cavity = case.interior_ped if self.pedestal else case.interior
        self.ext = {"friction": case.ext_plain, "magnet-skirt": case.ext_skirt,
                    "magnet-flat": case.ext_flat,
                    "magnet-pedestal": case.ext_ped}[name]
        self.clear = (g.CLEAR_FRICTION if name == "friction"
                      else g.CLEAR_MAGNET)
        self.plate_t = (g.LID_T_FRICTION if name == "friction"
                        else g.LID_T_MAGNET)
        self.centres = (case.magnets_skirt if name == "magnet-skirt"
                        else case.magnets_flat) if self.magnets else []
        # the base's own outlines, cut from the MESH just above the floor
        # (below every scoop; above the pedestal's plinth and cove) — so the
        # wall and corner checks don't compare generate.py with itself
        ring = max(polys(section(self.base, self.floor + 0.5 + (
            g.PEDESTAL_CHAMFER_WALL if self.pedestal else 0.0))),
            key=lambda p: p.area)
        self.mesh_outline = Polygon(ring.exterior)
        self.mesh_cavity = Polygon(max(ring.interiors,
                                       key=lambda h: Polygon(h).area))


def kind(case):
    return "combo" if hasattr(case, "sectors") else "plain"


def papers_of(case):
    """(paper, bisector deg) for every paper a case holds: a plain wedge lies
    on +X; a combo's two sectors open from the shared wall."""
    if hasattr(case, "sectors"):
        return [(sec, sec.half) for sec in case.sectors]
    return [(case, 0.0)]


# --------------------------------------------------------------------------
# checks — every design of every paper
# --------------------------------------------------------------------------


def check_parts(rep, d):
    for label, mesh in (("base", d.base), ("lid", d.lid),
                        ("lid-engraved", d.lid_engraved)):
        rep.check(f"{label} watertight, positive volume",
                  mesh.is_watertight and mesh.is_winding_consistent
                  and mesh.volume > 0.0, f"{mesh.volume / 1000.0:.1f} cm3")
    shared = overlap(d.base, d.lid)
    rep.check("closed lid and base share no volume", shared < 1e-6,
              f"{shared:.4f} mm3")


def check_counts(rep, case):
    want = EXPECT[kind(case)]
    have = {"side notches": len(case._side_notch_frames()),
            "grip arcs": len(case.grip_arcs),
            "finger bays": len(case._bays()),
            "magnet-skirt pairs": len(case.magnets_skirt),
            "flat/pedestal pairs": len(case.magnets_flat)}
    for what, n in want.items():
        rep.check(f"{n} {what}", have[what] == n, f"found {have[what]}")
    extras = sorted({e for name in case.designs
                     for e in expected_extras(case, name)})
    rep.check("extras: " + (", ".join(extras) or "none"),
              sorted(case.extras) == extras and all(
                  list(case.extras_for(name)) == expected_extras(case, name)
                  for name in case.designs), f"found {list(case.extras)}")


def check_shell(rep, d):
    """Wall and corners, measured on the base's own cross-section."""
    drift = d.mesh_cavity.symmetric_difference(d.cavity).area
    rep.check("cavity as designed", drift < 1.0, f"{drift:.3f} mm2 off")
    thin = min(p.distance(d.mesh_outline.exterior)
               for p in ring_points(d.mesh_cavity, 0.3))
    rep.at_least("thinnest wall", thin, g.WALL_T)
    # a sharp wall corner poking into the cavity catches paper edges, and the
    # telescoping lids have to follow it: closing the outline must be a no-op
    blunt = (d.mesh_cavity.buffer(g.CORNER_BLEND_R, quad_segs=g.QS)
             .buffer(-g.CORNER_BLEND_R, quad_segs=g.QS))
    sharp = blunt.difference(d.mesh_cavity).area
    rep.check("cavity has no sharp re-entrant corner", sharp < 0.5,
              f"{sharp:.3f} mm2 filled by a {g.CORNER_BLEND_R:g} mm closing")


def openings(sec, cavity):
    """How many through-cuts open a wall/skirt ring in a cross-section: each
    one splits the ring, so the pieces count them — unless the ring is still
    closed around the cavity."""
    closed = any(Polygon(h).area > 0.5 * cavity.area
                 for p in polys(sec) for h in p.interiors)
    return 0 if closed else len(polys(sec))


def check_telescoping(rep, d):
    """Skirt clearance measured on the meshes, all round, at two heights; the
    windows (side notches low, scoops high) only ever read wider."""
    rep.near("skirt bottom rides above the table", d.lid.bounds[0][2],
             g.PLINTH, 1e-6)
    want = EXPECT[kind(d.case)]
    windows = want["side notches"] + (
        want["grip arcs"] if d.name == "magnet-skirt" else 0)
    found = openings(section(d.lid, g.PLINTH + 1.0), d.mesh_cavity)
    rep.check(f"{windows} grip windows in the skirt's bottom edge",
              found == windows, f"found {found}")
    found = openings(section(d.base, d.top - g.POCKET_DEPTH - 1.0),
                     d.mesh_cavity)
    rep.check(f"{want['grip arcs']} scoops through the base wall",
              found == want["grip arcs"], f"found {found}")
    for z in (g.PLINTH + g.NOTCH_H / 2.0, d.top - g.POCKET_DEPTH - 1.0):
        skirt = section(d.lid, z)
        gaps = [p.distance(skirt) for p in ring_points(section(d.base, z), 0.4)
                if p.distance(d.ext.exterior) < 0.02]  # the base's outer face
        facing = [x for x in gaps if x <= d.clear + 0.6]
        ok = (len(facing) > len(gaps) / 2
              and abs(min(gaps) - d.clear) <= TOL)
        rep.check(f"lid-to-base clearance all round at z={z:.1f}", ok,
                  f"min {min(gaps):.3f} mm (want {d.clear:.3f})")


def check_lip(rep, d):
    z = d.top - g.LIP_H / 2.0
    lip, rim = section(d.lid, z), section(d.base, z)
    rep.check("alignment lip inside the cavity",
              d.cavity.contains(lip) and lip.intersection(rim).area < 1e-9)
    gaps = [x for x in (p.distance(rim) for p in ring_points(lip, 0.3))
            if x < 3.0]  # the pry slot reads wider
    rep.near("lip clearance", min(gaps), g.LIP_CLEAR)


def pocket_holes(sec):
    """The magnet-pocket holes of a cross-section, picked by their area."""
    want = math.pi * (g.POCKET_D / 2.0) ** 2
    return [(Polygon(h), p) for p in polys(sec) for h in p.interiors
            if abs(Polygon(h).area - want) < 0.15 * want]


def check_pockets(rep, d):
    n = EXPECT[kind(d.case)]["magnet-skirt pairs" if d.name == "magnet-skirt"
                             else "flat/pedestal pairs"]
    roof = d.plate_t - g.POCKET_DEPTH
    in_base = pocket_holes(section(d.base, d.top - g.POCKET_DEPTH / 2.0))
    in_lid = pocket_holes(section(d.lid, d.top + g.POCKET_DEPTH / 2.0))
    rep.check("one pocket per magnet, base and lid",
              len(in_base) == n and len(in_lid) == n,
              f"{len(in_base)} + {len(in_lid)} for {n} pairs")
    # each pair coaxial, and where the layout says
    drift = max((min(hb.centroid.distance(hl.centroid) for hl, _ in in_lid)
                 + min(hb.centroid.distance(Point(c)) for c in d.centres)
                 for hb, _ in in_base), default=0.0) if in_lid else 99.0
    rep.check("pocket pairs coaxial", drift <= TOL, f"{drift:.4f} mm")
    # wall left around each pocket, to the cavity and to the outside
    skin = min((min([hole.distance(face.exterior)]
                    + [hole.distance(other) for other in face.interiors
                       if not Polygon(other).equals(hole)])
                for hole, face in in_base), default=0.0)
    rep.at_least("wall around the pockets", skin, MIN_SKIN)
    worst = [0.0, 0.0, True]
    for c in d.centres:
        below, above = hits(d.base, c), hits(d.lid, c)
        depth = d.top - below[-1] if below else 99.0
        lid_roof = above[-1] - above[-2] if len(above) > 1 else 99.0
        lid_depth = above[-2] - d.top if len(above) > 1 else 99.0
        worst[0] = max(worst[0], abs(depth - g.POCKET_DEPTH),
                       abs(lid_depth - g.POCKET_DEPTH))
        worst[1] = max(worst[1], abs(lid_roof - roof))
        worst[2] &= bool(inside(
            d.base, [[c[0], c[1], d.top - g.POCKET_DEPTH - 0.2]])[0])
    rep.check("pocket depth, base and lid", worst[0] <= 1e-3,
              f"off by {worst[0]:.3f} mm (want {g.POCKET_DEPTH:.1f})")
    rep.check("lid roof over the magnets", worst[1] <= 1e-3,
              f"off by {worst[1]:.3f} mm (want {roof:.1f})")
    rep.check("base pockets are blind", worst[2])


def check_recess(rep, d):
    """Magnet lids are thinned to LID_CORE_T over the cavity only — the rim
    (dust contact) keeps the full plate, the recess stays off the pockets."""
    case = d.case
    core = (case.interior.buffer(-2.0, quad_segs=g.QS)
            if d.name == "magnet-skirt" else d.cavity.buffer(
                -(g.LIP_CLEAR + g.LIP_T + 2.0), quad_segs=g.QS))
    p = core.representative_point()
    z = hits(d.lid, (p.x, p.y))
    rep.near("lid core thickness", z[-1] - z[-2], g.LID_CORE_T, 1e-3)
    # a rim point: mid-wall, away from pockets and grip windows
    ring = d.cavity.buffer(g.WALL_T / 2.0, quad_segs=g.QS).exterior
    busy = [Point(c) for c in d.centres] + [
        Point(arc.xy(arc.r)) for arc in case.grip_arcs]
    rim = max((ring.interpolate(t, normalized=True)
               for t in np.linspace(0.0, 1.0, 40, endpoint=False)),
              key=lambda q: min(q.distance(b) for b in busy))
    z = hits(d.lid, (rim.x, rim.y))
    rep.near("lid rim keeps the full plate", z[-1] - z[-2], g.LID_T_MAGNET,
             1e-3)
    gap = min(Point(c).buffer(g.POCKET_D / 2.0).distance(core)
              for c in d.centres)
    rep.check("recess clear of the pockets", gap > 1.0, f"{gap:.2f} mm")


def check_side_notches(rep, d):
    """Each bottom-edge grip notch sits on straight wall (inside and out) and
    opens the skirt onto solid base wall."""
    z = g.PLINTH + g.NOTCH_H / 2.0
    for (px, py), nrm in d.case._side_notch_frames():
        tx, ty = g.polar(1.0, nrm + 90.0)
        nx, ny = g.polar(1.0, nrm)
        bend = max(
            max(Point(px + t * tx, py + t * ty).distance(
                    d.case.interior.boundary),
                Point(px + t * tx + g.WALL_T * nx,
                      py + t * ty + g.WALL_T * ny).distance(d.ext.boundary))
            for t in np.linspace(-g.NOTCH_W / 2.0 - 1.0,
                                 g.NOTCH_W / 2.0 + 1.0, 25))
        wall = (px + nx * g.WALL_T / 2.0, py + ny * g.WALL_T / 2.0)
        mid = g.WALL_T + d.clear + g.SKIRT_T / 2.0
        skirt = (px + nx * mid, py + ny * mid)
        ok = (bend <= 0.05 and inside(d.base, [[*wall, z]])[0]
              and not inside(d.lid, [[*skirt, z]])[0]
              and inside(d.lid, [[*skirt, g.PLINTH + g.NOTCH_H + 2.0]])[0])
        rep.check(f"side notch at ({px:.0f}, {py:.0f}) on straight wall, "
                  "opens onto the base", ok, f"{bend:.3f} mm off straight")


def solid_spans(mesh, xy):
    z = hits(mesh, xy)
    return list(zip(z[0::2], z[1::2]))


def check_grip_arcs(rep, d):
    """At every grip arc: the scoop is a through-cut, so the skirt must cover
    it whenever the box is closed. On magnet-skirt the back notch below it
    may never reach the scoop — a solid band keeps the dust seal."""
    for arc in d.case.grip_arcs:
        where = f"arc at {arc.deg:.1f}°"
        wall = solid_spans(d.base, off_axis(arc, arc.r + g.WALL_T / 2.0))
        scoop_bottom = wall[0][1]
        rep.check(f"{where}: scoop cut through the wall",
                  len(wall) == 1 and scoop_bottom < d.top - 1.0,
                  f"wall solid to z={scoop_bottom:.2f}")
        r_in = arc.r + g.WALL_T + d.clear
        skirt = solid_spans(d.lid, off_axis(arc, r_in + g.SKIRT_T / 2.0))
        covers = any(z0 <= scoop_bottom + 1e-6 and z1 >= d.top
                     for z0, z1 in skirt)
        rep.check(f"{where}: skirt covers the scoop", covers)
        if d.name == "friction":
            rep.near(f"{where}: friction lid has no back notch",
                     skirt[0][0], g.PLINTH, 1e-6)
            continue
        # notch ceiling: highest at the skirt's inner face (the ramp drops
        # toward the outside, so it faces up when the lid prints flipped)
        inner = solid_spans(d.lid, off_axis(arc, r_in + 0.05))[0][0]
        outer = solid_spans(d.lid, off_axis(arc, r_in + g.SKIRT_T - 0.05))[0][0]
        rep.near(f"{where}: back notch height", inner,
                 g.PLINTH + g.ARC_NOTCH_H, 0.05)
        rep.check(f"{where}: notch ramp faces up in print",
                  outer <= inner and (g.ARC_NOTCH_CHAMFER == 0.0
                                      or outer < inner),
                  f"ceiling {outer:.2f} outside, {inner:.2f} inside")
        rep.at_least(f"{where}: solid band between notch and scoop",
                     scoop_bottom - inner, g.ARC_NOTCH_GAP)


def check_pry_slot(rep, d):
    """The flat lids' pry slot opens the rim, but the lip behind it keeps the
    dust out: lip present across the whole slot, and deeper than the slot."""
    arc = d.case.grip_arcs[0]
    r_wall = arc.r + (g.BAY_D if d.pedestal else 0.0)
    z = d.top - g.PRY_H / 2.0
    wx, wy = arc.xy(r_wall + g.WALL_T / 2.0)
    rep.check("pry slot opens the rim",
              not inside(d.base, [[wx, wy, z]])[0]
              and inside(d.base, [[wx, wy, d.top - g.PRY_H - 0.3]])[0])
    lip = section(d.lid, d.top - g.PRY_H - 0.1)  # just below the slot floor
    cx, cy = arc.xy(r_wall)
    nx, ny = g.polar(1.0, arc.deg)
    backed = lip is not None and all(
        any(lip.contains(Point(cx + t * arc.tangent[0] - s * nx,
                               cy + t * arc.tangent[1] - s * ny))
            for s in np.arange(0.1, 6.0, 0.1))
        for t in np.linspace(-g.PRY_W / 2.0, g.PRY_W / 2.0, 21))
    rep.check("lip backs the whole pry slot", backed)


def check_engraving(rep, d):
    text = d.case.text_geometry()
    box = shp_box(*text.bounds)
    near = min((box.distance(Point(c)) for c in d.centres), default=99.0)
    rep.check("engraving on the lid, clear of the pockets",
              box.within(d.cavity.buffer(-4.0)) and
              near >= g.POCKET_D / 2.0 + 2.0)
    glyph = max(polys(text), key=lambda p: p.area)
    p = glyph.buffer(-0.5).representative_point()
    z = hits(d.lid_engraved, (p.x, p.y))
    rep.near("engraving depth", d.top + d.plate_t - z[-1], g.ENGRAVE_DEPTH,
             1e-3)
    rep.at_least("plate left under the engraving", z[-1] - z[-2], 1.0)


def paper_shape(paper, rot, tab_corner=0):
    """True paper outline on its bisector `rot`; tab_corner = -1 / +1 adds the
    hanging tab at the low / high seam corner."""
    poly = g.sector_poly(paper.angle, paper.side, steps_per_deg=6.0)
    if tab_corner:
        tab = shp_box(paper.side - 4.0, -TAB_W / 2.0,
                      paper.side + paper.cfg["tab_extra"], TAB_W / 2.0)
        tab = tab.buffer(-3.0, quad_segs=24).buffer(3.0, quad_segs=24)
        at = tab_corner * (paper.angle / 2.0
                           - math.degrees((TAB_W / 2.0 + 1.0) / paper.side))
        poly = unary_union([poly, affinity.rotate(tab, at, origin=(0, 0))])
    return affinity.rotate(poly, rot, origin=(0, 0))


def seat(shape, rot, cavity):
    """Slide a paper along its bisector: (home, out) = the push range in which
    it lies inside the cavity — None if it never fits. Home is not 0: the
    sharp tip has to clear the filleted apex."""
    inside_, (dx, dy) = prep(cavity), g.polar(1.0, rot)
    fits = [t for t in np.arange(0.0, 30.0, 0.02)
            if inside_.contains(affinity.translate(shape, dx * t, dy * t))]
    return (fits[0], fits[-1]) if fits else None


def moved(shape, rot, t):
    dx, dy = g.polar(1.0, rot)
    return affinity.translate(shape, dx * t, dy * t)


def seated(paper, rot, cavity):
    """The plain sheet pushed home on bisector `rot`, or None if it won't fit."""
    shape = paper_shape(paper, rot)
    span = seat(shape, rot, cavity)
    return None if span is None else moved(shape, rot, span[0])


def reach_along(geom, deg):
    """How far from the apex a shape reaches along direction `deg`."""
    cut = LineString([(0.0, 0.0), g.polar(1000.0, deg)]).intersection(geom)
    return max(math.hypot(x, y) for part in getattr(cut, "geoms", [cut])
               for x, y in part.coords)


def check_papers(rep, case):
    for paper, rot in papers_of(case):
        corners = (0, -1, 1) if paper.cfg["tab_extra"] > 0.0 else (0,)
        for corner in corners:
            span = seat(paper_shape(paper, rot, corner), rot, case.interior)
            tab = {0: "", -1: " + tab low", 1: " + tab high"}[corner]
            rep.check(f"{paper.slug} sheet{tab} fits, seated home",
                      span is not None and span[1] - span[0] >= 1.0,
                      "no fit" if span is None else
                      f"home {span[0]:.2f}, {span[1] - span[0]:.2f} mm play")


def check_pedestal(rep, d):
    case = d.case
    ped_top = g.FLOOR_T + g.PEDESTAL_H
    p = case.plinth.buffer(-5.0).representative_point()
    rep.near("plinth top height", hits(d.base, (p.x, p.y))[-1], ped_top, 1e-3)
    # every paper's arc edge must overhang its moat at its own finger bay,
    # seated home (the worst case), by what a fingertip needs
    # (less 0.1: both edges are polygonal arcs)
    for arc, (paper, rot) in zip(case.grip_arcs, papers_of(case)):
        sheet = seated(paper, rot, case.interior)
        rep.at_least(f"{paper.slug} overhang at its finger bay",
                     reach_along(sheet, arc.deg)
                     - reach_along(case.plinth, arc.deg),
                     g.MOAT_W - g.RADIAL_SLACK - 0.1, 0.0)
    bays = [b for b in polys(d.mesh_cavity.difference(
        case.interior.buffer(0.3))) if b.area > 20.0]
    want = EXPECT[kind(case)]["finger bays"]
    rep.check(f"{want} finger bays bulge out of the cavity",
              len(bays) == want, f"found {len(bays)}")
    # foot chamfer: just above the floor nothing may poke through the walls
    low = section(d.base, g.FLOOR_T + 0.1)
    outline = unary_union([Polygon(q.exterior) for q in polys(low)])
    rep.check("plinth foot chamfer stays inside the cavity",
              outline.symmetric_difference(case.ext_ped).area < 1.0)
    # wall cove: just above the plinth top nothing may overhang moat or bay
    if g.PEDESTAL_CHAMFER_WALL > 0.0:
        cove = section(d.base, ped_top + min(0.1, g.PEDESTAL_CHAMFER_WALL / 2))
        stray = cove.intersection(d.cavity.buffer(-0.01)).difference(
            case.plinth.buffer(0.02))
        rep.check("wall cove stays on the plinth footprint",
                  stray.area < 0.01, f"{stray.area:.3f} mm2 outside")


# --------------------------------------------------------------------------
# checks — combo only: divider plate and tables
# --------------------------------------------------------------------------


def poses(paper, rot, cavity, tab_corner=0):
    """Everywhere a sheet can lie in the cavity: a pose grid (rotation about
    the apex + translation), filtered to what stays inside."""
    inside_ = prep(cavity)
    for turn in np.arange(-8.0, 8.1, 2.0):
        shape = paper_shape(paper, rot + turn, tab_corner)
        for dx in np.arange(-2.0, 30.0, 1.5):
            for dy in np.arange(-6.0, 30.0, 1.5):
                pose = affinity.translate(shape, dx, dy)
                if inside_.contains(pose):
                    yield pose


def check_divider_holes(rep, case):
    """One finger hole per paper zone: whichever stack lies on top, the hole
    in the OTHER paper's zone stays uncovered wherever the top sheets slide."""
    (far, far_rot), (fan, fan_rot) = papers_of(case)
    fan_hole, horn_hole = case.divider_holes
    for hole, label in ((fan_hole, "fan"), (horn_hole, "horn")):
        rep.at_least(f"{label} hole: plate left around it",
                     hole.distance(case.divider_outline.exterior),
                     g.DIVIDER_HOLE_LAND)
    for hole, label, paper, rot, corners in (
            (fan_hole, "fan", far, far_rot, (0,)),
            (horn_hole, "horn", fan, fan_rot, (0, -1, 1))):
        gap = min(hole.distance(pose) for corner in corners
                  for pose in poses(paper, rot, case.interior, corner))
        rep.at_least(f"{label} hole stays clear of every {paper.slug} pose",
                     gap, HOLE_GAP, 0.0)
    plate = case.build_divider()
    rep.check("plate watertight with both holes",
              plate.is_watertight and plate.euler_number == -2)


def check_table(rep, case, d):
    """The table standing in one design's base: feet on the floor, clear of
    base, lid and the sheets below, and hard to tip."""
    (far, far_rot), (fan, fan_rot) = papers_of(case)
    table = case.build_table(d.pedestal)
    table.apply_translation([0.0, 0.0, d.floor])
    rep.check("table watertight", table.is_watertight and table.volume > 0.0)
    rep.check("table clear of base and lid",
              overlap(table, d.base) < 1e-6 and overlap(table, d.lid) < 1e-6)
    rep.near("table top above the paper floor", table.bounds[1][2] - d.floor,
             g.DIVIDER_LEG_H + g.DIVIDER_T, 1e-6)
    legs = [Point(xy).buffer(g.DIVIDER_POST_D / 2.0, quad_segs=g.QS)
            for xy, _ in case.table_posts[d.pedestal]] + list(case.table_feet)
    # every leg must actually reach the floor it stands on (plinth or moat)
    gap = max(abs(hits(table, (q.x, q.y))[0] - hits(d.base, (q.x, q.y))[-1])
              for q in (leg.representative_point() for leg in legs))
    rep.check("every table leg touches its floor", gap <= 1e-6,
              f"worst gap {gap:.3f} mm")
    # the long paper lies under the table: seated home it clears every leg,
    # and the far feet still leave it radial play
    flush = (far.int_angle - far.angle) / 2.0  # turned against either wall
    sheets = [seated(far, far_rot + turn, case.interior)
              for turn in (-flush, 0.0, flush)]
    clear = min(sheet.distance(leg) for sheet in sheets if sheet is not None
                for leg in legs)
    rep.at_least(f"{far.slug} seated home clears the legs", clear,
                 g.DIVIDER_POST_GAP)
    shape = paper_shape(far, far_rot)
    home, out = seat(shape, far_rot, case.interior)
    feet = unary_union(case.table_feet)
    play = next((t for t in np.arange(home, out, 0.02)
                 if moved(shape, far_rot, t).distance(feet) < 1e-3), out) - home
    rep.at_least(f"{far.slug} radial play under the table", play,
                 g.DIVIDER_FAR_PLAY, 0.03)
    # statics: table + upper stack over the hull of the feet
    hull = MultiPoint([c for leg in legs
                       for c in leg.exterior.coords]).convex_hull
    stack = seated(fan, fan_rot, case.interior)
    m_table, com = table.volume * PLA_G_MM3, table.center_mass
    worst = 1e9
    for sheets in (0, 50, 100):
        m = stack.area * PAPER_G_MM2 * sheets
        c = Point((m_table * com[0] + m * stack.centroid.x) / (m_table + m),
                  (m_table * com[1] + m * stack.centroid.y) / (m_table + m))
        worst = min(worst, c.distance(hull.exterior)
                    if hull.contains(c) else -c.distance(hull.exterior))
    rep.at_least("centre of mass inside the feet, 0-100 sheets on top",
                 worst, COM_MARGIN)


def check_print_extras(rep, case):
    for name in case.extras:
        mesh = case.build_extra(name)
        flat = section(mesh, min(0.1, g.DIVIDER_T / 2.0))
        rep.check(f"{name}: watertight, top flat on the bed",
                  mesh.is_watertight and abs(mesh.bounds[0][2]) < 1e-9
                  and flat.area > 0.9 * case.divider_outline.area)


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------


def verify_paper(slug):
    """All checks of one paper -> (display name, rows)."""
    rep = Report()
    rep.scope = "case"
    try:
        case = g.make_case(slug)
    except Exception as e:  # a guard in generate.py fired
        rep.check("case builds", False, f"{type(e).__name__}: {e}")
        return g.PAPERS[slug]["display"], rep.rows
    rep.check("case builds", True)
    check_counts(rep, case)
    check_papers(rep, case)
    combo = hasattr(case, "divider_holes")
    if combo:
        check_divider_holes(rep, case)
        check_print_extras(rep, case)
    for name in case.designs:
        rep.scope = name
        try:
            d = Design(case, name)
            check_parts(rep, d)
            check_shell(rep, d)
            check_engraving(rep, d)
            if d.telescoping:
                check_telescoping(rep, d)
                check_side_notches(rep, d)
                check_grip_arcs(rep, d)
            else:
                check_lip(rep, d)
                check_pry_slot(rep, d)
            if d.magnets:
                check_pockets(rep, d)
                check_recess(rep, d)
            if d.pedestal:
                check_pedestal(rep, d)
            if combo:
                check_table(rep, case, d)
        except Exception as e:  # a broken part must fail, never crash the run
            rep.check("checks ran", False, f"{type(e).__name__}: {e}")
    return case.cfg["display"], rep.rows


def main(argv=None):
    own = argparse.ArgumentParser(add_help=False)
    own.add_argument("--paper", action="append", choices=list(g.PAPERS))
    own.add_argument("-v", "--verbose", action="store_true")
    opts, gen_args = own.parse_known_args(argv)
    if "-h" in gen_args or "--help" in gen_args:
        print(__doc__)
    g.apply_printer_args(gen_args)  # the overrides (also answers --help)
    missing = [m for m in ("rtree", "scipy", "networkx")
               if importlib.util.find_spec(m) is None]
    if missing:
        sys.exit(f"verify.py needs {', '.join(missing)}: pip install -r "
                 "requirements-dev.txt (`make verify` does it for you)")
    print(f"tolerances — {g.tolerance_summary()}")
    print(f"shell — {g.shell_summary()}")
    slugs = opts.paper or list(g.PAPERS)
    started = time.time()
    results = [verify_paper(slug) for slug in slugs]

    checks = failed = designs = 0
    for slug, (display, rows) in zip(slugs, results):
        print(f"\n=== {display} ({slug}) ===")
        for scope in dict.fromkeys(r[0] for r in rows):
            mine = [r for r in rows if r[0] == scope]
            bad = [r for r in mine if not r[2]]
            designs += scope != "case"
            print(f"  {scope:16s} {'FAIL' if bad else 'PASS'}  "
                  f"{len(mine) - len(bad)}/{len(mine)}")
            for _, name, ok, detail in (mine if opts.verbose else bad):
                print(f"      {'ok  ' if ok else 'FAIL'} {name}"
                      + (f" — {detail}" if detail else ""))
        checks += len(rows)
        failed += sum(not r[2] for r in rows)
    print(f"\nverify: {len(slugs)} papers, {designs} designs, {checks} checks "
          f"— {'ALL PASS' if not failed else f'{failed} FAILED'} "
          f"({time.time() - started:.0f} s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
