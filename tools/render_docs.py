#!/usr/bin/env python3
"""Render the README images (<folder>/docs/renders[-XX].png and
engraving[-XX].png) for every paper in the registry. Software renderer via
matplotlib — no GPU/browser needed.

Usage:  python3 tools/render_docs.py
"""

import os
import types

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load_generator():
    """Import generate.py without running its main()."""
    mod = types.ModuleType("gen")
    path = os.path.join(ROOT, "generate.py")
    code = open(path).read().replace('if __name__ == "__main__":\n    main()', "")
    mod.__dict__["__file__"] = path
    exec(compile(code, path, "exec"), mod.__dict__)
    return mod


def show(ax, meshes_cols, elev=25, azim=-55):
    """Flat-shaded render with global painter depth sort."""
    tris, cols = [], []
    light = np.array([0.35, -0.45, 0.82])
    light /= np.linalg.norm(light)
    for mesh, color in meshes_cols:
        v, f = trimesh.remesh.subdivide_to_size(
            mesh.vertices.astype(np.float64), mesh.faces, max_edge=12.0)
        m = trimesh.Trimesh(v, f)
        tri = m.vertices[m.faces]
        shade = 0.5 + 0.5 * np.clip(m.face_normals.astype(np.float64) @ light, 0, 1)
        rgb = np.array(matplotlib.colors.to_rgb(color))
        tris.append(tri)
        cols.append(np.clip(shade[:, None] * rgb[None, :], 0, 1))
    tri, col = np.concatenate(tris), np.concatenate(cols)
    e, a = np.radians(elev), np.radians(azim)
    view = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    order = np.argsort(tri.mean(axis=1).astype(np.float64) @ view)
    ax.add_collection3d(
        Poly3DCollection(tri[order], facecolors=col[order], edgecolors="none"))
    lo, hi = tri.reshape(-1, 3).min(0), tri.reshape(-1, 3).max(0)
    c, r = (lo + hi) / 2, (hi - lo).max() / 2 * 0.92
    ax.set_xlim(c[0] - r, c[0] + r)
    ax.set_ylim(c[1] - r, c[1] + r)
    ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1))
    ax.set_proj_type("ortho")
    ax.set_axis_off()
    ax.view_init(elev=elev, azim=azim)


GRAY, STEEL = "#9aa2ad", "#dfe3e8"
TITLES = {"friction": "Friction fit", "magnet-skirt": "Magnetic (skirt)",
          "magnet-flat": "Magnetic (flat lid)",
          "magnet-pedestal": "Magnetic (pedestal)"}


def lift(m, dz):
    c = m.copy()
    c.apply_translation([0, 0, dz])
    return c


def suffix_for(g, case):
    return "" if case.cfg["folder"] == case.slug else "-" + case.short


def render_grid(g, case, out_path):
    n = len(case.designs)
    fig = plt.figure(figsize=(5 * n, 9), dpi=130)
    for col, design in enumerate(case.designs):
        pedestal = design == "magnet-pedestal"
        base = case.build_base(design)
        lid = case.build_lid(design)
        # the preview's default contents scene
        shown = next(sc["parts"] for sc in case.scenes
                     if sc["name"] == case.default_scene)
        ghosts = [(gh["mesh"], gh["color"]) for gh in case.ghosts(design)
                  if gh["name"] in shown]
        color = g.LID_COLORS[design]
        closed = [(base, GRAY), (lid, color)]
        lifted = [(base, GRAY)] + ghosts + [(lift(lid, 70), color)]
        if design.startswith("magnet"):
            centres = (case.magnets_skirt if design == "magnet-skirt"
                       else case.magnets_flat)
            mb, ml = case.magnet_ghosts(
                centres, case.base_h_ped if pedestal else None)
            lifted += [(mb, STEEL), (lift(ml, 70), STEEL)]
        ax = fig.add_subplot(2, n, col + 1, projection="3d")
        show(ax, closed)
        ax.set_title(f"{TITLES[design]} — closed", fontsize=11)
        ax = fig.add_subplot(2, n, col + 1 + n, projection="3d")
        show(ax, lifted)
        ax.set_title(f"{TITLES[design]} — lid lifted", fontsize=11)
    fig.suptitle(case.cfg["display"], fontsize=14, y=0.99)
    fig.patch.set_facecolor("white")
    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print("saved", out_path)


def render_engraving(g, case, out_path):
    """Crisp 2D top view of the flat lid, in the reader's orientation. By
    default (engrave_rot -90) the box's +X end — the arc with the scoop /
    pry slot — points away from the reader, so the wedge tip, the fan's flat
    bottom wall or a round box's far side faces them: world (x, y) -> view
    (h, v) = (-y, x); papers engraved along +X (engrave_rot 0, the combo) are
    shown as modelled."""
    fig, ax = plt.subplots(figsize=(8, 6), dpi=130)

    def view(xy):
        xs, ys = np.asarray(xy[0]), np.asarray(xy[1])
        if case.engrave_rot == 0:
            return xs, ys
        return -ys, xs

    def plot_poly(poly, **kw):
        for p in (poly.geoms if hasattr(poly, "geoms") else [poly]):
            ax.plot(*view(p.exterior.xy), **kw)
            for hole in p.interiors:
                ax.plot(*view(hole.xy), **kw)

    has_flat = "magnet-flat" in case.designs
    if has_flat:
        outline, lid_name = case.ext_flat, "flat lid"
    else:
        outline = case.ext_plain.buffer(g.CLEAR_FRICTION + g.SKIRT_T)
        lid_name = "friction lid"
    plot_poly(outline, color="#5f8cc4", lw=2)
    plot_poly(case.interior, color="#b8c4d4", lw=1, ls="--")
    text = case.text_geometry()
    for p in (text.geoms if hasattr(text, "geoms") else [text]):
        ax.fill(*view(p.exterior.xy), color="#2b4a6f")
        for hole in p.interiors:
            ax.fill(*view(hole.xy), color="white")
    if has_flat:
        for cx, cy in case.magnets_flat:
            h, v = view((cx, cy))
            ax.add_patch(plt.Circle((float(h), float(v)), g.POCKET_D / 2,
                                    fill=False, color="#8896a8", lw=1.2))
    ax.set_aspect("equal")
    ax.set_title(f'"{g.ENGRAVE_TEXT}" engraving — {g.ENGRAVE_DEPTH} mm deep, '
                 f"{lid_name}, {case.cfg['display']} (mm)", fontsize=11)
    ax.grid(alpha=0.25)
    fig.patch.set_facecolor("white")
    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print("saved", out_path)


def main():
    g = load_generator()
    for slug in g.PAPERS:
        case = g.make_case(slug)
        docs = os.path.join(case.out_dir, "docs")
        os.makedirs(docs, exist_ok=True)
        sfx = suffix_for(g, case)
        render_grid(g, case, os.path.join(docs, f"renders{sfx}.png"))
        render_engraving(g, case, os.path.join(docs, f"engraving{sfx}.png"))


if __name__ == "__main__":
    main()
