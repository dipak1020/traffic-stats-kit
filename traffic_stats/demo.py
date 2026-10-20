# -*- coding: utf-8 -*-
"""
Run the whole pipeline end to end against synthetic footage with known ground
truth, and score it.

    python -m traffic_stats.demo

No video, no model weights, no network. The point of the demo is not that it
counts synthetic rectangles; it is that it runs the gates from APPROACH.md
stage 8 and shows the one failure mode that matters, by running the detector
twice -- once with in-frame box merging and once without.
"""
import argparse
import os
from collections import deque

import numpy as np

from . import config, detect, stats, synth, track, validate


def run(site, scene, merge=True, sheet_path=None):
    det = detect.Detector(site, merge=merge)
    trk = track.Tracker(site)

    # Warm up the background model on empty road. Skipping this makes the
    # first seconds of every file produce garbage detections.
    rng = np.random.default_rng(1)
    for _ in range(45):
        warm = np.clip(scene.bg.astype(np.int16)
                       + rng.normal(0, 2.5, scene.bg.shape).astype(np.int16),
                       0, 255).astype(np.uint8)
        det(warm)

    crossings, busy, total = [], 0, 0
    recent = deque(maxlen=48)          # enough to reach back to best_frame
    crops = []
    for f, t, img, _night in scene.frames():
        boxes = det(img)
        total += 1
        if boxes:
            busy += 1
        recent.append((f, img))
        new = trk.update(boxes, f, t, is_day=det.last_is_day)
        crossings += new
        if sheet_path:
            cache = dict(recent)
            for c in new:
                src = cache.get(c.best_frame, img)
                x0, y0, x1, y1 = c.best_box
                crops.append(src[max(y0, 0):y1, max(x0, 0):x1])

    if sheet_path:
        validate.contact_sheet(crops, sheet_path)
    return crossings, stats.occupancy(busy, total)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--minutes", type=float, default=10.0)
    ap.add_argument("--headway", type=float, default=12.0,
                    help="mean seconds between vehicles, per direction")
    ap.add_argument("--night-after", type=float, default=None,
                    help="seconds after which the scene goes dark")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()

    site = config.DEMO
    os.makedirs(args.out, exist_ok=True)

    def fresh():
        return synth.Scene(site, minutes=args.minutes,
                           mean_headway_s=args.headway,
                           night_after_s=args.night_after)

    sc = fresh()
    good, occ = run(site, sc, merge=True,
                    sheet_path=os.path.join(args.out, "contact_sheet.png"))
    truth = sc.truth_counts()

    bad, _ = run(site, fresh(), merge=False)          # the control
    again, _ = run(site, fresh(), merge=True)         # determinism

    types = [track.classify_by_size(c.best_w_norm, c.best_h_norm,
                                    c.is_day, c.clear_view) for c in good]

    print("=" * 68)
    print("  SYNTHETIC SITE: %s   %d x %d @ %g fps   %g min"
          % (site.name, site.width, site.height, site.fps, args.minutes))
    print("=" * 68)

    print("\nGROUND TRUTH")
    print("  crossed the line        %d   (LR %d / RL %d, %d articulated)"
          % (truth["total"], truth["LR"], truth["RL"], truth["articulated"]))

    print("\nCOUNTED")
    err = 100.0 * (len(good) - truth["total"]) / max(truth["total"], 1)
    print("  with in-frame merging   %d   (%+.1f%%)" % (len(good), err))
    errb = 100.0 * (len(bad) - truth["total"]) / max(truth["total"], 1)
    print("  WITHOUT merging         %d   (%+.1f%%)  <- the usual bug"
          % (len(bad), errb))
    print("  occupancy               %.1f %% of time (no distance needed)" % occ)

    print("\nGATES  (APPROACH.md stage 8)")
    print(validate.report({
        "headway": validate.headway_gate(good, site),
        "determinism": validate.determinism_gate(good, again),
    }))
    print("  headway, no merge:")
    for d, g in validate.headway_gate(bad, site).items():
        print("      %s  %s" % (d, g["verdict"]))
        if g.get("histogram"):
            print("      %s  %s" % (" " * len(d), g["histogram"]))

    if args.night_after is not None:
        nd = sum(1 for c in good if not c.is_day)
        print("\n  day/night split         %d day, %d night crossings"
              % (len(good) - nd, nd))

    rows = stats.aggregate(good, site, minutes=5, types=types)
    print("\nFIVE-MINUTE TABLE  (same call with minutes=60 gives the hourly one)")
    print("  %-17s %5s %4s %4s %6s %8s" %
          ("bucket", "total", "LR", "RL", "cum", "headway"))
    for r in rows:
        print("  %-17s %5d %4d %4d %6d %8s"
              % (r["bucket_start"], r["total"], r["LR"], r["RL"],
                 r["cumulative"], r["mean_headway_s"]))
    pk = stats.peak(rows)
    if pk:
        print("  peak bucket %s with %d" % (pk["bucket_start"], pk["total"]))

    print("\nCOMPOSITION  (placeholder cut-points -- re-derive from your crops)")
    from collections import Counter
    got_t, tru_t = Counter(types), truth["by_type"]
    print("  %-24s %6s %6s" % ("class", "truth", "found"))
    for k in sorted(set(got_t) | set(tru_t)):
        print("  %-24s %6d %6d" % (k, tru_t.get(k, 0), got_t.get(k, 0)))
    ok = sum(min(tru_t.get(k, 0), got_t.get(k, 0)) for k in set(got_t) | set(tru_t))
    print("  agreement with truth    %.0f %%  (size rules only, no model)"
          % (100.0 * ok / max(truth["total"], 1)))

    print("\nNOT REPORTED")
    try:
        stats.speed(site)
    except ValueError as e:
        print("  speed/density:", str(e).split(".")[0] + ".")

    stats.write_timeline(good, site, os.path.join(args.out, "timeline.csv"), types)
    stats.write_csv(rows, os.path.join(args.out, "buckets.csv"))
    print("\nWROTE  %s/timeline.csv  %s/buckets.csv  %s/contact_sheet.png"
          % (args.out, args.out, args.out))
    print("LOOK AT THE CONTACT SHEET. No numeric gate replaces it.\n")


if __name__ == "__main__":
    main()
