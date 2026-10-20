---
name: traffic-stats
description: Automates offline, civil-engineering-grade traffic surveys from fixed CCTV video. Includes camera probing, road corridor calibration, multi-lane tracking, in-frame articulated truck merging, and the 4 validation gates.
---

# traffic-stats Agent Skill

Use this skill when processing roadside CCTV/DVR video to produce auditable traffic surveys (counts, vehicle classification, directionality, headway, Peak Hour Factor, and contact sheets) running entirely offline on CPU.

## Core Rules & Guardrails
1. **Zero Network Egress:** Never upload video frames, crops, or telemetry to external clouds.
2. **Look at the Contact Sheet:** Never certify numbers without auditing `contact_sheet.png`.
3. **Two-Line Crossing Protocol:** Require chronological crossing of $x_{\text{count}}$ and $x_{\text{verify}}$.
4. **Articulated Merging:** Merge cab and trailer in-frame using scale-normalized gap tolerance ($\le 0.45 \cdot H(x)$) and ground contact grade ($\le 0.15 \cdot H(x)$).

## Step-by-Step Workflow

### Step 1: Probe Camera & Stream Properties
Inspect resolution, framerate, codec, and mounting geometry:
```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,codec_name input_video.mp4
python -m traffic_stats check
```

### Step 2: Calibrate Site Corridor & Multi-Lane Geometry
Extract median asphalt and generate corridor overlay:
```bash
python -m traffic_stats calibrate --video path/to/sample.mp4 --out out/diagnostics
```

### Step 3: Run Batch Offline Processing
```bash
python -m traffic_stats run --videos /path/to/clips --out out/survey
```

### Step 4: Audit Validation Gates
Audit the output against the 4 engineering gates:
```bash
python -m traffic_stats audit --timeline out/survey/timeline.csv
```
Verify:
* Visual Gate: 100% of tiles on `contact_sheet.png` are genuine vehicles.
* Headway Gate: Fraction of headways $< 1.0\text{s}$ must be $\le 5\%$.
* Coverage Gate: Recording time continuity $> 95\%$.
* Determinism: Repeated runs yield bit-exact CSV records.
