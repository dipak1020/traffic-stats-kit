# -*- coding: utf-8 -*-
"""
Tracking and counting.

Two things make this work on real footage rather than clean footage:

  * association against a PREDICTED position, not the last one, so a vehicle
    that disappears behind a pole for a second stays one track instead of
    becoming two;
  * occlusion-aware frame selection -- the frame kept for measurement and for
    the snapshot is the largest CLEAR view, not the largest view. The largest
    view is usually the one with a pole across it.
"""
from dataclasses import dataclass, field
import datetime as dt

from . import geometry


@dataclass
class Crossing:
    tid: int
    t: dt.datetime                 # recorder time; localise later
    direction: str                 # "LR" or "RL"
    frame: int                     # frame index at the crossing
    span_x: float                  # px travelled, start to end
    best_frame: int                # frame to cut the snapshot from
    best_w_norm: float             # width in band-heights, from a clear view
    best_h_norm: float
    best_box: tuple
    clear_view: bool               # False = measurement is a lower bound
    is_day: bool
    # The view that WOULD have been chosen without occlusion-aware selection:
    # the largest view, which on a real site is usually the one with a pole
    # across it. Kept so the rejection can be shown, not merely asserted.
    alt_frame: int = -1
    alt_box: tuple = None
    alt_w_norm: float = 0.0


@dataclass
class _Track:
    tid: int
    cx: float
    cy: float
    box: tuple
    vx: float = 0.0
    frames: int = 1
    missed: int = 0
    x_first: float = 0.0
    counted: bool = False
    seen_verify: bool = False
    seen_count: bool = False
    best_score: float = -1e9
    best: tuple = None             # (frame, w_norm, h_norm, box, clear)
    any_score: float = -1e9        # largest view, occluded or not
    any_best: tuple = None
    hist: list = field(default_factory=list)


class Tracker:
    def __init__(self, site):
        self.site = site
        self.tracks = []
        self._next = 1

    # -----------------------------------------------------------------
    def _score(self, box):
        """
        Pick the frame to measure and photograph from.

        A frame where the vehicle spans an occluder or touches the image edge
        is REJECTED outright, not merely penalised: its width is a lower bound
        and its picture has a pole across it.
        """
        s = self.site
        x0, y0, x1, y1 = box
        clear = geometry.clear_view(s, x0, x1)
        if not clear:
            return -1.0, clear
        return geometry.w_norm(s, x0, x1), clear

    def update(self, boxes, frame_idx, t, is_day=True):
        s = self.site
        out = []
        cands = []
        for b in boxes:
            x0, y0, x1, y1 = b
            cands.append((0.5 * (x0 + x1), 0.5 * (y0 + y1), b))

        used = set()
        for tr in self.tracks:
            pred = tr.cx + tr.vx                      # one frame ahead
            best_i, best_d = -1, 1e18
            for i, (cx, cy, b) in enumerate(cands):
                if i in used:
                    continue
                d = abs(cx - pred) + 1.0 * abs(cy - tr.cy)
                # Velocity consistency. Without this, two vehicles passing in
                # opposite directions at the counting line can swap tracks:
                # each is a few pixels from the other's predicted position,
                # and both counts are then lost. Opposing motion is not a
                # near miss, it is a different vehicle.
                if tr.frames >= 2 and abs(tr.vx) > 1.0:
                    if (cx - tr.cx) * tr.vx < 0:
                        d += 1000.0
                if d < best_d:
                    best_i, best_d = i, d
            if best_i >= 0 and best_d <= s.max_match_d:
                cx, cy, b = cands[best_i]
                used.add(best_i)
                prev_cx = tr.cx
                nvx = cx - tr.cx
                tr.vx = nvx if tr.frames < 2 else 0.6 * tr.vx + 0.4 * nvx
                tr.cx, tr.cy, tr.box = cx, cy, b
                tr.frames += 1
                tr.missed = 0
                tr.hist.append((frame_idx, cx))

                sc, clear = self._score(b)
                wn = geometry.w_norm(s, b[0], b[2])
                if sc > tr.best_score:
                    tr.best_score = sc
                    tr.best = (frame_idx, wn,
                               geometry.h_norm(s, b[1], b[3], cx), b, clear)
                if wn > tr.any_score:
                    tr.any_score = wn
                    tr.any_best = (frame_idx, wn, b)

                # Line crossing. A pass needs BOTH lines, so a stationary
                # artifact that jitters across one of them never counts.
                if prev_cx != cx:
                    if (prev_cx - s.count_x) * (cx - s.count_x) <= 0:
                        tr.seen_count = True
                    if s.verify_x and (prev_cx - s.verify_x) * (cx - s.verify_x) <= 0:
                        tr.seen_verify = True
                both = tr.seen_count and (tr.seen_verify or not s.verify_x)
                if not tr.counted and both and tr.frames >= s.min_frames:
                    span = abs(cx - tr.x_first)
                    if span >= s.min_span_x or abs(tr.vx) * s.max_miss > s.min_span_x:
                        tr.counted = True
                        bf, bw, bh, bb, bc = (tr.best if tr.best else
                                              (frame_idx, 0.0, 0.0, b, False))
                        af, aw, ab = (tr.any_best if tr.any_best
                                      else (bf, bw, bb))
                        out.append(Crossing(
                            tid=tr.tid, t=t, direction="LR" if tr.vx > 0 else "RL",
                            frame=frame_idx, span_x=span, best_frame=bf,
                            best_w_norm=bw, best_h_norm=bh, best_box=bb,
                            clear_view=bc, is_day=is_day,
                            alt_frame=af, alt_box=ab, alt_w_norm=aw))
            else:
                tr.missed += 1
                tr.cx += tr.vx                        # coast through occlusion

        for i, (cx, cy, b) in enumerate(cands):
            if i in used:
                continue
            tr = _Track(tid=self._next, cx=cx, cy=cy, box=b, x_first=cx)
            tr.hist.append((frame_idx, cx))
            sc, clear = self._score(b)
            wn = geometry.w_norm(self.site, b[0], b[2])
            tr.best_score = sc
            tr.best = (frame_idx, wn,
                       geometry.h_norm(self.site, b[1], b[3], cx), b, clear)
            tr.any_score = wn
            tr.any_best = (frame_idx, wn, b)
            self._next += 1
            self.tracks.append(tr)

        self.tracks = [t_ for t_ in self.tracks
                       if t_.missed <= self.site.max_miss
                       and -200 <= t_.cx <= self.site.width + 200]
        return out


# ---------------------------------------------------------------------------
def classify_by_size(w_norm, h_norm, is_day=True, clear_view=True):
    """
    Tier-3 classification from size alone -- no model, no weights, no network.

    THESE CUT-POINTS ARE PLACEHOLDERS. They are shaped like real ones but they
    are not yours. Re-derive them from ~100 of your own labelled crops; they
    do not transfer between cameras, even similar ones. See APPROACH.md
    stage 6.
    """
    if not is_day:
        return "unclassified_night"
    if not clear_view:
        return "unclassified_occluded"
    if w_norm < 0.95 and h_norm < 0.75:
        return "motorcycle"
    if w_norm < 1.55:
        return "car"
    if w_norm < 2.20:
        return "pickup_van"
    if w_norm < 3.30:
        return "truck_2axle"
    return "truck_3axle_plus"
