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

## 2. Cloud Sample Dataset (Google Drive)

🔗 **Official Cloud Mirror:** [Google Drive Verification Dataset (365 MB)](https://drive.google.com/drive/folders/19WZarf0nnM5d9DlePg2Dy0LOZM7RJs-p?usp=share_link)

Because GitHub restricts single files over 100MB, the curated sample folder is hosted on Google Drive:

```
Sample_Traffic_Dataset/
├── 01_Real_CCTV_Corridor_Footage/
│   ├── A27_20260831122920.mp4          (60 MB — Morning daylight)
│   ├── A27_20260831193236.mp4          (91 MB — Afternoon peak flow)
│   ├── A27_20260831224837.mp4          (131 MB — Dusk day/night transition)
│   ├── A27_20260831233637.mp4          (79 MB — Night headlights)
│   └── real_audit_outputs/             (contact_sheet.png, timeline.csv, buckets.csv, gates.txt)
├── 02_Calibrated_Benchmark_Clips/
│   ├── CAM01_20260301080000.mp4 + truth CSV
│   ├── CAM01_20260301120000.mp4 + truth CSV
│   ├── CAM01_20260301173000.mp4 + truth CSV
│   ├── CAM01_20260301200000.mp4 + truth CSV
│   └── benchmark_outputs/              (SCORE.md, contact_sheet.png, timeline.csv)
└── README_QUICKSTART.txt               (1-command replication instructions)
```

### Who Uses This Cloud Link:
* **Infrastructure Clients & Highway Operators:** To test the offline CPU engine against real and calibrated footage.
* **Consulting Engineers & Survey Teams:** To verify that the software delivers the exact expected CSV and contact sheet outputs.
* **Prospective Partners & Recruiters:** To inspect the empirical accuracy and data quality without cloning hundreds of megabytes of video into git.

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
