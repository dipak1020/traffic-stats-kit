# -*- coding: utf-8 -*-
"""
The gates. Run these before anybody reads a number.

A pipeline reports numbers whether or not they mean anything, so the gates
test the SHAPE of the output against what traffic physically looks like,
rather than spot-checking vehicles. The over-count that motivated this file
was invisible vehicle-by-vehicle and obvious in one histogram.
"""
from collections import Counter

from .stats import headways, localise


def headway_gate(crossings, site, floor_s=1.0, tol=0.05):
    """
    Real traffic has a floor: two vehicles cannot be 8 m apart at 60 km/h.
    A spike below ~1 s means ONE VEHICLE IS BEING COUNTED TWICE -- almost
    always a long vehicle split into tractor and trailer.

    The fix belongs in detect.merge_boxes (same frame), never post hoc by
    timing: timing cannot tell a trailer from a genuinely following vehicle.
    """
    res = {}
    for d in ("LR", "RL"):
        ts = [lt for c, lt in localise(crossings, site) if c.direction == d]
        hw = headways(ts)
        if not hw:
            res[d] = {"n": 0, "verdict": "NO DATA"}
            continue
        bad = sum(1 for h in hw if h < floor_s)
        frac = bad / len(hw)
        res[d] = {
            "n": len(hw) + 1,
            "under_floor": bad,
            "fraction": round(frac, 3),
            "median_headway_s": round(sorted(hw)[len(hw) // 2], 1),
            "verdict": "PASS" if frac <= tol else "FAIL - suspected double counting",
            "histogram": _hist(hw),
        }
    return res


def _hist(hw, edges=(0, .5, 1, 1.5, 3, 6, 15, 30, 60, 1e9)):
    c = Counter()
    for h in hw:
        for a, b in zip(edges, edges[1:]):
            if a <= h < b:
                c["%g-%g s" % (a, b) if b < 1e9 else ">60 s"] += 1
                break
    return dict(c)


def coverage_gate(spans, min_pct=95.0, tol_s=90):
    """
    A peak hour computed over a day missing its afternoon is not a peak hour.

    spans is [(start, end)] of footage actually processed. Returns merged
    blocks, every gap, and a verdict on whether peaks may be published.
    """
    if not spans:
        return {"verdict": "NO DATA", "covered_pct": 0.0, "gaps": []}
    sp = sorted(spans)
    merged = [list(sp[0])]
    for a, b in sp[1:]:
        if (a - merged[-1][1]).total_seconds() <= tol_s:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    gaps = [(x[1], y[0]) for x, y in zip(merged, merged[1:])]
    span = (merged[-1][1] - merged[0][0]).total_seconds() or 1
    have = sum((b - a).total_seconds() for a, b in merged)
    pct = 100.0 * have / span
    return {
        "covered_pct": round(pct, 1),
        "blocks": [(a.isoformat(), b.isoformat()) for a, b in merged],
        "gaps": [(a.isoformat(), b.isoformat(),
                  round((b - a).total_seconds() / 60, 1)) for a, b in gaps],
        "verdict": "PASS" if pct >= min_pct
                   else "PARTIAL - label any peak as 'peak of available data'",
    }


def determinism_gate(run_a, run_b):
    """Same input twice, same output. A difference means a race condition."""
    ka = [(c.tid, c.direction, c.frame) for c in run_a]
    kb = [(c.tid, c.direction, c.frame) for c in run_b]
    return {"verdict": "PASS" if ka == kb else "FAIL - non-deterministic",
            "n_a": len(ka), "n_b": len(kb)}


def contact_sheet(crops, path, cols=8, tile=96, label=True):
    """
    Gate 1, and the one people skip: one tile per COUNTED VEHICLE, to LOOK at.

    Not one tile per frame -- per vehicle, cut from the clearest view of it.
    That is the audit trail: every number in the report traces back to a
    picture a human can check, and in practice that is how real defects get
    found. No numeric gate replaces it.
    """
    import cv2
    import numpy as np
    good = [c for c in crops if c is not None and c.size]
    if not good:
        return 0
    rows = (len(good) + cols - 1) // cols
    sheet = np.zeros((rows * tile, cols * tile), np.uint8)
    for i, c in enumerate(good):
        r, k = divmod(i, cols)
        t = cv2.resize(c, (tile, tile), interpolation=cv2.INTER_AREA)
        sheet[r * tile:(r + 1) * tile, k * tile:(k + 1) * tile] = t
        if label:
            cv2.putText(sheet, str(i + 1), (k * tile + 3, r * tile + 13),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, 255, 1, cv2.LINE_AA)
    for r in range(rows):
        sheet[r * tile, :] = 255
    for k in range(cols):
        sheet[:, k * tile] = 255
    cv2.imwrite(str(path), sheet)
    return len(good)


def report(gates):
    lines = []
    for name, g in gates.items():
        if isinstance(g, dict) and "verdict" in g:
            lines.append("  %-16s %s" % (name, g["verdict"]))
        else:
            for k, v in g.items():
                lines.append("  %-16s %-3s %s" % (name, k, v.get("verdict", "")))
    return "\n".join(lines)
