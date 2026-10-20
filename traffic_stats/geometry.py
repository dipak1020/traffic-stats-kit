# -*- coding: utf-8 -*-
"""
Perspective band geometry. Generic: everything here is derived from the two
polylines in the Site.

The central idea: in an oblique view the height of the road band at a given
column IS the local perspective scale. Divide a pixel measurement by it and
you get a scale-free quantity that is proportional to the real one, with no
camera calibration at all.
"""
import numpy as np


def _axes(site):
    fx = np.array([p[0] for p in site.far], float)
    fy = np.array([p[1] for p in site.far], float)
    nx = np.array([p[0] for p in site.near], float)
    ny = np.array([p[1] for p in site.near], float)
    if not (np.all(np.diff(fx) > 0) and np.all(np.diff(nx) > 0)):
        raise ValueError("far/near polylines must have strictly increasing x")
    return fx, fy, nx, ny


def band_at(site, x):
    """(top, bottom) of the carriageway at column x, padded."""
    fx, fy, nx, ny = _axes(site)
    return (np.interp(x, fx, fy) - site.pad,
            np.interp(x, nx, ny) + site.pad)


def band_h(site, x):
    a, b = band_at(site, x)
    return b - a


def on_road(site, cx, y_bottom):
    """
    Ground-contact rule (APPROACH.md stage 4).

    A detection counts only if its BOTTOM edge rests on the carriageway.
    Vegetation moves but never touches the road, so it is rejected for free,
    while a tall vehicle whose body reaches far up the image is still kept.
    """
    a, b = band_at(site, cx)
    h = b - a
    return (a - 0.20 * h) <= y_bottom <= (b + site.foot_mult * h)


def ground_frac(site, cx, y_bottom):
    """
    Where the box's ground contact sits ACROSS the band, 0 at the far edge and
    1 at the near edge. This is the lane position, and unlike a raw pixel row
    it is comparable between two boxes at different columns.

    Fragments of one long vehicle share a lane fraction even though their
    pixel ground rows differ, because the band slopes. Two vehicles in
    opposing lanes differ by roughly half a band. That distinction is what
    lets box merging fix fragmentation without fusing opposing traffic.
    """
    a, b = band_at(site, cx)
    return (y_bottom - a) / max(b - a, 1e-6)


def spans_occluder(site, x0, x1):
    """True if the box straddles anything standing in front of the road."""
    return any(x0 < b and x1 > a for a, b in site.occluders)


def touches_edge(site, x0, x1, margin=2):
    return x0 <= margin or x1 >= site.width - 1 - margin


def clear_view(site, x0, x1):
    """The snapshot/measurement test: nothing in the way, nothing cut off."""
    return not spans_occluder(site, x0, x1) and not touches_edge(site, x0, x1)


def corridor_mask(site):
    """
    Boolean mask of where a vehicle may legitimately appear: the carriageway,
    grown UPWARD by head_mult band-heights.

    Growing upward is not optional. A zone traced on the asphalt clips every
    truck, and the counts stay plausible while being wrong.
    """
    m = np.zeros((site.height, site.width), bool)
    xs = np.arange(site.width)
    a, b = band_at(site, xs)
    h = b - a
    top = np.clip((a - site.head_mult * h).astype(int), 0, site.height - 1)
    bot = np.clip((b + site.foot_mult * h).astype(int), 0, site.height - 1)
    lo, hi = site.far[0][0], site.far[-1][0]
    for x in range(site.width):
        if lo <= x <= hi and bot[x] > top[x]:
            m[top[x]:bot[x] + 1, x] = True
    return m


def road_mask(site):
    """The asphalt itself, restricted to night_cols. Used for day/night only."""
    m = np.zeros((site.height, site.width), bool)
    xs = np.arange(site.width)
    a, b = band_at(site, xs)
    c0, c1 = site.night_cols
    for x in range(site.width):
        if c0 <= x <= c1:
            t, u = int(max(a[x], 0)), int(min(b[x], site.height - 1))
            if u > t:
                m[t:u + 1, x] = True
    return m


def w_norm(site, x0, x1, cx=None):
    """Width in band-heights: scale-free, proportional to real length."""
    cx = 0.5 * (x0 + x1) if cx is None else cx
    return (x1 - x0) / max(band_h(site, cx), 1e-6)


def h_norm(site, y0, y1, cx):
    return (y1 - y0) / max(band_h(site, cx), 1e-6)
