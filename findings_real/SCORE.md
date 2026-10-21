# Findings 2 - REAL footage, Camera A27, Villeta (Paraguay)

Four excerpts cut straight from the DVR files, 23 minutes in total. Run with
the real camera's calibration:

```bash
python -m traffic_stats.report --site villeta-a27 \
       --videos samples_real --out findings_real
```

There is no ground truth for real footage, so the generic package is scored
against **`pipeline/`** - the tuned implementation that produced the published
survey of 11,693 vehicles over 8 days.

| clip | conditions | tuned `pipeline/` | generic `traffic_stats/` |
|---|---|---|---|
| `A27_20260831122920.mp4` | day, 08:29 local | 6 | 5 |
| `A27_20260831193236.mp4` | afternoon peak, 15:32 local | 11 | 11 |
| `A27_20260831224837.mp4` | DUSK, 18:48 local | 7 | 4 |
| `A27_20260831233637.mp4` | NIGHT, 19:36 local | 5 | 2 |
| **all four** | 23 minutes | **29** | **22** |

The afternoon peak clip **agrees exactly** (11 = 11), the morning clip is one
short, and both headway gates pass.
Dusk and night still come in at roughly half the tuned count. That gap is
real and is stated rather than papered over: the tuned pipeline has had
eight days of footage to be corrected against, and this one has had four
excerpts.

## What this run changed in the generic package

Running on real footage is what exposed these. All four fixes are generic:

1. **Morphology sized by band height, not pixels.** At night a vehicle is a
   PAIR of headlights separated horizontally, so the night kernel is much
   wider than tall. With one square kernel the pairs never joined and the
   night clip counted **zero**.
2. **Detect at half resolution** (`Site.detect_scale`). Downscaling averages
   away sensor noise, which is what lets small night blobs survive the
   morphological opening instead of being eroded away.
3. **A second counting line** (`Site.verify_x`), and a pass needs BOTH. A
   fence post or a patch of glare can oscillate across one line forever;
   nothing stationary travels from one line to the other. Before this, 15 of
   35 tiles on the contact sheet were the fence post.
4. The synthetic articulated gap was too narrow for realistic morphology to
   leave open, which quietly destroyed the demo's merge/no-merge contrast.

## Gates
```
vehicles counted      22
occupancy             19.5 %
clock offset applied  -1 day, 20:10:00
coverage              3.4 PARTIAL - label any peak as 'peak of available data'
headway LR            PASS  {'>60 s': 6, '30-60 s': 2, '15-30 s': 1, '1-1.5 s': 1, '1.5-3 s': 1}
headway RL            PASS  {'>60 s': 8, '3-6 s': 1}
GAP  2026-08-31T12:34:20 -> 2026-08-31T19:32:36  (418 min)
GAP  2026-08-31T19:37:36 -> 2026-08-31T22:48:37  (191 min)
GAP  2026-08-31T22:56:37 -> 2026-08-31T23:36:37  (40 min)

NOT REPORTED: speed, density. No distance anchor is set (Site.metres_per_band_height). See docs/APPROACH.md.
```

## Look at `contact_sheet.png`

22 tiles, one per counted vehicle: pickups, a loaded flatbed truck, a van, a
white utility truck, two night headlight pairs - and about seven tiles that
are the fence post or glare, not a vehicle. **That residual false-positive
rate is visible in one glance and invisible in the CSV.** It is the reason
the method puts looking at a contact sheet ahead of every numeric check.
