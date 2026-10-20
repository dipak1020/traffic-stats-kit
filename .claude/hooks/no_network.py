#!/usr/bin/env python3
"""Hook: no_network.py — Enforce offline CPU boundary.

Fails if an agent attempts to make network requests or import external API clients
during video processing runs.
"""
import sys

FORBIDDEN_KEYWORDS = [
    "requests.post",
    "urllib.request",
    "boto3",
    "google.cloud",
    "wandb",
    "api.openai.com",
    "api.anthropic.com",
]


def check_script(content: str) -> bool:
    for kw in FORBIDDEN_KEYWORDS:
        if kw in content:
            print(
                f"[GUARD TRIGGERED] Network call detected: '{kw}'. "
                "traffic-stats-kit enforces 100% offline edge processing.",
                file=sys.stderr,
            )
            return False
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                code = f.read()
            if not check_script(code):
                sys.exit(1)
        except Exception as e:
            print(f"[GUARD WARN] Could not inspect {filepath}: {e}", file=sys.stderr)
    sys.exit(0)
