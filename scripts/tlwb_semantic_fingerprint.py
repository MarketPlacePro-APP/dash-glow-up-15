#!/usr/bin/env python3
"""Stable deployment fingerprint for TLWB KPI code and material data.

Volatile check/build timestamps are normalized so deterministic hourly checks do not
create duplicate Vercel deployments. Data values, source statuses, application code,
protected APIs, middleware, and generated accounting payloads remain material.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

VOLATILE_JSON_KEYS = {
    "generated_at",
    "generatedAt",
    "build_timestamp",
    "buildTimestamp",
    "last_checked",
    "lastChecked",
    "last_synced",
    "lastSynced",
    "checked_at",
    "checkedAt",
    "fetched_at",
    "fetchedAt",
}
VOLATILE_ASSIGNMENT = re.compile(
    r"(?im)(generated_at|generatedAt|build_timestamp|buildTimestamp|last_checked|lastChecked|last_synced|lastSynced|checked_at|checkedAt|fetched_at|fetchedAt|sourceUpdatedAt|SourceUpdatedAt)(\s*[:=]\s*['\"])[^'\"]+"
)
TEXT_SUFFIXES = {".ts", ".tsx", ".js", ".mjs", ".json", ".css", ".html"}


def normalize_json(value):
    if isinstance(value, dict):
        return {key: normalize_json(item) for key, item in sorted(value.items()) if key not in VOLATILE_JSON_KEYS}
    if isinstance(value, list):
        return [normalize_json(item) for item in value]
    return value


def normalized_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    if path.suffix == ".json":
        try:
            value = normalize_json(json.loads(raw))
            return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
    if path.suffix in TEXT_SUFFIXES:
        text = raw.decode("utf-8", errors="replace").replace("\r\n", "\n")
        text = VOLATILE_ASSIGNMENT.sub(lambda match: f"{match.group(1)}{match.group(2)}<volatile>", text)
        return text.encode()
    return raw


def material_files(root: Path) -> list[Path]:
    fixed = [root / name for name in ("middleware.ts", "package.json", "vercel.json", "index.html")]
    trees = [root / "api", root / "src"]
    files = [path for path in fixed if path.is_file()]
    for tree in trees:
        if not tree.exists():
            continue
        for path in tree.rglob("*"):
            if not path.is_file() or path.suffix not in TEXT_SUFFIXES | {".png", ".webp", ".jpg", ".jpeg", ".svg"}:
                continue
            relative = path.relative_to(root).as_posix()
            if "/test/" in f"/{relative}/" or ".test." in path.name or ".spec." in path.name:
                continue
            files.append(path)
    for relative in ("public/tlwb-logo.png", "data/source_health.json", "data/phase2a_audit.json"):
        path = root / relative
        if path.is_file():
            files.append(path)
    return sorted(set(files), key=lambda path: path.relative_to(root).as_posix())


def fingerprint(root: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    files = material_files(root)
    for path in files:
        relative = path.relative_to(root).as_posix().encode()
        content = normalized_bytes(path)
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest(), len(files)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    value, count = fingerprint(args.src.resolve())
    if args.json:
        print(json.dumps({"fingerprint": value, "files": count}))
    else:
        print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
