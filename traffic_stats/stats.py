# -*- coding: utf-8 -*-
"""
Temporal statistics, in order of confidence.

The design rule here is a refusal: speed() and density() raise unless the
Site carries a distance measured on site. A wrong speed discredits the counts
printed next to it, so the pipeline would rather report nothing. Occupancy is
offered in its place -- it is what an inductive loop reports, and it needs no
calibration at all.
"""
import csv
from collections import Counter, defaultdict


def localise(crossings, site):
    """Apply the measured clock offset. Stage 2 -- never skip this."""
    return [(c, c.t + site.clock_offset) for c in crossings]


def _floor(t, minutes):
    if minutes >= 60:
        step = minutes // 60
        return t.replace(hour=(t.hour // step) * step, minute=0,
                         second=0, microsecond=0)
    return t.replace(minute=(t.minute // minutes) * minutes,
                     second=0, microsecond=0)


def headways(times):
    """Seconds between consecutive passes. The validation gate eats these."""
    ts = sorted(times)
    return [(b - a).total_seconds() for a, b in zip(ts, ts[1:])]


def aggregate(crossings, site, minutes=60, types=None):
    """
    One row per time bucket. minutes=60 gives the hourly table; the demo runs
    for minutes, so pass a smaller bucket there.

    The columns are deliberately the ones that need no distance calibration.
    """
    rows = defaultdict(lambda: {"LR": 0, "RL": 0, "t": [], "types": Counter()})
    for i, (c, lt) in enumerate(localise(crossings, site)):
        r = rows[_floor(lt, minutes)]
        r[c.direction] += 1
        r["t"].append(lt)
        r["types"][types[i] if types else "n/a"] += 1

    out, cum = [], 0
    total = sum(r["LR"] + r["RL"] for r in rows.values()) or 1
    for k in sorted(rows):
        r = rows[k]
        n = r["LR"] + r["RL"]
        cum += n
        hw = headways(r["t"])
        out.append({
            "bucket_start": k.strftime("%Y-%m-%d %H:%M"),
            "total": n,
            "LR": r["LR"],
            "RL": r["RL"],
            "cumulative": cum,
            "pct_of_period": round(100.0 * n / total, 1),
            "mean_headway_s": round(sum(hw) / len(hw), 1) if hw else "",
            "composition": " ".join("%s=%d" % kv for kv in r["types"].most_common()),
        })
    return out


def peak(rows):
    """The busiest bucket. Meaningless if coverage is incomplete -- say so."""
    return max(rows, key=lambda r: r["total"]) if rows else None


def occupancy(busy_frames, total_frames):
    """
    Percentage of time at least one vehicle was inside the measuring zone.

    The honest stand-in for density: no distance anchor, no assumptions.
    """
    return 100.0 * busy_frames / max(total_frames, 1)


def speed(site, *_):
    if site.metres_per_band_height is None:
        raise ValueError(
            "No distance anchor. Set Site.metres_per_band_height from a "
            "measurement taken ON SITE, or publish volume and omit speed. "
            "See docs/APPROACH.md stage 3.")
    raise NotImplementedError(
        "Anchor present: implement px/frame -> m/s here, then validate against "
        "free-flow speed on an uncongested segment before publishing.")


def density(site, *_):
    speed(site)          # same gate, same reason: k = q / v inherits it


def write_csv(rows, path):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def write_timeline(crossings, site, path, types=None):
    """One row per vehicle. This file is the audit trail."""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["local_time", "recorder_time", "track_id", "direction",
                    "type", "w_norm", "h_norm", "clear_view", "daylight",
                    "snapshot_frame"])
        for i, (c, lt) in enumerate(localise(crossings, site)):
            w.writerow([lt.strftime("%Y-%m-%d %H:%M:%S"),
                        c.t.strftime("%Y-%m-%d %H:%M:%S"), c.tid, c.direction,
                        types[i] if types else "n/a",
                        round(c.best_w_norm, 3), round(c.best_h_norm, 3),
                        int(c.clear_view), int(c.is_day), c.best_frame])
