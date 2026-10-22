# Theoretical Formulation & Engineering Approach

This document outlines the computer vision, signal processing, and civil engineering methodology implemented in `traffic-stats-kit`.

---

## 1. The Core Philosophy: Determinism Over Black Boxes

Traditional traffic video analytics often rely on end-to-end heavy neural networks (YOLO, DeepSORT) that:
1. Require high-wattage GPUs ($>250\,\text{W}$).
2. Hallucinate objects or fail unpredictably under glare, rain, and nighttime headlight bloom.
3. Fail silently without reproducible validation gates.

`traffic-stats-kit` inverts this hierarchy:
* **The physical signal is primary:** A vehicle is treated as an optical mass traveling across a calibrated road corridor.
* **Separation of counting from classification:** Vehicle detection and trajectory verification are strictly deterministic and rule-based. Machine learning (YOLO/CLIP) is optional and restricted to classification *after* a valid crossing is established.
* **Offline CPU execution:** Operates entirely on standard multi-core CPUs with zero network dependencies.

---

## 2. Pipeline Stages

```
[Video / DVR Stream]
        │
        ▼
1. Geometric Corridor Restriction (Polyline ROI)
        │
        ▼
2. Asphalt Background Subtraction (Median Temporal Slice)
        │
        ▼
3. Day / Night Morphological Filtering
        │
        ▼
4. Two-Line Cross Verification (Count Line + Verify Line)
        │
        ▼
5. In-Frame Articulated Vehicle Merging
        │
        ▼
6. 4 Engineering Validation Gates & Contact Sheet Audit
```

---

## 3. Mathematical & Algorithmic Formulations

### 3.1 Geometric Road Corridor & Optical Scale
The road surface is bounded by two calibrated polylines:
* $\mathcal{P}_{\text{far}} = \{(x_1, y_1), \dots, (x_n, y_n)\}$ (upper road boundary / horizon)
* $\mathcal{P}_{\text{near}} = \{(x_1', y_1'), \dots, (x_m', y_m')\}$ (lower road boundary / curb)

The local band height $H(x)$ at any horizontal coordinate $x$ defines the optical scale of the road:

$$H(x) = y_{\text{near}}(x) - y_{\text{far}}(x)$$

All spatial thresholds (bounding box tolerances, vehicle widths, kernel sizes) are normalized as fractions of $H(x)$, ensuring perspective invariance.

### 3.2 Median Temporal Asphalt Background Model
To reject stationary vehicles at red lights without memorization:

$$\mathcal{B}(x, y) = \mathrm{median}_{t \in \mathcal{S}} \Big\{ \mathcal{I}(x, y, t) \Big\}$$

The foreground difference image $\mathcal{D}(x, y, t)$ and binary activation mask $\mathcal{M}(x, y, t)$:

$$\mathcal{D}(x, y, t) = \big| \mathcal{I}(x, y, t) - \mathcal{B}(x, y) \big|$$

$$\mathcal{M}(x, y, t) = \begin{cases} 1, & \mathcal{D}(x, y, t) \ge \tau_{\mathrm{thresh}} \\ 0, & \mathcal{D}(x, y, t) < \tau_{\mathrm{thresh}} \end{cases}$$

### 3.3 Two-Line Verification Protocol
To eliminate false counts caused by tree shadows, camera oscillations, and stationary glare:
* **Counting Line:** $x = x_{\mathrm{count}}$
* **Verification Line:** $x = x_{\mathrm{verify}} = x_{\mathrm{count}} \pm \Delta x$

A trajectory $\mathcal{T} = \{(x_t, y_t)\}$ is registered as a verified vehicle passage if and only if:

$$\mathrm{Pass}_{\mathrm{valid}} \iff \exists \, (t_1 < t_2) : \quad x(t_1) = x_{\mathrm{count}} \quad \land \quad x(t_2) = x_{\mathrm{verify}}$$

Direction is signed by trajectory displacement $\Delta x = x(t_2) - x(t_1)$:

$$\mathrm{Direction} = \begin{cases} \text{Left-to-Right (LR)}, & x(t_2) > x(t_1) \\ \text{Right-to-Left (RL)}, & x(t_2) < x(t_1) \end{cases}$$

### 3.4 In-Frame Articulated Vehicle Merging
Articulated semi-trailers frequently appear as two disconnected blobs (tractor cab and trailer body) due to the low-contrast gap above the fifth wheel. 

Post-hoc timing merges are prone to merging two independent tailgating cars. Instead, `traffic-stats-kit` executes **in-frame spatial merging**:

$$\Delta x_{\mathrm{gap}} = |x_1 - x_2| - \frac{w_1 + w_2}{2} \le 0.45 \cdot H(x)$$

$$\Delta y_{\mathrm{contact}} = |y_{1,\mathrm{ground}} - y_{2,\mathrm{ground}}| \le 0.15 \cdot H(x)$$

### 3.5 Day / Night Adaptive Morphological Kernels
* **Daylight:** Compact vertical-horizontal structuring element ($0.18 \cdot H(x) \times 0.13 \cdot H(x)$) preserving vehicle contours while rejecting overhead wiring.
* **Nighttime:** Headlight glare creates two isolated bright spots. The system switches to an elongated horizontal kernel ($0.49 \cdot H(x) \times 0.18 \cdot H(x)$) bridging dual headlights into a singular vehicle entity before tracking.

### 3.6 Traffic Flow & Capacity Parameters (HCM)
* **Time Headway:** $h_i = t_i - t_{i-1}$
* **Peak Hour Factor:**
  $$\mathrm{PHF} = \frac{V_{\mathrm{hour}}}{4 \times V_{15,\max}}$$
* **Time Occupancy:**
  $$\rho_{\mathrm{occ}} = \frac{\sum_{i=1}^N \Delta t_{\mathrm{occupancy}, i}}{T_{\mathrm{period}}} \times 100\%$$

### 3.7 Solar Noon Clock Drift Correction
When roadside DVR internal clocks drift or reset:

$$t_{\mathrm{midpoint}} = \frac{t_{\mathrm{dawn}} + t_{\mathrm{dusk}}}{2}$$

$$\Delta t_{\mathrm{RTC}} = t_{\mathrm{midpoint}} - t_{\mathrm{solar}}(\phi, \lambda, \text{date})$$

This aligns camera timestamps with true astronomical local time without requiring GPS hardware.

---

## 4. The 4 Non-Negotiable Validation Gates

1. **Gate 1 (Contact Sheet Audit):** A tiled image matrix (`contact_sheet.png`) showing the highest-contrast crop of every counted vehicle. Must be visually reviewed by an engineer.
2. **Gate 2 (Headway Floor):** Consecutive vehicle headways $< 1.0\,\text{s}$ must not exceed $5\%$ of total count. Any spike signals unmerged articulated vehicles.
3. **Gate 3 (Coverage Threshold):** Survey temporal continuity must exceed $95\%$ of scheduled survey duration.
4. **Gate 4 (Determinism Gate):** Multi-threaded or repeated execution over the same clip sequence must produce bit-exact CSV timeline rows.

