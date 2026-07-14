# AGENTS.md

Instructions for AI coding agents working in this repo live in
**[CLAUDE.md](CLAUDE.md)** — read it first. The essentials:

- Everything (STLs, previews, index.html, README images) is **generated** from
  `generate.py` — never edit generated files by hand; regenerate with `make`
  (all builds run in Docker, no local Python needed).
- Printer-fit tolerances — friction lid 0.28 mm/side, magnet-skirt lid
  0.50 mm/side, flat/pedestal alignment lip 0.5 mm/side, magnet pockets
  Ø6.4 × 3.2 mm for Ø6 × 3 discs — are CLI flags, not constants to edit:
  `make generate GEN_ARGS="--clear-friction 0.32"` (full table in
  README → Fit tuning; shown in each preview's Dimensions panel).
- Keep README (supported-papers table, gallery, tolerances), HOWTO.md and
  CLAUDE.md in sync with the `PAPERS` registry in `generate.py`.
