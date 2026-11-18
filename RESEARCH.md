# Filter-paper research notes

Research behind the paper families that were added to Filtarr, or are planned, after the
five original papers and the combo box. Status as of **2026-11-18**:

| Family | Status | Section |
|---|---|---|
| Kalita fan ("trapezoid") 101 / 102 / 103 | **boxed in this PR** (`kalita-101`, `kalita-102`, `kalita-103`), all four designs | [2](#2-kalita-fan-trapezoid-papers-101--104) |
| Kalita fan 104 | researched only | [2](#2-kalita-fan-trapezoid-papers-101--104) |
| AeroPress Standard + XL discs | **boxed in this PR** (round boxes, all four designs) | [3](#3-aeropress-paper-discs) |
| Origami dripper papers (cone + wave) | researched only, single pass | [4](#4-origami-dripper-papers) |
| Kalita Wave 155 / 185 and other flat-bottom cups | researched only | [5](#5-kalita-wave-155--185-and-other-flat-bottom-cups) |
| Drip-machine papers (Melitta-style cones, US baskets) | researched only | [6](#6-drip-machine-papers) |

Boxes for the researched-only families will come in a **follow-up PR** (maintainer's decision,
2026-11-18). Section [7](#7-not-yet-boxed--planned-follow-up) has the plan and the measurements
that would settle the open points.

## 1. Purpose and method

**Purpose.** Each box is sized from paper dimensions. This file records where every number came
from, so a later caliper check can replace the weak ones without redoing the research.

**Method.**

- Dimensions come from maker specifications, maker packaging and retail listings, plus a few
  third-party measurements (caliper, tape, photo traces). Shapes and missing values are derived
  from geometry. Most pages were fetched directly. Where only a search snippet was available,
  the text says so.
- Each family went through two passes. One agent did the research, then a second agent
  fact-checked it: it re-fetched the sources, re-derived the numbers and looked for
  counter-evidence. This file uses the fact-checked values and lists the notable corrections in
  each section. **Exception: Origami (section 4) had only the first pass.**
- **Max-envelope rule.** A box is driven by the largest credible paper of its class, not the
  typical one. Smaller variants that must also fit are then checked against it. Depth comes from
  the thickest credible 100-pack (or the retail pack) plus headroom. This is the house rule:
  papers are **never squeezed**. For the Kalita fans, whose shape takes three numbers, the
  "envelope" is a **reference sheet** that sets the box angle; the box is then sized so that
  every listed sheet — reference and variants, some of them larger in one dimension — fits, and
  `make verify` seats each one (section 2).
- **Not caliper-checked yet.** No number here was measured on the maintainer's own papers.
  Section 7 lists the measurements that would confirm or correct the boxes.

**Provenance tags** used in the tables:

| Tag | Meaning |
|---|---|
| <sup>S</sup> | spec: maker page, maker packaging or official listing |
| <sup>R</sup> | retail: shop or distributor copy |
| <sup>M</sup> | measured by a third party (caliper, tape, pixel trace of a photo) |
| <sup>D</sup> | derived: geometry or arithmetic from other numbers |
| <sup>A</sup> | assumed or extrapolated |
| <sup>U</sup> | reported, but could not be re-fetched in the fact-check |

All lengths are in mm. Flat papers are measured as stored, folded flat.

## 2. Kalita fan ("trapezoid") papers 101 – 104

**Boxed in this PR: 101, 102, 103.** 104 is researched only: its dimensions come from a single
retailer, and it is a commercial size.

### Naming

- The user's "FP-01/02/03" are **FP101 / FP102 / FP103**. Kalita's official names are
  "FP101ロシ" etc. (the "うまみを引き出す" line). There is also an FP104.
- The size number is the cup class: 101 = 1–2, 102 = 2–4, 103 = 4–7, 104 = 7–12 people<sup>S</sup>.
- **Shape name.** Kalita's own pages use no shape word, only "101ロシ / FP101ロシ".
  "扇形 / Fan series / カリタFanシリーズ" comes from retailers. Japanese retail and blogs mostly
  say 台形 or "カリタ式". English retail says wedge, fan-shaped or trapezoid, and sometimes,
  wrongly, "cone". These are **not** the Wave papers (KWF-155/185, section 5).
- The 5-digit numbers are Kalita item codes, not sizes.

| Line | Sizes | Count | Item codes (white / brown)<sup>S</sup> |
|---|---|---|---|
| FP | 101–104 | 100 (bag) | 101: 11109 / 11111 · 102: 13127 / 13129 · 103: 15085 / 15087 · 104: 17029 / 17031 |
| NK (lighter paper, 5 mm thinner bag) | 101–103 | 100 (bag) | 101: 11105 / 11107 · 102: 13123 / 13125 · 103: 15081 / 15083 |
| Boxed ロシ 40P | 101–103 | 40 (box) | 101: 11037 / 11141 · 102: 13039 / 13143 · 103: 15027 / 15131 |
| 珈琲屋さん ロシ | 101–103 | 100 (box) | 101: 11151 · 102: 13165 · 103: 15127 |
| MM / POOH printed | 101–102 | 40 (box) | e.g. MM101ロシ (II) 12199 |

### Geometry model

The flat paper is a **truncated sector**. The cone rule `180·sin(A/2)` does not apply.

- Frame: the sides' virtual apex O is at the origin, with the centre line on +X.
- Bottom edge (the crimp seam): straight, perpendicular to +X at distance `d`, length
  `b = 2·d·tan(α/2)`.
- Sides: straight, along ±α/2. One side is crimped and the other is a plain fold.
- Top: a circular arc of radius `R` about O.
- Derived values: centre height `h = R − d`, chord (the max width) `c = 2R·sin(α/2)`, sagitta
  `R(1 − cos(α/2))`, side `R − d/cos(α/2)`.
- **Solving from measured (c, h, b):** find `t = α/2` with `c/(2 sin t) − b/(2 tan t) = h`. Then
  `R = c/(2 sin t)` and `d = b/(2 tan t)`.
- **Evidence**<sup>M</sup>: a pixel trace of Kalita's own 102 product render. The two sides
  are equal within 1.5 %. Ten points on the top arc lie 457 px ±1 % from O, so the arc is
  concentric with the virtual apex. The bottom-corner angles average 127.8° (= 90° + α/2), and
  the trace gives α ≈ 75.6°. An oblique third-party photo (takunomi, brand unknown) supports the
  arc shape only, not the angle.
- **Cross-check with the drip-machine research (section 6).** Modelling a Melitta-type paper as
  a level-rim liner puts the top curve's centre 21–23 mm below the bottom edge, not at O. Its
  distance from O then varies by only ~3 mm, so an interior arc centred on O still encloses the
  paper. The two models disagree about the arc centre, but the box sizing is the same under
  either.

### Dimensions

c × h is chord × centre height. α / R / d are derived from (c, h, b) with the solve above.

| Size | c × h | b (bottom) | typical → α / R / d<sup>D</sup> | side / sagitta<sup>D</sup> | **max envelope (c, h, b)** → α / R / d<sup>D</sup> | widest-angle variant<sup>D</sup> | confidence |
|---|---|---|---|---|---|---|---|
| 101 | 134 × 80<sup>R</sup> (h ≤ ~79: the 40P box is 80×29×143<sup>S</sup>) | 50<sup>R</sup>, one shop | 71.4° / 114.8 / 34.8 | 71.9 / 21.6 | **(138, 80, 53)** → 73.3° / 115.6 / 35.6 | b 45 → 76.0° | medium |
| 102 | 160 × 100<sup>R</sup> | 50<sup>R</sup> (range 44–53) | 73.7° / 133.3 / 33.3 | 91.7 / 26.7 | **(165, 105, 53)** → 70.9° / 142.2 / 37.2 | b 44 → 77.9° | medium |
| 103 | 193 × 127<sup>R</sup> | 53<sup>A</sup> (from Toyo 103) | 72.5° / 163.1 / 36.1 | 118.3 / 31.6 | **(195, 130, 56)** → 70.0° / 170.0 / 40.0 | b 47 → 75.7° | low |
| 104 | 225 × 155<sup>R</sup>, one shop | 55<sup>A</sup> | 71.1° / 193.5 / 38.5 | 146.2 / 36.1 | (230, 157, 58) → 71.2° / 197.5 / 40.5 | b 50 → 73.2° | low |

Where the envelopes (the registry's reference sheets) come from:

- **101:** chord 138 is margin over the retail 134–135. The 40P box caps h.
- **102:** chord 165 (Askul 扇形102 16.5 cm<sup>S</sup>, Brooks 102 165<sup>S</sup>), h 105 (Melitta 1x2 folded 160×105<sup>R</sup>; Brooks 103<sup>S</sup> — the envelope first used 103, then went to 105 so that the Melitta 1x2 sheet keeps the full 3.5 mm at the arc instead of 1.5), b 53 (Toyo 102<sup>S</sup>). The 102 bottom range of 44–53 combines rblack NK102 50<sup>R</sup>, Melitta 1x2 47<sup>S</sup>, Toyo 53<sup>S</sup> and the render trace (b/c 0.28 → ≈45<sup>D</sup>).
- **103:** chord 195 is the cap from Kalita's own boxes (40P 130×29×196, 珈琲屋さん 130×58×195<sup>S</sup>). Generic 103 papers retail up to 20×13 cm<sup>R</sup> (search snippet only), so a (200, 130, 56) paper is also checked (a `variants` entry, see below).

### Stack heights and depth

| Size | FP bag (100) | NK bag (100) | 40P box | 珈琲屋さん box (100) |
|---|---|---|---|---|
| 101 | 200×45×82, 86 g | 190×40×82, 76 g | 80×29×143 | 85×60×143, 126.8 g |
| 102 | 235×45×102, 122 g | 225×40×102, 110 g | 110×29×168 | 116×60×165 |
| 103 | 280×50×130, 220 g | 280×45×130, 162 g | 130×29×196 | 130×58×195, 261 g |
| 104 | 290×50×155, 300 g | — | — | — |

All values in this table are <sup>S</sup> (kalita.co.jp / kalita.shop).

- **Typical 100-stack** = FP bag thickness: 45 for 101/102 and 50 for 103/104 (NK 40/45).
- **Max 100-stack ≈ 58 (101/102) / 57 (103)**: the inner thickness of the 珈琲屋さん boxes.
  Estimated from box weights, that line's paper is ≈30 % heavier per sheet<sup>D</sup> (low
  confidence; per sheet FP ≈0.81 g, 40P ≈0.94 g, 珈琲屋さん ≈1.05 g).
- The Kalita × tower steel case (185×57×137) holds "片面約50枚づつ計約100枚"<sup>S</sup>.
- Per ply ≈0.225 mm<sup>D</sup> (45 mm / 200 plies). That is in line with coffeeadastra's
  0.206–0.210<sup>M</sup> for V60/CAFEC paper; Kalita paper was not measured.
- **Box depth 58 for 101–103** covers every Kalita line. The "pack + 7" minimum would be 52
  (101/102) or 57 (103).
- The crimp seam lofts one side; flipping half the stack balances it.

### Equivalents (by overall size)

| Kalita | Same class | Data points |
|---|---|---|
| 101 | Melitta 1x1, Toyo TS101, CAFEC Abaca 101 | Japanese comparison sources pair 1×1 with 101; no Melitta 1x1 dimensions found |
| 102 | Melitta 1x2, US #2, Brooks 102, Toyo TS102, HARIO 台形102, Askul 扇形102, STRIX 102, CAFEC Abaca 102 | Melitta 1x2 底47×高102<sup>S</sup>, folded 160×105<sup>R</sup> · Brooks 165 / 54 / 103 (top / bottom / height)<sup>S</sup> · Toyo 底53×高102<sup>S</sup> · HARIO 158×99<sup>R</sup> · Askul 165×102<sup>S</sup> · STRIX 160×100<sup>R</sup> · US #2 159×102<sup>M</sup> (tape) |
| 103 | Melitta 1x4, US #4, EU "Size 4", Brooks 103, Tingstad 1x4, Toyo TS103, CAFEC Abaca 103 | Melitta JP PO-148B 底52×高128<sup>S</sup> · Brooks 195 / 54 / 128<sup>S</sup> · Tingstad Ø50 / Ø190 × 125<sup>S</sup> · Toyo 底53×高128<sup>S</sup> · US #4 190.5×127<sup>M</sup> (tape) |
| 104 | Melitta 1x6 (by height) | Melitta 1x6 150 tall<sup>S</sup>; Kalita 104 is ~5 mm taller |

Two traps:

- **Melitta's old 100-series is a different paper.** Its 101 / 102 … are narrower-angle papers
  (old 102 ≈ 115 tall<sup>S</sup>, Tingstad). The EU "Größe 2" corresponds to that **old 102,
  not to 1x2** (de.wikipedia). These papers do not fit a 102-class box.
- The bottom widths and angles of the Melitta / US papers are not confirmed to match Kalita's.
  Wikipedia's "Melitta 54°" is unsourced and is not the flat-paper angle: Melitta 1x2's own spec
  solves to ≈73–75°<sup>D</sup>.

### Box sizing (this PR) and why not reuse an existing box

- **Interior from a reference sheet plus every listed sheet.** The registry's (c, h, b) is a
  reference sheet — the "max envelope" column above. Its fan angle α + 3° about the virtual apex
  is the box angle; then a flat bottom wall, a concentric top arc, `tab_extra` 0 (no hanging tab),
  depth 58. The box is sized over **every** listed sheet (reference + `variants`), because some
  variants are larger than the reference in one dimension (101: b 55 > 53; Brooks 102: b 54 > 53;
  generic 103: c 200 > 195).
- **The bottom wall is placed by the pushed-home rule**, not "3.5 mm behind d". The naive wall
  leaves ≈0 mm at the bottom corners, where the stack wedges. Instead, the wall sits where the
  sheet with the **widest bottom**, pushed home, keeps a 2 mm side gap (square to the side walls)
  at its bottom corners; every sheet's crimped edge then rests on the flat part of the wall, clear
  of the r4 corner fillets (0.47–0.60 mm of flat wall left beside the widest bottoms, more for
  the others). The arc sits 3.5 mm (`RADIAL_SLACK`) beyond the farthest pushed-home arc of any
  sheet, and the pedestal's moat is widened so that the **shortest** sheet still overhangs it by
  11.5 mm at the finger bay (`MOAT_W` − `RADIAL_SLACK`; taller sheets overhang more — like
  `tab_extra` widening the moat on the V60 boxes). The exact rules are in `generate.py`.
- **Driven from the envelope, not typical values.** An interior built from typical 102 values
  would hold a (165, 103, 53) paper 0.09 mm **over** at the side wall.
- **Every listed sheet is checked.** `make verify` seats each one home in the 2D interior and
  demands: its bottom edge on the bottom wall with ≥ 1 mm of push play; both bottom corners on
  the flat wall, ≥ 0.3 mm before the fillets; sides and arc ≥ 1 mm from the walls including the
  fillets (outside the 2 mm corner zone); and in the pedestal design ≥ 11.4 mm of overhang
  across the finger bay. Measured, default build:

  | Box | Sheet (c, h, b) | flat wall at the corners / clearance to the walls / play, mm | pedestal overhang, mm |
  |---|---|---|---|
  | 101 | reference (138, 80, 53) | 1.60 / 2.05 / 4.08 | 11.5 |
  | 101 | (134, 80, 45) · (134, 80, 50) · (134, 80, 55) | 5.60 / 4.08 / 4.08 · 3.10 / 2.65 / 4.08 · 0.60 / 1.91 / 4.08 | 11.5 · 11.5 · 11.5 |
  | 102 | reference (165, 105, 53) | 1.01 / 1.99 / 3.48 | 16.5 |
  | 102 | (160, 100, 44) · (160, 100, 50) | 5.51 / 2.76 / 8.48 · 2.51 / 2.30 / 8.48 | 11.5 · 11.5 |
  | 102 | Melitta 1x2 (160, 105, 47) · Brooks 102 (165, 103, 54) | 4.01 / 3.27 / 3.48 · 0.51 / 1.83 / 5.48 | 16.5 · 14.5 |
  | 103 | reference (195, 130, 56) | 0.47 / 1.86 / 3.48 | 14.5 |
  | 103 | (193, 127, 47) · (193, 127, 53) · generic (200, 130, 56) | 4.97 / 2.79 / 6.48 · 1.97 / 2.07 / 6.48 · 0.47 / 1.77 / 3.48 | 11.5 · 11.5 · 14.5 |

  The widest bottoms (101: b 55, Brooks 102: b 54, 103: b 56) set the bottom wall, so they keep
  the least flat wall at the corners; there, the sheet's side passes the start of the fillet
  0.38–0.50 mm away (inside the corner zone). The widest angle (generic 103: 73.2° in a 73.0°
  box) keeps the least clearance at the side walls. The 101's arc is set by the (134, 80, 55)
  sheet: its virtual apex sits 3.4 mm behind the box's, so its arc corners reach farthest, and the
  others get 4.08 mm at the arc instead of 3.5. These checks are 2D, on the paper outlines as
  modelled; no real sheet has been tried yet.
- **Shipped interiors** (length along the centre line × interior angle, flat bottom wall):
  101 84 mm × 76° (60), 102 109 mm × 74° (59), 103 134 mm × 73° (61), depth 58 (66 in the
  pedestal design); pedestal moats 15.6 / 20 / 18 mm. Each preview's Dimensions panel repeats the
  interiors. With the flat and pedestal lids the 2.5 mm alignment lip leaves 55.5 mm of the 58
  along the walls (where the crimped edges lie) — still more than 5 mm above a 50 mm bag stack.

Existing boxes do not serve Kalita papers well. Figures below use 93° interiors, `apex_tip_x`
1.514 and papers seated home:

| Existing box | r_int | depth | Kalita 101 | Kalita 102 (radial slack) | Verdict |
|---|---|---|---|---|---|
| v60-cafec-02 | 132.01 | 54 | fits | 6.2 typical / 1.6 at the envelope | OK for FP/NK bags, too shallow for the 58 of the 珈琲屋さん line |
| v60-cafec-01 | 111.01 | 47 | 5.0 typical / 3.6 at the envelope | does not fit | 101 only |
| v60-01 | 118.0 | 42 | fits (12.0) | **−7.8, does not fit** | too shallow |
| v60-02 | 140.0 | 42 | fits | 14.2 / 9.6 | 42 is below the 45 mm bag, so the stack is squeezed |

In every 93° box a ≈73–76° stack also swings about ±9° sideways. 103 and 104 fit no existing box.

### Corrections from the fact-check

- The max 100-stack went from 50 to **58** (101/102) and from 55 to **57** (103/104), based on
  Kalita's own 珈琲屋さん boxes.
- Max fan angles went up (101 → 76°, 102 → 78°, 103 → 76°, 104 → 73.5°): a smaller bottom with
  the same chord and height widens the fan.
- Interiors were re-derived from the max envelopes. Typical-value interiors had zero slack.
  (Later, after the geometry review: sized over every listed sheet, see above.)
- The reuse table was recomputed with `apex_tip_x` = 1.514, not 1.66. v60-01 does **not** hold a
  Kalita 102.
- "Never map Kalita 102 to US #2" was withdrawn. Tape-measured US #2 / #4 match 102 / 103 by
  overall size.
- "扇形 / Fan series" is a retail term, not Kalita's official name.
- The 101 bottom of 50 rests on one shop. The cited Korean listing was the NK102 page.

<details><summary>Sources — Kalita fan papers</summary>

- Kalita official product pages:
  [1836](https://www.kalita.co.jp/products/coffeefilter/1836),
  [1837](https://www.kalita.co.jp/products/coffeefilter/1837),
  [1839](https://www.kalita.co.jp/products/coffeefilter/1839),
  [1840](https://www.kalita.co.jp/products/coffeefilter/1840),
  [1845](https://www.kalita.co.jp/products/coffeefilter/1845),
  [1847](https://www.kalita.co.jp/products/coffeefilter/1847),
  [1858](https://www.kalita.co.jp/products/coffeefilter/1858),
  [1860](https://www.kalita.co.jp/products/coffeefilter/1860),
  [1862](https://www.kalita.co.jp/products/coffeefilter/1862),
  [1864](https://www.kalita.co.jp/products/coffeefilter/1864),
  [1865](https://www.kalita.co.jp/products/coffeefilter/1865),
  [1866](https://www.kalita.co.jp/products/coffeefilter/1866),
  [1874](https://www.kalita.co.jp/products/coffeefilter/1874),
  [1877](https://www.kalita.co.jp/products/coffeefilter/1877),
  [1881](https://www.kalita.co.jp/products/coffeefilter/1881),
  [1884](https://www.kalita.co.jp/products/coffeefilter/1884),
  [1888](https://www.kalita.co.jp/products/coffeefilter/1888),
  [1891](https://www.kalita.co.jp/products/coffeefilter/1891),
  [2270](https://www.kalita.co.jp/products/coffeefilter/2270),
  [set/1861](https://www.kalita.co.jp/products/set/1861),
  [set/3681](https://www.kalita.co.jp/products/set/3681)
- Kalita shop: [1483](https://kalita.shop/item/1483), [1557](https://kalita.shop/item/1557),
  [1558](https://kalita.shop/item/1558), [1559](https://kalita.shop/item/1559),
  [1672](https://kalita.shop/item/1672)
- Retail dimensions:
  [Rakuten livingut (101–104 sheet sizes)](https://item.rakuten.co.jp/livingut/uni487611/),
  [wb.coffee 101](https://www.wb.coffee/shop/kalita-101-filters-box-of-100-filters-43603),
  [Amazon.com 101](https://www.amazon.com/Entered-Pieces-Kalita-Coffee-Filter/dp/B001TM6FEI),
  [Amazon.co.jp NK102](https://www.amazon.co.jp/dp/B002TUZ6WG),
  [rblack.co.kr NK102](https://rblack.co.kr/product/%EC%B9%BC%EB%A6%AC%ED%83%80-nk102-%EC%BB%A4%ED%94%BC%ED%95%84%ED%84%B0-100%EB%A7%A4%EC%9E%85%ED%99%A9%EC%83%892-4%EC%9D%B8%EC%9A%A9/59/),
  [Askul AUU0141](https://www.askul.co.jp/p/AUU0141/), [AUU0142](https://www.askul.co.jp/p/AUU0142/),
  Askul spec fields for Toyo 102 / 103, Melitta 1x2 and 扇形102:
  [8202110](https://www.askul.co.jp/p/8202110/), [NK99903](https://www.askul.co.jp/p/NK99903/),
  [EP82689](https://www.askul.co.jp/p/EP82689/), [8204132](https://www.askul.co.jp/p/8204132/);
  [nishimuta-eshop 103](https://www.nishimuta-eshop.com/view/item/000000008555),
  [Cainz generic 103](https://www.cainz.com/g/4549509979043.html),
  [STRIX 102](https://strixdesign.jp/featured_item/sd-903/),
  [gourmetkava Melitta 1x2](https://www.gourmetkava.cz/en/kavove-filtry-/melitta-original-1x2-coffee-filters-597p),
  [Kurasu](https://kurasu.kyoto/products/kalita-fan-shaped-white-paper-filter-101-102-103-100-sheets),
  [colourbrown 102 (render traced)](https://colourbrown.com/products/kalita-102-wedge-shaped-coffee-filter-paper-pack-40pcs)
- Measurements and other:
  [clearlycoffee US #2 / #4 tape](https://www.clearlycoffee.com/whats-the-difference-between-2-and-4-coffee-filters/),
  [coffeeadastra ply thickness](https://coffeeadastra.com/2019/08/04/an-in-depth-analysis-of-coffee-filters-2/),
  [takunomi photo](https://takunomi-coffee.com/paperfilter2/),
  [Wikipedia: Coffee filter](https://en.wikipedia.org/wiki/Coffee_filter),
  [Brooks 102](https://www.brooks.co.jp/product/detail/211102),
  [Brooks 103](https://www.brooks.co.jp/product/detail/211103)

</details>

## 3. AeroPress paper discs

**Boxed in this PR: Standard and XL.** The stored shape is a stack of flat single-ply discs: no
apex, seam, tab or crimp, and the discs don't nest. Thin discs cling to each other, so picking
one needs edge access.

### Discs

| Disc | Ø typical | Ø max | Thickness per sheet | Packs | Stack, typical / max | Confidence |
|---|---|---|---|---|---|---|
| **AeroPress Standard** (white / natural): Original, Clear, Premium, Steel, Go, Go Plus | 63.5<sup>S</sup> (2.5 in) | 65<sup>R</sup> (JP / US shops) | 0.120 ± 0.022<sup>M</sup> (caliper, coffeeadastra) | 350 white, 200 natural<sup>S</sup>; kits ship with 100 | 350: **44 / 50**<sup>D</sup> (0.125 / 0.142 per sheet) | high |
| **AeroPress XL** (white / natural): XL only | 73.7<sup>S</sup> (2.9 in) | 74<sup>D</sup> (retail 72–73) | 0.12<sup>A</sup> (= Standard; pack weights agree) | 200<sup>S</sup> | 200: **25 / 29**<sup>D</sup> | medium |
| Aesir Premium (V1 / V2), Standard size | 63.5<sup>A</sup> ("same diameter") | 65<sup>A</sup> | 0.220 ± 0.022<sup>M</sup> (one source) | 100 / 300 (identical discs)<sup>R</sup> | 100: 22 · 300: 66–73<sup>D</sup> | medium |
| CAFEC (Sanyo Sangyo), apparently export-only | 63<sup>R</sup> (one shop) | 64<sup>A</sup> | 0.15<sup>R</sup> (two shops) | 100 | 15 / 17<sup>D</sup> | low |
| Generic "6.4 cm" discs | 64<sup>R</sup> | 65 | unpublished (assume 0.12–0.15) | 300–800 (in sleeves) | — | low |
| Metal discs (AeroPress stainless, Able, IMS, Prismo) | ≈62<sup>R</sup> (IMS "D62", 61–63) | 63.5 | rigid | — | — | low |

**Cross-checks on the Standard 350-stack:**

- A maker's "double stack ~90 mm" in a Ø66 holder (Thingiverse 792350) gives 0.129 per sheet.
- A Ø65 holder with 40 mm inside height for 360 discs, slightly compressed (Printables 414912),
  gives 0.111 per sheet.
- The Cults3D Go holder is Ø65 × 45 inside.
- Package depths: 43<sup>R</sup> (JP shop), 4.3 cm (Rushfaster), 1.6 in (Target) and 1.75 in
  (Bean & Bean).
- So a 350 stack is ≈40–45 mm. Nobody has caliper-measured a full stack.

**Metal and odd sizes:**

- The Able Disk's "69.85 mm" is a packaging size; one listing gives 62.2 mm.
- Able Disk XL is listed at 72<sup>R</sup>. The AeroPress XL stainless disc is 2.9 in<sup>S</sup>.
- Fellow Prismo 60<sup>U</sup>.

### Box sizing

| Box | Registry `diameter` (largest disc held) | Radial slack | **Interior Ø** | **Interior depth** | Depth reasoning |
|---|---|---|---|---|---|
| Standard | 65.0 | 1.0 | **67** | **55** | 50 worst-case stack + 2.5 lip + ≈2.5 margin |
| XL | 75.0 (74 rounded up) | 1.0 | **77** | **35** | 29 worst-case stack + 2.5 lip + ≈3.5 margin; also covers the 33 mm retail carton |

**Why Ø67 / Ø77.** Working DIY holders use Ø65 (Printables 414912, Cults3D) and Ø66
(Thingiverse 792350). Ø67 gives 1 mm per side over the largest listed 65 mm disc, and 1.75 mm
over the spec disc. More slack lets the stack shift. The base footprint is Ø71 / Ø81 with 2.0
walls, before lid features.

**Why the depth includes the lip.**

- The flat-lid designs (magnet-flat, magnet-pedestal) carry a 2.5 mm alignment lip (`LIP_H` 2.5,
  `LIP_T` 1.8, `LIP_CLEAR` 0.5).
- In the Ø67 bore the lip ring spans R 33.0 → 31.2. The disc edge sits at R 31.75 (Ø63.5) to
  R 32.5 (Ø65). So the lip comes down **onto the disc edges**, and the headroom at the edge is
  depth − 2.5. The XL is the same: lip R 38.0 → 36.2, disc edge R 36.85–37.5.
- A wedge stack keeps ≥3.5 mm from the arc wall and misses the lip. A disc in a close bore
  cannot.
- At the "pack + 7" depth of 52 the edge would get 49.5, less than the 50 mm worst case.
- One depth serves all four designs, although the friction and magnet-skirt lids have no lip in
  the bore.

**Capacity of the Standard box** (52.5 mm usable at the edge):

| Fits | Does not fit |
|---|---|
| one official 350-pack (≤50) | an Aesir 300-pack (66–73) |
| ≈215–240 Aesir discs | the official holder's 550 (≈78) |
| ≈310–350 CAFEC discs | |
| 100 Aesir + 200 official (≈47 typical) | |

The two misfits would need a tall variant of ≈82 mm, which is not built. The XL box holds one
200-pack. It cannot take a Standard 350 stack, even with a spacer ring: that would need an XL box
55 deep.

**Designs — the maintainer's decisions (2026-11-18):**

- All four designs for both sizes, magnet-skirt included.
- The round friction lid is **twist-off with no side grip notches**: a rotating notch could line
  up with the scoop and leave a dust slit.

**Agent choices awaiting the maintainer's review:**

- The engraving is narrower and centred. The 60 mm text fails the "inside interior − 4" guard:
  Ø67 − 8 = 59 mm max chord.
- A D-shaped pedestal: the moat only in front of the finger bay (research target: ≥10 mm of
  disc overhang, like the wedge boxes' 11.5). At the middle of the bay the stack overhangs the
  moat by 11.5–13 mm — official Ø63.5 to the largest Ø65 discs (XL: 11.7–13), pushed away
  from the bay; toward the bay's edges less (≥7.7 mm). Its wall cove is capped at 0.8 mm (under
  the 1 mm disc slack), so the largest discs lie flat on it. Whether 0.12 mm discs sag into the
  moat is unverified.
- The magnet-skirt tripod: side notches at ±120°, three lobes 120° apart (the lid fits three
  ways) instead of a keyed, one-way layout.
- Depths 55 (Standard) / 35 (XL): worst-case stack + the flat lids' 2.5 mm lip + margin.

### Naming and holders

- **Official name:** "Paper Micro-Filters".
- **SKUs:** AER81F12 (Standard 350 white), AER81NA12 (Standard 200 natural), AERXLF12 /
  AERXLFNA12 (XL 200), AERXLMF12 (XL stainless)<sup>R</sup>. AER80FH1 (Filter Holder) is
  unconfirmed.
- **Japan:** "エアロプレス用ペーパーフィルター". The same 350-pack is listed at 63 (Tonya) and
  65 (connexcoffee, 0141coffee).
- **Official holders:**
  - Filter Holder: up to 550, Standard only<sup>S</sup>.
  - Go Filter Holder: 20<sup>S</sup>.
  - Travel Filter Holder (aluminium, two compartments): 50, Standard + XL<sup>R</sup>.
  - Go Plus built-in holder: 25<sup>U</sup>.

### Corrections from the fact-check

- The box depths went from 52 / 32 to **55 / 35**, because of the lip over the disc edges. The
  draft's own arithmetic ("fluffed 50 + 7 = 52") did not add up.
- The typical stack went from 43 to 44 (Standard) and from 24.5 to 25 (XL), to agree with
  0.125 per sheet.
- Aesir's "spec" thickness copies coffeeadastra's measurement, error bar included, so it is one
  source. The SKU "AESIR-FLT-100" was not found anywhere.
- The UK FAQ's "20" refers to the Go holder. The Travel holder holds 50 and takes both sizes.
- Spacer-ring sharing works only with a 55-deep XL box.
- A Ø49–51 pedestal would leave only 6.75 mm of disc overhang.

<details><summary>Sources — AeroPress</summary>

- Official: [micro-filters](https://aeropress.com/products/micro-filters),
  [XL micro-filters](https://aeropress.com/products/aeropress-xl-paper-micro-filters),
  [XL natural](https://aeropress.com/products/aeropress-natural-paper-micro-filters-xl),
  [Filter Holder 550](https://help.aeropress.com/en-US/how-many-micro-filters-fit-into-the-aeropress-filter-holder-729200),
  [Go holder 20](https://help.aeropress.com/en-US/how-many-micro-filters-fit-into-the-aeropress-go-filter-holder-123173),
  [filters FAQ](https://help.aeropress.com/en-US/articles/filters-33629),
  [aeropress.co.uk FAQ](https://www.aeropress.co.uk/pages/faqs)
- Measured: [coffeeadastra](https://coffeeadastra.com/2019/08/04/an-in-depth-analysis-of-coffee-filters-2/)
- Retail (Standard): [KaffeBox](https://www.kaffebox.no/product/aeropress-filter/),
  [Coffee Chronicler](https://coffeechronicler.com/aeropress-filters/),
  [Two Chimps](https://twochimpscoffee.com/blogs/aeropress-filters/),
  [connexcoffee](https://connexcoffee.net/shop/product/aeropress-paper/),
  [0141coffee](https://0141coffee.jp/?pid=134634533), [Tonya](https://www.tonya.co.jp/shop/g/g34136/),
  [The Coffee Shop JP](https://os.thecoffeeshop.jp/fs/thecoffeeshop/aeropress_paperfilter),
  [Target](https://www.target.com/p/aeropress-paper-micro-filters/-/A-50490282),
  [Rushfaster](https://rushfaster.com.au/products/aeropress-paper-micro-filters-standard-pack-of-350),
  [Bean & Bean](https://beannbean.com/products/aeropress-micro-filters-for-aeropress-aeropress-go),
  [Seattle Coffee Gear](https://www.seattlecoffeegear.com/aeropress-filters-350-count),
  [Canadian Tire](https://www.canadiantire.ca/en/pdp/aeropress-biodegradable-paper-coffee-micro-filter-350-pk-0766541p.html),
  [Espresso Parts 350](https://www.espressoparts.com/products/aeropress-standard-micro-filters-350-count),
  [Espresso Parts natural 200](https://www.espressoparts.com/products/aeropress-standard-natural-paper-micro-filters-200-ct),
  [Kaffeemacher kit](https://kaffeemacher.de/en/products/aeropress-the-original-incl-100-filters)
- Retail (XL): [Dwight's](https://dwights.co.nz/products/aeropress-xl-paper-filters-200pk),
  [Espresso Parts XL](https://www.espressoparts.com/products/aeropress-xl-micro-filters-200-ct),
  [XL natural](https://www.espressoparts.com/products/aeropress-xl-natural-paper-micro-filters-200-ct),
  [XL stainless](https://www.espressoparts.com/products/aeropress-xl-stainless-steel-reusable-filter),
  [Rushfaster XL](https://rushfaster.com.au/products/aeropress-paper-micro-filters-xl-pack-of-200),
  [Rushfaster XL natural](https://rushfaster.com.au/products/aeropress-natural-paper-micro-filters-xl-pack-of-200),
  [Target XL](https://www.target.com/p/aeropress-xl-micro-filters-200ct/-/A-91774849),
  [REI XL](https://www.rei.com/product/234184/aeropress-xl-natural-micro-filters-package-of-200),
  [CoffeeGeek XL](https://coffeegeek.com/blog/new-products/the-aeropress-xl-is-here-worth-the-wait/)
- DIY holders: [Thingiverse 792350](https://www.thingiverse.com/thing:792350),
  [Printables 414912](https://www.printables.com/model/414912-aeropress-filter-container),
  [Cults3D Go holder](https://cults3d.com/en/3d-model/home/filter-holder-aeropress-go),
  [wezhape](https://wezhape.com/products/aeropress-filter-holder-high-for-two-filter-packs),
  [Printables 530570 (XL)](https://www.printables.com/model/530570-aeropress-xl-coffee-maker-filter-holder),
  [Thingiverse 6088196 (XL)](https://www.thingiverse.com/thing:6088196)
- Third-party discs: [KaffeBox Aesir](https://www.kaffebox.no/product/aesir-premium-aeropress-filters/),
  [Alternative Brewing Aesir](https://alternativebrewing.com.au/products/aesir-paper-filter/),
  [Eight Ounce Aesir](https://eightouncecoffee.com/products/aesir-filters),
  [Amazon Aesir](https://www.amazon.ca/AESIR-Filters-100/dp/B072M5HG4Q),
  [Runty Roaster CAFEC](https://www.runtyroaster.com/products/filtry-cafec-dla-aeropress),
  [KaffeBox CAFEC](https://www.kaffebox.no/product/cafec-premium-coffee-filter-for-aeropress/),
  [Scandinavian Alps CAFEC](https://scandinavianalpscoffee.com/products/aeropress-micro-filters-cafeac-made-in-japan),
  [CAFEC catalogue](https://cafec-jp.com/jp/catalog/), [CAFEC filter papers](https://cafec-jp.com/products/filterpaper/),
  [desertcart generic](https://www.desertcart.sn/products/384893410-400-pcs-filter-paper-compatible-with-aeropress-6-4cm-2),
  [Homegrounds](https://www.homegrounds.co/best-filters-for-aeropress/)
- Metal discs: [IMS D62SF15](https://www.idrinkcoffee.com/products/ims-e-b-lab-stainless-steel-aeropress-filter-150-microns-d62sf15),
  [Woolworths 61 mm](https://www.woolworths.com.au/shop/productdetails/1115179437),
  [Able Disk](https://thebasicbarista.com/products/able-disk-reusable-aeropress-filter),
  [desertcart Able](https://www.desertcart.uy/products/1559572),
  [Someware Able](https://goingsomeware.com/products/able-disk-standard),
  [MyDeal Prismo](https://www.mydeal.com.au/fellow-prismo-filter-10159380),
  [coffeeforums](https://www.coffeeforums.co.uk/threads/stainless-filter-for-aeropress.41221/),
  [home-barista sticky papers](https://www.home-barista.com/tips/diy-3d-printed-slanted-holder-for-sticky-filter-papers-t104526.html)

</details>

## 4. Origami dripper papers

> **Researched only; boxes, if any, come in the follow-up PR (maintainer's decision,
> 2026-11-18).** This section had **one research pass and no independent fact-check.** Treat
> its numbers as provisional.

**Bottom line: Origami users need no new box sizes.**

- **Cone papers go in the tabless CAFEC boxes** `v60-cafec-01` / `v60-cafec-02`, not the depth-42
  all-brands V60 boxes. Those are 42 deep, sized for smooth Hario paper that nests at
  ~32 mm/100. Origami's two-sided crepe does not nest (≈0.5 mm per folded filter<sup>R</sup>, so
  ≈50 per 100<sup>D</sup>). A full pack would be squeezed; ≤ ~80 sheets would fit.
- **Wave papers go in the future Kalita Wave boxes** (section 5).

| Paper | Form | Pack | Published sheet size | Likely real cut | 100-stack, typical / max | Maps to |
|---|---|---|---|---|---|---|
| Paper Filter [Cone] 2杯用 / Cup2 / S, made by CAFEC | flat cone → 90° wedge<sup>D</sup> (60° cone); tabless expected, not stated | 100 | ≈100×100×0.5<sup>R</sup> (one shop) | ≈101×106<sup>D</sup> (CAFEC cup 1 cut) | 45<sup>D</sup> / 50<sup>D</sup> | **v60-cafec-01** (side 106, depth 47) |
| Paper Filter [Cone] 4杯用 / Cup4 / M, made by CAFEC | as above | 100 | ≈130×130×0.5<sup>R</sup> (one shop) | ≈121×127<sup>D</sup> (CAFEC cup 4 cut) | 50<sup>D</sup> / 55<sup>A</sup> | **v60-cafec-02** (side 127, depth 54) |
| Paper Filter [Wave] CUP2 / S ("155") | nested flat-bottom cup, narrow pleats for 20 ribs | 50<sup>S</sup> | none published | Kalita Wave 155 class<sup>R</sup> | — | future Wave 155 / 185 box |
| Paper Filter [Wave] CUP4 / M ("185") | as above | 50<sup>S</sup> | none published | Kalita Wave 185 class<sup>R</sup> | — | future Wave 185 box |
| Sibarist ORIGAMI SE FAST (for S) | flat pre-creased round sheet | 25 / 100<sup>S</sup> | no diameter | — | — | none (niche) |

**Why the Cup4 is probably not a true 130 mm sheet:**

- **Pack weights:** net 122–128 g against 85–88 g<sup>R</sup>, a ratio of ≈1.44. That matches the
  CAFEC cup 1 → cup 4 area ratio of 1.435; 100 → 130 would give 1.69.
- **Distributor package:** 120×140×80<sup>R</sup>. A 130 mm quarter-disc cannot lie flat in a
  120 mm side.
- **Dripper slant:** the official dripper is Φ138×H87 with a Φ25 hole<sup>S</sup>. For a 60° cone
  that implies an inner slant of ≈125.5<sup>D</sup>. The S dripper, Φ115×H70, gives ≈106.

**Margins in the mapped boxes:**

| Paper | Box | Footprint | Depth | If a measurement says otherwise |
|---|---|---|---|---|
| Cup2 | v60-cafec-01 | fine | 47, i.e. 3 mm under the worst-case 50 (the same trade-off as CAFEC cup 1) | raise the depth to 52–54 if a stack measures ≈50 |
| Cup4 | v60-cafec-02 | 127 + 3.5 = 130.5 holds a 121–127 sheet, but only 0.5 mm beyond the retail 130 | fine | if a ruler shows > 127, bump the side to 130 (≈ +3 mm footprint, still fits CAFEC cup 4) |

**Naming:**

- Brand ORIGAMI (K-ai Co., Gifu; origami-kai.com).
- Drippers: S (1–2 cups) Φ115×H70 and M (2–4) Φ138×H87<sup>S</sup>; Air S Φ110×H70 and Air M
  Φ142×H87. The Pinn (a 55° cone) uses the 2-cup paper.
- Codes: cone 78764008 / 78765005; wave 78750957 / 78750964; Cone+Wave sets 78750971 /
  78750988.
- Retailers equate Origami S with V60-01 / Kalita 155, and M with V60-02 / Kalita 185.
- The wave papers launched 2024-10-24. Most listings say they are made in China; one says Japan.

<details><summary>Sources — Origami (single pass)</summary>

- Official: [paper filter (cone)](https://origami-kai.com/en/products/origami_paper_filter),
  [paper filter (wave)](https://origami-kai.com/en/products/paper-filter-wave)
- Sheet sizes and packs: [Kyoto Sajikame Cup2](https://shop.kyoto-sajikame.jp/?pid=174373896),
  [Kyoto Sajikame Cup4](https://shop.kyoto-sajikame.jp/?pid=173786043),
  [Yahoo phezzan](https://store.shopping.yahoo.co.jp/phezzan/sa-4536058764008.html),
  [Belco Cup2](https://www.belco.fr/en/equipements/ORIGAMI_99300188),
  [Belco Cup4](https://www.belco.fr/en/equipements/ORIGAMI_99300288),
  [Slow Pour](https://www.slowpoursupply.co/products/origami-paper-filter),
  [Highwire](https://www.highwirecoffee.com/products/origami-drip-filters-medium-pack-100),
  [Komameya (CAFEC-made)](https://komameyalab.base.shop/items/86078633),
  [Kohiraifu](https://kohiraifu.com/products/origami-paper-filter),
  [Rogue Wave](https://roguewavecoffee.ca/products/origami-coffee-filter-paper-100-sheets),
  [Roberta Sami](https://www.robertasami.com/filters),
  [doma](https://www.domacoffee.com/products/origami-filter),
  [TRUNK](https://trunkcoffee.thebase.in/items/27974724),
  [captncoffee](https://captncoffee.com/en-int/products/origami-filterpapier-cup-4-fur-origami-dripper-m-100-stuck),
  [home-barista thread](https://www.home-barista.com/brewing/origami-cone-wave-filter-new-era-on-brewing-t64604-10.html),
  [The Roasters Pack](https://theroasterspack.com/products/origami-dripper-1)
- Cone angle: [gota.cafe Pinn](https://gota.cafe/en/recipes/origami-pinn),
  [The Basic Barista dripper](https://thebasicbarista.com/products/origami-dripper)
- Wave: [Kurasu](https://kurasu.kyoto/products/origami-paper-filter-wave),
  [Kurasu JP](https://jp.kurasu.kyoto/products/origami-coffee-filter-wave),
  [gota.cafe wave](https://gota.cafe/ja/filters/origami-wave),
  [wb.coffee](https://www.wb.coffee/shop/origami-paper-filters-flat-bottom-s-wave-2-155mm-52478),
  [Hooray](https://hooraycoffee.ca/products/cafec-abaca-plus-filter-paper),
  [Slow Pour wave](https://www.slowpoursupply.co/products/origami-wave-filter-box-in-2-sizes),
  [Stitch](https://stitch.coffee/products/origami-wave-filter-paper),
  [Origami AU](https://origamidripper.au/products/origami-wave-filter),
  [Rakuten launch notice](https://item.rakuten.co.jp/bikenshop/selxki23124201/),
  [umaicoffee](https://www.umaicoffee.jp/product/4846),
  [chronic.ch Sibarist](https://chronic.ch/en/products/sibarist-wave),
  [The Basic Barista wave](https://thebasicbarista.com/products/origami-wave-filters),
  [Lois](https://loisthestore.com/products/origami-original-paper-filter-copy)
- Sibarist SE: [sibarist.coffee](https://sibarist.coffee/products/origami),
  [Kurasu](https://jp.kurasu.kyoto/en/products/sibarist-origami-limited-fast-specialty-coffee-filter),
  [Slow Pour](https://www.slowpoursupply.co/collections/round-filters/origami)

</details>

## 5. Kalita Wave 155 / 185 and other flat-bottom cups

> **Researched only; boxes come in the follow-up PR (maintainer's decision, 2026-11-18).**

Kalita makes only two Wave sizes<sup>S</sup>. The number is the **flat-sheet diameter**
(全幅). The filters are pre-formed one-ply cups with **20 waves**<sup>S</sup> around a flat
bottom, and they store as a **nested cup stack**. ("TSUBAME" is a Kalita dripper line, not a
filter.)

| | Wave 155 (KWF-155) | Wave 185 (KWF-185) |
|---|---|---|
| Cups | 1–2<sup>S</sup> | 2–4<sup>S</sup> |
| Flat-sheet Ø | 155<sup>S</sup> | 185<sup>S</sup> |
| Flat bottom disc | 40<sup>S</sup> | 40<sup>S</sup> |
| Bottom footprint, typical / max | 50<sup>R</sup> / 55<sup>A</sup> | 50<sup>R</sup> (Altura 51) / 55<sup>A</sup> |
| **Rim Ø across the wave tips**, typical / max | **88 / 95**<sup>D</sup> (see note) | **105**<sup>R</sup> (Wataru 104) / **114**<sup>R</sup> (Altura) |
| Cup height, typical / max | 50<sup>R</sup> (Wataru 51) / 55<sup>D</sup> | 61<sup>R</sup> / 65<sup>D</sup> |
| Nest rise per extra filter Δ, typical / max | 0.33 / 0.45<sup>D</sup> | 0.42 / 0.48<sup>D</sup> |
| **100-stack height**, typical / max | **83 / 100**<sup>D</sup> | **103 / 108**<sup>D</sup> (max = inside of the 100P carton) |
| 50P carton | 111×90×69, 80 g<sup>S</sup> | 111×111×85, 107 g<sup>S</sup> |
| 100P package | 110×110×80, 100 g<sup>R</sup> | 120×120×110, 150 g<sup>R</sup> |
| Sheet weight | 1.1 g<sup>R</sup> | 1.4 g<sup>R</sup> |
| Codes, 50P current / older (same JAN) | 22227 / #22211<sup>S</sup> | 22228 / #22210<sup>S</sup> |
| Code, 100P | #22213<sup>R</sup> | #22212<sup>R</sup> |
| Confidence | low | medium |

- **The 155 rim is the least certain number.** The only listing, Wataru's 74, is probably the
  valley circle. Five pieces of evidence point to a tip circle of ≈88–93:
  - the 90 mm carton depth;
  - the Ø100 flange of the WDS/WDC-155 dripper;
  - a 155 filter's sides conform to a 185 dripper;
  - a paper-length model gives tips at ≈92 and valleys at ≈74;
  - a 74 rim would imply a 13° wall, which cannot nest within the carton.
- The retail "Φ185 H43 / Φ155 H15" figures are wrong. An H43 cup would need a ≈154 mm rim,
  which cannot fit the 111 mm carton.
- **Reference container:** the Kalita & RIN filter case (44324) is ≈118×118×95 inside
  (125×125×110 outside) and holds "約75枚" of either size<sup>S</sup>. Coffee Sakura says
  100 × 155 or 75 × 185<sup>R</sup>.
- **Size compatibility:** the 155 has the same bottom as the 185, so a 155 stack sits inside any
  185-size box. A 185 in a 155 dripper sticks out ≈15 mm.

**Stack model.**

- The stack is a frustum from the footprint Ø_b to the rim Ø_t over the cup height h1, then a
  cylinder of Ø_t up to `h1 + (N − 1)·Δ`. Always use the wave-tip circle for Ø_t.
- Self-check: `Ø_t = Ø_b + 2L·sin α`, `h1 = L·cos α`, with `L = R_flat − r_b`. For the 185 this
  gives L 67.5, α ≈ 23.6°, h1 ≈ 62, which matches Wataru.
- "Per 100" means the height of a 100-stack, **not 100·Δ**. A draft made that mistake, which
  would have built a box ≈60 mm too shallow.

**Other flat-bottom cups:**

| Paper | Data | Box relevance |
|---|---|---|
| Origami Wave CUP2 / CUP4 | no published dimensions; sold as interchangeable with 155 / 185 (section 4) | allow +3–5 mm on the rim and ≈3 mm extra headroom |
| Orea Wave | 185 size only<sup>R</sup> (flat 185×185) | 185 box |
| Sibarist WAVE S / M | wave equivalents (their FLAT S / M are not fluted) | 155 / 185 boxes |
| Timemore Basket Paper Filter 01 (B75) | flat 155, base 55, H48, 50-pack<sup>U</sup>; rim ≈83<sup>D</sup> | 155 class |
| Kalita Basket Filter 205 (22175; business line, not branded Wave) | flat 205, bottom 95, 50P carton 147×147×68, 140 g<sup>S</sup>; rim ≤ ~145, 50-stack ≤ ~66, cup ≤ 55<sup>D</sup> (bounds only) | needs a measurement |
| Orea Big Boy filter | 8 cm flat bottom, 100-pack, 600 ml – 1 L<sup>R</sup>; no flat Ø, rim or height published | needs a measurement |

**Proposed round boxes** (plain cylinder interior):

| Box | Interior Ø | Depth, 100-pack | Depth, 50-pack | Notes |
|---|---|---|---|---|
| **Wave 185** (priority; also holds 155) | **118–120** | **≥ 120** (108 packed + 12 fluff; also covers the 112.5 worst-case combination) | ≈95 (83 + 10–12) | equals the inside of Kalita's case; don't go below ~110, since that 95-deep case is rated for only 75 × 185 |
| Wave 155 (optional) | ≈99–100 | ≥ 105, comfortably 110 | ≈85 | Ø92 is too tight if the rim opens to ≈92–93 |

- **Lid:** the whole top must open. Use a lay-on lid in magnet-flat style or a telescoping
  friction lid. The lip ring must sit outside Ø_t, and the lid must not press on the stack:
  pleats crush under axial load.
- **No scoop, side notches, pedestal or finger bay.** The top filter is picked from inside its
  cup.
- Don't taper the interior to follow the cone. The as-stored wall angle is uncertain, rims relax
  after opening, and a narrowing cone wedges the stack.
- One parametric round-cup case, driven by (Ø_t, h1, Δ, N), would also cover Origami Wave, Orea
  Wave, Sibarist WAVE, Timemore B75, Kalita Basket 205 and the US machine baskets (section 6).

**Corrections from the fact-check:**

- The 155 rim went from 74 to 88 typical / 95 max.
- The per-100 field had been filled as 100·Δ; it is now the stack height.
- Max cup heights went up to 55 / 65. The 185 Δ max went to 0.48 and its 100-stack max to 108.
- The claim that "100 × 185 do not fit Kalita's case" has no source.
- A larger Kalita flat-bottom paper does exist (Basket Filter 205).
- The current codes are 22227 / 22228.

<details><summary>Sources — Kalita Wave and flat-bottom cups</summary>

- Kalita official: [KWF-155](https://www.kalita.co.jp/products/coffeefilter/3760),
  [KWF-185](https://www.kalita.co.jp/products/coffeefilter/3761),
  [wave series (20 waves)](https://www.kalita.co.jp/products/waveseries/),
  [Kalita & RIN case](https://www.kalita.co.jp/products/mill/3748),
  [set 3135](https://www.kalita.co.jp/products/set/3135), [set 3136](https://www.kalita.co.jp/products/set/3136),
  [Basket Filter 205](https://www.kalita.co.jp/products/b_filter/2113),
  [business filters](https://www.kalita.co.jp/products/b_filter)
- Per-sheet and pack data: [Wataru 155](https://watarucoffee-onlinestore.com/?pid=157347976),
  [Wataru 185](https://watarucoffee-onlinestore.com/?pid=157329432),
  [Altura 185](https://www.alturacoffee.co.nz/accessories/brew-products/kalita-kwf-185-wave-filter-papers-50-sheets/),
  [tsujimoto 185](https://tsujimoto-coffee.com/c/all/stekinadougu/e_bland/e_kalita/tk-22199),
  [tsujimoto 155](https://tsujimoto-coffee.com/c/all/stekinadougu/e_bland/e_kalita/tk-22201),
  [tao 155](https://shop.tao.co.jp/products/detail/74),
  [Re:CENO](https://www.receno.com/coffeefilter2/ka-wf.php),
  [0141coffee 185 100P](https://0141coffee.jp/?pid=125604860),
  [0141coffee 155 100P](https://0141coffee.jp/?pid=125604780),
  [highfive 155 100P](https://highfive0801.thebase.in/items/12668656),
  [Yahoo 155](https://store.shopping.yahoo.co.jp/roomania-l/4901369222118.html),
  [malki](https://www.shop.malki-coffee.com/products/detail/160),
  [yamato-ya](https://shop.yamato-ya.jp/8573/), [Tonya](https://www.tonya.co.jp/shop/g/g303122/),
  [Coffee Sakura case](https://shop.coffeesakura.co.jp/products/coffeefiltercase01-1),
  [dscafestyle 2021](https://dscafestyle.com/todays-coffee/2021-06-03/),
  [dscafestyle 185 in 155](https://dscafestyle.com/how-to-coffee/wavefilter185_use_kalitawave155/),
  [coffee-pharmacist](https://coffee-pharmacist.com/wavefilter-bag)
- Equivalents: [Basic Barista Orea Wave](https://thebasicbarista.com/en-us/products/orea-wave-filters),
  [Rogue Wave Origami Wave](https://roguewavecoffee.ca/products/origami-wave-paper-filter),
  [Coffee Parts Timemore B75](https://www.coffeeparts.com.au/timemore-wave-filter-paper-01-for-b75-50pcs),
  [Timemore](https://www.timemore.com/products/timemore-basket-paper-filter-01-for-b75),
  [Rogue Wave Big Boy](https://www.roguewavecoffee.ca/products/orea-big-boy-filter),
  [3FE Big Boy](https://3fe.com/products/orea-big-boy-filter-paper),
  [Slow Pour Big Boy specs](https://www.slowpoursupply.co/pages/big-boy-specs)

</details>

## 6. Drip-machine papers

> **Researched only; boxes come in the follow-up PR (maintainer's decision, 2026-11-18).**

### A. Melitta-style cone papers (the same fan family as Kalita)

The 1x2 / 1x4 / 1x6 papers share one shape and differ only in size. Tingstad says they "all have
the same shape and angle"<sup>S</sup>. They match Kalita 102 / 103 / 104 by overall size
(section 2).

| Class | Names | b (bottom) | h (centre height) | c (top chord) | θ<sup>D</sup> | side<sup>D</sup> | sagitta<sup>D</sup> | R from the virtual apex<sup>D</sup> | 100-stack, typical / max |
|---|---|---|---|---|---|---|---|---|---|
| **1x2** | Melitta 1x2, US #2, Kalita 102, Brooks 102 | 52<sup>A</sup> / 54<sup>S</sup> (Brooks; Melitta JP 47<sup>S</sup>) | 101<sup>D</sup> / 103<sup>S</sup> (Tingstad 100<sup>S</sup>) | 162<sup>D</sup> / 165<sup>S</sup> (Kalita 160<sup>R</sup>) | 75° (72.2–75.4), max 77 | 90 / 93 | 30 / 31 | 135 / 140 | 45<sup>D</sup> (Melitta JP 100P box 48 thick<sup>S</sup>; Kalita NK bag 40<sup>S</sup>) / 54<sup>U</sup> |
| **1x4** | Melitta 1x4, US #4, EU "Size 4", Kalita 103, Brooks 103, Tingstad 1x4 | 52<sup>S</sup> (PO-148B) / 54<sup>S</sup> (Brooks); Tingstad 50<sup>S</sup>; "2 in"<sup>R</sup> | 127<sup>R</sup> / 128<sup>S</sup> (Tingstad 125<sup>S</sup>) | 193<sup>R</sup> / 195<sup>S</sup> (Tingstad 190<sup>S</sup>) | 75° (74.7–75.8), max 77 | 115 / 118 (retail 4.5 in = 114<sup>R</sup>) | 35 / 37 | 161 / 166 | 50 / 56<sup>D</sup> (EU 80-box 42–43 thick<sup>R</sup>; Kalita bags 45 / 50<sup>S</sup>) |
| **1x6** | Melitta 1x6, US #6, ≈ Kalita 104 | 52 / 54<sup>A</sup> | 150<sup>S</sup> (Tingstad) / 155<sup>R</sup> (Kalita 104) | 220<sup>D</sup> / 226 | 75° (73.7–74.5), max 77 | 139 / 144 | 40 / 41 | 184 / 192 | only 40-packs found (21 per 40<sup>U</sup>) |

- **The arched top is required, not just reported.** Model the paper as the flat layout of a
  level-rim liner in a slot-to-round-rim dripper. Such a liner always has a side edge shorter
  than its centre height. Fitted to the spec triples, the model gives θ ≈ 75°, side ≈ 0.90·h and
  sagitta ≈ 0.28·h. The retail #4 side of 4.5 in (114) agrees.
- A retailer's "side 125–130 mm" (Deer) is rejected. The same page also claims an impossible
  "58–62° between sidewall and axis".
- **Arc centre.** In this model the top curve is a near-circle of radius ≈1.17·h, centred
  21–23 mm below the bottom edge, not at the virtual apex (32–35 mm below). See section 2 for
  the Kalita trace, which found it concentric.
- **Box rule that holds under either model:** `R_need = h_max + (b_max/2)/tan α`, where α is the
  interior half-angle. The paper's bottom corners decide how far it slides in, and the farthest
  point is the top centre. For 1x4 at α 40°, R_need = 160.2; for 1x2, 135.2.

**Proposed cone boxes** (follow-up):

| Box | Interior angle | r_int | Chord | Depth | Holds |
|---|---|---|---|---|---|
| **1x4 / #4 / Kalita 103** (priority 1) | 80° (θ max 77 + 3) | ≈166 (R_need 160.2 + `apex_tip_x` ≈2.2 + 3.5) | ≈213 | 60 (63 by "pack + 7") | 1x4, #4, Kalita 103; also 1x2 / Kalita 102 and old-102 / EU "Größe 2" (reach ≈147 < 161) |
| 1x2 / #2 (priority 2) | 80° | ≈141 | — | 58 | 1x2, #2, Kalita 102 |
| 1x6 / Kalita 104 | 80° | ≈193 | ≈248 | ≈58–60 | low demand; skip unless asked |

- The apex can be clipped at ≈29 mm, since no paper reaches it. That gives the 1x4 box a
  ≈137 mm centre line.
- **1x2 alternative:** the existing v60-02 outline (93°, r_int 140.0) holds a Brooks-size
  165 / 54 / 103 paper with ≈11 mm to spare. Only its depth of 42 is too shallow, so a "v60-02
  outline, depth 58" variant would carry 100 #2 papers and both V60-02 sizes.

**Relation to this PR's Kalita boxes.**

- **1x4 class:** by overall size (≤195 × ≤128, b 50–54) it falls inside the kalita-103 envelope
  (195 × 130, b 56; variants down to b 47, ≈75.7°, are checked).
- **1x2 class:** kalita-102's reference height is Melitta 1x2's 105, and `make verify` seats both
  Melitta 1x2 (160, 105, 47: 3.27 mm min clearance, 3.48 mm play) and Brooks 102
  (165, 103, 54: 1.83 / 5.48 mm — its bottom is 1 mm wider than the reference's 53, so it sets
  the bottom wall). Both checks use the fan model, so the liner-model caveat below applies to
  them too.
- **Uncertainty:** if the liner model is right (θ up to 77°, corners ≈4 mm lower), a 1x4 sheet
  meets the side walls slightly before it reaches the bottom wall. Whether it then keeps its
  slack is unverified.
- **Decision for the follow-up:** after one Melitta sheet is measured, either point 1x4 / 1x2
  users to the Kalita boxes or build the 80° boxes.

### B. US flat-bottom basket filters

A basket filter's spec "height", "depth" or "walls" figure is the **slanted wall** `w`, not the
vertical height. The cup height is `h = √(w² − ((rim − base)/2)²)`, and the stack height is
`h + (N − 1)·Δ`.

| Filter | Flat Ø | Base Ø | Slant wall | Cup height<sup>D</sup>, typical / max | Free rim Ø | Δ<sup>D</sup> | Stack | Confidence |
|---|---|---|---|---|---|---|---|---|
| **8–12 cup** (Mr. Coffee, Rockline / Brew Rite, Melitta, Hamilton Beach, store brands) | 200<sup>U</sup> / 203<sup>D</sup> | 83<sup>U</sup> / 89<sup>U</sup> (Mr. Coffee 3 in<sup>R</sup>) | 2.5 in<sup>R</sup> | 50 / 64 | 145 / 168<sup>U</sup> | 0.15 / 0.17 | 200-pack 80 / 83<sup>U</sup>; per 100: 65 / 81<sup>D</sup> | low |
| **Bunn home** (BCF100-B 100 ct, 20106.0000 1000 ct) | 216<sup>S</sup> (8.5 in) | 76<sup>S</sup> (3 in) | 70<sup>S</sup> (2.75 in) | 61 / 70 | 146 (limited by the pack) | 0.20–0.22 | 100-pack 83<sup>R</sup> (the pack is 5.75×5.75×3.25 in) | medium |
| **4–6 cup junior** | 175<sup>R</sup> (vxb 6.88 in; Brodys 7.87<sup>U</sup>) | 78<sup>R</sup> (3.07 in) | 48<sup>R</sup> (1.88 in) | 42 / 48 | ≈125<sup>A</sup> / 140 | — | packs of 200–400<sup>R</sup> | low |
| **Bunn 12-cup commercial** (20115.0000) | 248<sup>S</sup> (9 3/4 in, flattened) | 108<sup>S</sup> (4 1/4 in) | 70<sup>D</sup> | 58 / 70 | 185–198<sup>D</sup> (from an unverified case size) | 0.26–0.27 | 500 per bag; per 100: 84–97<sup>D</sup> | low |

**Proposed basket boxes** (follow-up; round, plain cylinder like the Wave boxes):

| Box | Interior Ø | Depth | Holds |
|---|---|---|---|
| **8–12 cup basket** | ≈172 | ≈90 for a 200-pack (83 + headroom); 85 for a 100-pack | 8–12 cup, Bunn home 100-packs (146 × 83) and 4–6 cup junior filters |
| Bunn 12-cup commercial | ≈205 | ≈105 for 100 | derived only, so build it last or never |

### Which sizes matter where

| Region | Most common machine paper | Second | Notes |
|---|---|---|---|
| Europe | **1x4 / Size 4**: "gebräuchlichste Größe für Kaffeemaschinen" (de.wikipedia) | 1x2 | standard pack 80; "Filtertüte" is a Melitta trademark, so other brands say Größe 2 / 4; the old 100-series is still seen in the Nordics |
| US | **8–12 cup basket** (Mr. Coffee, Hamilton Beach, Black+Decker, Bunn home) | #4 cone (cone-basket and premium machines) | packs of 100 / 200; this brand split is general knowledge, not sourced |
| Japan | Kalita 101–104 / Melitta JP 1x1 · 1x2 · 1x4 | — | Kalita 102 / 103 ≈ Melitta 1x2 / 1x4 |

So the follow-up priorities are a **1x4 cone box** (Europe, and US #4) and a round **8–12 cup
basket box** (US).

**Corrections from the fact-check:**

- θ ≈ 75°, not 73°. The 1x4 sagitta is 35, not 32, and the 1x2 side is 90, not 93.
- The arc is not centred on the apex in the liner model, so the box rule became R_need. The 1x4
  r_int drops from 169–170 to ≈166.
- Basket cup heights drop (57→50, 70→61, 48→42, 70→58) because spec "heights" are slant walls.
  The 8–12 cup max per 100 rises from 75 to 81.
- EU "Größe 2" is the **old** Melitta 102, not 1x2.
- The Bunn 5.75×5.75×3.25 in package is the 100-count retail pack, not a shipping box.
- The generic 8–12 cup basket numbers, the Bunn commercial case size and the 20116 / 20122 code
  mapping stayed unverified (the shops blocked fetching).

<details><summary>Sources — drip-machine papers</summary>

- Cone specs: [Brooks 102](https://www.brooks.co.jp/product/detail/211102),
  [Brooks 103](https://www.brooks.co.jp/product/detail/211103),
  [Askul PO-148B](https://www.askul.co.jp/p/NK99905/),
  [Melitta JP 1x4](https://www.melitta.co.jp/melitta_hh/paper/original1_4_nb/),
  [rayes-glass PE-12GB](https://www.rayes-glass.com/SHOP/PE-12GB.html),
  [Tingstad 1x4](https://www.tingstad.com/se-en/beverages-edibles/coffee/coffee-filters/coffee-filters-1x4-white-200-pack-104000),
  [Tingstad filter guide](https://www.tingstad.com/se-en/alla-kategorier/kunskapscenter/produktguider/kaffefilter),
  [Rakuten livingut](https://item.rakuten.co.jp/livingut/uni487611/),
  [Kalita 1888](https://www.kalita.co.jp/products/coffeefilter/1888),
  [Kalita set/1864](https://www.kalita.co.jp/products/set/1864),
  [Kalita set/1845](https://www.kalita.co.jp/products/set/1845),
  [Kalita set/1881](https://www.kalita.co.jp/products/set/1881),
  [kalita.us.com](http://www.kalita.us.com/products/coffeefilter/3096),
  [thecoffeebrewers #4](https://www.thecoffeebrewers.com/4whcofi2ctfo.html),
  [kaffee24 1x4/80](https://www.kaffee24.de/melitta-kaffeefilter-filtertueten-aroma-1x4-80-stueck),
  [office-partner](https://www.office-partner.de/melitta-filtert.1x4-weiss-80st-n1000047070),
  [desertcart 6658076](https://www.desertcart.hu/products/47986101-melitta-6658076-pack-original-size-1x4-80-filter-coffee-makers-brown-plastic),
  [de.wikipedia Kaffeefilter](https://de.wikipedia.org/wiki/Kaffeefilter),
  [Deer (values rejected)](https://www.deercoffeefilter.com/what-is-the-exact-size-of-the-4-coffee-filters-is-it-compatible-with-all-8-12-cup-models-from-mr-coffee-or-hamilton-beach/),
  [cafefrida 1x6 (unreachable)](https://cafefrida.de/melitta-filtertueten-1x6/)
- Baskets: [thriftywhite Mr. Coffee](https://shop.thriftywhite.com/mr-coffee-8-12-cup-filters-100-ct-1-pkg/),
  [retail.bunn.com 20106](https://retail.bunn.com/20106.0000),
  [Baumann BCF100-B](https://www.baumannpaper.com/show_product/BUN-BCF100B),
  [Bunn spec sheet A1.16](https://argo.webstaurantstore.com/documents/specsheets/paperfilter1.pdf),
  [WebstaurantStore 20115](https://www.webstaurantstore.com/9-3-4-x-4-1-4-12-cup-coffee-filter-bunn-20115-0000-case/234201150000.html),
  [vxb junior](https://vxb.com/products/4-to-6-cup-junior-basket-style-coffee-filters-whit)
- Unreachable in the fact-check (values marked <sup>U</sup>):
  [Amazon 8–12 cup](https://www.amazon.com/Coffee-Filters-Commercial-Machine-Disposable/dp/B0BJ6BCRD1),
  [Lowe's Melitta basket](https://www.lowes.com/pd/Melitta-Brown-Basket-Coffee-Filters-8-12-Cup-100-Count/8639269),
  [eBay](https://www.ebay.com/itm/314349487698),
  [KaTom 20115](https://www.katom.com/021-201150000.html),
  [Brodys junior](https://www.amazon.com/Brodys-Coffee-Filters-4-6-Cups/dp/B0D5139H9K)

</details>

## 7. Not yet boxed — planned follow-up

| Paper / family | Research status | Planned box (follow-up PR) | What would unblock it |
|---|---|---|---|
| Kalita 104 (FP104) | checked; dimensions from one retailer | fan box from envelope (230, 157, 58), depth 58; low demand | a second dimension source, the bottom edge |
| Origami Cone Cup2 / Cup4 | single pass | none new: document them under v60-cafec-01 / -02 | the real Cup4 side (≤127?), a 100-stack height |
| Origami Wave CUP2 / CUP4 | single pass | covered by the Wave boxes | any published dimensions |
| **Kalita Wave 185** (+ Origami Wave M, Orea Wave, Sibarist WAVE M) | checked | round Ø118–120 × ≥120 (100) / ≈95 (50); also holds 155 | a real stack height and its growth after opening |
| Kalita Wave 155 (+ Origami Wave S, Timemore B75, Sibarist WAVE S) | checked | optional round Ø≈100 × ≥105–110 (100) / ≈85 (50) | the rim across the wave tips |
| **Melitta 1x4 / US #4 / EU Size 4** | checked | point users to kalita-103, or build an 80° × r_int ≈166 × 60 box | one sheet: side edge and corner height |
| Melitta 1x2 / US #2 | checked | kalita-102 (Melitta 1x2 and Brooks 102 pass its variant check), or the v60-02 outline at depth 58 | one real sheet in a printed kalita-102 base |
| Old Melitta 102 / EU "Größe 2" | partial (only the 115 mm height is known) | point users to the 1x4 box | b, top width and angle |
| Melitta 1x6 / US #6 | checked | 80° × r_int ≈193; skip unless asked | — |
| **US 8–12 cup basket** (+ Bunn home, 4–6 cup junior) | checked; generic numbers unverified | round Ø≈172 × 90 | the free rim and stack height of a real 100 / 200 pack |
| Bunn 12-cup commercial | derived only | round Ø≈205 × 105; build last or never | the case size |
| Kalita Basket Filter 205, Orea Big Boy | partial | the same round-cup case | a physical measurement |
| AeroPress tall (the official 550 holder, Aesir 300) | checked | Standard box at depth ≈82 | the maintainer's call on capacity |

### Open measurement requests for the maintainer

A ruler is enough for most of these; a caliper is better for sheet edges.

1. **One Kalita FP102 sheet, flat:** bottom crease b, side, corner-to-corner chord c, centre
   height h, and the arc height above the corners. Expected: b 45–50, c 158–160, h ≈100,
   sagitta ≈27, α 74–76°.
2. **The bottom crease of FP101 and FP103.**
   - 101: the 50 comes from one shop. A bottom well under 45 mm (the machine-paper model allows
     ≈40–46) is outside the checked variants.
   - 103: no Kalita figure exists; 53 is assumed from Toyo.
3. **The loose 100-stack height of opened FP102 and FP103 packs,** when opened and a week later.
   This settles depth 52 / 57 against the 58 used.
4. **A loose AeroPress Standard 350-stack** measured with a ruler, fresh and a day after opening.
   Expected 40–45; the box is sized for 50. If available, also an XL 200-stack (expected 25–29).
5. **Kalita Wave:** the 155 rim across the wave tips (74 or 88–95?), and the 100-stack height of
   both sizes, packed and a week after opening.
6. **One Melitta 1x4 (or US #4) sheet:** side edge and corner height. This narrows θ (72–76°)
   and decides between the two arc models.
7. **Origami Cone Cup4:** the side length (121–127 or 130?), a free 100-stack height (≈50?) and
   whether there is a tab.
8. **US basket filters** (any contributor): the free rim Ø and stack height of a 100-pack and a
   200-pack.
9. **The Aesir disc diameter.** 65 max is assumed.
