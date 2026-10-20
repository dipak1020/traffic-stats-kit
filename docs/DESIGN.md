# Architecture & Design Principles

## 1. Design Invariants

`traffic-stats-kit` adheres to strict civil engineering principles:

1. **Refusal Over Fiction:**  
   If a parameter cannot be rigorously justified (e.g., vehicle speed without verified ground-truth distance calibration), the pipeline raises an explicit exception rather than outputting plausible guesses.

2. **Upstream Decoupling:**  
   The weakest stage (semantic classification via vision models) must never sit upstream of the strongest stage (deterministic optical presence counting). If classification fails or is omitted, volume and directionality remain 100% accurate.

3. **Deterministic Memory Footprint:**  
   Processes video frames sequentially in a rolling buffer. Memory consumption remains strictly bounded regardless of whether the video is 10 minutes or 24 hours long ($< 250\,\text{MB}$ RAM).

4. **Multi-Agent Interoperability:**  
   The codebase exposes uniform CLI commands and structured JSON/CSV telemetry so autonomous coding agents (Gemini, Claude, Antigravity, Codex) can run audits, calibrate polylines, and inspect contact sheets without ad-hoc scripts.
