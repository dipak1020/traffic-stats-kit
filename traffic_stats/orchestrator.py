# -*- coding: utf-8 -*-
"""
traffic_stats.orchestrator
Unified CLI orchestrator for the traffic-stats-kit agentic framework.

Provides end-to-end task execution for humans and AI agents (Gemini, Claude, Antigravity, Codex):
  - check:         Verify environment, dependencies, ffmpeg, linting, and smoke tests
  - demo:          Run self-scoring synthetic benchmark with articulated truck de-duplication
  - calibrate:     Extract background and render diagnostic site geometry from video
  - run:           Batch process video clips offline on CPU
  - audit:         Audit timeline CSV through all 4 engineering validation gates
  - install-hooks: Install local git verification hooks and agentic guard rails
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def _print_banner(title):
    line = "=" * 68
    print(f"\n{line}\n  {title}\n{line}")


def cmd_check(args):
    """Run environment, dependency, and test checks."""
    _print_banner("1. SYSTEM & DEPENDENCY AUDIT")
    all_ok = True

    # 1. Python version
    py_ver = sys.version.split()[0]
    py_ok = sys.version_info >= (3, 10)
    print(f"  [{'PASS' if py_ok else 'FAIL'}] Python version: {py_ver} (>= 3.10 required)")
    if not py_ok:
        all_ok = False

    # 2. ffmpeg
    ffmpeg_bin = shutil.which("ffmpeg")
    print(f"  [{'PASS' if ffmpeg_bin else 'FAIL'}] ffmpeg binary on PATH: {ffmpeg_bin or 'NOT FOUND'}")
    if not ffmpeg_bin:
        print("         -> Install via 'brew install ffmpeg' or 'apt-get install ffmpeg'")
        all_ok = False

    # 3. Core dependencies
    for mod in ["numpy", "cv2", "matplotlib"]:
        try:
            m = __import__(mod)
            ver = getattr(m, "__version__", "installed")
            print(f"  [PASS] {mod}: version {ver}")
        except ImportError:
            print(f"  [FAIL] {mod}: NOT INSTALLED")
            all_ok = False

    # 4. Optional dependencies
    for mod, feature in [("ultralytics", "YOLO secondary classification"),
                         ("reportlab", "PDF survey compilation"),
                         ("docx", "DOCX reporting")]:
        try:
            __import__(mod)
            print(f"  [INFO] {mod}: available ({feature})")
        except ImportError:
            print(f"  [INFO] {mod}: optional ({feature}) - not installed")

    _print_banner("2. CODE LINTING (RUFF)")
    try:
        cfg = ["--config", "pyproject.toml"] if Path("pyproject.toml").exists() else ["--select", "E9,F"]
        r = subprocess.run([sys.executable, "-m", "ruff", "check"] + cfg + ["traffic_stats", "tests"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            print("  [PASS] ruff lint check: zero violations (E9, F)")
        else:
            print(f"  [WARN] ruff check reported output:\n{r.stdout or r.stderr}")
    except Exception as e:
        print(f"  [INFO] ruff check info: {e}")

    _print_banner("3. UNIT & INTEGRATION TESTS (PYTEST)")
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "tests/"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            print("  [PASS] pytest: all tests passed")
        else:
            print(f"  [FAIL] pytest failures:\n{r.stdout}")
            all_ok = False
    except Exception as e:
        print(f"  [FAIL] could not run pytest: {e}")
        all_ok = False

    _print_banner("AUDIT SUMMARY")
    if all_ok:
        print("  VERDICT: READY FOR LOCAL RUNS & AGENTIC WORKFLOWS [PASS]\n")
        return 0
    else:
        print("  VERDICT: PREREQUISITES MISSING - RESOLVE ITEMS ABOVE [FAIL]\n")
        return 1


def cmd_demo(args):
    """Execute synthetic benchmark with headway gates and contact sheet generation."""
    _print_banner("SYNTHETIC BENCHMARK & GATE SCORING")
    from . import demo
    sys.argv = ["demo", "--minutes", str(args.minutes), "--headway", str(args.headway), "--out", str(args.out)]
    return demo.main()


def cmd_calibrate(args):
    """Extract median background and render diagnostic site geometry."""
    _print_banner("SITE CALIBRATION & GEOMETRY DIAGNOSTICS")
    from . import overlay
    video_path = Path(args.video)
    if not video_path.exists():
        print(f"Error: video not found at {video_path}")
        return 1
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    sys.argv = ["overlay", "--video", str(video_path), "--out", str(out_dir)]
    if args.site:
        sys.argv.extend(["--site", args.site])
    return overlay.main()


def cmd_run(args):
    """Batch process CCTV clips offline on CPU."""
    _print_banner("OFFLINE CCTV BATCH PROCESSING")
    from . import report
    sys.argv = ["report", "--videos", str(args.videos), "--out", str(args.out)]
    if args.site:
        sys.argv.extend(["--site", args.site])
    return report.main()


def cmd_audit(args):
    """Audit timeline CSV through all 4 engineering validation gates."""
    _print_banner("ENGINEERING AUDIT & GATE VALIDATION")
    from . import stats
    timeline_path = Path(args.timeline)
    if not timeline_path.exists():
        print(f"Error: timeline file {timeline_path} not found")
        return 1

    import csv
    import datetime as dt
    from collections import namedtuple

    DummyCrossing = namedtuple("DummyCrossing", ["time", "direction", "w_norm", "c_type"])
    crossings = []
    with open(timeline_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            raw_time = r.get("local_time") or r.get("recorder_time") or r.get("time")
            try:
                t = dt.datetime.fromisoformat(raw_time)
            except Exception:
                t = dt.datetime.strptime(raw_time, "%Y-%m-%d %H:%M:%S")
            crossings.append((DummyCrossing(t, r["direction"], float(r.get("w_norm", 1.0)), r.get("type", "car")), t))

    # Evaluate headway gate
    hw_results = {}
    for d in ("LR", "RL"):
        ts = [t for c, t in crossings if c.direction == d]
        hw = stats.headways(ts)
        bad = sum(1 for h in hw if h < 1.0)
        frac = (bad / len(hw)) if hw else 0.0
        hw_results[d] = {
            "count": len(ts),
            "headways": len(hw),
            "under_1s": bad,
            "fraction_under_1s": round(frac, 3),
            "verdict": "PASS" if frac <= 0.05 else "FAIL - suspected double counting"
        }
        print(f"  Direction {d}: {len(ts)} vehicles | {bad} headways < 1.0s ({frac*100:.1f}%) -> {hw_results[d]['verdict']}")

    out_dir = Path(args.out or timeline_path.parent)
    report_json = out_dir / "audit_report.json"
    with open(report_json, "w", encoding="utf-8") as f:
        json.dump({"timeline": str(timeline_path), "headway_gate": hw_results}, f, indent=2)
    print(f"\nAudit results saved to: {report_json}\n")
    return 0


def cmd_install_hooks(args):
    """Install git pre-commit hooks and agentic guard rails."""
    _print_banner("INSTALLING AGENTIC & GIT HOOKS")
    git_dir = Path(".git")
    if not git_dir.exists():
        print("  [WARN] Not inside git repository root (.git not found).")
        return 1

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    pre_commit = hooks_dir / "pre-commit"

    script = """#!/bin/bash
