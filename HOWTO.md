# How to add a new paper variant

Every case in this repo is generated from one registry entry in `generate.py`.
Adding a new filter paper takes one dict and one command.

## 1. Work out the paper's flat geometry

You need three numbers for the flat, folded paper (as it comes out of the pack):

| Field | How to get it |
|---|---|
| `side` | Measure the **longest straight edge** from the tip, in mm — usually the crimped seam edge, which is ~10 mm longer than the plain folded edge. |
| `angle` | The wedge angle of the flat paper. If you know the dripper's cone angle **A** (full apex angle), the flat folded paper is `180 × sin(A/2)` degrees. V60 (60° cone) → 90°. Deep 27 (27° cone) → 42°. Or measure a photo. |
| `tab_extra` | Extra radial clearance in mm for the round hanging tab some brands put on the arc edge. The tab's *position* varies by brand, so we widen the whole interior radially — one box then fits every brand. Papers without tabs: `0`. Typical tab: `5`. |
| `depth` (optional) | Interior depth in mm; default 42. Measure a loose 100-stack (or use the pouch thickness) and add ~5 mm so papers are never squeezed. Smooth papers (Hario) stack ~32 mm per 100 → the default fits; creped papers (CAFEC) stay near their pouch thickness → 47–54 mm. |

Sanity check: the width across the wide-end corners should be
`2 × arc_radius × sin(angle/2)`, where `arc_radius ≈ side − seam excess (~10 mm)`.
Compare with a ruler or the product photos.

## 2. Add the registry entry

In `generate.py`, add to `PAPERS`:

```python
"kalita-185": {
    "display": "Kalita Wave 185",      # shown in the preview, Pages index, doc images
    "folder": "kalita",                # output directory (created if missing)
    "side": 130.0,
    "angle": 90.0,
    "tab_extra": 0.0,
    # optional: interior depth override for lofty (creped) papers, mm
    # "depth": 47.0,
    # optional: generate only some designs (default: all four)
    # "designs": ("friction",),
},
```

Notes:
- The key (`kalita-185`) becomes the STL filename prefix and the preview name.
  If the key equals `folder`, the preview is `<folder>/preview.html`; otherwise
  `<folder>/preview-<rest>.html` (e.g. `v60/preview-01.html`,
  `v60/preview-cafec-01.html`).
- Multiple papers can share a folder (see the `v60-*` entries).
- `designs` restricts which case designs are generated, e.g. `("friction",)` —
  the default (all four) is right for most papers. The `magnet-pedestal` design
  derives everything (bay, moat, +8 mm height) from the same entry.
- Everything else (walls, lid clearances, magnets, scoop, engraving position)
  scales automatically from `side`/`angle` — the shared parameters live at the
  top of `generate.py` if a paper ever needs different treatment.
- `engrave_rot` (optional, degrees) turns the lid engraving. The default `-90`
  keeps the house rule — upright when the wedge tip points at you; `0` puts the
  baseline along +X. Only the combo box sets it.

### One box for two papers (`combines`)

Instead of `side` / `angle` / `tab_extra`, an entry can name two existing
papers — the box then holds either of them, or both at once with a divider:

```python
"combo": {
    "display": "Combo — CAFEC Deep 27 + V60 01",
    "folder": "combo",
    "combines": ("deep27", "v60-01"),  # slugs of two entries above
    "engrave_rot": 0.0,                # text along the long shared wall
    # optional: "depth" (default: the deeper of the two), "designs"
},
```

What you get (`ComboCase` in `generate.py`; everything is placed automatically):

- Both wedges are overlaid on the same tip against **one shared straight wall**
  (the +X axis; both open counter-clockwise from it) — an asymmetric keyhole.
  Each paper is sized with its own slack formula (same angular slack and
  radius as its dedicated box), and re-measuring one of the referenced papers
  updates the combo too.
