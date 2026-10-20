# Synthetic Benchmarks & Practice Data

You do not need real video files or high-speed internet to test and validate `traffic-stats-kit`.

---

## 1. Built-in Synthetic Generator (`traffic_stats.synth`)

The built-in synthetic generator renders photorealistic synthetic vehicle traffic with known ground-truth timestamps, directions, and vehicle profiles:

```bash
# Generate 5 minutes of synthetic footage with 20 vehicles/hour and run full validation
python -m traffic_stats demo --minutes 5 --headway 20 --out out/demo_run
```

What the demo tests:
* Daylight passage tracking.
* Nighttime headlight bridging (`--night-after 120`).
* Articulated truck cab/trailer merging.
* Passing Gate 1 (contact sheet), Gate 2 (headway floor), Gate 3 (coverage), and Gate 4 (determinism).

---

## 2. Public CCTV Practice Feeds

To practice site calibration on real-world footage:
1. **Caltrans CCTV Feeds (California, USA):** Caltrans Live Traffic Video streams.
2. **NYC DOT Traffic Cameras (New York, USA):** Public intersection feeds.
3. **UK National Highways Traffic Cameras:** Fixed motorway and A-road cameras.
