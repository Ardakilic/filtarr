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
    # optional: generate only some designs (default: all three)
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
  the default (all three) is right for most papers.
- Everything else (walls, lid clearances, magnets, scoop, engraving position)
  scales automatically from `side`/`angle` — the shared parameters live at the
  top of `generate.py` if a paper ever needs different treatment.

## 3. Generate and check

Runs inside Docker — no local Python needed:

```bash
make generate     # STLs + per-paper preview HTMLs
make docs         # README images into <folder>/docs/
```

Open the new preview in a browser and check with the **ghost paper stack**
toggle that the paper (cream) has visible slack to the walls in every
direction. `generate.py` prints each part's bounding box — make sure it fits
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
- Commit and push to `main` — the GitHub Pages site
  ([ardakilic.github.io/filtarr](https://ardakilic.github.io/filtarr/))
  republishes automatically, new folders included; nothing to configure.
