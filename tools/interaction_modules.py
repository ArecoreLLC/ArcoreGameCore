"""Install/check versioned interaction modules; games run from their local copies.

python tools/interaction_modules.py vendor --project <consumer> --godot-dir game
python tools/interaction_modules.py check --project <consumer>
Use --update only after reviewing a new shared version. Local edits always fail.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = "GameCore.interaction.lock.json"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def confined(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("Expected a relative path")
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if path == root or not path.is_relative_to(root):
        raise ValueError("Path escapes root: " + relative)
    return path


def check(project):
    project = Path(project).resolve()
    lock = json.loads((project / LOCK).read_text(encoding="utf-8"))
    if lock.get("schema") != "gamecore.interaction-lock.v1" or not lock.get("files"):
        raise ValueError("Invalid/empty interaction lock")
    seen = set()
    for record in lock["files"]:
        target = record["target"]
        if target in seen:
            raise ValueError("Duplicate target: " + target)
        seen.add(target)
        if digest(confined(project, target)) != record["sha256"]:
            raise ValueError("Installed module changed: " + target)
    return lock


def vendor(project, godot_dir=".", selected=None, update=False, root=ROOT):
    project, root = Path(project).resolve(), Path(root).resolve()
    godot = project if godot_dir == "." else confined(project, godot_dir)
    catalog = json.loads((root / "shared/interaction-modules.json").read_text(encoding="utf-8"))
    modules = {m["id"]: m for m in catalog["modules"]}
    chosen = set(selected or modules)
    if not chosen or not chosen <= modules.keys():
        raise ValueError("Unknown/empty module selection")
    for key in list(chosen):
        chosen.update(modules[key].get("dependencies", []))
    old = check(project) if (project / LOCK).exists() else None
    if old and not {m["id"] for m in old["modules"]} <= chosen:
        raise ValueError("Keep previously installed modules selected; removals need explicit review")
    records, pending = [], []
    for key in sorted(chosen):
        spec = modules[key]
        for file in spec["files"]:
            source = confined(root, file["source"])
            if digest(source) != file["sha256"]:
                raise ValueError("Canonical source differs from manifest: " + file["source"])
            target = confined(godot if spec["runtime"] == "godot" else project, file["destination"])
            record = dict(module=key, version=spec["version"], source=file["source"],
                          target=target.relative_to(project).as_posix(), sha256=file["sha256"])
            records.append(record)
            previous = next((f for f in old["files"] if f["target"] == record["target"]), None) if old else None
            if previous and previous["sha256"] != record["sha256"] and not update:
                raise ValueError("Shared version changed; review then use --update")
            if target.exists() and digest(target) != record["sha256"] and previous is None:
                raise ValueError("Refusing to overwrite unmanaged file: " + str(target))
            pending.append((source, target))
    if len({r["target"] for r in records}) != len(records):
        raise ValueError("Module destinations collide")
    if old and not {r["target"] for r in old["files"]} <= {r["target"] for r in records}:
        raise ValueError("Removing or moving installed files requires explicit migration")
    # Validate the entire set first; per-file replacement, lock last. An interrupted
    # update fails check() rather than certifying a partly updated bundle.
    for source, target in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".gamecore-tmp")
        temporary.write_bytes(source.read_bytes())
        temporary.replace(target)
    lock = dict(schema="gamecore.interaction-lock.v1", modules=[dict(id=k, version=modules[k]["version"]) for k in sorted(chosen)], files=records)
    temporary = project / (LOCK + ".tmp")
    temporary.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    temporary.replace(project / LOCK)
    return check(project)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["vendor", "check"])
    parser.add_argument("--project", required=True)
    parser.add_argument("--godot-dir", default=".")
    parser.add_argument("--module", action="append")
    parser.add_argument("--update", action="store_true")
    args = parser.parse_args()
    result = check(args.project) if args.action == "check" else vendor(args.project, args.godot_dir, args.module, args.update)
    print(json.dumps({"status": "passed", "modules": len(result["modules"]), "files": len(result["files"])}))
