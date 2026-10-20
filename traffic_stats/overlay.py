# -*- coding: utf-8 -*-
"""
Render what the pipeline is actually doing, so it can be checked by eye.

    python -m traffic_stats.overlay --video clips/CAM01_20260301080000.mp4 \
                                    --out out/

Writes three images:

  geometry.png     the median background with the corridor, the road band,
                   the occluder columns and the counting line drawn on it.
                   Check this against a frame containing the LARGEST vehicle
                   you expect -- a zone traced on the asphalt clips trucks,
                   and the counts stay plausible while being wrong.

  artifacts.png    ARTIFACT CLEANING, side by side. Top row: the largest view
                   of each vehicle, which is what you get without
                   occlusion-aware selection -- usually the frame with a pole
                   across it. Bottom row: the view the pipeline actually
                   keeps. Same vehicles, same run.

  daynight.png     one tile per minute of footage, with the measured median
                   asphalt luma. The day/night switch is the most error-prone
                   stage in the whole pipeline and this is how you check it.
"""
import argparse
import os
import sys
from collections import deque

import cv2
import numpy as np

from . import config, detect, geometry, track


def median_background(site, path, n=160):
    """Immune to passing traffic: the road is whatever is there most of the
    time. Keyframes only, because this does not need every frame."""
    frames = []
    for i, g in enumerate(detect.frames_from_video(path, site)):
        if i % 7 == 0:
            frames.append(g)
        if len(frames) >= n:
            break
    if not frames:
        raise SystemExit("no frames decoded from %s" % path)
    return np.median(np.stack(frames), axis=0).astype(np.uint8)


