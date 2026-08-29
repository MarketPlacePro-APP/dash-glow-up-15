#!/usr/bin/env python3
"""Collect recent TLWB Slack posts without failing on optional channels."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path("/Users/seanwilliams/.openclaw/workspace-main")
RECENT = ROOT / "skills" / "tlwb-preview-reporting" / "scripts" / "recent_slack.py"


def run_channel(channel: str, limit: int) -> tuple[bool, str]:
    proc = subprocess.run(
        [sys.executable, str(RECENT), channel, str(limit)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        timeout=45,
        check=False,
    )
    body = (proc.stdout or proc.stderr or "").strip()
    if proc.returncode == 0:
        return True, body
    return False, body.splitlines()[0] if body else f"exit {proc.returncode}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("channels", nargs="+")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    checked: list[str] = []
    unavailable: list[str] = []
    sections: list[str] = []

    for raw in args.channels:
        channel = raw.lstrip("#")
        ok, body = run_channel(channel, args.limit)
        if ok:
            checked.append(channel)
            sections.append(f"## #{channel}\n{body or '(no recent messages)'}")
        else:
            unavailable.append(f"{channel}: {body}")
            sections.append(f"## #{channel}\nUNAVAILABLE: {body}")

    summary = [
        "Channels checked: " + (", ".join(checked) if checked else "none"),
        "Channels unavailable: " + (", ".join(unavailable) if unavailable else "none"),
    ]
    text = "\n".join(summary + ["", *sections])
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n")
    print("\n".join(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
