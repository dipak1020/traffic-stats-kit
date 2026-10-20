# -*- coding: utf-8 -*-
"""
Synthetic footage with known ground truth, so the pipeline is testable with
no video, no weights and no network. This is what makes the repo "mock but
workable": every gate below runs against a count you actually know.

It is deliberately not easy footage. It contains:
  * perspective that varies across the frame (vehicles shrink with distance)
  * a pole in front of the carriageway, which splits blobs passing behind it
  * articulated vehicles drawn as TWO rectangles with a gap, which is exactly
    the fragmentation that causes double counting
  * sensor noise and a slow brightness drift
  * an optional night segment where only headlights are visible
"""
import datetime as dt
import numpy as np

from . import geometry

# w_norm, h_norm, articulated?, probability
TYPES = [
    ("motorcycle",       0.70, 0.60, False, 0.15),
    ("car",              1.30, 0.80, False, 0.45),
    ("pickup_van",       1.80, 0.95, False, 0.20),
    ("truck_2axle",      2.60, 1.15, False, 0.13),
    ("truck_3axle_plus", 3.90, 1.25, True,  0.07),
]


def _background(site):
    """Static scene: sky, verge, asphalt, and one pole in front of the road."""
    img = np.full((site.height, site.width), 72, np.uint8)       # verge
    img[:int(0.12 * site.height), :] = 148                       # sky
    xs = np.arange(site.width)
    a, b = geometry.band_at(site, xs)
    for x in range(site.width):
        t, u = int(max(a[x], 0)), int(min(b[x], site.height - 1))
        if u > t:
            img[t:u + 1, x] = 112                                # asphalt
    for x0, x1 in site.occluders:                                # the pole
        img[:, x0:x1 + 1] = 38
    return img


