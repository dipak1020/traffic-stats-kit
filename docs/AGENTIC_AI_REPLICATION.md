# Agentic AI Replication Blueprint — traffic-stats-kit

A complete, field-tested guide for autonomous AI coding agents (**Claude Code**, **Gemini CLI**, **Antigravity**, **Codex**) and human engineers to replicate this edge-native traffic analysis framework on any computer.

---

## 1. System Mission & Core Constraints

`traffic-stats-kit` turns roadside CCTV and DVR video into an auditable, civil-engineering-grade traffic survey (vehicle counts, directionality, headway, occupancy, hourly volume, and visual verification sheets) **entirely offline on CPU**.

* **Sub-12W Edge Execution:** Zero GPU requirements; runs on standard laptops or edge IPCs.
* **Zero Network Egress:** 100% offline signal processing with zero telemetry or video leaks.
* **Human-in-the-Loop Verification:** No numbers are certified without human visual audit of `contact_sheet.png`.

---

## 2. The 5-Phase Autonomous Replication Workflow

```
[Phase 1: Camera Type & Stream Probing]
                  │
                  ▼
[Phase 2: Directionality & Multi-Lane Geometry]
                  │
                  ▼
[Phase 3: Guardrails & Tool Limitation Hooks]
                  │
                  ▼
[Phase 4: Batch Processing on CPU]
                  │
                  ▼
[Phase 5: Human-in-the-Loop 4-Gate Certification]
```

---

## Phase 1: Camera Type & Video Source Diagnostics

Before calibrating road coordinates, the agent must test and identify the camera specifications:

```bash
# 1. Probe video container, codec, resolution, and framerate
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate,codec_name,bit_rate,duration \
  -of json input_video.mp4
```

### Camera Classification Matrix:
| Camera Parameter | Supported Range | Impact on Pipeline |
|---|---|---|
| **Resolution** | 720p ($1280 \times 720$) to 4K ($3840 \times 2160$) | Normalized via local road band height $H(x)$ |
| **Framerate** | $15\,\text{fps}$ to $30\,\text{fps}$ | Establishes time delta $\Delta t = 1/\text{fps}$ for headway |
| **Codec** | H.264 (AVC) / H.265 (HEVC) | Hardware or CPU decode via system `ffmpeg` |
| **Mounting Angle** | Oblique Roadside ($30^\circ - 60^\circ$) | Default perspective corridor |
| **Overhead Gantry** | Nadir / High Angle ($>70^\circ$) | Symmetrical bounding box mode |
| **Lighting Mode** | Day RGB / Night Infrared (IR) | Automatic morphological kernel switching |

### Camera Diagnostic Command:
```bash
python -m traffic_stats check
```

---

## Phase 2: Directionality & Multi-Lane Configuration

### 1. Two-Line Trajectory Directionality
To avoid false crossings from wind oscillations and shadows, the system requires an optical mass to break two lines chronologically:
* **Counting Line:** $x = x_{\text{count}}$
* **Verification Line:** $x = x_{\mathrm{verify}} = x_{\mathrm{count}} \pm \Delta x$

Direction classification:
$$\mathrm{Direction} = \mathrm{sgn}\big(x(t_2) - x(t_1)\big) = \begin{cases} \text{Left-to-Right (LR)}, & x(t_2) > x(t_1) \\ \text{Right-to-Left (RL)}, & x(t_2) < x(t_1) \end{cases}$$

### 2. Multi-Lane Road Carriageways
When analyzing multi-lane highways or roads with distinct lanes:

```python
# traffic_stats/config.py
LANE_CONFIG = {
    "num_lanes": 2,
    "lanes": [
        {
            "id": "lane_1_slow",
            "y_bounds": (380, 520),  # Pixel vertical slice
            "direction": "LR",
            "count_x": 640,
            "verify_x": 720,
        },
        {
            "id": "lane_2_fast",
            "y_bounds": (520, 680),
            "direction": "RL",
            "count_x": 640,
            "verify_x": 560,
        }
    ]
}
```

