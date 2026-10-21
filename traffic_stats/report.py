# -*- coding: utf-8 -*-
"""
Run the pipeline over a folder of real video files and write the survey.

    python -m traffic_stats.report --videos /path/to/folder --out out/

Produces, per run:

    timeline.csv       one row per counted vehicle -- the audit trail
    buckets.csv        hourly volume, direction split, cumulative, headway
    crops/             one image per counted vehicle
    contact_sheet.png  GATE 1: look at this before reading any number
    gates.txt          headway, coverage and determinism verdicts
    coverage.txt       every continuous block of footage and every gap

Edit traffic_stats/config.py first. It is the only site-specific file, and
nothing below will be meaningful until the corridor, the counting line and
the clock offset are right for your camera.
"""
import argparse
import datetime as dt
import os
import re
import sys
from collections import deque

from . import config, detect, stats, track, validate

# Recorders usually encode the start time in the filename. Add yours here
# rather than relying on file mtime, which changes when files are copied.
STAMP = [
    re.compile(r"(?P<Y>20\d\d)(?P<m>\d\d)(?P<d>\d\d)(?P<H>\d\d)(?P<M>\d\d)(?P<S>\d\d)"),
    re.compile(r"(?P<Y>20\d\d)-(?P<m>\d\d)-(?P<d>\d\d)[_T ](?P<H>\d\d)[-:](?P<M>\d\d)[-:](?P<S>\d\d)"),
]


def start_time(path):
    """Recorder time this file starts at. Local time comes later, via the
    measured clock offset -- do not conflate the two."""
    name = os.path.basename(path)
    for rx in STAMP:
        m = rx.search(name)
        if m:
            g = {k: int(v) for k, v in m.groupdict().items()}
            return dt.datetime(g["Y"], g["m"], g["d"], g["H"], g["M"], g["S"])
    return dt.datetime.fromtimestamp(os.path.getmtime(path))


def process(path, site, det, trk, crops_dir, t0=None, sheet_cap=200):
    """One file. The detector and tracker are shared across files on purpose:
    the background model should not be thrown away at every file boundary."""
    import cv2
    t0 = t0 or start_time(path)
    recent = deque(maxlen=64)
    crossings, crops, busy, n = [], [], 0, 0

    for i, gray in enumerate(detect.frames_from_video(path, site)):
        t = t0 + dt.timedelta(seconds=i / site.fps)
        boxes = det(gray)
        n += 1
        if boxes:
            busy += 1
        recent.append((i, gray))
        new = trk.update(boxes, i, t, is_day=det.last_is_day)
        crossings += new
        cache = dict(recent)
        for c in new:
            src = cache.get(c.best_frame, gray)
            x0, y0, x1, y1 = c.best_box
            crop = src[max(y0, 0):y1, max(x0, 0):x1]
            if crop.size:
                cv2.imwrite(os.path.join(
                    crops_dir, "%s_%06d_%s.jpg"
                    % (os.path.splitext(os.path.basename(path))[0], c.tid,
                       c.direction)), crop)
                if len(crops) < sheet_cap:
                    crops.append(crop)

    end = t0 + dt.timedelta(seconds=n / site.fps)
    return crossings, crops, (t0, end), busy, n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--videos", required=True, help="folder of video files")
    ap.add_argument("--out", default="out")
    ap.add_argument("--site", default="demo",
                    help="which Site from traffic_stats/config.py: %s"
                         % ", ".join(config.SITES))
    ap.add_argument("--ext", default=".mp4,.mkv,.avi,.ts")
    ap.add_argument("--bucket", type=int, default=60, help="minutes per row")
    args = ap.parse_args(argv)

    try:
        site = config.SITES[args.site]
    except KeyError:
        raise SystemExit("unknown --site %r; choose from %s"
                         % (args.site, ", ".join(config.SITES)))
    site = site.scaled()      # detect at the Site's processing resolution          # <- point this at YOUR site
    if site.name == "demo-synthetic":
        print("WARNING: still running the synthetic demo site. Define your "
              "own Site in traffic_stats/config.py -- the geometry below is "
              "not your camera's.\n", file=sys.stderr)

    exts = tuple(e.strip().lower() for e in args.ext.split(","))
    files = sorted(os.path.join(args.videos, f) for f in os.listdir(args.videos)
                   if f.lower().endswith(exts) and not f.startswith("."))
    if not files:
        print("no video files in %s" % args.videos, file=sys.stderr)
        return 1

    crops_dir = os.path.join(args.out, "crops")
    os.makedirs(crops_dir, exist_ok=True)

    det = detect.Detector(site)
    trk = track.Tracker(site)
    allc, sheet, spans, busy, total = [], [], [], 0, 0

    for p in files:
        print("  %s" % os.path.basename(p), flush=True)
        c, cr, span, b, n = process(p, site, det, trk, crops_dir)
        allc += c
        sheet += cr[:max(0, 200 - len(sheet))]
        spans.append(span)
        busy += b
        total += n
        print("    %4d vehicles, %5.1f min" % (len(c), n / site.fps / 60))

    types = [track.classify_by_size(c.best_w_norm, c.best_h_norm,
                                    c.is_day, c.clear_view) for c in allc]
    rows = stats.aggregate(allc, site, minutes=args.bucket, types=types)
    stats.write_timeline(allc, site, os.path.join(args.out, "timeline.csv"), types)
    stats.write_csv(rows, os.path.join(args.out, "buckets.csv"))
    validate.contact_sheet(sheet, os.path.join(args.out, "contact_sheet.png"))

    cov = validate.coverage_gate(spans)
    hw = validate.headway_gate(allc, site)
    with open(os.path.join(args.out, "gates.txt"), "w", encoding="utf-8") as fh:
        fh.write("vehicles counted      %d\n" % len(allc))
        fh.write("occupancy             %.1f %%\n" % stats.occupancy(busy, total))
        fh.write("clock offset applied  %s\n" % site.clock_offset)
        fh.write("coverage              %s %s\n" % (cov["covered_pct"], cov["verdict"]))
        for d, g in hw.items():
            fh.write("headway %-3s           %s  %s\n"
                     % (d, g["verdict"], g.get("histogram", "")))
        for a, b, mins in cov["gaps"]:
            fh.write("GAP  %s -> %s  (%.0f min)\n" % (a, b, mins))
        fh.write("\nNOT REPORTED: speed, density. No distance anchor is set "
                 "(Site.metres_per_band_height). See docs/APPROACH.md.\n")

    pk = stats.peak(rows)
    print("\n%d vehicles, coverage %.1f%% (%s)"
          % (len(allc), cov["covered_pct"], cov["verdict"]))
    if pk:
        print("peak %s: %d vehicles%s" % (
            pk["bucket_start"], pk["total"],
            "" if cov["verdict"] == "PASS" else "  [peak of AVAILABLE data]"))
    for d, g in hw.items():
        print("headway %s: %s" % (d, g["verdict"]))
    print("\nwrote %s/ -- now LOOK at contact_sheet.png before believing any "
          "of it." % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
