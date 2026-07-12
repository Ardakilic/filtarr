# CLAUDE.md — Filtarr

Parametric 3D-printed storage boxes for pour-over filter papers (project/brand name:
**Filtarr**). Everything (STLs, previews, index.html, README images) is **generated
from Python** — never edit STLs or generated HTML by hand; change `generate.py` and
regenerate.

Remote: `github.com/Ardakilic/filtarr` (public). GitHub Pages
(`ardakilic.github.io/filtarr`) republishes the whole checkout — index.html +
previews + STLs — on every push to `main` via `.github/workflows/pages.yml`
(configure-pages/upload-pages-artifact/deploy-pages; Pages source = Actions).
License: dual — MIT for code (`LICENSE`), CC BY 4.0 for models/images
(`LICENSE-MODELS`).

## Layout

```
generate.py                  shared engine: PAPERS registry + Case class + export/preview
                             + build_index() -> index.html (Pages landing page)
preview_template.html        template for the self-contained 3D previews
Makefile / Dockerfile        canonical build path: everything runs in Docker
.github/workflows/pages.yml  publishes the whole checkout to GitHub Pages on push to main
tools/render_docs.py         README image renderer (matplotlib, loops all papers)
tools/fetch_three.py         downloads latest three.module.min.js + three.core.min.js
vendor/                      both three.js files + THREE_VERSION (committed)
LICENSE / LICENSE-MODELS     MIT (code) / CC BY 4.0 (models & images)
HOWTO.md                     how to add a new paper variant (keep in sync with PAPERS)
index.html                   generated Pages landing page — never edit by hand
deep27/                      CAFEC Deep 27 outputs: stl/, docs/, preview.html
v60/                         V60 outputs: 01, 02, cafec-01, cafec-02 (stl/, docs/, preview-*.html)
```

Per design: 3 STLs (base / lid / lid-engraved), named
`<paper>-case-<design>-<part>.stl`. Design keys: `friction | magnet-skirt |
magnet-flat` (also the preview tab keys). A PAPERS entry may restrict designs
via `"designs": (...)`; currently all five papers ship all three designs (the
CAFEC entries were friction-only briefly — the user asked for all three).

## Commands

The canonical build is Docker-based (validated: image `python:3-slim` = latest
Python 3 on Debian slim, per docker-library docs; Dockerfile adds
fonts-liberation + pip requirements):

```bash
make              # generate + docs
make generate     # all papers -> stl + previews + index.html (builds image first)
make docs         # -> <folder>/docs/*.png
make vendor       # refresh both three.js files in vendor/ to the latest release
make image        # (re)build the filtarr-build Docker image only
make clean        # delete generated outputs
open deep27/preview.html   # interactive check (Safari is the only browser)
```

For dev-only verification (ray casts need rtree+scipy, not in requirements.txt):
`python3 -m venv .venv && .venv/bin/pip install -r requirements.txt rtree scipy`.

## Technology decisions (and why)

- **Python mesh stack, not OpenSCAD**: OpenSCAD is not installed on this machine.
  Geometry = 2D outlines in **shapely** (buffers give fillets for free) extruded with
  **trimesh** (`extrude_polygon`, needs `mapbox_earcut`), booleans via **manifold3d**.
- **2.5D construction**: every part is built in "closed box world coordinates"
  (wedge apex at the origin, opening along +X, z = 0 at the table) from vertical
  prisms and cutters; lids are flipped into print orientation
  (`print_orientation_lid`) only at export. Previews use world orientation.
- **Per-paper scaling**: paper-specific geometry lives in the `Case` class, driven by
  a `PAPERS` registry entry (side / angle / tab_extra). Positions that must scale
  with box size are fractions of R_INT (`MAG_SIDE_FRAC`, `NOTCH_FRAC`,
  `ENGRAVE_POS_FRAC`); absolute sizes (walls, pockets, scoop) are shared constants.
- **Docker as canonical build**: the Dockerfile (`python:3-slim`, Debian slim —
  chosen per docker-library/python guidance: pre-built wheels, small image) installs
  requirements + `fonts-liberation`. All wheels (manifold3d, shapely, matplotlib…)
  have linux/arm64 builds, so it works under Apple-Silicon Docker.
