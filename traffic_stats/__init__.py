"""
traffic_stats — a generic, camera-agnostic traffic-statistics pipeline.

Mock but workable: `python -m traffic_stats.demo` runs the whole thing end to
end against synthetic footage, with no video, no model weights and no network.

Stages, in the order of docs/APPROACH.md:

    config    the one site-specific file
    geometry  perspective band, corridor mask, ground contact, occluders
    detect    background subtraction + in-frame box merging
    track     velocity-predicted association, line crossing = one count
    stats     volume, cumulative, headway, occupancy, peak
    validate  the gates that decide whether the counts are trustworthy
    synth     synthetic road footage with known ground truth
    demo      run everything, score it against the ground truth
"""

__all__ = ["config", "geometry", "detect", "track", "stats", "validate", "synth"]
__version__ = "0.1.0"
