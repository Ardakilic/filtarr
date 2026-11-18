# How to add a new paper variant

Every case in this repo is generated from one registry entry in `generate.py`.
Adding a new filter paper takes one dict and one command — as long as its outline
is one of the shapes the generator knows (wedge, flat-bottom fan, disc).

## 1. Pick the shape and measure the paper

The box follows the outline of the paper as it lies in the pack. The PAPERS key
`"shape"` picks the outline (and the `Case` class that builds it):

| `shape` | Papers | Class |
|---|---|---|
| `"wedge"` (default, can be left out) | cone papers folded flat: V60, CAFEC Deep 27, Origami cone … | `Case` |
| `"trapezoid"` | flat-bottom fan papers: Kalita 101 / 102 / 103, Melitta-style 1x2 / 1x4 … | `TrapezoidCase` |
| `"round"` | flat paper discs: AeroPress … | `RoundCase` |

Pre-formed cups (Kalita Wave, basket filters) are none of these — they nest
instead of lying flat; see [RESEARCH.md](RESEARCH.md) for the planned boxes.

### Wedge (cone papers)

| Field | How to get it |
|---|---|
| `side` | Measure the **longest straight edge** from the tip, in mm — usually the crimped seam edge, which is ~10 mm longer than the plain folded edge. |
| `angle` | The wedge angle of the flat paper. If you know the dripper's cone angle **A** (full apex angle), the flat folded paper is `180 × sin(A/2)` degrees. V60 (60° cone) → 90°. Deep 27 (27° cone) → 42°. Or measure a photo. |
| `tab_extra` | Extra radial clearance in mm for the round hanging tab some brands put on the arc edge. The tab's *position* varies by brand, so we widen the whole interior radially — one box then fits every brand. Papers without tabs: `0`. Typical tab: `5`. |

Sanity check: the width across the wide-end corners should be
`2 × arc_radius × sin(angle/2)`, where `arc_radius ≈ side − seam excess (~10 mm)`.
Compare with a ruler or the product photos.

### Trapezoid (flat-bottom fan papers)

Lay one sheet flat and measure three things:

| Field | How to get it |
|---|---|
| `width` | the **top chord** `c`: straight across the arc, corner to corner |
| `height` | the **centre height** `h`: from the bottom edge to the top of the arc, along the centre line |
| `bottom` | the **bottom edge** `b`: the straight crimped seam at the narrow end |
| `variants` (optional) | `((width, height, bottom), ...)` of other real sheets the box must also hold — other brands or batches. The box is sized to fit every one, and `make verify` seats each one (≥ 1 mm of play and of clearance to the walls, corners on the flat bottom wall, pedestal overhang). |

