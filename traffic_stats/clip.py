# -*- coding: utf-8 -*-
"""
Write the synthetic scene out as a real video file, so the full real-footage
path can be exercised without downloading anything.

    python -m traffic_stats.clip --minutes 10 --out clips/

Produces an H.264 MP4 whose filename carries a timestamp in the format
report.py parses, plus a sidecar `*_truth.csv` with the ground truth. Then:

    python -m traffic_stats.report --videos clips/ --out out_real/

exercises ffmpeg decoding, timestamp parsing, per-file processing, crops,
coverage and the gates -- the parts traffic_stats.demo skips because it
generates frames in memory.

The clip is small (10 minutes at 6 fps, 640x360, grey) -- a few MB, not
something that should ever be committed. Regenerate it instead; it is
deterministic for a given seed.
"""
import argparse
import csv
import datetime as dt
import os
import subprocess
import sys

from . import config, synth


def write_clip(site, path, minutes, headway, night_after, seed, fps=None,
               crf=28):
    fps = fps or site.fps
    scene = synth.Scene(site, minutes=minutes, mean_headway_s=headway,
                        night_after_s=night_after, seed=seed)
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "gray",
        "-s", "%dx%d" % (site.width, site.height), "-r", "%g" % fps,
        "-i", "-",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf),
        "-pix_fmt", "yuv420p", str(path),
    ]
    try:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    except FileNotFoundError:
        print("ffmpeg not found on PATH. Install it, or use "
              "traffic_stats.demo, which needs no ffmpeg.", file=sys.stderr)
        raise SystemExit(1)

    n = 0
    for _f, _t, img, _night in scene.frames():
        p.stdin.write(img.tobytes())
        n += 1
    p.stdin.close()
    if p.wait() != 0:
        raise SystemExit("ffmpeg failed")
    return scene, n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="clips")
    ap.add_argument("--minutes", type=float, default=10.0)
    ap.add_argument("--headway", type=float, default=20.0)
    ap.add_argument("--night-after", type=float, default=None)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--start", default="20260301080000",
                    help="recorder timestamp encoded in the filename")
    ap.add_argument("--name", default="CAM01")
    ap.add_argument("--crf", type=int, default=28,
                    help="h264 quality; synthetic noise is incompressible, "
                         "so low numbers make very large files")
    args = ap.parse_args(argv)

    site = config.DEMO
    os.makedirs(args.out, exist_ok=True)
    stem = "%s_%s" % (args.name, args.start)
    path = os.path.join(args.out, stem + ".mp4")

    scene, n = write_clip(site, path, args.minutes, args.headway,
                          args.night_after, args.seed, crf=args.crf)

    t0 = dt.datetime.strptime(args.start, "%Y%m%d%H%M%S")
    truth_path = os.path.join(args.out, stem + "_truth.csv")
    with open(truth_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["recorder_time", "direction", "type", "articulated",
                    "crossed_counting_line"])
        for v in scene.truth:
            w.writerow([(t0 + dt.timedelta(seconds=v["t_s"])
                         ).strftime("%Y-%m-%d %H:%M:%S"),
                        v["dir"], v["type"], int(v["artic"]),
                        int(v["crossed"])])

    tc = scene.truth_counts()
    size = os.path.getsize(path) / 1e6
    print("wrote %s  (%.1f MB, %d frames, %.1f min)"
          % (path, size, n, n / site.fps / 60))
    print("wrote %s" % truth_path)
    print("ground truth: %d crossed the counting line "
          "(LR %d / RL %d, %d articulated)"
          % (tc["total"], tc["LR"], tc["RL"], tc["articulated"]))
    print("\nnow:  python -m traffic_stats.report --videos %s --out out_real"
          % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
