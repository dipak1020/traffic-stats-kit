# -*- coding: utf-8 -*-
"""
Detection: background subtraction inside the corridor, then the two rules
that matter more than the subtractor does.

  1. ground contact        -- geometry.on_road
  2. in-frame box merging  -- merge_boxes, below

Rule 2 is the one everybody gets wrong. A long vehicle is not one blob: the
gap between tractor and trailer splits it, and each fragment crosses the
counting line. Union them IN THE SAME FRAME. Merging afterwards by timing
cannot distinguish a tractor+trailer from a truck genuinely followed by a bus
half a second later, and appearance matching does not rescue it either,
because two crops of the same scene share mostly background.
"""
import cv2
import numpy as np

from . import geometry


def merge_boxes(site, boxes):
    """
    Union boxes that are two parts of one vehicle.

    Three conditions, all necessary:

      * the horizontal gap is small RELATIVE TO THE LOCAL PERSPECTIVE SCALE.
        A fixed pixel gap cannot work: the same real gap is twice as wide
        near the camera.
      * the vertical extents overlap.
      * the two boxes rest in the SAME LANE, compared as a FRACTION OF THE
        BAND rather than as a pixel row. Fragments of one vehicle share a
        lane fraction; two vehicles passing in opposite lanes differ by about
        half a band. Comparing raw pixel rows instead fails on exactly the
        vehicles this rule exists for: a long vehicle spans enough columns
        that the sloping road puts its cab and its trailer on visibly
        different image rows.

    Applied iteratively, so a cab plus two trailer sections collapse in one
    pass.
    """
    out = [list(b) for b in boxes]
    changed = True
    while changed and len(out) > 1:
        changed = False
        out.sort(key=lambda b: b[0])
        for i in range(len(out) - 1):
            x0, y0, x1, y1 = out[i]
            X0, Y0, X1, Y1 = out[i + 1]
            gap = X0 - x1
            cx = 0.5 * (x1 + X0)
            bh = geometry.band_h(site, np.clip(cx, 0, site.width - 1))
            ov = min(y1, Y1) - max(y0, Y0)
            span = max(y1 - y0, Y1 - Y0)
            same_lane = abs(geometry.ground_frac(site, 0.5 * (x0 + x1), y1)
                            - geometry.ground_frac(site, 0.5 * (X0 + X1), Y1)
                            ) <= site.foot_align
            if (gap <= site.gap_mult * bh and span > 0
                    and ov / span >= site.vovl_min and same_lane):
                out[i] = [min(x0, X0), min(y0, Y0), max(x1, X1), max(y1, Y1)]
                del out[i + 1]
                changed = True
                break
    return [tuple(int(v) for v in b) for b in out]