`width` / `height` / `bottom` describe one **reference** sheet — typically the
largest of the size. `fan_solve()` derives the fan angle, arc radius and
virtual-apex distance from it (and raises a clear error if the three numbers
can't belong to one flat fan: `height` must exceed `√(width² − bottom²) / 2`);
that angle, plus the usual 3° slack, is the box's. Add every **other** sheet
you want to hold as a `variants` entry — don't take the max of each
measurement over several brands: the angle depends on all three numbers, so
a made-up "max" sheet matches no real one. A variant may be larger than the
reference in one dimension (a wider bottom, a longer chord). The box is then
sized over all of them: the **widest bottom edge** sets the flat bottom wall
(pushed home, every sheet's crimped edge rests on its flat part, the widest
one's corners `TRAP_SIDE_CLEAR` (2 mm) square to the side walls), the sheet
reaching **farthest** sets the arc (`RADIAL_SLACK`, 3.5 mm beyond it — usually
the tallest), and the **shortest** one the pedestal moat (it still overhangs by
11.5 mm). Fan papers have no
hanging tab: `tab_extra` is `0.0`; `side` / `angle` are rejected.

### Round (paper discs)

| Field | How to get it |
|---|---|
| `diameter` | the **largest disc** the box must hold, in mm — size it to the biggest real sheet, not the spec (AeroPress: spec Ø63.5, listings up to Ø65 → `65.0`). The bore adds `DISC_SLACK` (1 mm) all round. |
| `stack_h` (optional) | height of a typical pack, mm — only drives the preview's ghost stack (never more than `depth − 4`). |

`side`, `angle` and `tab_extra` are rejected. For the depth, remember that the
flat lids' 2.5 mm alignment lip comes down over the disc edges in a close round
bore: worst-case stack + 2.5 + a few mm of margin.

### Depth (every shape)

| Field | How to get it |
|---|---|
| `depth` (optional) | Interior depth in mm; default 42. Measure a loose pack (or use the pouch thickness) and add ~5 mm so papers are never squeezed. Smooth papers (Hario) stack ~32 mm per 100 → the default fits; creped papers (CAFEC) stay near their pouch thickness → 47–54 mm; Kalita → 58; AeroPress 350-pack → 55. |

## 2. Add the registry entry

In `generate.py`, add to `PAPERS`. These are three of the real entries — copy
the one with your shape:

```python
"v60-cafec-02": {                      # wedge (no "shape" key needed)
    "display": "CAFEC cone cup 4 (V60-02 size, tabless)",  # preview, index, docs
    "folder": "v60",                   # output directory (created if missing)
    "side": 127.0,
    "angle": 90.0,
    "tab_extra": 0.0,
    "depth": 54.0,                     # optional, default DEPTH (42)
    # optional: generate only some designs (default: all four)
    # "designs": ("friction",),
},
"kalita-102": {
    "display": "Kalita 102 (FP102 / NK102)",
    "folder": "kalita",
    "shape": "trapezoid",
    "width": 165.0,                    # reference sheet: top chord,
    "height": 105.0,                   #   centre height,
    "bottom": 53.0,                    #   crimped bottom edge (-> angle)
    "variants": ((160.0, 100.0, 44.0), (160.0, 100.0, 50.0),  # other sheets
                 (160.0, 105.0, 47.0),    # Melitta 1x2
                 (165.0, 103.0, 54.0)),   # Brooks 102
    "tab_extra": 0.0,
    "depth": 58.0,
},
"aeropress-xl": {
    "display": "AeroPress XL",
    "folder": "aeropress",
    "shape": "round",
    "diameter": 75.0,                  # largest disc to hold
    "depth": 35.0,
    "stack_h": 25.0,                   # preview ghost: a typical 200-pack
},
```

Notes:
- The key (`kalita-102`) becomes the STL filename prefix and the preview name.
  If the key equals `folder`, the preview is `<folder>/preview.html`; otherwise
  `<folder>/preview-<rest>.html` (e.g. `v60/preview-01.html`,
  `kalita/preview-102.html`, `aeropress/preview-xl.html`).
- Multiple papers can share a folder (see the `v60-*`, `kalita-*` and
  `aeropress*` entries). A **new** folder also needs a line in the Makefile
  `clean` target — the only hard-coded folder list.
- `designs` restricts which case designs are generated, e.g. `("friction",)` —
  the default (all four) is right for most papers. The `magnet-pedestal` design
  derives everything (bay, moat, +8 mm height) from the same entry.
- Everything else (walls, lid clearances, magnets, scoop, engraving position)
  is derived automatically from the entry — the shared parameters live at the
  top of `generate.py`, the shape-specific ones (`TRAP_*`, `DISC_SLACK`,
  `ROUND_*`) at the top of their class's section.
- `engrave_rot` (optional, degrees) turns the lid engraving. The default `-90`
  keeps the house rule — upright when the wedge tip (or the Kalita box's flat
  bottom end) points at you; `0` puts the baseline along +X. Only the combo box
  sets it.

What each shape gets:

- **Wedge**: magnet-skirt 4 pairs (2 on the arc, 1 per side), flat/pedestal 3
  pairs (tip + both arc corners), two side grip notches.
- **Trapezoid**: magnet-skirt 4 pairs, flat/pedestal 4 pairs (one per corner:
  both bottom corners + both arc corners), two side grip notches placed just
  past the bottom-corner fillets, a pedestal moat widened so the shortest
  listed sheet still overhangs it by 11.5 mm.
- **Round**: magnet-skirt 3 pairs in lobes at 60° / 180° / 300°, flat/pedestal
  3 pairs at 120°, so the skirt and flat lids fit in three orientations (glue
  the base magnets same pole up; the pedestal lid is keyed by its bay); the
  friction lid is twist-off with no grip notches, the magnet-skirt lid has
  side notches at ±120° plus the back thumb notch; a D-shaped pedestal whose
  wall cove is capped at `DISC_SLACK` − 0.2 (0.8 mm) so the largest discs lie
  flat; a scoop 0.75 × as wide (27 mm) and a narrower engraving.

### A new shape

`make_case(slug)` builds every case: it returns a `ComboCase` for `combines`
entries and otherwise the class registered for the entry's `shape` in
`CASE_CLASSES` (`{"wedge": Case, "trapezoid": TrapezoidCase, "round":
RoundCase}`); an unknown shape raises a clear `ValueError`. A new shape is a
`Case` subclass that overrides `_derive_paper_geometry()` (it must set `r_int`,
`depth`, `interior`, `engrave_xy` and `grip_arcs`) plus whichever layout hooks
differ (`_side_notch_frames`, `_skirt_magnet_centres`, `_flat_magnet_centres`,
`_plinth`, `scoop_w`, `engrave_width`, `lid_notch_cutters`, `paper_ghost`, the
wording properties), runs its guards from its own `_check()`, and registers
with one line after the class: `CASE_CLASSES["<shape>"] = <ShapeCase>`.
`tools/verify.py` then needs that kind's block in its PER-KIND TABLES section
(`EXPECT`, `PAPER_SHAPES`, `SIDE_NOTCH_WALL`, `PEDESTAL_OVERHANG`,
`CASE_CHECKS`, `DESIGN_CHECKS`) — a missing entry doesn't stop the run: it
fails with a "checks ran" row naming the missing table entry. The existing papers must stay byte-identical: see the hash gate
in CLAUDE.md.

### One box for two papers (`combines`)

Instead of `side` / `angle` / `tab_extra`, an entry can name two existing
**wedge** papers — the box then holds either of them, or both at once with a
divider:

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
two different slugs, both plain (non-combo) wedge entries that exist in
`PAPERS` (a trapezoid or round member is rejected), and the longer paper must
also be the narrower one — otherwise its own box
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

Code that builds cases should call `make_case(slug)` — it returns the right
class for the entry (`Case("combo")` itself fails; combo, trapezoid and round
cases have no `side` / `angle` of their own, and a combo has no
`paper_ghost()` — use
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
bands, that the paper outline (tab included) fits when pushed home — for a
trapezoid entry every sheet in `variants` too (corners on the flat bottom
wall, overhang at the pedestal's bay), for a round one the disc play and that
the largest disc lies flat on the pedestal — the pedestal overhang — plus,
for `combines` entries, the divider holes and both tables. It exits non-zero on any FAIL. Useful while iterating:
`make verify GEN_ARGS="--paper kalita-102"` (repeatable) limits it to your
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
- a fan paper's crimped bottom edge lies against the flat bottom wall without
  its corners catching,
- papers are easy to pick out.

Then print the matching lid.

## 5. Publish

- Update the README by hand: add a row to the supported-papers table and an
  entry (render image + live preview link) to the gallery.
- `make verify` passes (see step 3).
- Commit and push to `main` — the GitHub Pages site
  ([ardakilic.github.io/filtarr](https://ardakilic.github.io/filtarr/))
  republishes automatically, new folders included; nothing to configure.
