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
generate.py                  shared engine: PAPERS registry + Case / ComboCase classes
                             (always instantiate via make_case(slug)) + export/preview
                             + build_index() -> index.html (Pages landing page)
preview_template.html        template for the self-contained 3D previews
Makefile / Dockerfile        canonical build path: everything runs in Docker
.github/workflows/pages.yml  publishes the whole checkout to GitHub Pages on push to main
tools/render_docs.py         README image renderer (matplotlib, loops all papers via make_case)
tools/verify.py              geometry self-test: every PAPERS entry × design, built in memory
                             (never touches outputs) -> PASS/FAIL table, exit 1 on failure
tools/fetch_three.py         downloads latest three.module.min.js + three.core.min.js
vendor/                      both three.js files + THREE_VERSION (committed)
LICENSE / LICENSE-MODELS     MIT (code) / CC BY 4.0 (models & images)
HOWTO.md                     how to add a new paper variant (keep in sync with PAPERS)
index.html                   generated Pages landing page — never edit by hand
deep27/                      CAFEC Deep 27 outputs: stl/, docs/, preview.html
v60/                         V60 outputs: 01, 02, cafec-01, cafec-02 (stl/, docs/, preview-*.html)
combo/                       Combo (Deep 27 + V60 01) outputs: stl/ (12 design STLs + 3 divider
                             STLs), docs/, preview.html
requirements.txt             PINNED (==, incl. transitive) — see the reproducibility gotcha
requirements-dev.txt         pinned ray-cast extras for tools/verify.py (rtree, scipy, …)
```

Per design: 3 STLs (base / lid / lid-engraved), named
`<paper>-case-<design>-<part>.stl`; a case may add `extras` exported once as
`<paper>-case-<name>.stl` (the combo's `divider`, `divider-table`,
`divider-table-pedestal`; `Case.extras_for(design)` says which go with a
design, `build_extra(name)` returns them in PRINT orientation — the plate as
modelled, the tables legs-up). Design keys:
`friction | magnet-skirt | magnet-flat | magnet-pedestal` (also the preview tab
keys). A PAPERS entry may restrict designs via `"designs": (...)`; currently
all six entries (five papers + the combo) ship all four designs (the CAFEC
entries were friction-only briefly — the user asked for all of them).

## Commands

The canonical build is Docker-based. History: the image was `python:3-slim`
(validated = latest Python 3 on Debian slim, per docker-library docs); since
2026-09-21 it is pinned to `python:3.14-slim` and `requirements.txt` is pinned
too, because the floating pair silently re-triangulated every STL (see the
reproducibility gotcha). Dockerfile adds fonts-liberation + pip requirements:

```bash
make              # generate + docs
make generate     # all papers -> stl + previews + index.html (builds image first)
make generate GEN_ARGS="--clear-friction 0.32"   # fit-tolerance overrides
make docs         # -> <folder>/docs/*.png
make verify       # tools/verify.py: geometry self-test, PASS/FAIL table, exit 1 on FAIL
make verify GEN_ARGS="--clear-friction 0.32"     # verify a tuned build
make vendor       # refresh both three.js files in vendor/ to the latest release
make image        # (re)build the filtarr-build Docker image only
make clean        # delete generated outputs
open deep27/preview.html   # interactive check (Safari is the only browser)
```

The default `make` target is unchanged (generate + docs); `make verify` is
separate. It installs the pinned `requirements-dev.txt` (rtree, scipy, … —
the ray-cast extras, deliberately NOT in requirements.txt) in a THROWAWAY
container and then runs `tools/verify.py` — nothing is installed on the host:
Arda's rule (2026-09-21) is Docker only, no local venv/pip. For one-off
ray-cast experiments use the same pattern: `docker run --rm -v "$PWD":/work
-w /work filtarr-build sh -c "pip install -q -r requirements-dev.txt &&
python <script>"`. (`make generate` depends on the `image` target; with the
pins in place a rebuild is byte-neutral, so `make` is safe — see the
reproducibility gotcha.)

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
  A `"combines"` entry builds a `ComboCase(Case)` instead (two papers, one box —
  see the combo section of the design map); `make_case(slug)` picks the class.
- **Docker as canonical build**: the Dockerfile (`python:3.14-slim`, Debian slim —
  the slim flavour chosen per docker-library/python guidance: pre-built wheels,
  small image; pinned to the minor since 2026-09-21, was the floating
  `python:3-slim`) installs the pinned requirements + `fonts-liberation`. All
  wheels (manifold3d, shapely, matplotlib…) have linux/arm64 builds, so it works
  under Apple-Silicon Docker. The Makefile `vendor` target runs in the same
  bare `python:3.14-slim` image.
