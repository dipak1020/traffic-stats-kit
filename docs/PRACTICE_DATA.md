# Test Video Corridors & Sample Datasets

You do not need massive external video downloads to validate `traffic-stats-kit`, but when conducting field evaluations or sharing sample datasets with prospective clients, use the cloud and synthetic sources below.

---

## 1. Built-in Synthetic Generator (`traffic_stats.synth`)

The fastest way to test the complete pipeline on any computer without downloading video files:

```bash
# Generate 5 minutes of synthetic traffic (20 vehicles/hour) and run full gate validation
python -m traffic_stats demo --minutes 5 --headway 20 --out out/demo_run
```

What the demo validates:
* Day passage tracking and velocity back-calculation.
* Nighttime twin headlight bridging (`--night-after 120`).
* Articulated tractor-trailer in-frame spatial merging.
* Passing the 4 Non-Negotiable Gates (visual contact sheet, headway floor, coverage, determinism).

---

## 2. Cloud Sample Dataset (Google Drive & OneDrive)

### What to Place in Your Shared Cloud Drive:
Because GitHub restricts files over 100MB, keep a curated sample folder in Google Drive or OneDrive with:

```
Sample_Traffic_Dataset/
├── 01_Daylight_Corridor_10min.mp4     # Standard daytime sample (10 min, ~250 MB)
├── 02_Nighttime_Corridor_10min.mp4    # Nighttime headlights & glare sample (10 min, ~250 MB)
├── expected_outputs/                  # Pre-computed verification benchmarks
│   ├── timeline.csv                   # Verified row-per-vehicle ground truth
│   ├── buckets.csv                    # Hourly volumes & Peak Hour Factor
│   └── contact_sheet.png              # Audit contact sheet
└── README_QUICKSTART.txt              # Command-line test instructions
```

### Who Uses This Cloud Link:
* **Infrastructure Clients & Highway Operators:** To test the offline CPU engine against their own video feeds.
* **Consulting Engineers & Survey Teams:** To verify that the software delivers the exact expected CSV and contact sheet outputs.
* **Prospective Partners & Recruiters:** To inspect the empirical accuracy and data quality without cloning gigabytes of video into git.

---

## 3. Public CCTV Traffic Benchmarks

For open benchmark comparisons and practicing camera corridor calibration:

1. **Caltrans Live Video Feeds (California, USA):**
   * Highway corridor feeds across I-5, I-80, and US-101.
   * Useful for testing multi-lane divided carriageway tracking.
2. **NYC DOT Traffic Cameras (New York, USA):**
   * Urban intersection video feeds.
   * Useful for testing low-speed vehicle tracking and pedestrian filtering.
3. **CDnet 2014 Benchmark (ChangeDetection.net):**
   * Standard computer vision baseline clips (`baseline/highway`, `cameraJitter/badweather`).
4. **Kaggle Vehicle Detection & Tracking Datasets:**
   * Open CCTV road video archives (fixed camera angle, 1080p).
