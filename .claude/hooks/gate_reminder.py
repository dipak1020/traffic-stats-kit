#!/usr/bin/env python3
"""Hook: gate_reminder.py — Remind agent of the 4 non-negotiable validation gates.

Executed after pipeline processing or report generation to mandate contact sheet visual inspection.
"""
from pathlib import Path
import sys


def verify_gate_artifacts(output_dir: str):
    p = Path(output_dir)
    contact_sheet = p / "contact_sheet.png"
    timeline = p / "timeline.csv"

    if not contact_sheet.exists() and timeline.exists():
        print(
            "[GATE NOTICE] 'timeline.csv' was generated, but 'contact_sheet.png' is missing! "
            "Gate 1 requires an auditable contact sheet before publishing any survey data.",
            file=sys.stderr,
        )
    else:
        print(
            "[GATE REMINDER] Remember the 4 Non-Negotiable Gates:\n"
            "  1. Visual Gate: Inspect 100% of tiles on contact_sheet.png\n"
            "  2. Headway Gate: Consecutive headways < 1.0s must be <= 5%\n"
            "  3. Coverage Gate: Survey continuity must exceed 95%\n"
            "  4. Determinism Gate: Bit-exact CSV records on repeated runs"
        )


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "out"
    verify_gate_artifacts(out)
    sys.exit(0)