class Scene:
    """Generates frames and records the ground truth as it goes."""

    def __init__(self, site, minutes=10.0, mean_headway_s=12.0,
                 night_after_s=None, seed=7,
                 t0=dt.datetime(2026, 3, 1, 8, 0, 0)):
        self.site = site
        self.bg = _background(site)
        self.rng = np.random.default_rng(seed)
        self.n_frames = int(minutes * 60 * site.fps)
        self.t0 = t0
        self.night_after = night_after_s
        self.truth = []          # one entry per vehicle actually spawned
        self.live = []
        p = np.array([t[4] for t in TYPES], float)
        self.p = p / p.sum()
        self.next_spawn = {"LR": 0.0, "RL": mean_headway_s * 0.5}
        self.mean_hw = mean_headway_s

    # -----------------------------------------------------------------
    def _spawn(self, direction, t_s):
        i = self.rng.choice(len(TYPES), p=self.p)
        name, wn, hn, artic, _ = TYPES[i]
        s = self.site
        speed = float(self.rng.uniform(22, 30))      # px per frame
        self.live.append({
            "idx": len(self.truth),
            "type": name, "wn": wn, "hn": hn, "artic": artic,
            "dir": direction,
            "x": -40.0 if direction == "LR" else s.width + 40.0,
            "vx": speed if direction == "LR" else -speed,
            "lane": 0.92 if direction == "LR" else 0.42,
            "shade": int(self.rng.integers(165, 205)),
        })
        self.truth.append({"type": name, "dir": direction, "t_s": t_s,
                           "artic": artic, "crossed": False})

    def _draw(self, img, v):
        """
        Draw the body column by column, with its ground line FOLLOWING the
        road band. A long vehicle drawn as a plain rectangle hangs below the
        carriageway at one end, where the ground-contact rule then correctly
        rejects it -- a bug in the generator that looks exactly like a bug in
        the detector.
        """
        s = self.site
        cx = float(np.clip(v["x"], 0, s.width - 1))
        bh = geometry.band_h(s, cx)
        vh = max(int(v["hn"] * bh), 3)
        vw = max(int(v["wn"] * bh), 3)
        if v["artic"]:
            # tractor + gap + trailer: ONE vehicle, two blobs
            cab = int(0.33 * vw)
            # A tractor-semitrailer gap, ~0.45 band-heights. Wide enough
            # that morphology does not close it -- which is the realistic
            # case, and the reason merge_boxes has to exist at all.
            gap = max(int(0.45 * bh), 3)
            seg = [(0, cab), (cab + gap, vw)]
        else:
            seg = [(0, vw)]
        left = int(v["x"] - vw / 2)
        for u0, u1 in seg:
            x0, x1 = max(left + u0, 0), min(left + u1, s.width)
            if x1 <= x0:
                continue
            xs = np.arange(x0, x1)
            a, b = geometry.band_at(s, xs)
            y_bot = (a + v["lane"] * (b - a)).astype(int)
            for k, x in enumerate(xs):
                yb = int(np.clip(y_bot[k], 1, s.height - 1))
                img[max(yb - vh, 0):yb, x] = v["shade"]

    def _draw_night(self, img, v):
        """After dark the body is invisible; only the lamps are not."""
        s = self.site
        cx = float(np.clip(v["x"], 0, s.width - 1))
        bh = geometry.band_h(s, cx)
        a, b = geometry.band_at(s, cx)
        y = int(a + v["lane"] * (b - a) - 0.25 * bh)
        r = max(int(0.22 * bh), 2)
        x = int(v["x"])
        for dx in ((-int(0.35 * bh), int(0.35 * bh)) if v["wn"] > 0.95 else (0,)):
            cv_x0, cv_x1 = max(x + dx - r, 0), min(x + dx + r, s.width)
            if cv_x1 > cv_x0:
                img[max(y - r, 0):y + r, cv_x0:cv_x1] = 245

    # -----------------------------------------------------------------
    def frames(self):
        """Yields (frame_index, timestamp, grey_frame, is_night_truth)."""
        s = self.site
        for f in range(self.n_frames):
            t_s = f / s.fps
            night = self.night_after is not None and t_s >= self.night_after
            for d in ("LR", "RL"):
                if t_s >= self.next_spawn[d]:
                    self._spawn(d, t_s)
                    self.next_spawn[d] = t_s + float(
                        self.rng.exponential(self.mean_hw)) + 1.5

            img = self.bg.copy()
            if night:
                img = (img * 0.22).astype(np.uint8)
                for x0, x1 in s.occluders:
                    img[:, x0:x1 + 1] = 12
            for v in self.live:
                (self._draw_night if night else self._draw)(img, v)
            for x0, x1 in s.occluders:          # the pole is IN FRONT
                img[:, x0:x1 + 1] = 12 if night else 38

            img = np.clip(img.astype(np.int16)
                          + self.rng.normal(0, 2.5, img.shape).astype(np.int16)
                          + int(4 * np.sin(f / 90.0)), 0, 255).astype(np.uint8)

            # Ground truth is "crossed the counting line", not "spawned":
            # a vehicle still in flight when the clip ends was never
            # countable, and charging it to the detector is not honest.
            for v in self.live:
                before = v["x"]
                v["x"] += v["vx"]
                if (before - s.count_x) * (v["x"] - s.count_x) <= 0:
                    self.truth[v["idx"]]["crossed"] = True
            self.live = [v for v in self.live if -120 <= v["x"] <= s.width + 120]

            yield f, self.t0 + dt.timedelta(seconds=t_s), img, night

    # -----------------------------------------------------------------
    def truth_counts(self):
        """
        Ground truth: vehicles that actually crossed the counting line while
        the clip was running. Vehicles still in flight at the end were never
        countable.
        """
        tr = [t for t in self.truth if t["crossed"]]
        out = {"total": len(tr), "LR": 0, "RL": 0, "articulated": 0,
               "spawned": len(self.truth), "by_type": {}}
        for t in tr:
            out[t["dir"]] += 1
            out["articulated"] += int(t["artic"])
            out["by_type"][t["type"]] = out["by_type"].get(t["type"], 0) + 1
        return out
