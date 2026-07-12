# The magnet-spring design (experimental)

A spring-loaded dispenser variant of the flat-lid case, proposed by Murat
([the original idea](https://claude.ai/share/bc6dbcb1-b02e-4122-bf81-30d38f8fa52e)):
a **follower plate** in the paper's silhouette floats the stack upward on light
compression springs, so when you lift the lid the **top paper is always waiting
at the rim** — whether 100 papers remain or one. No reaching into a deep tray,
ever.

```
   lid (flat, 3 corner magnet pairs)────────┐
   ═══════════════════════════════════════ ╵ ← rim
   ── travel-stop ledge (4 mm below rim) ──     the plate can't pass this;
      ┆ paper stack, floating ┆                 papers can
      ├───────────────────────┤ ← follower plate (paper silhouette)
      │  anti-cocking skirt   │
      ╿ spring  ╿ spring  ╿     ← 3 light springs in locating rings
   ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁ ← floor
```

## How it differs from the original conversation (and why)

The conversation sketched a card-shoe style dispenser: retaining lips at the
mouth, a permanent thumb window, a TPU friction pad, and a refill latch. Four
deliberate changes:

1. **No dispensing window or retaining lips.** A permanently open window
   defeats Filtarr's whole reason to exist (dust/odour protection), and
   single-sheet separation lips are unreliable on flat paper stacks (full
   surface contact + static means doubles). Instead, the *lid itself* is the
   retainer: closed, the stack floats gently against the lid's underside;
   open, the top sheet is presented at the rim where a thumb pinches it
   trivially — separation is done by your fingers, which are better at it
   than any lip.
2. **No refill latch.** Loading is top-down with the lid off: drop the new
   100-pack in — its own weight (and your hand) pushes the plate down — and
   close the lid. A latch would add a moving part for a once-a-quarter action.
3. **Travel stop with zero extra parts.** The cavity has two tiers: the lower
   tier is 1.5 mm wider all around. The plate is sized between the tiers, so
   it rides freely below but **cannot pass the ledge** 4 mm under the rim.
   Papers (3+ mm smaller than the upper tier) pass through unhindered. No
   pins, no clips, no glued stops.
4. **Anti-cocking is geometric, not spring-count magic.** The plate carries an
   8 mm perimeter skirt (limits tilt to a few degrees before it can bind) *and*
   three springs placed like a tripod (apex + both wide corners), the same
   proven positions as the corner magnets.

## Hardware (BOM)

| Item | Count | Spec |
|---|---|---|
| Disc magnets | 6 | Ø6 × 3 mm (same as the other magnetic designs) |
| Compression springs | 3 | **Ø8–10 mm OD, 0.4 mm wire**, free length ≈ interior depth (42–55 mm), solid height ≤ 8 mm |

The springs sit in Ø10.6 mm locating rings on the floor and under the plate.
They are **not glued** — disassembly is trivial.

### Force budget (the rule that makes it safe)

- The springs' job is only to lift the stack: ~1.2 N for 100 papers.
- At full compression the **total** spring force must stay under ~4 N.
  Three 0.4 mm-wire Ø10 springs at ~0.015–0.02 N/mm give ~2–3 N total. ✓
- The three corner magnet pairs retain the lid with roughly 6–12 N —
  comfortably over 2× the spring force, so the lid never creeps open. If you
  substitute stiffer springs, re-check this margin.
- Paper pressure at 3 N spread over the sheet area is < 0.5 kPa — far below
  anything that marks paper. Constant-force (negator) springs are the premium
  upgrade if you ever find the presentation height drifting between full and
  empty; standard light coils are fine in practice.

## Risk register

| Risk | Assessment | Mitigation in this design |
|---|---|---|
| Lid pushed open by the springs | Real if springs are over-specced | Force budget above; magnet-closure only (the friction lid's 0.28 mm fit is NOT rated to hold spring force — that's why there is no friction-spring variant) |
| Follower cocking/jamming | The classic failure of flat followers | 8 mm perimeter skirt + tripod spring layout + 0.5 mm/side running clearance in the wider lower tier |
| Plate ejected when empty | Would launch the last papers | Two-tier ledge is a hard travel stop 4 mm under the rim |
| Long-term marking of the top sheet | Lid lip presses a line on the top paper's edge zone for months | Light force (< 0.5 kPa); contact is on the sheet's outer margin, outside the brew area. Creped CAFEC paper is more susceptible than smooth Hario — prefer this design for Hario papers, or accept a faint edge line on the top sheet |
| Printed-spring creep | Printed PLA/PETG springs relax under constant load within weeks | Metal springs only — the pockets are sized for commodity hardware, like the magnet pockets |
| FDM friction on the walls | Layer lines drag on the skirt | 0.5 mm/side clearance; if it still drags, a light sand of the skirt or a wipe of PTFE/silicone (not oil — dust magnet) |
| Dust ingress | None beyond magnet-flat | Same closed rim, same lip-backed pry slot, no new openings |
| Bed size | Base grows 1.5 mm/side vs magnet-flat | Largest spring part is still smaller than the pedestal design's finger bay; V60-02 stays under 220 mm |
| Papers never squeezed rule | Springs press the stack by design | The *springs* compress, not the papers: sheet pressure < 0.5 kPa (vs ~2 kPa from just resting your hand on a stack). The interior also gains 12 mm so capacity is unchanged |

## Printing & assembly

1. Print base, lid (plain or engraved) and the **follower** — the follower
   prints top-face-down like the lids: smooth paper face on the bed, skirt and
   locating rings upward, no supports.
2. Glue the 6 magnets exactly as in the README (base first, snap-stack, then
   lid).
3. Stand the 3 springs in the floor rings, lower the follower so its rings
   swallow the spring tops. No glue.
4. Drop the paper stack on the plate, press, close the lid.

## Loading & daily use

- **Take a paper**: lift the lid — the top sheet is at the rim; pinch and go.
- **Refill**: lid off, drop the fresh stack on the plate, press down, lid on.
- The stack floats against the closed lid at ~2 N. If the lid ever feels like
  it "pops" when the magnets release, your springs are too stiff — see the
  force budget.
