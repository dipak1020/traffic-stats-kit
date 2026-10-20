# -*- coding: utf-8 -*-
"""
The ONE site-specific file.

Everything else in this package is generic. Adding a camera means adding a
Site here: two polylines along the road edges, a counting line, and the
columns of anything standing in front of the carriageway.

See docs/APPROACH.md stage 3, and docs/CALIBRATION.md for the tracing
procedure.
"""
from dataclasses import dataclass, field
import datetime as dt


@dataclass
class Site:
    # ---- identity -------------------------------------------------------
    name: str
    width: int                      # frame width the geometry was traced at
    height: int
    fps: float                      # frames per second actually processed

    # ---- road geometry (stage 3) ----------------------------------------
    far: list                       # [(x, y)] upper road edge, x increasing
    near: list                      # [(x, y)] lower road edge, x increasing
    pad: int = 6                    # px margin outside the traced edges
    head_mult: float = 1.6          # band-heights of headroom above the road
    foot_mult: float = 0.20         # band-heights of slack below it

    # ---- obstructions ---------------------------------------------------
    occluders: list = field(default_factory=list)   # [(x0, x1)] poles, signs

    # ---- measurement lines ----------------------------------------------
    count_x: int = 0                # a pass is counted crossing this column
    # A SECOND line, well away from the first. A track counts only once it
    # has crossed BOTH. A swaying post, a wire shadow or a patch of glare can
    # oscillate across one line indefinitely; nothing stationary can travel
    # from one line to the other. This is the cheapest false-positive filter
    # there is, and it costs one number.
    verify_x: int = 0
    class_x: tuple = (0, 0)         # window where size is measured

    # ---- time base (stage 2) --------------------------------------------
    clock_offset: dt.timedelta = dt.timedelta(0)    # add to recorder time

    # ---- detection / tracking (stage 4-5) -------------------------------
    min_span_x: int = 0             # px a track must travel to be real
    min_frames: int = 4
    max_match_d: float = 45.0       # px, against the PREDICTED position
    max_miss: int = 12              # frames of occlusion tolerated
    gap_mult: float = 0.55          # band-heights: max gap to union two boxes
    vovl_min: float = 0.25          # min vertical overlap to union two boxes
    foot_align: float = 0.25        # max difference in LANE POSITION (as a
                                    # fraction of band height) between two
                                    # boxes for them to be one vehicle
    min_area_frac: float = 0.06     # of band_h^2
    # Morphology sized as a FRACTION OF BAND HEIGHT, not in pixels, so the
    # same Site works whether you process at 640x360 or 1280x720. At night
    # the kernel is much wider than it is tall: a vehicle is a PAIR of
    # headlights separated horizontally, and they have to be joined into one
    # blob or every vehicle is counted twice -- or, worse, neither fragment
    # survives the minimum-travel test and it is counted not at all.
    open_frac: float = 0.08
    dil_day_frac: tuple = (0.18, 0.13)      # (width, height) of band_h
    dil_night_frac: tuple = (0.49, 0.18)
    dil_iter: int = 2

    # ---- day / night (stage 1e) -----------------------------------------
    night_luma: int = 75            # MEDIAN road luma below this = night
    night_cols: tuple = (0, 0)      # columns away from any lamp
    night_light: int = 170          # a night blob must contain a pixel this bright

    # ---- distance anchor (stage 3) --------------------------------------
    # Set this ONLY from a measurement taken on site. While it is None,
    # stats.py refuses to report speed or density. That refusal is the
    # feature: see docs/APPROACH.md stage 7.
    metres_per_band_height: float | None = None

    # Detect at a fraction of the calibration resolution. Downscaling is not
    # only cheaper: it averages away sensor noise, which is what lets small
    # night blobs survive the morphological opening instead of being eroded
    # away. Calibrate once at full resolution, detect at half.
    detect_scale: float = 1.0

    def scaled(self, f=None):
        """A copy of this Site with every pixel quantity multiplied by f.

        Everything the pipeline measures is either scale-free (w_norm is a
        ratio of two lengths in the same frame) or derived from the band, so
        rescaling the geometry rescales the whole method consistently.
        """
        f = self.detect_scale if f is None else f
        if f == 1.0:
            return self
        sc = lambda v: int(round(v * f))
        import dataclasses
        return dataclasses.replace(
            self,
            name="%s@%gx" % (self.name, f),
            width=sc(self.width), height=sc(self.height),
            far=[(sc(x), sc(y)) for x, y in self.far],
            near=[(sc(x), sc(y)) for x, y in self.near],
            pad=max(1, sc(self.pad)),
            occluders=[(sc(a), sc(b)) for a, b in self.occluders],
            count_x=sc(self.count_x), verify_x=sc(self.verify_x),
            class_x=(sc(self.class_x[0]), sc(self.class_x[1])),
            night_cols=(sc(self.night_cols[0]), sc(self.night_cols[1])),
            min_span_x=sc(self.min_span_x),
            max_match_d=self.max_match_d * f,
            detect_scale=1.0,
        )

    def __post_init__(self):
        if self.count_x and any(a <= self.count_x <= b for a, b in self.occluders):
            raise ValueError(
                "count_x=%d sits behind an occluder %r. Move the counting "
                "line: this is the most consequential placement in the "
                "whole pipeline." % (self.count_x, self.occluders))
        if self.verify_x and any(a <= self.verify_x <= b
                                 for a, b in self.occluders):
            raise ValueError("verify_x=%d sits behind an occluder"
                             % self.verify_x)
        if not self.min_span_x:
            self.min_span_x = int(0.20 * self.width)
        if self.night_cols == (0, 0):
            self.night_cols = (self.far[0][0], self.far[-1][0])
        if self.class_x == (0, 0):
            self.class_x = (int(0.70 * self.width), self.width - 1)