- **Engraving**: text outlines from `matplotlib.textpath.TextPath` (hence matplotlib
  in requirements), glyph holes assembled via `symmetric_difference` over rings.
  `FONT_CANDIDATES` order: Arial Bold (macOS/Windows) → Liberation Sans Bold (the
  Docker image's metric-compatible Arial substitute — the canonical output) →
  regular weights. Gotcha: `FontProperties(family="sans-serif")` must be
  `family=["sans-serif"]` (a bare string is parsed as a fontconfig pattern → crash).
- **Previews are fully self-contained** (~4–9 MB each): the latest three.js
  **ES-module** build (UMD was dropped after r160) is base64-embedded in
  `<script type="text/plain">` blocks and loaded at runtime via **blob dynamic
  imports** — no import maps, works offline from `file://` in Safari/Chrome/
  Firefox. CRITICAL gotcha (caused a black page once): since r167 the module
  build is split into `three.module.min.js` + `three.core.min.js`, and the module
  does `import ... from "./three.core.min.js"` — a relative specifier cannot
  resolve from a blob URL, so `boot()` first blobs the core, then string-replaces
  every `./three.core.min.js` in the module source with the core's blob URL
  before importing. `tools/fetch_three.py` downloads BOTH files. Meshes are
  base64 binary STL parsed by ~20 lines of JS. Why embedded: `file://` fetch is
  CORS-blocked and this machine has no Chrome, only Safari. Custom orbit controls
  (no addons in the module core). Light intensities are on the r155+ physical
  scale (~π × the pre-r155 values) — don't copy old three.js examples'
  intensities. Template placeholders: `/*__THREE_B64__*/`,
  `/*__THREE_CORE_B64__*/`, `/*__DATA__*/null`; title/subtitle via `DATA.title`;
  variant tabs are built dynamically from `DATA.variants` keys (papers can have a
  designs subset); `DATA.print` drives the "Print these two" panel — download
  links to the exact STL files (+ magnet count) for the selected variant and
  engraving toggle (engraving is ON by default).
  Smoke-test embedded payloads without a browser: extract both b64 blocks from a
  generated preview, write them side by side, `node -e "import('./three.module.min.js')"`.
- **Verification without a browser/GPU** (no headless Chrome for screenshots):
  - watertight assert + volume/bounding printout in `generate.py`
  - `trimesh` ray casts for depths/clearances (needs `rtree` + `scipy`, dev-only)
  - `tools/render_docs.py` matplotlib software renders (global painter sort +
    `subdivide_to_size`, else triangles overdraw wrongly)
  - quick 2D shapely outline plots for footprint questions — far cheaper than 3D
  - `node --check` on the script extracted from a generated preview for JS syntax

## Verified paper geometry (do not re-derive)

Cone with full apex angle A → flat sector `360·sin(A/2)`° → folded wedge
`180·sin(A/2)`°.

- **Deep 27**: 27° cone → 42.02° wedge (photo-confirmed 42.7°±1°). Side 155 mm
  (user-measured), arc wide end R≈155 about the tip, ~8 mm crimp seam on one edge,
  **no tab**. 100-pack pouch 205×160×40 mm ≈ the true free stack → depth 47.
- **100-pack stack heights** (researched; drive per-paper `depth`, user rule:
  papers must never be squeezed): single ply 206–210 µm (coffeeadastra caliper
  data), folded filter = 2 plies. Smooth Hario paper nests when stacked:
  ~32 mm/100 measured → depth 42 (default). CAFEC one-sided crepe does NOT nest:
  a 100-stack ≈ its pouch thickness — Deep 27 & cup 1 pouches 40 mm → depth 47;
  cup 4 pouch 50 mm → depth 54. The crimp seam lofts one side; flipping half the
  stack balances it (wedge is symmetric — README tip). Footprints/bed sizes are
  unaffected by depth.
- **V60 01/02**: 60° cone → 90° wedge. Hario official flat sheet specs: 02 =
  125 × 125 mm (measured up to 125 × 128), 01 = 100 × 100 mm (measured up to
  105 × 107) — the user's Amazon-style image claiming 120/100 mm seam edges was
  ~5 mm under real Hario sheets (likely a generic clone). Hario papers have a
  **hanging tab** (~15 mm wide, protrudes ~5–7 mm) on the arc edge next to the seam
  corner; CAFEC cone papers (cup 1 ≈ 101 × 106, cup 4 ≈ 121 × 127) have NO tab;
  clones vary — so `tab_extra` enlarges the interior radially and one box fits all
  brands. The `v60-cafec-*` entries are tabless/compact cases for CAFEC-only
  users (cup 4 friction fits a 200 mm bed vs 220 for the all-brands V60-02).
  Papers fluff up after opening; keep generous slack (V60 community lesson: boxes
  repeatedly had to be rescaled).

## Design map (3 designs × plain/engraved lid = 6 variants per paper)

Shared: interior = paper angle + 3° slack, R_INT = side + rounded-apex offset
(`apex_tip_x`) + 3.5 slack + tab_extra; interior depth = per-paper `depth`
(default `DEPTH` 42; Deep 27 & cup 1: 47, cup 4: 54); walls/floor 2.4; interior
corners filleted r4 via `buffer(-r).buffer(r)`.

- **friction**: full-cover telescoping lid (skirt outside the base wall), clearance
  0.28/side; wide-end wall finger scoop (covered by the skirt when closed); skirt
  stops 3 mm above the table (`PLINTH`) + bottom-edge notches so the halves separate.
- **magnet-skirt**: same shell, clearance 0.50 (glide fit), 4 magnet pairs in outward
  wall lobes (2 on the arc at ±13°, 1 per straight side at 0.6·R_INT). Kept for A/B
  testing, but the user prefers the flat style aesthetically.
- **magnet-flat**: user's preferred reference style (orange corner-magnet box /
  "MAG BOX" CAD image): flat 4.6 mm lay-on lid + 2.5 mm alignment lip, 3 magnet pairs
  in smoothly blended corner bulges (apex + both wide-end corners; centres found by
  `Case._step_out` marching until the pocket clears the interior). No scoop (the
  whole top opens) — instead a 20 × 2.2 mm pry slot under the lid edge mid-arc.

