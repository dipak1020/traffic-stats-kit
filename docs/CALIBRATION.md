# Camera Calibration & Site Geometry Guide

Calibrating a new camera in `traffic-stats-kit` requires modifying a single configuration structure in `traffic_stats/config.py`.

---

## 1. Step-by-Step Calibration Workflow

### Step 1: Extract Diagnostic Background
Run the diagnostic calibration command on a sample video clip (5–10 minutes long):
```bash
python -m traffic_stats calibrate --video path/to/sample.mp4 --out out/diagnostics
```
This generates:
* `median_background.png`: Temporal median image removing passing traffic.
* `band_profile.png`: Vertical luminance variance across the roadway.

---

## 2. Defining Road Corridor Boundaries

Open `median_background.png` in any image editor or GIS tool (e.g., GIMP, Fiji, QGIS) and record pixel coordinates $(x, y)$:

```python
from traffic_stats.config import Site
import datetime as dt

MY_SITE = Site(
    name="villeta-km20-north",
    width=1920,
    height=1080,
    fps=15.0,
    # Far road edge (upper boundary of driving lanes)
    far=[
        (100, 420),
        (650, 410),
        (1200, 415),
        (1920, 430)
    ],
    # Near road edge (lower boundary / asphalt shoulder)
    near=[
        (100, 680),
        (700, 690),
        (1300, 710),
        (1920, 730)
    ],
    # Occluders: horizontal pixel spans of utility poles, trees, or bridge pillars
    occluders=[
        (540, 575),    # Concrete power pole
        (1420, 1460)   # Road sign stanchion
    ],
    # Counting line X coordinate (must NOT fall inside any occluder span!)
    count_x=980,
    # Clock offset if DVR drifted
    clock_offset=dt.timedelta(seconds=0),
    # Optional physical scale calibration (meters per band height at count_x)
    metres_per_band_height=14.5
)
```

---

## 3. Critical Placement Rules

1. **Occluder Clearance:** `Site.__post_init__` enforces that `count_x` does not intersect any column interval defined in `occluders`.
2. **Band Height Regularity:** The vertical distance between `near` and `far` must remain positive across the entire horizontal extent:
   $$y_{\mathrm{near}}(x) > y_{\mathrm{far}}(x) \quad \forall x \in [0, \text{width}]$$
3. **Verify Line Offset:** By default, `verify_x` is automatically placed at $x_{\text{count}} \pm 0.35 \cdot H(x_{\text{count}})$.
