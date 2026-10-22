<div align="center">

# 🚦 traffic-stats-kit

### First Principles in Traffic Video Analytics: A Deterministic Engineering Approach to Roadway Monitoring

[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776ab.svg?logo=python&logoColor=white)](#)
[![Tests: Passing](https://img.shields.io/badge/Tests-100%25%20Passing-brightgreen.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docs: CC BY 4.0](https://img.shields.io/badge/Docs-CC%20BY%204.0-lightgrey.svg)](LICENSE-DOCS)
[![Compute: Offline CPU](https://img.shields.io/badge/Compute-Offline%20CPU%20%28%3C12W%29-2ea44f.svg)](#)
[![Validation: 4 Gates](https://img.shields.io/badge/Validation-4%20Engineering%20Gates-0366d6.svg)](#)
[![Dataset: Google Drive](https://img.shields.io/badge/Dataset-Google%20Drive%20Mirror%20%28365%20MB%29-8a3ffc.svg)](https://drive.google.com/drive/folders/19WZarf0nnM5d9DlePg2Dy0LOZM7RJs-p?usp=share_link)

**[📄 Technical Documentation](docs/ARTICLE.md)** • **[📁 Verification Dataset (Google Drive)](https://drive.google.com/drive/folders/19WZarf0nnM5d9DlePg2Dy0LOZM7RJs-p?usp=share_link)**

---

</div>

Turn fixed-camera CCTV and roadside DVR footage into an auditable, civil-engineering-grade traffic survey: per-vehicle timeline, travel directionality, vehicle classification, hourly volume buckets, headway distributions, lane occupancy, and an automated visual contact sheet showing every counted vehicle.

> **Runs 100% offline on standard multi-core CPUs (<12W) using deterministic OpenCV and NumPy. Zero cloud dependencies, zero external GPUs, and zero telemetry leaks.**

Field-validated over **170+ hours of continuous roadside Hikvision DVR recordings (11,693 vehicles over 8 days)** in the Villeta industrial corridor, Paraguay.

```
Raw CCTV Stream  ──►  1D Virtual Loops  ──►  Temporal Median Asphalt  ──►  Two-Line Turnstile  ──►  Visual Proof & CSVs
```

---

## 🗺️ System Architecture & Engineering Methodology

<div align="center">

![The Agentic Technique & Human-in-the-Loop Vision Pipeline](docs/agent_technique_map.png)

*Figure: Publication-grade architecture map in high-contrast light theme outlining the closed iteration loop, machine/human division of labour, the 4 operational axioms, and defensive vision techniques.*

</div>

---

## 📸 Visual Integrity: Gate 1 Contact Sheet

In civil engineering, an unverified number is worse than no number at all. Every survey run automatically produces a tiled photographic matrix of every vehicle counted:

<div align="center">

![Visual Audit Contact Sheet — Camera A27 Field Excerpts](docs/contact_sheet.png)

*Figure: Automated Visual Contact Sheet generated directly from 4 real Camera A27 DVR excerpts (Villeta, Paraguay). Human reviewers can visually audit 500 vehicle crossings in under 30 seconds.*

</div>

---

## 📐 Mathematical Foundations & First Principles

`traffic-stats-kit` rejects opaque black boxes in favor of geometric discipline and physical constraints:

### 1. Perspective-Invariant Road Corridor & Optical Scale
Given upper horizon boundary **P_far** and lower curb boundary **P_near**, the local optical band height **H(x)** serves as the scene's self-calibrating physical ruler:

$$H(x) = y_{\mathrm{near}}(x) - y_{\mathrm{far}}(x)$$

Every spatial threshold (bounding box tolerances, morphological kernels, coupling clearances) scales as a dimensionless fraction of $H(x)$:

$$\mathrm{Tolerance}_{\mathrm{norm}}(x) = \gamma \cdot H(x)$$

### 2. Temporal Median Asphalt Baseline
Rather than hoping to catch an empty road by chance, the pristine asphalt reference $\mathcal{B}(x, y)$ is extracted directly from active traffic using the statistical temporal median across uniformly sampled frames $\mathcal{S}$:

$$\mathcal{B}(x, y) = \mathrm{median}_{t \in \mathcal{S}} \big[ \mathcal{I}(x, y, t) \big]$$

$$\mathcal{D}(x, y, t) = \big| \mathcal{I}(x, y, t) - \mathcal{B}(x, y) \big|$$

$$\mathcal{M}(x, y, t) = \begin{cases} 1, & \mathcal{D}(x, y, t) \ge \tau_{\mathrm{thresh}} \\ 0, & \mathcal{D}(x, y, t) \lt \tau_{\mathrm{thresh}} \end{cases}$$

### 3. Chronological Two-Line Turnstile Gate
A single tripwire triggers on tree shadows, swaying wires, and headlight reflections. We enforce chronological dual-line passage verification:

$$\mathrm{Pass}_{\mathrm{valid}} \iff \exists \, (t_1 \lt t_2) : \quad x(t_1) = x_{\mathrm{count}} \quad \land \quad x(t_2) = x_{\mathrm{verify}}$$

$$\mathrm{Direction} = \mathrm{sgn}\big(x(t_2) - x(t_1)\big) = \begin{cases} \text{Left-to-Right (LR)}, & x(t_2) \gt x(t_1) \\ \text{Right-to-Left (RL)}, & x(t_2) \lt x(t_1) \end{cases}$$

### 4. Scale-Normalized In-Frame Articulated Coupling
Tractor-trailers frequently split into two blobs because asphalt shows through above the fifth wheel. We couple adjacent blobs in-frame sharing tire-contact grade:

$$\Delta x_{\mathrm{gap}} = |x_1 - x_2| - \frac{w_1 + w_2}{2} \le 0.45 \cdot H(x)$$

$$\Delta y_{\mathrm{contact}} = |y_{1,\mathrm{ground}} - y_{2,\mathrm{ground}}| \le 0.15 \cdot H(x)$$

### 5. Traffic Flow Parameters (HCM Standards)
* **Time Headway:** $h_i = t_i - t_{i-1}$ (Automated double-count flag floor: $h_i < 1.0\text{ s}$)
* **Peak Hour Factor (PHF):**

  $$\mathrm{PHF} = \frac{V_{\mathrm{hour}}}{4 \cdot V_{15,\max}}$$

* **Spatial Occupancy Ratio:**

  $$\rho_{\mathrm{occ}} = \frac{\sum_{i=1}^N \Delta t_{\mathrm{occupancy}, i}}{T_{\mathrm{period}}} \times 100\%$$

### 6. Astronomical Solar Noon RTC Clock Recovery
Roadside DVR internal clocks drift substantially. The astronomical time offset is recovered from true solar noon:

$$t_{\mathrm{midpoint}} = \frac{t_{\mathrm{dawn}} + t_{\mathrm{dusk}}}{2}$$

$$\Delta t_{\mathrm{RTC}} = t_{\mathrm{midpoint}} - t_{\mathrm{solar}}(\phi, \lambda, \text{date})$$

---

## 🛡️ The 4 Non-Negotiable Engineering Validation Gates

| Gate | Engineering Criterion | Safety & Integrity Purpose |
| :--- | :--- | :--- |
| **1. Visual Audit** | 100% of tiles on `contact_sheet.png` | Human reviewer inspects photograph of every counted vehicle |
| **2. Headway Floor** | $h_i < 1.0\,\text{s}$ must be $\le 5\%$ of volume | Flags unmerged tractor-trailer combinations and shadow splits |
| **3. Coverage Continuity** | Valid recorded footage $> 95\%$ | Prevents partial-day peaks from corrupting capacity baselines |
| **4. Bit Determinism** | Exact byte-for-byte CSV row matching | Guarantees mathematical reproducibility across hardware |

---

## 🚀 Quick Start (Mac & Linux)

### 1. Prerequisites & Installation

```bash
# System dependencies (macOS)
brew install ffmpeg python@3.12

# Clone the repository
git clone https://github.com/dipak1020/traffic-stats-kit.git
cd traffic-stats-kit

# Set up virtual environment
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Run with One Command

```bash
bash run_on_mac.sh
```

### 3. Step-by-Step Execution

```bash
# A. Synthetic self-scoring benchmark (in memory, no ffmpeg required)
python -m traffic_stats.demo --minutes 5 --headway 20

# B. Process the calibrated benchmark clips
python -m traffic_stats.report --videos samples --out out_benchmark --bucket 60

# C. Process REAL field CCTV footage (Camera A27 calibration)
python -m traffic_stats.report --site villeta-a27 --videos samples_real --out out_real --bucket 60

# D. Render visual diagnostic overlays (geometry, asphalt luma, artifacts)
python -m traffic_stats.overlay --site villeta-a27 --video samples_real/A27_20260831193236.mp4 --out out_real/diagnostics
```

---

## 📂 Deliverables & Output Schema

| File Name | Engineering Purpose | Format |
| :--- | :--- | :--- |
| `contact_sheet.png` | **Visual Audit Matrix:** Tiled image of every vehicle crop | PNG image |
| `timeline.csv` | **Microscopic Log:** Timestamp, direction, normalized width, velocity | CSV table |
| `buckets.csv` | **Macroscopic Volumes:** Hourly traffic volume, direction split, PHF | CSV table |
| `gates.txt` | **Integrity Report:** Poisson headway distribution, coverage continuity | Plain text |
| `diagnostics/` | Roadway band geometry, median background, day/night asphalt luma | PNG directory |

---

## 🤖 Multi-Agent Framework Integration

`traffic-stats-kit` natively supports autonomous AI workflows:

| Agent / Interface | Configuration File | Operational Role |
| :--- | :--- | :--- |
| **Gemini CLI** | [`GEMINI.md`](GEMINI.md) | High-level architectural validation and contact sheet visual QA |
| **Antigravity / Codex** | [`AGENTS.md`](AGENTS.md) | Pipeline test execution, edge performance, and multi-agent loops |
| **Claude Code** | [`CLAUDE.md`](CLAUDE.md) | Direct tool invocation and custom skill execution |
| **Pre-commit Hooks** | `.claude/hooks/` | Local guards (`no_network.py`, `calibration_guard.py`) |

---

## 📜 Licence

* **Code:** [MIT License](LICENSE). Copyright &copy; 2026 Dipak Kumar.
* **Documentation & Diagrams:** Creative Commons Attribution 4.0 International ([CC BY 4.0](LICENSE-DOCS)).

---

## 👤 Author & Attribution

**Dipak Kumar**  
Computational Modeling & Simulation Specialist  
Asunción, Paraguay  
GitHub: [@dipak1020](https://github.com/dipak1020) • Repository: [traffic-stats-kit](https://github.com/dipak1020/traffic-stats-kit)
