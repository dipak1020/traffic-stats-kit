# Workspace Rules — traffic-stats-kit (Civil Engineering & Edge CV)

Guidelines, behavioral constraints, and tool integration instructions for autonomous AI coding agents (Gemini CLI, Claude Code, Antigravity, and Codex) operating within the `traffic-stats-kit` repository.

This project is completely standalone and dedicated to offline, civil-engineering-grade traffic surveys.

---

## 1. Project Mission & Agent Roles

* **Mission:** Turn fixed roadside CCTV/DVR video into auditable traffic surveys (vehicle counts, directionality, headway, occupancy, hourly volume, and visual verification sheets) running entirely offline on CPU (sub-12W).
* **Gemini CLI (GEMINI.md):** High-level analysis, SOP compliance, visual QA of contact sheets, and architecture verification.
* **Claude Code (CLAUDE.md):** Interactive debugging, site calibration refinement, gate enforcement via `.claude/hooks/`, and skills execution.
* **Antigravity / Codex (AGENTS.md):** Autonomous orchestration, test suite execution, batch pipeline processing, and data asset governance.

---

## 2. Core Coding & Behavioral Rules

1. **Offline Edge Execution Only:** Never make external network requests, upload video frames, or download model weights during a processing run. All inference must remain CPU-bound and local.
2. **Look at the Contact Sheet:** Never report numbers without auditing `contact_sheet.png`. The eye catches what numeric summaries hide.
3. **Two-Line Verification Protocol:** A valid pass requires crossing `count_x` AND `verify_x` in chronological order. Stationary artifacts, pole shadows, and wire oscillations must never generate false vehicle counts.
4. **In-Frame Articulated Vehicle Merging:** Tractor-trailer combinations must be merged in-frame based on ground-line contact ($\Delta y \le 0.15 \cdot H(x)$) and scale-normalized gap tolerance ($\Delta x \le 0.45 \cdot H(x)$). Never attempt post-hoc timing merges.
5. **Time Base Verification:** Re-baseline against solar noon if external ground-truth timestamps are absent.
6. **Protected Site Geometry:** Do not alter site calibration coordinates (`traffic_stats/config.py`) without re-deriving the median asphalt background.

---

## 3. The 4 Non-Negotiable Engineering Validation Gates

Before certifying any survey dataset:
* [ ] **Gate 1 (Contact Sheet Audit):** 100% of tiles on `contact_sheet.png` represent verified vehicles.
* [ ] **Gate 2 (Headway Floor):** Fraction of consecutive passes with headway $< 1.0\,\text{s}$ must be $\le 5\%$ (`headway LR PASS`, `headway RL PASS`).
* [ ] **Gate 3 (Coverage Threshold):** Time coverage must exceed $95\%$ of the scheduled survey period; any gaps must be explicitly logged.
* [ ] **Gate 4 (Determinism Gate):** Repeated runs over identical footage must yield bit-exact CSV timeline records.

---

## 4. The Unified Orchestrator CLI

```bash
# 1. Verify environment, ffmpeg, linter (ruff), and test suite (pytest)
python -m traffic_stats check

# 2. Run self-scoring synthetic benchmark with articulated vehicle de-duplication
python -m traffic_stats demo --minutes 5 --headway 20 --out out

# 3. Calibrate a new CCTV camera site (extract median background & overlay corridor)
python -m traffic_stats calibrate --video path/to/sample.mp4 --out out/diagnostics

# 4. Batch process a directory of video clips offline on CPU
python -m traffic_stats run --videos /path/to/clips --out out/survey

# 5. Audit an existing timeline CSV through the 4 engineering validation gates
python -m traffic_stats audit --timeline out/survey/timeline.csv

# 6. Install git verification pre-commit hooks and agentic guard rails
python -m traffic_stats install-hooks
```
