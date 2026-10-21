====================================================================
  traffic-stats-kit: Sample Verification Dataset & Benchmarks
====================================================================

This folder contains verified test footage and ground-truth outputs
for the traffic-stats-kit offline edge computing engine.

FILES IN THIS FOLDER:
---------------------
1. 01_Daylight_Corridor_Sample.mp4
   - Standard daytime road corridor clip.
   - Tests optical band perspective, vehicle scale normalization,
     and articulated tractor-trailer spatial box merging.

2. 02_Nighttime_Corridor_Sample.mp4
   - Nighttime low-light clip.
   - Tests twin headlight bridging and nighttime glare filtering.

3. expected_outputs/
   - timeline.csv: Row-by-row verified timestamps, w_norm, and directions.
   - buckets.csv: Aggregated volume intervals and peak-hour analysis.
   - contact_sheet.png: Audit matrix of every counted vehicle crop.

RUNNING THE VERIFICATION PIPELINE LOCALLY:
------------------------------------------
Clone the repository:
  git clone https://github.com/dipak10101/traffic-stats-kit.git
  cd traffic-stats-kit

Run the test suite against the sample videos:
  python3 -m traffic_stats demo --minutes 1 --out out/my_audit

For technical equations and methodology:
  Open docs/METHODOLOGY.html in any web browser.
====================================================================
