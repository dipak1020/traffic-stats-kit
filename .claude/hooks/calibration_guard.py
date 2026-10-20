#!/usr/bin/env python3
"""Hook: calibration_guard.py — Protect site calibration geometry.

Prevents silent or unintended modifications to verified road corridor
polylines and counting line coordinates during automated batch runs.
"""
import sys

PROTECTED_VARIABLES = [
    "FAR_POLY",
    "NEAR_POLY",
    "COUNT_LINE_X",
    "VERIFY_LINE_X",
    "BAND_HEIGHT_REF",
]


def check_patch(diff_content: str) -> bool:
    for var in PROTECTED_VARIABLES:
        if f"+{var}" in diff_content or f"-{var}" in diff_content:
            print(
                f"[GUARD TRIGGERED] Attempted modification to protected geometry: '{var}'. "
                "Road corridor polylines must only be altered during explicit site calibration.",
                file=sys.stderr,
            )
            return False
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            if not check_patch(content):
                sys.exit(1)
        except Exception as e:
            print(f"[GUARD WARN] Could not inspect {filepath}: {e}", file=sys.stderr)
    sys.exit(0)