* **Lane Change & Overtaking Deduplication:** A vehicle trajectory tracked across multiple frames retains a single persistent `track_id`. If a vehicle straddles the lane divider, it is assigned to the lane containing its centroid ground-contact point ($y_{\text{bottom}}$), preventing double counting.

---

## Phase 3: Guardrails & Tool Limitations

Autonomous coding agents must operate under strict guardrails to prevent data leaks, resource exhaustion, and false survey outputs:

### 🛡️ Guardrail 1: Zero Network Egress (`no_network.py`)
* **Rule:** The agent MUST NOT upload video frames, crops, or telemetry to external APIs or cloud models during a run.
* **Reason:** Roadside CCTV often contains private license plates and commercial transport logs subject to regulatory data protection.

### 🛡️ Guardrail 2: Calibration Immutability (`calibration_guard.py`)
* **Rule:** An agent executing a batch run is prohibited from modifying `traffic_stats/config.py` or ROI coordinates without re-deriving the median asphalt background.
* **Reason:** Changing coordinate geometry mid-batch invalidates historical vehicle widths and time baselines.

### 🛡️ Guardrail 3: Memory & Resource Safeguards
* **Rule:** Video frames must be processed as a temporal stream via OpenCV/FFmpeg generator pipes, never loaded into memory all at once.
* **Cap:** Max RAM footprint $\le 1.8\,\text{GB}$, CPU utilization capped at $N-1$ physical cores.

### 🛡️ Guardrail 4: The 4 Non-Negotiable Human-in-the-Loop Quality Gates
Before any survey number is published, the agent must pass the 4 engineering gates:
1. **Gate 1 (Contact Sheet Visual Audit):** 100% of vehicle crops on `contact_sheet.png` must depict verified vehicles.
2. **Gate 2 (Headway Floor):** Fraction of consecutive passes with $h_i < 1.0\,\text{s}$ must be $\le 5\%$. Any spike flags unmerged multi-axle trailers.
3. **Gate 3 (Coverage Continuity):** Validated recording continuity must exceed $95\%$ of scheduled survey time.
4. **Gate 4 (Determinism Gate):** Repeated execution over the same clip yields bit-exact CSV timeline entries.

---

## 4. Agent Execution Recipes (Copy-Paste Prompts)

### Recipe A: Calibrating a New CCTV Camera
> **Prompt for Agent:**  
> *"Inspect the video file at `data/sample.mp4`. First, identify the camera resolution, framerate, and codec using ffprobe. Second, extract the median asphalt background image over 60 temporal frames. Third, overlay the road corridor polylines and dual verification lines, saving the diagnostic overlay to `out/calibration_preview.png`. Do not alter code outside of `traffic_stats/config.py`."*

### Recipe B: Running Offline Batch Processing
> **Prompt for Agent:**  
> *"Process all 10-minute video clips in `data/cctv_footage/` using the CPU orchestrator. Ensure in-frame articulated truck merging is active with scale-normalized gap tolerance 0.45·H(x). Output `timeline.csv`, hourly `buckets.csv`, and generate `contact_sheet.png` for human audit. Do not make any external network requests."*

### Recipe C: Auditing Survey Integrity & Gates
> **Prompt for Agent:**  
> *"Run `python -m traffic_stats audit --timeline out/timeline.csv`. Report the percentage of consecutive headways under 1.0 second for both LR and RL directions. Verify that coverage continuity exceeds 95% and flag any gaps in survey hours."*

---

## 5. Output Deliverables Structure

```
out/
├── timeline.csv        # Row-per-vehicle: timestamp, direction, class, optical width
├── buckets.csv         # Hourly volume, directional split, Peak Hour Factor (PHF)
├── audit_report.json   # Machine-readable gate verification verdicts
├── contact_sheet.png   # Tiled matrix of all detected vehicles (HITL audit)
└── crops/              # Watermarked high-resolution crop of each vehicle
```

---

## 6. Author & Civil Engineering Standards

* **Author:** Dipak Kumar
* **Field Provenance:** 170h Continuous CCTV Survey / 11,693 Vehicles (Villeta Corridor)
* **Standards Adherence:** Highway Capacity Manual (HCM), AASHTO Green Book, offline Edge AI protocols.