- **Engraving**: text outlines from `matplotlib.textpath.TextPath` (hence matplotlib
  in requirements), glyph holes assembled via `symmetric_difference` over rings.
  `FONT_CANDIDATES` order: Arial Bold (macOS/Windows) → Liberation Sans Bold (the
  Docker image's metric-compatible Arial substitute — the canonical output) →
  regular weights. Gotcha: `FontProperties(family="sans-serif")` must be
  `family=["sans-serif"]` (a bare string is parsed as a fontconfig pattern → crash).
- **Previews are fully self-contained** (~8–12 MB each): the latest three.js
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
  engraving toggle (engraving is ON by default); optional `extras` (per design,
  from `Case.extras_for`) follow under their own bold `extras_title` heading
  ("Optional divider, both papers at once — print one"), each with a note.
  Preview-only contents: `Case.ghosts(design)` returns ALL ghost parts of a
  design, and **scenes** choose which show together — `Case.scenes`
  (name / label / part names) → `DATA.scenes`, `Case.default_scene` →
  `DATA.scene`. One scene renders as the old on/off checkbox (plain papers:
  "Ghost paper stack"); several turn it into "Show contents" + a radio list
  (combo: each paper alone / both + loose plate / both + table; default
  `table`). Gotcha: the template's `ROWS` list FILTERS the Dimensions keys — a
  new `dims` key is silently dropped unless added there (`divider` and `table`
  were).
  Smoke-test embedded payloads without a browser: extract both b64 blocks from a
  generated preview, write them side by side, `node -e "import('./three.module.min.js')"`.
- **Verification without a browser/GPU** (no headless Chrome for screenshots).
  **`make verify` (`tools/verify.py`) is THE way** — the committed test. It
  builds every PAPERS entry × design in memory via `make_case` (never touches
  the outputs), prints a PASS/FAIL table and exits 1 on any failure; it takes
  the same override flags as generate.py plus `--paper <slug>` (repeatable).
  Coverage, for every paper/design: watertight; closed lid ∩ base = 0; skirt
  clearances == CLEAR_*; lip; magnet pockets (count, depth, roof, coaxial,
  blind, skin); min wall; skirt bottom = PLINTH; side notches on a straight
  wall; scoop dust-seal band at every grip arc; no arc notch on friction
  lids; recess/rim; pry slot; engraving; papers (incl. the tab at BOTH seam
  corners) fit seated home; pedestal plinth / overhang / chamfer clipping.
  Combo: divider holes, both tables (feet touch the floor, no interference,
  top height, seated-home leg clearance, far-foot play, CoM margin). Plus two
  structural nets: explicit FEATURE COUNTS per case/design (side notches,
  grip arcs, magnet pairs, finger bays, extras) so a silently dropped feature
  fails the run, and "no sharp re-entrant cavity corner" measured on a mesh
  cross-section (guards the combo's r6 shoulder closing). A new
  paper is covered automatically (it loops PAPERS); a new FEATURE needs a new
  check there. The **two gates before committing an engine change**:
  (1) `make verify` passes, (2) the same-image hash gate shows the papers you
  did not mean to touch are byte-identical (see the reproducibility gotcha).
  Complements — for looking, not gating:
  - watertight assert + volume/bounding printout in `generate.py`
  - ad-hoc `trimesh` ray casts for a new depth/clearance question (extras from
    `requirements-dev.txt`, throwaway container — then promote the check into
    `tools/verify.py`)
  - `tools/render_docs.py` matplotlib software renders (global painter sort +
    `subdivide_to_size`, else triangles overdraw wrongly) — look the renders over
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

## Design map (4 designs × plain/engraved lid = 8 variants per paper)

Shared: interior = paper angle + 3° slack, R_INT = side + rounded-apex offset
(`apex_tip_x`) + 3.5 slack + tab_extra; interior depth = per-paper `depth`
(default `DEPTH` 42; Deep 27 & cup 1: 47, cup 4: 54); walls/floor 2.0
(reduced from 2.4 on 2026-07-20 print feedback — "bulletproof"; friction lid
plate also 2.4→2.0); interior corners filleted r4 via `buffer(-r).buffer(r)`.
Magnet lids (skirt/flat/pedestal) keep `LID_T_MAGNET` 4.6 ONLY at the rim and
pockets — the 4.6 is structural: 3.2 pocket + 1.4 roof, thinner would let the
magnet pairs touch — and are recessed from below to `LID_CORE_T` 2.0 over the
cavity (~45 % lid weight off; recess stops 2 mm inside the lip root so rim
contact/dust seal is untouched). Lid skirts are `SKIRT_T` 1.6 (closed hoop +
braced by the base wall when closed → thinner than free-standing walls is
fine). Weight economics (why the pedestal plinth stays a solid slab): slicers
print WALLS solid but fill SLABS at 10-15 % infill, so grams live in vertical
surfaces — an STL-hollow ribbed plinth would print HEAVIER than the infilled
solid one. Don't "optimize" slabs; thin walls instead.

- **friction**: full-cover telescoping lid (skirt outside the base wall), clearance
  0.28/side; wide-end wall finger scoop (covered by the skirt when closed); skirt
  stops 3 mm above the table (`PLINTH`) + bottom-edge notches so the halves separate.
- **magnet-skirt**: same shell, clearance 0.50 (glide fit), 4 magnet pairs in outward
  wall lobes (2 on the arc at ±13°, 1 per straight side at 0.6·R_INT); lobes are
  blended into the wall with the same `CORNER_BLEND_R` closing as the flat-lid
  bulges (print feedback 2026-07-24: raw tangent lobes felt fragile, like pipes
  glued on — the closing adds side gussets; the lid channel follows automatically
  since it derives from `ext_skirt`). Kept for A/B testing, but the user prefers
  the flat style aesthetically. Opening (use feedback 2026-08-01: 4 pairs
  ≈ 25–30 N vs ~23–35 N weak-user sustained pinch — two side notches weren't
  enough): the lid adds a THIRD notch mid-arc (`ARC_NOTCH_*` 24 w × 10 h, r4 —
  what the thumb feels is the FLAT ledge W−2r, per ANSUR thumb-breadth data — with
  a 1 mm ceiling ramp cut by a tilted second `slot_cutter`; the ramp faces up in
  print orientation, no overhang). Fingers pinch the side notches, thumb pushes
  the back ledge up → the arc pairs peel first, then the sides. The magnet-skirt
  scoop bottom is DERIVED = notch top + `ARC_NOTCH_GAP` (6) so notch and scoop can
  never overlap (dust seal by construction — v1 instead capped the notch under the
  friction-depth scoop and the user rejected the cramped 6 mm window / 1 mm
  sliver). Guards: `slot_cutter` clamps corner radii (else an empty-polygon
  buffer crashes far from the cause, e.g. --floor-t ≤ 1.5), --arc-notch-gap < 0.8
  errors, and a channel-breaking --arc-notch-w raises with the measured margin
  (worst paper v60-cafec-01: 3.37 mm at the default 24). Friction lid keeps 2
  notches + the 8 mm-above-floor scoop deliberately — no magnets to peel; its
  STLs stayed bit-identical through this change.
- **magnet-flat**: user's preferred reference style (orange corner-magnet box /
  "MAG BOX" CAD image): flat 4.6 mm lay-on lid + 2.5 mm alignment lip, 3 magnet pairs
  in smoothly blended corner bulges (apex + both wide-end corners; centres found by
  `Case._step_out` marching until the pocket clears the interior; the combo has
  four convex corners → 4 pairs). No scoop (the
  whole top opens) — instead a 20 × 2.2 mm pry slot under the lid edge mid-arc.
- **magnet-pedestal**: magnet-flat shell + easy paper picking. Added 2026-07-12
  after the user found flat-lid picking hard; he chose it over a bay-only fix
  because tabbed Hario papers make press-and-slide unreliable (researched:
  combines the Hario paper stand's minimal-contact floor with the Yamazaki
  Tosca's closed-rim recess). Full-height finger bay bulged outward mid-arc
  (`BAY_W` 34 × `BAY_D` 12, box∪interior smoothed by the `CORNER_BLEND_R`
  closing; the rim stays closed → dust-proof; the pry slot moves to the bay's
  front face, still backed by the lip) + pedestal floor (`PEDESTAL_H` 8)
  stopping `MOAT_W` 15 + tab_extra short of the arc wall, so every brand's
  paper edge (and the Hario tab) overhangs the moat — one sheet is pinched
  from below, down to the last paper. The interior is deepened by PEDESTAL_H,
  so headroom stays = per-paper depth (never squeezed) and the closed box is
  8 mm taller. Base is diff-then-union: cavity cut first, plinth unioned after.
  The plinth carries TWO 45° chamfers (0.2 mm staircases — identical to what
  the slicer would emit, so printability is unchanged; both CLI flags, 0
  disables), softening the section changes that telegraph shrink witness
  lines (print feedback 2026-07-24, Kazım — and researched sizing, do not
  shrink them back: such transitions need 1.5–3 mm, sub-mm only addresses
  elephant-foot, and even then they attenuate rather than eliminate — FDM
  limit; slicer side helps: outer-wall-first, less solid infill):
  `PEDESTAL_CHAMFER_BOTTOM` 2.0 (`--chamfer-bottom`) at the plinth foot in
  the moat — fades the line on the base's UNDERSIDE; papers rest 8 mm above,
  unaffected. MUST stay clipped to the cavity (∩ interior_ped): along the
  straight sides the plinth boundary coincides with the walls and an
  unclipped buffer pokes through them once > WALL_T (caught in a demo).
  `PEDESTAL_CHAMFER_WALL` 1.2 (`--chamfer-side-wall`) is a cove where the
  plinth TOP meets the side walls/apex (the user marked this corner on a
  screenshot) — fades the ring where the slab's solid section ends. Clipped
  to the plinth footprint (nothing may overhang the moat/bay). Kept small
  DELIBERATELY: near the apex the papers' slack → 0, so a cove ≥ ~2 mm would
  prop the bottom sheets' tip edges up; at 1.2 the contact is a ≤1.2 mm edge
  kiss on the first ~45 mm from the tip — accepted by the user.

Magnets: Ø6 × 3 mm discs (user owns these), pockets Ø6.4 × 3.2 → ~0.2 mm recess per
side so pairs never touch (controlled snap, one-hand open). Polarity is set at glue
time (README procedure). Pockets always open toward a print-top surface (no
bridging): bases print upright, lids upside down (also makes the engraving crisp
against the bed).

Printer-fit tolerances (CLEAR_FRICTION 0.28, CLEAR_MAGNET 0.50, LIP_CLEAR 0.5,
POCKET_D 6.4, POCKET_DEPTH 3.2), shell thicknesses (WALL_T/FLOOR_T 2.0,
SKIRT_T 1.6), the combo dividers (DIVIDER_T 1.6, DIVIDER_CLEAR 1.0,
DIVIDER_LEG_H 22 → `--divider-t` / `--divider-clear` / `--divider-leg-h`) and
grip geometry (NOTCH_W/H 22/10,
ARC_NOTCH_W/H/GAP/CHAMFER 24/10/6/1, SCOOP_W 36, SCOOP_ABOVE_FLOOR 8) are
argparse flags
(`apply_printer_args` in generate.py, exposed as
`make generate GEN_ARGS="--clear-friction 0.32"` / `--wall-t 1.6`) so parts
can be tuned per printer without code edits — added for the user's friend
Kazım who prints these. Previews list them in the Dimensions → Tolerances,
Shell and Grip rows (+ Divider / Table on the combo); keep the README
Printing bullets + Fit-tuning table in sync. The complete flag list (21 —
audit it against `python generate.py --help`; `tools/verify.py` accepts the
same ones): `--clear-friction` `--clear-magnet` `--lip-clear` `--pocket-d`
`--pocket-depth` `--wall-t` `--floor-t` `--skirt-t` `--divider-t`
`--divider-clear` `--divider-leg-h` `--notch-w` `--notch-h` `--arc-notch-w`
`--arc-notch-h` `--arc-notch-gap` `--arc-notch-chamfer` `--scoop-w`
`--scoop-above-floor` `--chamfer-bottom` `--chamfer-side-wall`.

Engraving: `ENGRAVE_TEXT` = "Filtarr" (the project/brand name), 0.6 mm deep
(3 layers), 60 mm wide, centred at 0.7·R_INT on the bisector. Orientation is a
**user decision that was already flipped once**: text up-vector = **+X**, i.e.
upright when the wedge TIP points at the reader (the default `engrave_rot` −90
in `Case.text_geometry` encodes this). Don't "fix" it again without asking.
Per-paper `"engrave_rot"` / `Case.engrave_xy` exist only for the combo (below).

### Combo case — `PAPERS["combo"]`, `ComboCase`: Deep 27 + V60 01 in one box

Decision record (2026-09-21): Arda asked for one box for both papers and
floated "V60 angle × Deep 27 length". Offered A full wedge (93° × R160) /
B symmetric keyhole (both wedges on one bisector; recommended) / C asymmetric
keyhole (both against one shared wall) — he CHOSE **C**, **depth 47 + divider
plate**, **all four designs**. A is dead, don't re-propose it — measured:
233–248 mm wide unrotated, a Deep 27 stack spins ±26°, V60 01 slides 51 mm,
interior 208 vs 165 cm², and Deep 27 even LOSES radial slack (3.4 mm: the
blunter apex shrinks the tip offset). B measured 167 × 172 (min square 158);
C won on its slim 175 × 122 footprint.

Second round, same day, after he reviewed the preview — all USER DECISIONS:
(1) the along-the-long-wall engraving (`engrave_rot` 0) is **CONFIRMED**;
(2) the divider gets a finger hole on BOTH sides — "so I can pull from either
side"; (3) a table-style divider IN ADDITION to the loose plate, users choose
either; (4) the V60 end gets "the thumb notch and the hole to hold the paper,
just like the deep27's end" → second scoop + second magnet-skirt thumb notch
at the fan arc; (5) he circled the horn's flat inner wall on a screenshot:
"this end may need a notch for the friction and mag skirt" → third
bottom-edge side notch on W_horn — NOTE the exact form (same cutter as the
side notches, mid-wall) is the AGENT'S reading of that circle and **awaits
his confirmation on the new preview**; (6) "Pin requirements.txt, it's a
good catch"; (7) "Bed size is not important now. Users can slice already
with their current tools."

- **Registry**: `"combines": ("deep27", "v60-01")` references the entries
  (no duplicated numbers; re-measurements propagate). `make_case(slug)` picks
  the class — `Case("combo")` raises KeyError. Validation raises a clear
  ValueError: exactly two different, existing, plain (non-combo) slugs, and
  the longer paper must also be the narrower. A combo deliberately has NO
  `side` / `angle` / `half` / `apex_tip_x` of its own (so a single-wedge
  formula can't run on it unnoticed) and `ComboCase.paper_ghost` raises
  NotImplementedError — use `ghosts(design)`. The sectors are plain `Case` instances —
  `self.far` (largest r_int: Deep 27) and `self.fan` (V60 01) — so each keeps
  its OWN legacy formula (int_angle 45°/93°, r_int 164.95/118.01) although the
  union apex is blunter than Deep 27's own: "never squeezed" beats the ~5 mm
  that could be shaved. Consequence: the shared apex is the fan's, so a
  Deep 27 stack slides `far.apex_tip_x − fan.apex_tip_x` = 4.94 mm deeper than
  in its own box and each paper has ~8–9.5 mm radial play (dedicated boxes:
  3.5) — harmless, but anything measured from a paper's arc edge must use the
  PUSHED-HOME position (see Pedestal). depth = max of the two (47).
- **Frame (differs from the plain wedge!)**: apex at the origin, the SHARED
  long wall on +X (θ = 0), both sectors open CCW — far 0→45°, fan 0→93° (the
  orientation of the plot Arda chose from; STLs export bounding-box-compact
  as-is). Outline: W_long (θ=0, normal −90°) → A_far (R 164.95, mid θ 22.5° =
  `grip_arcs[0]`) → W_horn (back down the θ=45° ray, R 165→118, normal 135°)
  → re-entrant **shoulder** at r_fan∠45° ≈ (83, 83) → A_fan (exposed fan arc,
  θ 45→93°, mid 69° = `grip_arcs[1]`) → W_fan (θ=93°, normal 183°). Convex
  corners: apex, r_far∠0°, horn tip r_far∠45°, fan top r_fan∠93°.
- **Interior** = union → legacy r4 opening → PLUS an r6 (`CORNER_BLEND_R`)
  closing. An opening only rounds convex corners, so the shoulder stayed a
  knife-sharp wall corner poking into the cavity (measured 0.003 mm): paper
  edges catch on it and the telescoping lids would get a sharp internal
  corner. With the closing the base's outer groove is r = 6 − WALL_T = 4 and
  the lid channels are smooth (measured lid gap = nominal 0.280 / 0.500 all
  round, shoulder included). Combo-only ON PURPOSE: any extra buffer
  re-discretises arcs and changes legacy STL bytes.
- **Legacy untouched**: ONE init flow — `Case.__init__` = cfg →
  `_derive_paper_geometry()` (paper → r_int, depth, interior, engraving
  centre; the hook ComboCase replaces) → base_h / engrave_rot →
  `_derive_outlines()`; `ComboCase.__init__` just calls `super().__init__()`
  then `_check()`. Further hooks run the same float ops in the same order as
  before (`_bay`/`_bays`, `_plinth`, `_side_notch_frames`, `ghosts(design)`,
  `scenes`, `extras_for`). The mid-arc grips iterate `self.grip_arcs`, a list
  of `ArcFrame(r, deg)` (`.xy(r)`, `.deg`, `.tangent`): a plain wedge has ONE
  element, a `BisectorFrame` whose `xy` / `tangent` are spelled as the old
  exact literals (`(r, 0.0)`, 0.0, `(0, 1, 0)`) instead of cos/sin of 0 — that
  is what keeps published STLs bit-identical; don't "simplify" it away. Proven
  by the hash gate (see gotchas): all legacy STLs identical before/after
  every round.
- **Mid-arc grips at BOTH ends** (user decision 4): `grip_arcs` =
  [A_far mid (R 164.95, 22.5°), A_fan mid (R 118.01, 69°)]. Every arc gets a
  scoop (`scoop_cutters`, friction + magnet-skirt bases), a magnet-skirt
  thumb notch + ramp (each with its own channel guard; the derived scoop
  bottom applies to both) and a pedestal finger bay; only `grip_arcs[0]`
  hosts the flat lids' pry slot (and the pedestal's, on bay #1's face).
  Friction lid: no thumb notches, as before. Whatever one paper leaves free
  is still finger room for the other.
- **Side grip notches** (friction + magnet-skirt lids): THREE. Two on the
  walls that FORM THE APEX (W_long, W_fan) at NOTCH_FRAC·r_FAN = 42.5 mm →
  61.6 mm pinch, identical to the V60-01 box (the far radius would push the
  W_fan notch off its wall); the third (user decision 5, agent's reading —
  awaiting confirmation) mid-way along W_horn at R = (r_fan + r_far)/2 ≈
  141.5 on the 45° ray = (100, 100), normal 135°, same cutter. The former
  open point — the far thumb notch sits ~139 mm from the apex pinch, a
  two-hand reach — is ADDRESSED, not print-tested: the new fan-arc thumb
  notch is ≈ 92 mm from the pinch midpoint (V60-01 box: 89, Deep 27 box:
  110), so the one-hand "pinch + thumb push" works from the V60 end, and the
  W_horn notch gives the far end a grip next to its own thumb notch.
- **magnet-skirt**: 4 pairs — A_far at 22.5° ± 13°, W_long at 0.6·r_far,
  W_fan at 0.6·r_fan. NOT more: Arda already finds 4 pairs strong
  (2026-08-01). A_fan carries none — the glide-fit hoop aligns, magnets only
  hold down — so its thumb notch has no flanking arc pair: pushing there
  peels the W_fan pair first.
- **magnet-flat / pedestal**: one pair per convex corner = 4 pairs / 8 magnets
  (plain wedges: 3 / 6); `_step_out` headings = bisector of the two outward
  normals meeting there: apex 226.5° (start: the fan's filleted tip on the
  46.5° ray), r_far∠0° → −45°, horn tip → 90°, fan top → 138°. Magnet counts
  everywhere now come from `2*len(magnets_*)` (were hard-coded 8/6).
- **Pedestal**: stepped plinth = interior ∩ (disc_fan ∪ (far wedge ∩
  disc_far)) → legacy r2 opening → r6 closing (rounds the concave junction
  near 97∠45°) → ∩ interior, with disc radius = r_int − MOAT_W − tab_extra −
  **slide**, slide = the paper's own `apex_tip_x` − the fan's (0 for the fan,
  4.94 for Deep 27) → fan plinth edge R 97.0, far plinth edge **R 145.0**
  (not 150). Why the slide term: the moat must be measured from the paper's
  PUSHED-HOME arc edge; the first version (R 150) left a pushed-home Deep 27
  stack only 6.78 mm of overhang at its bay — now 11.7 mm (Deep 27) / 11.5 mm
  (V60 01), on par with the dedicated boxes. Deep 27's edge overhangs the far
  moat (R 145→165), V60's the fan moat (R 97→118, θ 45→93°); inside θ < 45°
  the V60 arc edge just rests on the Deep 27 plinth (Deep 27 sheets need that
  support; V60 sheets are picked at the fan bay). TWO bays: the legacy bay
  rotated to A_far mid + an identical one at A_fan mid (34 mm ≈ 16.5° of the
  48° arc). Both chamfers work unchanged.
- **Engraving**: `engrave_rot` 0, centred on `interior.centroid` ≈ (74, 52) —
  baseline along W_long, upright when the long flat wall faces the reader (as
  in the plot he picked from). Proposed by the agent, **CONFIRMED by Arda
  (2026-09-21)** — now a user decision like the legacy +X rule (which is
  untouched); don't flip either without asking.
- **Dividers — two, users print ONE** (user decision 3; `extras` =
  `divider`, `divider-table`, `divider-table-pedestal`; `extras_for(design)`
  pairs the plate with the right table). Shared top: interior offset by
  `DIVIDER_CLEAR` 1.0, `DIVIDER_T` 1.6, with TWO Ø22 finger holes (user
  decision 2 — "pull from either side"): one in the fan-ONLY zone at
  `DIVIDER_HOLE_FRAC` 0.62·r_fan ∠ 69° ≈ (26, 68), one in the horn-ONLY zone
  mid-horn on the far bisector, R = (r_fan + r_far)/2 ≈ 141.5 ∠ 22.5° ≈
  (131, 54) → whichever stack lies on top, one hole is uncovered (guards:
  ≥ 8 mm land; fan hole disjoint from the far wedge, horn hole outside the
  fan disc). Flags `--divider-t` / `--divider-clear` / `--divider-leg-h`;
  the preview's Divider + Table rows show them.
- **Table divider** (`_derive_table`, `build_table(pedestal)`; the sturdy
  choice, fixed split): the same top on legs, `DIVIDER_LEG_H` 22 = clear
  height under the top → ≈55 Deep 27 sheets below, 47 − 22 − 1.6 = 23.4 mm
  above for V60 01 (guard: ≥ 10 mm must remain). Stacking order is the
  OPPOSITE of the loose plate — Deep 27 on the FLOOR, V60 01 on the table —
  because legs can only stand where no paper lies: three Ø8 round posts
  (`DIVIDER_POST_D`) in the fan-only zone, as near as allowed to the apex,
  the fan-top corner and the shoulder (≥ `DIVIDER_POST_GAP` 2 outside the
  wedge the Deep 27 paper sweeps, off the finger holes), + two arc-segment
  feet (`DIVIDER_FOOT_T` 3.2 × `DIVIDER_FOOT_W` 16) hugging the far arc next
  to the horn's two corners, clear of the far scoop / bay window. The feet
  leave a pushed-home Deep 27 stack 4.02 mm of radial play (guard
  `DIVIDER_FAR_PLAY` ≥ 3; the code's `play` and the verifier agree). Room
  above the table: 23.4 mm, 20.9 mm at the very edge under the flat lids'
  lip ring. The PEDESTAL
  needs its own STL: the table stands on the plinth, but its far feet and the
  fan-top post reach `PEDESTAL_H` down into the moats, while the apex and
  shoulder posts move onto the plinth (`DIVIDER_POST_INSET` 3 from its edge —
  the standard shoulder spot would land on the plinth-foot chamfer at the fan
  moat's dead end; the fan-top post keeps its standard XY, on the plinth it
  would pull the support hull in). Exported legs-UP (top on the bed, no
  bridging). Statics, independently reproduced (2026-09-21): CoM margin
  ≥ 40 mm on both tables; press-to-tip force standard 2.15 / 4.61 / 7.06 N,
  pedestal 1.76 / 3.65 / 5.54 N (empty / 50 / 100 V60 sheets), weakest spot =
  the apex corner. Leg-vs-stack fit, verified: with the Deep 27 stack SEATED
  HOME every leg clears it by 2.62–3.30 mm, but over the sheet's feasible
  poses only 14 % clear all legs by ≥ 1 mm (worst pose needs a 5 mm nudge);
  collisions by leg: far foot high side 65 %, far foot low side 36 %, apex
  post 33 %, shoulder post 1 %, fan-top post 0 %. The binding constraint is
  LENGTHWISE — ~8 mm of play in the box but only 4.02 mm before the arc edge
  rides onto the far feet → verdict "sound PROVIDED the stack is seated
  home"; hence the README tip (push the stack home into the tip first; pushed
  out > ~4 mm its wide edge lands under the far feet, skewed it can also foul
  the post beside the tip). Possible refinement if Arda finds it fiddly (NOT
  done): a lead-in chamfer on the far feet's inner bottom edge, so dropping
  the table in pushes the stack home. NOT print-tested.
- **Loose plate** (`build_divider`, prints flat; flexible split but
  statically marginal): stacking order from
  measured statics, not a hunch (55 g/m² × 2 plies, plate 30.9 g, tipping
  margin = combined centroid's distance inside the lower stack's footprint,
  WORST case over the papers' push range): (a) V60 01 on the floor / plate /
  Deep 27 on top = **+9.4 / +5.8 / +2.7 mm** at 25 / 50 / 100 Deep 27 sheets
  over genuine 107 mm V60 sheets → the recommended, stable order; (b) the
  reverse = +2.7 / −0.5 / −3.1 mm → tips from about half a pack. With
  undersized V60-size sheets (R ≈ 100 mm clones, CAFEC cup 1) order (a) is
  marginal too (−1.2 mm at 50, −4.3 mm at 100); sliding the lower stack
  outward, toward the horn, restores margin (README tip). Root cause: the
  ASYMMETRIC footprint + a loose plate riding on a soft stack — neither
  paper's footprint contains the other's centroid with real margin; the
  symmetric keyhole (B) would not have this. **Experimental, NOT
  print-tested.** The table divider above is the answer to this weakness;
  Arda wanted both kept.
- **Preview**: combo `ghosts(design)` returns every usage mode's parts and
  four scenes pick among them — `full-deep27`, `full-v60-01` (a 26 mm pack of
  either), plate scene (`plate-lower` V60 16 mm / `plate` / `plate-upper`
  Deep 27 20 mm — `PREVIEW_COMBO_STACK_H`), table scene (`table-lower`
  Deep 27 / `table` / `table-upper` V60; default scene = `table`); the
  pedestal design lifts them onto its plinth and shows its own table. Both
  papers are drawn PUSHED HOME into the shared (fan) apex. The V60 ghost's tab
  bump follows the legacy convention (paper centre line) → it lands next to
  the shoulder, still inside the cavity. The print panel keeps "Print these
  two" and appends the dividers under "Optional divider, both papers at once
  — print one".
- **Guards** (`ComboCase._check` — every one of these fails SILENTLY
  otherwise, the meshes stay watertight): simple-polygon interior, sane
  plinth, pockets inside their exterior with ≥ 0.4 mm skin to the cavity and
  to the outside (0.4 = one perimeter; 1.0 was tried and rejected
  `--pocket-d 8.4`, which the plain papers accept), notch ends on their wall
  (< 0.05 mm), grip arcs clear of corners/shoulder, both divider holes in
  their own zone, table: ≥ 10 mm left above, posts apart / inside the top /
  outside the far wedge / fully on the plinth or on flat moat floor clear of
  the foot chamfer and bays, feet leave ≥ 3 mm play and clear the far
  scoop/bay window, text bbox inside interior − 4 and clear of pockets.
- Verified 2026-09-21, first two rounds (ray casts, throwaway container; then
  re-checked by an independent agent, which is where the pushed-home moat
  fix, the statics numbers and the divider flags came from): all 12 pockets
  3.200 deep / 1.400 roof; closed lid ∩ base = 0 mm³ on all four designs; lip
  clears 0.5; papers clear the walls by ≥ 2.0 (Deep 27) / 1.5 mm (V60 01);
  pushed-home overhang at the bays 11.7 / 11.5 mm; divider ∩ base = 0;
  flag-override sets stay watertight. The third-round additions (second
  scoop / thumb notch, W_horn notch, second hole, tables) rest on the
  watertight asserts, the `_check` guards, the implementer's statics and the
  round-four independent re-verification of the tables; all of it is now
  encoded in `make verify`, which is the thing to re-run.

## Adding a paper (checklist — details in HOWTO.md)

1. Add a `PAPERS` entry in `generate.py`: `display`, `folder`, `side`, `angle`,
   `tab_extra`, optional `designs` subset. Wedge angle from the dripper cone:
   `180·sin(cone_angle/2)`. A two-paper box instead takes
   `"combines": (long_narrow_slug, short_wide_slug)` (+ optional `engrave_rot`,
   `depth`) — no side/angle of its own; any code looping PAPERS must go through
   `make_case(slug)` and the `paper_txt` / `interior_txt` / `geo_txt` wording
   properties rather than reading `case.side` / `case.angle`. A new folder also
   needs a line in the Makefile `clean` target (the only hard-coded folder list).
2. `make` — regenerates STLs, the paper's preview, index.html and docs images;
   glance at the printed bounding boxes/volumes for sanity.
3. `make verify` — must PASS for every row (the new entry is picked up
   automatically; `--paper <slug>` narrows it while iterating). Then open the
   preview: ghost-paper toggle must show slack to every wall.
4. Update README by hand: supported-papers table + gallery entry (renders image
   + live preview link). index.html needs nothing — it's generated.
5. Commit + push to `main` — Pages republishes automatically.

## Conventions & gotchas

- `slot_cutter` profiles live in the (tangent, z) plane; frames are built
  right-handed (`t = up × n`) — a mirrored frame flips normals and silently breaks
  booleans.
- Pocket cutters take **explicit z0..z1**: past bug — a helper that over-extended by
  +1 mm cut the lid roof to 0.4 mm. `make verify` ray-casts pocket depth + roof —
  run it after touching them.
- matplotlib 3D has no real z-buffer: trust `tools/render_docs.py` output for
  *shape* only, never fine detail (use 2D plots or ray casts for that).
- Builds AND verification are canonical through `make` (Docker): `make verify`
  installs its extras in a throwaway container — no local venv (Arda's rule;
  `.venv` is still gitignored from earlier days).
- **Reproducible STL bytes = pinned toolchain** (found + fixed 2026-09-21).
  History: the Dockerfile floated on `python:3-slim` with an unpinned
  `requirements.txt`, and an image rebuild that day re-triangulated all 60
  legacy STLs vs commit 9131303 — IDENTICAL bounding boxes, ≤ 0.0021 mm³
  volume delta (last-bit floats / 2–42 triangles; prints unaffected), but
  every byte, git diff and Pages upload churned; the versions behind the old
  committed STLs were never recorded. Arda: "Pin requirements.txt, it's a
  good catch" → `requirements.txt` now pins with `==`: numpy 2.5.3, shapely
  2.1.2, trimesh 5.1.0, manifold3d 3.5.3, mapbox_earcut 2.1.0, matplotlib
  3.11.2 + matplotlib's transitive deps (contourpy, cycler, fonttools,
  kiwisolver, packaging, pillow, pyparsing, python-dateutil, six). The
  Dockerfile base went `python:3-slim` → `python:3.14-slim` as well — the
  AGENT'S addition, not something he asked for (also touched: the Makefile
  `vendor` target and the `tools/fetch_three.py` docstring). Verified
  byte-neutral: after `make image` + regenerate all 75 STL hashes were
  unchanged — so `make` (which rebuilds the image) is safe again. Drift is
  now OPT-IN: bumping a pin (or the Python minor) means expect EVERY STL to
  re-triangulate → check the printed bounding boxes/volumes and commit the
  regenerated STLs together with the pin change. For "did my code change
  touch the legacy papers?" use a **hash gate on the SAME image**: hash the
  STLs built from HEAD sources (`git show HEAD:generate.py` into a scratch
  dir) vs the new sources — never reason from a git diff that also spans a
  toolchain change. Generation is deterministic on one image.
  Git cost: the six previews total ~76 MB and are rewritten by every
  regeneration; with the pinned toolchain they stay byte-stable, so only real
  changes cost git history — another reason not to bump pins casually.
  Renovate: origin has a `renovate/configure` branch (Renovate onboarding,
  seen 2026-09-21) — once enabled, its PRs will bump these pins; each bump
  re-triangulates every STL, so such a PR must be regenerated (`make image &&
  make`), pass `make verify`, and be committed TOGETHER with the regenerated
  outputs — never merged as a bare requirements.txt change.
  One deliberate exception: `fonts-liberation` stays UNPINNED in apt — a hard
  apt version pin would break the build at the next Debian point release
  (old package versions vanish from the mirrors). Canonical font behind the
  published engravings: fonts-liberation 1:2.1.5-3, LiberationSans-Bold.ttf
  md5 3073c99843570b858634c66019a17b7f — the Dockerfile carries that comment
  next to the `fonts-liberation` install line. A font change would re-triangulate ONLY the
  `*-lid-engraved.stl` files; if those alone churn after an image rebuild,
  compare that md5 first.
  STILL OPEN (user's call): the 65 legacy generated files (60 STLs + 5
  previews) whose bytes changed purely from that earlier drift. Since the
  pins now match the toolchain that produced them, COMMITTING them is the
  consistent choice (a `git restore` would bring back bytes no pinned build
  can reproduce) — a recommendation, not a decision.
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
- First print feedback (2026-07-20, from his printing friend Kazım): shells felt
  "bulletproof"/heavy → walls, floor and friction lid went 2.4→2.0 and magnet
  lids got the LID_CORE_T underside recess. Kazım wanted everything ≤2 mm; the
  magnet-lid rim can't (pocket 3.2 + roof 1.4 = 4.6, else magnets touch).
- Still pending from real use: friction-fit tolerance, magnet snap strength,
  scoop width; the magnet-skirt back thumb notch (2026-08-01, from Arda's own
  use feedback — magnets too strong for two side grips) is designed and shipped
  but not print-tested yet. If it's still hard to open, the researched next
  step (user's call, separate change): deepen ONLY the two arc pockets ~0.4 mm
  per side → arc pairs become designed break-tabs (~45 % less push force,
  ~23 % less total hold).
- Widest parts per paper (the pedestal design is the largest, except on the
  combo): V60-02 ~219 mm (needs a 220 bed), CAFEC cup 4 ~207 mm, V60-01
  ~187 mm, CAFEC cup 1 ~177 mm, Deep 27 ~182 mm (pedestal base; its other
  designs stay ~172, so only Deep 27's pedestal outgrows a 180 bed), combo
  ~192 × 135 mm (magnet-skirt lid; pedestal 185 × 135, friction base
  175 × 122). These are UNROTATED widths: with free rotation about Z the
  smallest square bed is only ≈157 mm for V60-02 flat/pedestal and ≈163 mm for
  the Deep 27 pedestal (measured 2026-09-21 — a 45° turn puts both on a 180
  bed); over the 13 combo parts measured in round two the min square was
  162.1–179.7 mm (on a 180 bed friction, magnet-flat AND magnet-skirt (lid
  177.3) fit when rotated, the pedestal base (179.7) effectively does not;
  everything fits 220/256 as exported). Keep the numbers, but Arda said
  (2026-09-21): "Bed size is not important now. Users can slice already with
  their current tools." → do NOT flag bed limits prominently any more and
  don't pad docs with bed-fit analysis; one factual "largest part as
  exported" line is enough, go further only if he asks.
- Combo box (2026-09-21): shape C, depth 47 + divider, all four designs, and
  the second-round requests (engraving confirmed, two holes, table divider,
  V60-end grips, W_horn notch, pinned requirements, no bed-size talk) were
  Arda's decisions (see the combo section). Pending from real use / his
  confirmation: (1) the W_horn side notch — agent's reading of his screenshot
  circle, awaiting his OK on the new preview; (2) divider stability — the
  loose plate's statics are thin (esp. with undersized V60 sheets), the table
  is the sturdy answer; NEITHER is print-tested; (3) friction-lid fit around
  the re-entrant shoulder (a telescoping lid over a non-convex 175 mm profile
  is less forgiving than a convex one — may want a looser `--clear-friction`);
  (4) the V60-end scoop + thumb notch — addressed the 139 mm reach point on
  paper (≈ 92 mm now), not print-tested. Also open: commit vs restore the 65
  drift-rebuilt legacy generated files (recommendation: commit — see the
  reproducibility gotcha), and the `python:3.14-slim` base pin, which was the
  agent's addition.
- Test file (2026-09-21): before committing the combo Arda asked that the
  test cover the new case. None existed — not in any branch or in history —
  so the session's throwaway verification scripts were promoted to the
  committed `tools/verify.py` + `requirements-dev.txt` + `make verify`. Keep
  it current: a new feature without a check there is untested.
- Working style he asked for (2026-09-21): delegate research / file changes /
  checks to subagents (Opus for research and checks), Docker only — no local
  installs, Context7 for library docs, ask before open design choices, and
  show the result before committing or pushing.