def draw_geometry(site, bg, path):
    img = cv2.cvtColor(bg, cv2.COLOR_GRAY2BGR)
    xs = np.arange(site.width)
    a, b = geometry.band_at(site, xs)
    h = b - a
    top = a - site.head_mult * h
    bot = b + site.foot_mult * h

    # corridor: the road band grown UPWARD, because vehicles rest on the road
    # but their bodies extend up the image
    shade = img.copy()
    lo, hi = site.far[0][0], site.far[-1][0]
    for x in range(lo, min(hi + 1, site.width)):
        y0, y1 = int(max(top[x], 0)), int(min(bot[x], site.height - 1))
        if y1 > y0:
            shade[y0:y1, x] = (0.65 * shade[y0:y1, x]
                               + 0.35 * np.array([90, 200, 90])).astype(np.uint8)
    img = cv2.addWeighted(shade, 0.55, img, 0.45, 0)

    for ys, col in ((a, (0, 215, 255)), (b, (0, 215, 255))):
        pts = np.array([[x, int(ys[x])] for x in range(lo, min(hi + 1, site.width))])
        cv2.polylines(img, [pts], False, col, 1, cv2.LINE_AA)

    for x0, x1 in site.occluders:
        cv2.rectangle(img, (x0, 0), (x1, site.height - 1), (60, 60, 230), 2)
        cv2.putText(img, "occluder", (max(x0 - 26, 2), 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (60, 60, 230), 1, cv2.LINE_AA)

    for x, lab in ((site.count_x, "count x=%d" % site.count_x),
                   (site.verify_x, "verify x=%d" % site.verify_x)):
        if not x:
            continue
        cv2.line(img, (x, 0), (x, site.height - 1), (255, 255, 255), 1,
                 cv2.LINE_AA)
        cv2.putText(img, lab, (x + 4, site.height - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 255), 1,
                    cv2.LINE_AA)
    cv2.putText(img, "green = corridor   yellow = road band   red = occluders"
                     "   white = both lines, a pass must cross BOTH",
                (6, site.height - 26),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (240, 240, 240), 1, cv2.LINE_AA)
    cv2.imwrite(path, img)


def _pair_sheet(pairs, path, tile=120, cols=8):
    """Two rows per group: what you would have kept, and what was kept."""
    if not pairs:
        return 0
    cols = min(cols, len(pairs))
    groups = (len(pairs) + cols - 1) // cols
    head, banner = 18, 26
    sheet = np.zeros((banner + groups * (2 * tile + head), cols * tile, 3),
                     np.uint8)
    for i, (bad, good, label) in enumerate(pairs):
        g, k = divmod(i, cols)
        y0 = banner + g * (2 * tile + head) + head
        x0 = k * tile
        for row, (im, col) in enumerate(((bad, (60, 60, 230)),
                                         (good, (90, 200, 90)))):
            t = cv2.cvtColor(cv2.resize(im, (tile, tile),
                                        interpolation=cv2.INTER_AREA),
                             cv2.COLOR_GRAY2BGR)
            cv2.rectangle(t, (0, 0), (tile - 1, tile - 1), col, 2)
            sheet[y0 + row * tile:y0 + (row + 1) * tile, x0:x0 + tile] = t
        cv2.putText(sheet, label, (x0 + 4, y0 - 6), cv2.FONT_HERSHEY_SIMPLEX,
                    0.36, (235, 235, 235), 1, cv2.LINE_AA)
    cv2.putText(sheet, "TOP (red) = largest view, pole across it        "
                       "BOTTOM (green) = largest CLEAR view -- what the "
                       "pipeline keeps        labels: track  w_norm "
                       "rejected -> kept",
                (6, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (235, 235, 235), 1,
                cv2.LINE_AA)
    cv2.imwrite(path, sheet)
    return len(pairs)


def run(site, path, out):
    det = detect.Detector(site)
    trk = track.Tracker(site)
    recent = deque(maxlen=96)
    pairs, lumas, minute_tiles = [], [], []

    for i, g in enumerate(detect.frames_from_video(path, site)):
        boxes = det(g)
        recent.append((i, g))
        lumas.append(det.last_luma)
        if i % int(site.fps * 60) == 0:
            minute_tiles.append((i, g.copy(), det.last_luma))
        for c in trk.update(boxes, i, None, is_day=det.last_is_day):
            if c.alt_frame == c.best_frame or len(pairs) >= 16:
                continue
            cache = dict(recent)
            if c.alt_frame not in cache or c.best_frame not in cache:
                continue
            ab, bb = c.alt_box, c.best_box
            bad = cache[c.alt_frame][max(ab[1], 0):ab[3], max(ab[0], 0):ab[2]]
            good = cache[c.best_frame][max(bb[1], 0):bb[3], max(bb[0], 0):bb[2]]
            if bad.size and good.size:
                pairs.append((bad, good, "#%d  %.2f -> %.2f"
                              % (c.tid, c.alt_w_norm, c.best_w_norm)))

    n = _pair_sheet(pairs, os.path.join(out, "artifacts.png"))

    # day / night strip
    if minute_tiles:
        tile = 150
        strip = np.zeros((tile + 24, tile * len(minute_tiles), 3), np.uint8)
        for j, (idx, g, lum) in enumerate(minute_tiles):
            t = cv2.cvtColor(cv2.resize(g, (tile, tile),
                                        interpolation=cv2.INTER_AREA),
                             cv2.COLOR_GRAY2BGR)
            strip[24:, j * tile:(j + 1) * tile] = t
            day = lum >= site.night_luma
            cv2.putText(strip, "%02d min  luma %.0f  %s"
                        % (idx / site.fps / 60, lum, "DAY" if day else "NIGHT"),
                        (j * tile + 4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.36,
                        (90, 200, 90) if day else (60, 160, 255), 1, cv2.LINE_AA)
        cv2.imwrite(os.path.join(out, "daynight.png"), strip)

    return n, lumas


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", default="out")
    ap.add_argument("--site", default="demo",
                    help="which Site from traffic_stats/config.py: %s"
                         % ", ".join(config.SITES))
    args = ap.parse_args(argv)

    try:
        site = config.SITES[args.site]
    except KeyError:
        raise SystemExit("unknown --site %r; choose from %s"
                         % (args.site, ", ".join(config.SITES)))
    site = site.scaled()      # detect at the Site's processing resolution
    os.makedirs(args.out, exist_ok=True)

    bg = median_background(site, args.video)
    cv2.imwrite(os.path.join(args.out, "median_background.png"), bg)
    draw_geometry(site, bg, os.path.join(args.out, "geometry.png"))
    n, lumas = run(site, args.video, args.out)

    print("wrote %s/geometry.png  (check it against a frame with the biggest "
          "vehicle you expect)" % args.out)
    print("wrote %s/artifacts.png  (%d vehicles where the largest view was "
          "rejected as obstructed)" % (args.out, n))
    print("wrote %s/daynight.png   (median asphalt luma per minute; threshold "
          "is %d)" % (args.out, site.night_luma))
    if lumas:
        print("      luma range %.0f - %.0f" % (min(lumas), max(lumas)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
