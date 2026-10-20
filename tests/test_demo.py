"""Smoke test: the synthetic demo runs end to end and writes its outputs."""
import subprocess
import sys


def test_demo_runs(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "traffic_stats.demo", "--minutes", "5", "--headway", "20"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(__import__("pathlib").Path(__file__).resolve().parents[1]),
             "PATH": __import__("os").environ["PATH"]},
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "out" / "timeline.csv").exists()
