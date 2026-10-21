====================================================================
  traffic-stats-kit: Real Project CCTV Dataset & Verification Package
====================================================================
Author: Dipak Kumar
Repository: https://github.com/dipak10101/traffic-stats-kit

This package contains the field-recorded CCTV road survey footage from
Camera A27 (Villeta, Paraguay), along with the calibrated benchmark
clips, exact ground-truth CSVs, and verified audit outputs.

Everything runs entirely on local CPU using first-principles OpenCV and
NumPy. No GPUs, no cloud dependencies, and zero telemetry.

--------------------------------------------------------------------
DIRECTORY CONTENTS
--------------------------------------------------------------------

1. 01_Real_CCTV_Corridor_Footage/
   Four raw DVR excerpts cut directly from the 170-hour field survey
   (31 August 2026), testing day, peak, dusk, and night conditions:

   - A27_20260831122920.mp4 (60 MB)
     Morning daylight corridor (08:29 local time).
     Tests optical band perspective and truck scale normalization.

   - A27_20260831193236.mp4 (91 MB)
     Afternoon peak traffic corridor (15:32 local time).
     Tests multi-vehicle flow and foreground fence-post occlusion logic.

   - A27_20260831224837.mp4 (131 MB)
     Dusk transition (18:48 local time).
     Tests automatic day/night threshold switching on asphalt luma.

   - A27_20260831233637.mp4 (79 MB)
     Nighttime low-light corridor (19:36 local time).
     Tests twin headlight pairing across wide morphological kernels.

   - real_audit_outputs/
     Pre-computed verified results from the real camera run:
     * contact_sheet.png : Visual proof sheet of every counted vehicle crop.
     * timeline.csv      : Timestamped vehicle log with normalized width.
     * buckets.csv       : Binned traffic volumes and peak hour index.
     * gates.txt         : 4-Gate engineering integrity validation report.
     * diagnostics/      : Optical geometry and day/night luma graphs.

2. 02_Calibrated_Benchmark_Clips/
   Four synthetic validation clips with exact ground-truth CSVs:
   - CAM01_20260301080000.mp4 + CAM01_20260301080000_truth.csv
   - CAM01_20260301120000.mp4 + CAM01_20260301120000_truth.csv
   - CAM01_20260301173000.mp4 + CAM01_20260301173000_truth.csv
   - CAM01_20260301200000.mp4 + CAM01_20260301200000_truth.csv
   - benchmark_outputs/ (contact_sheet.png, timeline.csv, SCORE.md)

--------------------------------------------------------------------
HOW TO RUN ON YOUR MAC / LINUX MACHINE
--------------------------------------------------------------------

1. Prerequisites:
   brew install ffmpeg python@3.12
   python3 -m venv .venv && source .venv/bin/activate
   pip install numpy opencv-python matplotlib

2. Run against the Real CCTV Footage:
   python -m traffic_stats.report --site villeta-a27 \
          --videos "01_Real_CCTV_Corridor_Footage" \
          --out "out_real" --bucket 60

3. Run against the Benchmark Clips:
   python -m traffic_stats.report \
          --videos "02_Calibrated_Benchmark_Clips" \
          --out "out_benchmark" --bucket 60

4. Generate Visual Diagnostics:
   python -m traffic_stats.overlay --site villeta-a27 \
          --video "01_Real_CCTV_Corridor_Footage/A27_20260831193236.mp4" \
          --out "out_real/diagnostics"

5. Review Results:
   Always inspect 'contact_sheet.png' first to visually confirm detected
   vehicles, followed by 'gates.txt' for Poisson headway verification.
====================================================================
