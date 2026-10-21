# Findings 1 - synthetic clips, scored against known ground truth

Generated on 2026-10-18. Every number traces to an image in `crops/`.

```bash
python -m traffic_stats.report --videos samples --out findings
```

| clip | conditions | truth | counted | error |
|---|---|---|---|---|
| `CAM01_20260301080000.mp4` | day, quiet (~20 s headway) | 68 | 62 | -8.8 % |
| `CAM01_20260301120000.mp4` | day, busy (~9 s headway) | 119 | 99 | -16.8 % |
| `CAM01_20260301173000.mp4` | DAY -> NIGHT, switches mid-clip | 74 | 72 | -2.7 % |
| `CAM01_20260301200000.mp4` | NIGHT, headlights only | 26 | 26 | +0.0 % |
| **all four** | 38 min | **287** | **259** | **-9.8 %** |

The night clip is exact. Counting from headlights alone is the stage
most implementations get wrong, so that is the one worth checking first.

## Vehicle type - size rules only, no model, no weights, no network

| class | truth | found |
|---|---|---|
| car | 118 | 74 |
| motorcycle | 46 | 25 |
| pickup_van | 59 | 45 |
| truck_2axle | 42 | 38 |
| truck_3axle_plus | 22 | 10 |
| unclassified_night | 0 | 67 |

`w_norm = box width / road-band height at that column`. The band height IS
the local perspective scale, so one number is comparable anywhere in the
frame with no camera calibration at all.

Night vehicles are counted but deliberately NOT classified. After dark the
blob is glare, not a body, so a size rule would be inventing an answer.

## Gates
```
vehicles counted      259
occupancy             37.5 %
clock offset applied  0:00:00
coverage              5.2 PARTIAL - label any peak as 'peak of available data'
headway LR            PASS  {'15-30 s': 33, '30-60 s': 18, '6-15 s': 31, '3-6 s': 26, '>60 s': 7, '1.5-3 s': 6}
headway RL            PASS  {'6-15 s': 47, '30-60 s': 20, '15-30 s': 23, '3-6 s': 26, '1.5-3 s': 12, '>60 s': 7, '1-1.5 s': 1}
GAP  2026-03-01T08:10:00 -> 2026-03-01T12:00:00  (230 min)
GAP  2026-03-01T12:10:00 -> 2026-03-01T17:30:00  (320 min)
GAP  2026-03-01T17:42:00 -> 2026-03-01T20:00:00  (138 min)

NOT REPORTED: speed, density. No distance anchor is set (Site.metres_per_band_height). See docs/APPROACH.md.
```

Both headway gates PASS: no spike under one second, so nothing is counted
twice. Coverage is flagged PARTIAL, so the busiest clip is labelled *peak of
available data* rather than the peak hour. Both gaps were derived from the
files on disk, not hardcoded.