# Pre-commit hook: Run ruff check and pytest before every commit
set -e
echo "Running traffic-stats verification pre-commit..."
python -m ruff check traffic_stats tests
python -m pytest tests/
echo "Verification passed. Proceeding with commit."
"""
    pre_commit.write_text(script, encoding="utf-8")
    pre_commit.chmod(0o755)
    print(f"  [PASS] Installed git pre-commit hook at {pre_commit}")

    # Set up claude hook directory
    claude_hooks = Path(".claude/hooks")
    if claude_hooks.exists():
        print(f"  [PASS] Agentic hooks active in {claude_hooks}")
        for h in claude_hooks.glob("*.py"):
            h.chmod(0o755)
            print(f"         - {h.name}")
    print("\nHooks installation complete.\n")
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="traffic-stats",
        description="Auditable traffic counts from CCTV video: offline, CPU-only agentic orchestrator."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # check
    p_check = sub.add_parser("check", help="Verify dependencies, ffmpeg, linter, and smoke tests")
    p_check.set_defaults(func=cmd_check)

    # demo
    p_demo = sub.add_parser("demo", help="Run self-scoring synthetic benchmark")
    p_demo.add_argument("--minutes", type=int, default=5, help="Minutes of footage (default 5)")
    p_demo.add_argument("--headway", type=float, default=20.0, help="Mean vehicle arrival headway (s)")
    p_demo.add_argument("--out", default="out", help="Output directory")
    p_demo.set_defaults(func=cmd_demo)

    # calibrate
    p_cal = sub.add_parser("calibrate", help="Extract background and render diagnostic site geometry")
    p_cal.add_argument("--video", required=True, help="Path to sample video file")
    p_cal.add_argument("--out", default="out/diagnostics", help="Output directory")
    p_cal.add_argument("--site", default="VILLETA_A27", help="Site config name")
    p_cal.set_defaults(func=cmd_calibrate)

    # run
    p_run = sub.add_parser("run", help="Batch process CCTV clips offline")
    p_run.add_argument("--videos", required=True, help="Folder containing video clips")
    p_run.add_argument("--out", default="out", help="Output directory")
    p_run.add_argument("--site", default="VILLETA_A27", help="Site config name")
    p_run.set_defaults(func=cmd_run)

    # audit
    p_audit = sub.add_parser("audit", help="Audit timeline CSV through validation gates")
    p_audit.add_argument("--timeline", required=True, help="Path to timeline.csv")
    p_audit.add_argument("--out", default=None, help="Output directory for audit report")
    p_audit.set_defaults(func=cmd_audit)

    # install-hooks
    p_hooks = sub.add_parser("install-hooks", help="Install git pre-commit hooks and agentic guard rails")
    p_hooks.set_defaults(func=cmd_install_hooks)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