class Detector:
    """
    Stateful: the background model has to see a few seconds of road before it
    means anything. Feed every frame in order, including the warm-up.
    """

    def __init__(self, site, merge=True, history=300, var_threshold=28):
        self.site = site
        self.merge = merge
        self.corridor = geometry.corridor_mask(site)
        self.road = geometry.road_mask(site)
        self.bs = cv2.createBackgroundSubtractorMOG2(
            history=history, varThreshold=var_threshold, detectShadows=False)
        # Kernels derived from the typical band height, so they scale with
        # the processing resolution instead of being pixel constants.
        bh = float(geometry.band_h(site, site.width // 2))
        self.k_open = self._kern(site.open_frac, site.open_frac, bh, 3)
        self.k_day = self._kern(*site.dil_day_frac, bh=bh, lo=3)
        self.k_night = self._kern(*site.dil_night_frac, bh=bh, lo=3)
        self.r_day = self._radii(self.k_day, site.dil_iter)
        self.r_night = self._radii(self.k_night, site.dil_iter)
        self.last_is_day = True

    @staticmethod
    def _kern(fx, fy, bh, lo=3):
        w = max(lo, int(round(fx * bh)) | 1)
        h = max(lo, int(round(fy * bh)) | 1)
        return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (w, h))

    @staticmethod
    def _radii(k, iters):
        """How much each edge grew, so it can be given back before measuring."""
        return ((k.shape[1] // 2) * iters, (k.shape[0] // 2) * iters)

    # -- stage 1e -----------------------------------------------------------
    def is_day(self, gray):
        """
        MEDIAN luma of the asphalt, away from any lamp.

        The obvious test -- mean luma of the scene -- fails outright: one pole
        lamp pulls the mean up and every night frame reads as day.
        """
        v = float(np.median(gray[self.road]))
        self.last_luma = v
        return v >= self.site.night_luma

    # -- stage 4 ------------------------------------------------------------
    def __call__(self, gray):
        s = self.site
        day = self.is_day(gray)
        self.last_is_day = day

        fg = self.bs.apply(gray)
        fg[~self.corridor] = 0
        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, self.k_open)
        k = self.k_day if day else self.k_night
        fg = cv2.dilate(fg, k, iterations=s.dil_iter)
        rx, ry = self.r_day if day else self.r_night

        n, _, st, _ = cv2.connectedComponentsWithStats((fg > 0).astype(np.uint8), 8)
        boxes = []
        for i in range(1, n):
            x, y, w, h, area = st[i]
            x1, y1 = x + w, y + h
            # Dilation is for CONNECTING, not for measuring. Left in, it adds
            # the kernel radius to every edge, which inflates w_norm by a
            # constant amount -- enough on its own to push motorcycles over
            # the car threshold. Give it back before anything is measured.
            if w > 2 * rx and h > 2 * ry:
                x, y, x1, y1 = x + rx, y + ry, x1 - rx, y1 - ry
                w, h = x1 - x, y1 - y
            cx = x + 0.5 * w
            bh = geometry.band_h(s, np.clip(cx, 0, s.width - 1))
            if area < s.min_area_frac * bh * bh:
                continue
            if not geometry.on_road(s, cx, y1):          # ground contact
                continue
            if not day:
                # Motion only, PLUS a real light source inside the blob. An
                # early version OR-ed in a static bright-pixel threshold to
                # catch headlights; it fired forever on the lamp and produced
                # 38 "crossings" in four minutes of empty midnight road.
                if gray[y:y1, x:x1].max() < s.night_light:
                    continue
            boxes.append((x, y, x1, y1))

        return merge_boxes(s, boxes) if self.merge else boxes


# ---------------------------------------------------------------------------
# Real-footage frame source. The demo does not need it; a real site does.
# ---------------------------------------------------------------------------
def frames_from_video(path, site, ss=None, dur=None):
    """
    Decode to greyscale at the site's resolution and fps, one frame at a time.

    Keyframe-only decoding (-skip_frame nokey) is ~30x faster and is the right
    choice for scanning or for day/night contact sheets, but NOT for counting:
    tracking needs regular sampling.
    """
    import subprocess
    import sys
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error"]
    if ss is not None:
        cmd += ["-ss", str(ss)]
    cmd += ["-i", str(path)]
    if dur is not None:
        cmd += ["-t", str(dur)]
    cmd += ["-vf", "fps=%g,scale=%d:%d,format=gray" % (site.fps, site.width, site.height),
            "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    nbytes = site.width * site.height
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         bufsize=nbytes * 8)
    drained = False
    try:
        while True:
            buf = p.stdout.read(nbytes)
            if len(buf) < nbytes:
                drained = True
                break
            yield np.frombuffer(buf, np.uint8).reshape(site.height, site.width)
    finally:
        # A caller that stops early (a median background needs 160 frames, not
        # 4000) leaves ffmpeg writing into a closed pipe, which it reports as
        # a broken-pipe error. That is our doing, not a decode problem, so
        # stop ffmpeg deliberately and discard what it says about it.
        p.stdout.close()
        if not drained and p.poll() is None:
            p.terminate()
        err = p.stderr.read()
        p.stderr.close()
        p.wait()
        if drained and err.strip():
            sys.stderr.write(err.decode("utf-8", "replace"))