Magnets: Ø6 × 3 mm discs (user owns these), pockets Ø6.4 × 3.2 → ~0.2 mm recess per
side so pairs never touch (controlled snap, one-hand open). Polarity is set at glue
time (README procedure). Pockets always open toward a print-top surface (no
bridging): bases print upright, lids upside down (also makes the engraving crisp
against the bed).

Engraving: `ENGRAVE_TEXT` = "Filtarr" (the project/brand name), 0.6 mm deep
(3 layers), 60 mm wide, centred at 0.7·R_INT on the bisector. Orientation is a
**user decision that was already flipped once**: text up-vector = **+X**, i.e.
upright when the wedge TIP points at the reader (the `rotate(-90)` in
`Case.text_geometry` encodes this). Don't "fix" it again without asking.

## Adding a paper (checklist — details in HOWTO.md)

1. Add a `PAPERS` entry in `generate.py`: `display`, `folder`, `side`, `angle`,
   `tab_extra`, optional `designs` subset. Wedge angle from the dripper cone:
   `180·sin(cone_angle/2)`.
2. `make` — regenerates STLs, the paper's preview, index.html and docs images;
   check the printed bounding boxes against the user's printer bed.
3. Open the preview: ghost-paper toggle must show slack to every wall.
4. Update README by hand: supported-papers table + gallery entry (renders image
   + live preview link). index.html needs nothing — it's generated.
5. Commit + push to `main` — Pages republishes automatically.

## Conventions & gotchas

- `slot_cutter` profiles live in the (tangent, z) plane; frames are built
  right-handed (`t = up × n`) — a mirrored frame flips normals and silently breaks
  booleans.
- Pocket cutters take **explicit z0..z1**: past bug — a helper that over-extended by
  +1 mm cut the lid roof to 0.4 mm. Verify depths with ray casts after touching them.
- matplotlib 3D has no real z-buffer: trust `tools/render_docs.py` output for
  *shape* only, never fine detail (use 2D plots or ray casts for that).
- Builds are canonical through `make` (Docker); a scratch venv is only for dev
  verification (ray casts). `.venv` is gitignored.
- Previews carry an "← All papers" link hard-coded to `../index.html` — previews
  must stay exactly one folder below the repo root or the link breaks.
- Keep the README supported-papers table, README gallery and HOWTO.md in sync
  with `PAPERS` (the Pages index syncs itself).
- The Pages site was enabled once via
  `gh api -X POST repos/Ardakilic/filtarr/pages -f build_type=workflow` — the
  workflow token cannot create it (only deploy to it).

## User context

- User: Arda (ardakilicdagi@gmail.com, GitHub `Ardakilic`); published as
  "Filtarr", dual-licensed MIT (code) + CC BY 4.0 (models & images).
- Previews confirmed working in his browser after the r167 core-split fix.
- Print feedback pending: friction-fit tolerance, magnet snap strength, scoop width.
- Widest parts per paper: V60-02 ~219 mm (needs a 220 bed), CAFEC cup 4 ~207 mm,
  V60-01 ~187 mm, CAFEC cup 1 ~176 mm, Deep 27 ~172 mm — flag bed-size limits
  when relevant.
