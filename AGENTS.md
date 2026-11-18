# AGENTS.md

Instructions for AI coding agents working in this repo live in
**[CLAUDE.md](CLAUDE.md)** — read it first. The essentials:

- Everything (STLs, previews, index.html, README images) is **generated** from
  `generate.py` — never edit generated files by hand; regenerate with `make`
  (all builds run in Docker, no local Python needed — and no local installs).
- The `PAPERS` registry has eleven entries in three shapes: five wedge papers
  (`Case`), three Kalita flat-bottom fans (`"shape": "trapezoid"` →
  `TrapezoidCase`: `kalita-101/102/103`), two AeroPress disc sizes
  (`"shape": "round"` → `RoundCase`: `aeropress`, `aeropress-xl`), plus the
  **combo** (`"combines": ("deep27", "v60-01")` → `ComboCase`, an asymmetric
  keyhole that holds both papers). Always build cases with `make_case(slug)`
  (dispatches via `CASE_CLASSES`), never `Case(slug)` directly; combo,
  trapezoid and round cases have no `side` / `angle` of their own. A Kalita
  entry's `width` / `height` / `bottom` is a REFERENCE sheet (it sets the box
  angle); the box is sized so every listed sheet — reference + `variants`,
  some larger in one dimension — fits, and `make verify` seats each one.
- Per design 3 STLs (base / lid / engraved lid). The combo adds three optional
  divider STLs, users print one: a loose plate (V60 01 below, Deep 27 on top)
  or a table on legs (Deep 27 below, V60 01 on top; the pedestal design has
  its own table). Magnets: skirt 8, flat/pedestal 6 on the wedges; 8 on every
  magnetic design of the Kalita and combo boxes (four corners); 6 on every
  magnetic design of the round boxes (3 pairs, 120° apart — base magnets
  glued same pole up). The round friction lid is twist-off with NO grip
  notches (user decision). The combo's telescoping designs carry their grips
  at BOTH arcs (two scoops, magnet-skirt: two thumb notches) plus three side
  notches.
- Printer-fit tolerances — friction lid 0.28 mm/side, magnet-skirt lid
  0.50 mm/side, flat/pedestal alignment lip 0.5 mm/side, magnet pockets
  Ø6.4 × 3.2 mm for Ø6 × 3 discs — shell thicknesses (2.0 mm walls/floor),
  grip geometry (side notches, the magnet-skirt back thumb notch + its scoop
  band, the scoop), the pedestal chamfers and the combo dividers
  (`--divider-t` / `--divider-clear` / `--divider-leg-h`) are CLI flags, not
  constants to edit: `make generate GEN_ARGS="--clear-friction 0.32"` or
  `--wall-t 1.6` (full table in README → Fit tuning; shown in each preview's
  Dimensions panel). The magnet lids' 4.6 mm is fixed by the pocket depth
  (3.2) + roof (1.4); their undersides are recessed to 2.0 mm instead — don't
  "fix" the 4.6.
- The toolchain is **pinned** (`requirements.txt` with `==`, Dockerfile
  `python:3.14-slim`) so rebuilds reproduce the published STLs byte for byte.
  Bumping a pin re-triangulates every STL: regenerate, verify, and commit the
  outputs together with the bump.
- Run **`make verify`** before committing (`tools/verify.py`: every paper ×
  design built in memory, PASS/FAIL table, exit 1 on failure; same flags as
  generate.py plus `--paper <slug>`). New papers are covered automatically; a
  new feature needs a new check there, a new shape its per-kind block.
- Keep README (supported-papers table, gallery, tolerances), HOWTO.md,
  CLAUDE.md, RESEARCH.md and this file in sync with the `PAPERS` registry in
  `generate.py`. Origami, Kalita Wave, Kalita 104 and drip-machine papers are
  research only (RESEARCH.md) — boxes in a follow-up, no PAPERS entries yet.
