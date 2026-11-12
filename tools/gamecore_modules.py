"""Versioned portable module catalog and explicit, hash-locked installation."""
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def contained(root, relative):
    root = Path(root).resolve()
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ":" in relative:
        raise ValueError(f"Expected relative path: {relative}")
    target = (root / relative).resolve()
    if target == root or root not in target.parents:
        raise ValueError(f"Path escapes root: {relative}")
    return target


def write_json(path, value):
    atomic_write(path, (json.dumps(value, indent=2) + "\n").encode())


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".gamecore-")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def registry(root=ROOT, selected=None):
    data = read_json(root / "shared/modules.json")
    if data.get("schema_version") != 1 or not isinstance(data.get("modules"), list):
        raise ValueError("Unsupported module registry")
    modules = {}
    for module in data["modules"]:
        key = module["id"]
        if not re.fullmatch(r"[a-z][a-z0-9-]*", key) or key in modules:
            raise ValueError(f"Invalid/duplicate module id: {key}")
        if not re.fullmatch(r"\d+\.\d+\.\d+", module["version"]):
            raise ValueError(f"Invalid version: {key}")
        if selected is None or key in selected:
            source = contained(root, module["source"])
            if digest(source) != module["sha256"]:
                raise ValueError(f"Registry source drift: {key}; review and version the registry entry")
            for reference in [module["documentation"], *module["tests"]]:
                if not contained(root, reference).is_file():
                    raise ValueError(f"Missing module reference: {reference}")
        modules[key] = module
    for module in modules.values():
        if any(dep not in modules for dep in module["dependencies"]):
            raise ValueError(f"Unknown dependency: {module['id']}")
    visiting, visited = set(), set()
    def visit(key):
        if key in visiting:
            raise ValueError("Module dependency cycle")
        if key in visited:
            return
        visiting.add(key)
        for dep in modules[key]["dependencies"]:
            visit(dep)
        visiting.remove(key)
        visited.add(key)
    for key in modules:
        visit(key)
    return modules


def selections(project, manifest):
    result = {}
    destinations = set()
    for item in manifest["modules"]:
        key = item["id"]
        target = contained(project, item["destination"])
        if key in result or str(target).lower() in destinations:
            raise ValueError("Duplicate module or destination")
        if not item["destination"].replace("\\", "/").startswith("Source/") or target.suffix != ".h":
            raise ValueError("Module destination must be a header under Source/")
        result[key] = item
        destinations.add(str(target).lower())
    if not result:
        raise ValueError("No selected modules")
    return result


def check_lock(project, manifest):
    chosen = selections(project, manifest)
    lock = read_json(contained(project, "Config/GameCore.modules.lock.json"))
    if lock.get("schema_version") != 1 or lock.get("project_id") != manifest["project_id"]:
        raise ValueError("Module lock schema/project mismatch")
    entries = lock.get("modules", [])
    if len(entries) != len(chosen) or {m["id"] for m in entries} != set(chosen):
        raise ValueError("Module lock does not match project selections; run sync --update")
    for entry in entries:
        wanted = chosen[entry["id"]]
        if any(entry[k] != wanted[k] for k in ("version", "destination")):
            raise ValueError(f"Module selection changed: {entry['id']}")
        if digest(contained(project, entry["destination"])) != entry["sha256"]:
            raise ValueError(f"Modified installed module: {entry['id']}; preserve/reconcile edits before sync")
    return lock


def sync(project, manifest, update=False, root=ROOT):
    catalog = registry(root, {item["id"] for item in manifest["modules"]})
    chosen = selections(project, manifest)
    lock_path = contained(project, "Config/GameCore.modules.lock.json")
    old = read_json(lock_path) if lock_path.exists() else None
    if old:
        if old.get("schema_version") != 1 or old.get("project_id") != manifest["project_id"]:
            raise ValueError("Existing lock belongs to another schema/project")
        for entry in old["modules"]:
            if digest(contained(project, entry["destination"])) != entry["sha256"]:
                raise ValueError(f"Modified installed module: {entry['id']}; refusing overwrite")
    entries, copies = [], []
    for key, item in chosen.items():
        module = catalog[key]
        if module["version"] != item["version"]:
            raise ValueError(f"Unavailable version for {key}: {item['version']}")
        if not set(module["dependencies"]).issubset(chosen):
            raise ValueError(f"Explicit dependency selections required for {key}")
        target = contained(project, item["destination"])
        previous = next((e for e in old["modules"] if e["destination"] == item["destination"]), None) if old else None
        prior_release = next((e for e in old["modules"] if e["id"] == key), None) if old else None
        if prior_release and prior_release["version"] == item["version"] and prior_release["sha256"] != module["sha256"]:
            raise ValueError(f"Source changed without a version bump: {key}")
        if target.exists() and not previous and digest(target) != module["sha256"]:
            raise ValueError(f"Unmanaged destination differs: {target}")
        entries.append({**item, "source": module["source"], "sha256": module["sha256"]})
        copies.append((target, contained(root, module["source"]).read_bytes()))
    lock = {"schema_version": 1, "project_id": manifest["project_id"], "modules": entries}
    if old and old != lock and not update:
        raise ValueError("Dependency change requires explicit sync --update")
    # Preflight all inputs before writing; lock written last. Interrupted copies fail check_lock.
    for target, payload in copies:
        atomic_write(target, payload)
    write_json(lock_path, lock)
    return lock