# ---------------------------------------------------------------------------
# A synthetic site, so the package runs with no footage at all.
# Deliberately shaped like a real one: oblique view, perspective that varies
# across the frame, and one pole in front of the road.
# ---------------------------------------------------------------------------
DEMO = Site(
    name="demo-synthetic",
    width=640, height=360, fps=6.0,
    far=[(146, 44), (200, 46), (250, 48), (300, 50), (350, 55),
         (400, 61), (450, 67), (488, 73), (525, 80), (575, 94), (639, 110)],
    near=[(146, 70), (200, 71), (250, 74), (300, 77), (350, 84),
          (400, 92), (450, 101), (488, 109), (525, 119), (575, 135), (639, 157)],
    pad=4,
    occluders=[(262, 272)],
    count_x=390,
    verify_x=300,
    min_span_x=130,
    max_match_d=45.0,
    clock_offset=dt.timedelta(0),
)


# ---------------------------------------------------------------------------
# A REAL camera, as the worked example. This is the whole of what adding a
# site costs: two polylines traced on a median background, the columns of the
# two fence posts standing in front of the road, a counting line placed clear
# of both, and the clock offset measured from the footage itself.
#
# Nothing else in the package changes. Compare it with DEMO above -- same
# fields, different numbers.
# ---------------------------------------------------------------------------
VILLETA_A27 = Site(
    name="villeta-a27",
    width=1280, height=720, fps=6.0,
    far=[(292, 88), (400, 93), (500, 97), (600, 101), (700, 111), (800, 122),
         (900, 135), (975, 146), (1050, 161), (1150, 188), (1279, 220)],
    near=[(292, 140), (400, 143), (500, 148), (600, 155), (700, 168),
          (800, 185), (900, 203), (975, 219), (1050, 239), (1150, 271),
          (1279, 315)],
    pad=8,
    occluders=[(524, 544), (1072, 1099)],   # two fence posts
    count_x=780,                            # clear of both posts
    verify_x=480,                           # and a second line 300 px away
    class_x=(900, 1279),                    # where vehicles are most side-on
    min_span_x=260,          # full-res px a track must travel to be a pass
    max_match_d=140.0,       # full-res; becomes 70 at the 0.5 detect scale
    max_miss=12,             # ~2 s of occlusion tolerated
    # Measured from the footage: daylight midpoint against true solar noon at
    # the site. SIGN: stats.localise does local = recorder + clock_offset, and
    # the recorder runs 3 h 50 min FAST, so the offset is NEGATIVE.
    # Undetected, every hourly
    # statistic would be shifted by nearly four hours.
    clock_offset=dt.timedelta(hours=-3, minutes=-50),
    # The lamp: the day/night median is taken well to the left of it.
    night_cols=(292, 820),
    night_luma=75,
    night_light=170,
    # Calibrated at 1280x720, detected at 640x360.
    detect_scale=0.5,
    # Still unset, deliberately. Two independent estimates put the visible
    # road at ~34 m, but both rested on size samples that exist only in the
    # near half of the frame, and the resulting speed was implausible for a
    # highway. One tape measure on site unblocks speed and density.
    metres_per_band_height=None,
)

SITES = {"demo": DEMO, "villeta-a27": VILLETA_A27}