- The **longer** paper becomes the far arc; **both** arcs (the far arc and the
  exposed part of the wide paper's arc) carry the mid-arc grips — a scoop each
  on the telescoping bases, a thumb notch each on the magnet-skirt lid, a
  finger bay each on the pedestal (the flat lids' pry slot stays on the far
  arc only). The telescoping lids get three bottom-edge grip notches: one on
  each wall next to the tip and one on the long end's flat inner wall. The
  flat/pedestal lids get one magnet pair per convex corner (4 pairs); the
  pedestal gets one moat per paper; the engraving is centred on the lid.
- Extra STLs for storing both papers at once (users print one):
  `<paper>-case-divider.stl`, a loose plate (short/wide paper on the floor,
  plate, long/narrow paper on top), and `<paper>-case-divider-table.stl` /
  `-divider-table-pedestal.stl`, the same top on legs with the OPPOSITE order
  (long/narrow paper on the floor, short/wide paper on the table — legs can
  only stand where no paper lies). Both have a finger hole in each paper's
  own zone. Which extras go with which design comes from
  `case.extras_for(design)`; the preview's print panel lists them under
  `case.extras_title`.

Constraints, each raising a clear `ValueError`: `combines` must name exactly
two different slugs, both plain (non-combo) entries that exist in `PAPERS`,
and the longer paper must also be the narrower one — otherwise its own box
already holds both. Further guards catch magnet pockets that would break into
the cavity, grip notches off their wall, a degenerate pedestal, divider
finger holes outside their zone or without enough plate around them, table
legs that enter the long paper's wedge / foul a scoop, bay or the pedestal
chamfer, and engraving that runs off the lid.

In a combo each paper has a little more lengthwise play than in its own box
(~8–9.5 mm instead of 3.5 mm: the shared tip is the wider paper's, blunter
one) — the pedestal moats and the preview ghosts already account for papers
pushed home into that tip. The dividers' top thickness, wall gap and the
table's leg height are flags (`--divider-t`, `--divider-clear`,
`--divider-leg-h`).

Code that builds cases should call `make_case(slug)` — it returns a `Case` or
a `ComboCase` depending on the entry (`Case("combo")` itself fails, and a
combo has no `side` / `angle` / `paper_ghost()` of its own — use
`ghosts(design)` and the `paper_txt` / `interior_txt` / `geo_txt` wording
properties). Preview contents are **scenes**: `case.scenes` lists named sets
of ghost parts and `case.default_scene` picks the one shown first — a plain
paper has one scene (the on/off "Ghost paper stack"), the combo has four
(each paper alone, both with the loose plate, both with the table).

## 3. Generate and check

Runs inside Docker — no local Python needed:

```bash
make generate     # STLs + per-paper preview HTMLs
make docs         # README images into <folder>/docs/
make verify       # geometry self-test — must print PASS for every row
```

Printer-fit tolerances (lid clearances, magnet pockets) can be overridden per
run without touching code: `make generate GEN_ARGS="--clear-friction 0.32"` —
see README → Fit tuning for the full flag list.

**`make verify`** (`tools/verify.py`) loops over `PAPERS`, so your new entry is
covered automatically — nothing to register. It rebuilds every paper × design
in memory and checks what a watertight mesh can still get wrong: closed lid
vs base interference, lid clearances, magnet pockets (count, depth, roof,
alignment, wall around them), minimum wall, notches and scoop dust-seal
bands, that the paper outline (tab included) fits when pushed home, the
pedestal overhang — plus, for `combines` entries, the divider holes and both
tables. It exits non-zero on any FAIL. Useful while iterating:
`make verify GEN_ARGS="--paper kalita-185"` (repeatable) limits it to your
paper, and the same override flags as `generate.py` verify a tuned build.
Run it after `make` and **before committing**.

Open the new preview in a browser and check with the **ghost paper stack**
toggle that the paper (cream) has visible slack to the walls in every
direction (a combo preview has a scene picker instead: each paper alone, or
both with either divider). `generate.py` prints each part's bounding box — make sure it fits
your printer bed. The landing page (`index.html`) picks the new paper up
automatically, including its render image and STL download links.

## 4. Verify with a real paper before publishing

Papers differ between brands and batches (the V60 community re-learned this
many times). Print just the **base** of one design, drop a real stack of
papers in, and confirm:

- papers lie flat with a few mm of wiggle in every direction,
- the tab (if any) doesn't touch the wall,
- papers are easy to pick out.

Then print the matching lid.

## 5. Publish

- Update the README by hand: add a row to the supported-papers table and an
  entry (render image + live preview link) to the gallery.
- `make verify` passes (see step 3).
- Commit and push to `main` — the GitHub Pages site
  ([ardakilic.github.io/filtarr](https://ardakilic.github.io/filtarr/))
  republishes automatically, new folders included; nothing to configure.
