# traffic_stats — generic traffic statistics from fixed-camera video

Camera-agnostic reference implementation of `docs/APPROACH.md`. Mock, but
workable: it runs end to end with **no video, no model weights and no
network**, against synthetic footage whose ground truth is known, and scores
itself against it.

```bash
python -m traffic_stats.demo                          # synthetic + gates
python -m traffic_stats.demo --night-after 120        # exercise the night path
python -m traffic_stats.report --videos /footage      # real files
```

## Adding a camera

One file: `config.py`. Trace two polylines along the road edges, place the
counting line clear of every obstruction, record the occluder columns, and set
the clock offset you measured. Nothing else is site-specific.

```python
MY_SITE = Site(
    name="main-st-north", width=1280, height=720, fps=6.0,
    far =[(292, 88), ..., (1279, 220)],     # upper road edge
    near=[(292,140), ..., (1279, 315)],     # lower road edge
    occluders=[(524, 544), (1072, 1099)],   # poles, measured from the median background
    count_x=780,                            # clear of both poles
    clock_offset=dt.timedelta(hours=3, minutes=50),
)
```

`Site.__post_init__` refuses a counting line that sits behind an occluder.
That is the most consequential placement in the pipeline, so it fails loudly
rather than producing plausible nonsense.

## What it reports, and what it refuses to

Volume, direction split, cumulative, headway, occupancy, peak hour and
coverage — none of which need a distance calibration.

`stats.speed()` and `stats.density()` **raise** until
`Site.metres_per_band_height` is set from a distance measured on site. The
refusal is the feature: a wrong speed discredits the counts printed beside it.

## Before believing any number

```python
validate.headway_gate(crossings, site)   # spike under 1 s = double counting
validate.coverage_gate(spans)            # partial day = not a peak hour
validate.determinism_gate(run_a, run_b)  # same input, same output
validate.contact_sheet(crops, path)      # LOOK AT IT
```

The contact sheet is one tile per counted vehicle, cut from the clearest view
of it. No numeric gate replaces looking at it.

## Classification

`track.classify_by_size` is tier 3 from geometry alone — no model, no weights,
no network. **Its cut-points are placeholders.** Re-derive them from about a
hundred of your own labelled crops; they do not transfer between cameras, even
similar ones. Swap in a learned detector if you want tier 2 class names, but
keep counting independent of it: the weakest stage must never sit upstream of
the strongest output.

## Requirements

Python 3.10+, `numpy`, `opencv-python`, and `ffmpeg` on PATH for real video.
The demo needs no ffmpeg. No GPU.
