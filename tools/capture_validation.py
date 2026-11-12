"""Capture source-pinned consumer evidence without executing any commands.

Checks are declarations, not inferred approval. Passed checks require a command
and nonempty local evidence. The receipt records their hashes for later review.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def contained(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"Path escapes consumer root: {name}")
    return path


def identity(root, path):
    data = path.read_bytes()
    return {"path": path.relative_to(root).as_posix(), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def capture(root, sources, checks):
    root = Path(root).resolve()
    files = {}
    for source in sources:
        path = contained(root, source)
        if not path.exists():
            raise ValueError(f"Missing source: {source}")
        for child in ([path] if path.is_file() else sorted(path.rglob("*"))):
            if child.is_file():
                child = contained(root, child)
                files[child.relative_to(root).as_posix()] = identity(root, child)
    if not files:
        raise ValueError("No source files selected")
    evidence = []
    seen = set()
    for check in checks:
        if not check.get("id") or check["id"] in seen:
            raise ValueError("Check IDs must be nonempty and unique")
        seen.add(check["id"])
        if check.get("status") not in {"passed", "failed", "blocked", "not_run"}:
            raise ValueError(f"Invalid status: {check['id']}")
        artifacts = [identity(root, contained(root, p)) for p in check.get("artifacts", [])]
        if check["status"] == "passed" and (not check.get("command", "").strip() or not artifacts or any(a["bytes"] == 0 for a in artifacts)):
            raise ValueError(f"Passed check requires command and nonempty evidence: {check['id']}")
        evidence.append({**check, "artifacts": artifacts})
    ordered = [files[key] for key in sorted(files)]
    digest = hashlib.sha256(json.dumps(ordered, sort_keys=True).encode()).hexdigest()
    return {"schema_version": 1, "recorded_utc": datetime.now(timezone.utc).isoformat(),
            "scope": "Declared check outcomes with source/evidence hashes; not independent gameplay certification",
            "source_sha256": digest, "sources": ordered, "checks": evidence}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--source", action="append", required=True)
    parser.add_argument("--checks", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = capture(args.root, args.source, json.loads(args.checks.read_text(encoding="utf-8-sig")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Receipts are append-only. Choose a new filename for a new baseline.
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(f"Recorded {len(result['sources'])} sources and {len(result['checks'])} checks: {args.output}")


if __name__ == "__main__":
    main()
