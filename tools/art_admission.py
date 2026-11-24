"""Reusable source/rig, atlas and articulated-export admission.

See shared/inkfury/ART_ADMISSION.md for schema, policy and transaction limits.
"""
from dataclasses import dataclass
from functools import wraps
import hashlib
import json
import math
import os
from pathlib import Path, PureWindowsPath
import shutil
import struct
import tempfile


class ValidationError(ValueError):
    """Invalid input, provenance, geometry, or unsafe path."""


class InstallationError(RuntimeError):
    """Installation failed; rollback was attempted (details in message)."""


def require(condition, message="Invalid art data"):
    if not condition:
        raise ValidationError(str(message))


def checked(function):
    @wraps(function)
    def call(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (ValidationError, InstallationError):
            raise
        except (OSError, ValueError, KeyError, TypeError, IndexError, struct.error) as exc:
            raise ValidationError(f"{function.__name__}: {exc}") from exc
    return call


@dataclass(frozen=True)
class Layout:
    frame_size: int = 384
    columns: int = 4
    rows: int = 4
    clips: tuple = ("idle", "cast", "guard", "hit")
    margin: int = 2
    atlas: str = "final/{id}.png"
    model: str = "{id}/animated.glb"
    frame: str = "{id}/frame_{frame:02d}.png"

    def validate(self):
        require(all(type(n) is int and n > 0 for n in (self.frame_size, self.columns, self.rows)), "Invalid atlas dimensions")
        require(type(self.margin) is int and 0 <= self.margin < self.frame_size / 2, "Invalid margin")
        require(len(self.clips) == self.rows and len(set(self.clips)) == self.rows, "Each atlas row must have a distinct clip")
        require(all(isinstance(c, str) and c for c in self.clips), "Invalid clip names")


def safe_path(root, relative):
    require(isinstance(relative, str) and relative, "Empty or non-string path")
    windows = PureWindowsPath(relative)
    require(not windows.drive and not windows.root and ".." not in windows.parts and ":" not in relative, "Unsafe path: " + relative)
    path = Path(relative)
    require(not path.is_absolute() and ".." not in path.parts, "Unsafe path: " + relative)
    root = Path(root).resolve()
    result = (root / path).resolve()
    require(result != root and result.is_relative_to(root), "Path escapes root: " + relative)
    return result


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def indexed(records):
    require(isinstance(records, list), "Records must be a list")
    result = {}
    for record in records:
        name = record["id"]
        require(isinstance(name, str) and name and name.isascii() and name.replace("_", "").isalnum(), "Unsafe asset ID")
        require(name.casefold() not in {key.casefold() for key in result}, "Duplicate asset IDs")
        result[name] = record
    return result


@checked
def admit(manifest_path, batch_path, library_path, *, layout=Layout(), replace=False,
          receipt_name="receipt.json", receipt_root=None, source_key="svg",
          rig_recipes=("articulated-v1", "articulated-volume-v2")):
    """Verify the entire batch, stage copies, then publish with rollback.

    Library paths are relative to library_path.parent. receipt_root controls
    receipt references; omit it to record an absolute receipt path.
    """
    layout.validate()
    manifest_path, batch, library_path = map(lambda p: Path(p).resolve(), (manifest_path, batch_path, library_path))
    receipt_path = safe_path(batch, receipt_name)
    manifest, receipt, library = map(read_json, (manifest_path, receipt_path, library_path))
    require(receipt["status"] == "complete", "Batch has not finished")
    sources, records, known = indexed(manifest["subjects"]), indexed(receipt["subjects"]), indexed(library["assets"])
    require(set(sources) == set(records), "Manifest/receipt IDs differ")
    reference = str(receipt_path)
    if receipt_root is not None:
        reference = receipt_path.relative_to(Path(receipt_root).resolve()).as_posix()
    destinations = {}
    for name, entry in known.items():
        destination = safe_path(library_path.parent, entry["path"])
        require(destination != library_path and destination not in destinations, "Conflicting library paths")
        destinations[destination] = name
    pending = []
    for name, record in records.items():
        spec = sources[name]
        source = safe_path(manifest_path.parent, spec[source_key])
        require(digest(source) == record["source_sha256"], f"Source changed during render: {name}")
        if "rig" in spec or "rig_sha256" in record or record.get("render_recipe") in rig_recipes:
            rig_path = safe_path(manifest_path.parent, spec["rig"])
            require(digest(rig_path) == record["rig_sha256"], f"Rig changed during render: {name}")
            require(read_json(rig_path)["source_sha256"] == record["source_sha256"], f"Rig targets a different source: {name}")
        png = safe_path(batch, layout.atlas.format(id=name))
        require(digest(png) == record["sha256"], f"Atlas hash mismatch: {name}")
        from PIL import Image
        with Image.open(png) as image:
            require(image.format == "PNG" and image.size == (layout.frame_size * layout.columns, layout.frame_size * layout.rows), f"Invalid atlas: {name}")
            image.verify()
        require((record["frame_size"], record["columns"], record["rows"]) == (layout.frame_size, layout.columns, layout.rows), "Receipt layout mismatch")
        relative = known[name]["path"] if name in known else name + ".png"
        destination = safe_path(library_path.parent, relative)
        require(destination != library_path and destinations.get(destination, name) == name, "Conflicting destination paths")
        destinations[destination] = name
        require(not destination.exists() or replace or digest(destination) == record["sha256"], f"Refusing to overwrite different artwork: {name}")
        if name in known:
            require(replace or known[name]["sha256"] == record["sha256"], f"Conflicting library ID: {name}")
            require(digest(destination) == known[name]["sha256"], f"Runtime file differs from its receipt: {name}")
        entry = dict(record, path=relative, receipt=reference)
        if name in known and "supersedes_sha256" in known[name]:
            entry["supersedes_sha256"] = known[name]["supersedes_sha256"]
        if name in known and known[name]["sha256"] != record["sha256"]:
            entry["supersedes_sha256"] = known[name]["sha256"]
        pending.append((png, destination, entry))
        known[name] = entry
    library["assets"] = list(known.values())
    # All staging and backup work completes before the first runtime write.
    with tempfile.TemporaryDirectory(prefix=".art-admission-", dir=library_path.parent) as temporary:
        stage = Path(temporary)
        changes = []
        for i, (source, destination, entry) in enumerate(pending):
            staged = stage / f"new-{i}"
            shutil.copy2(source, staged)
            require(digest(staged) == entry["sha256"], "Atlas changed during staging")
            changes.append((staged, destination))
        staged_manifest = stage / "manifest"
        staged_manifest.write_text(json.dumps(library, indent=2) + "\n", encoding="utf-8")
        changes.append((staged_manifest, library_path))
        backups = {}
        for i, (_, destination) in enumerate(changes):
            backup = stage / f"old-{i}"
            if destination.exists():
                shutil.copy2(destination, backup)
                backups[destination] = backup
            else:
                backups[destination] = None
        published, directories = [], []
        try:
            for staged, destination in changes:
                missing = []
                parent = destination.parent
                while not parent.exists():
                    missing.append(parent)
                    parent = parent.parent
                for parent in reversed(missing):
                    parent.mkdir()
                    directories.append(parent)
                os.replace(staged, destination)
                published.append(destination)
        except OSError as exc:
            failures = []
            for destination in reversed(published):
                try:
                    if backups[destination] is None:
                        destination.unlink()
                    else:
                        os.replace(backups[destination], destination)
                except OSError as rollback:
                    failures.append(str(rollback))
            for directory in reversed(directories):
                try:
                    directory.rmdir()
                except OSError as rollback:
                    failures.append(str(rollback))
            raise InstallationError(f"Installation failed: {exc}; rollback " + ("failed: " + "; ".join(failures) if failures else "completed")) from exc
    return library


@checked
def validate_articulation(batch, *, layout=Layout(), receipt_name="receipt.json", report_path=None):
    from PIL import Image
    layout.validate()
    batch = Path(batch)
    receipt = json.loads((safe_path(batch, receipt_name)).read_text(encoding='utf-8'))
    require(receipt['status'] == 'complete', 'Invalid articulated export')
    records = []
    for subject in indexed(receipt['subjects']).values():
        name = subject['id']
        raw = safe_path(batch, layout.model.format(id=name)).read_bytes()
        require(struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)), 'Invalid articulated export')
        length, kind = struct.unpack_from('<II', raw, 12)
        require(kind == 1313821514 and length % 4 == 0 and 20 + length + 8 <= len(raw), 'Invalid JSON chunk')
        model = json.loads(raw[20:20 + length])
        offset = 20 + length
        size, kind = struct.unpack_from('<II', raw, offset)
        require(kind == 5130562 and size % 4 == 0 and offset + 8 + size == len(raw), 'Invalid binary chunk')
        binary = raw[offset + 8:offset + 8 + size]

        def accessor(index):
            require(type(index) is int and 0 <= index < len(model['accessors']), 'Invalid accessor index')
            a = model['accessors'][index]
            require('sparse' not in a, 'Sparse accessor needs explicit validation support')
            require(type(a['bufferView']) is int and 0 <= a['bufferView'] < len(model['bufferViews']), 'Invalid buffer view')
            view = model['bufferViews'][a['bufferView']]
            require(view.get('buffer', 0) == 0, 'Invalid articulated export')
            count = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
            fmt = '<' + {5121: 'B', 5123: 'H', 5125: 'I', 5126: 'f'}[a['componentType']] * count
            stride = view.get('byteStride', struct.calcsize(fmt))
            start = view.get('byteOffset', 0) + a.get('byteOffset', 0)
            view_start = view.get('byteOffset', 0)
            view_end = view_start + view['byteLength']
            require(0 <= view_start <= start <= view_end <= len(binary), 'Invalid accessor bounds')
            require(type(a['count']) is int and a['count'] > 0 and stride >= struct.calcsize(fmt), 'Invalid accessor stride/count')
            require(start + (a['count'] - 1) * stride + struct.calcsize(fmt) <= view_end, 'Accessor exceeds buffer view')
            values = [struct.unpack_from(fmt, binary, start + i * stride) for i in range(a['count'])]
            if a.get('normalized'):
                divisor = {5121: 255, 5123: 65535}[a['componentType']]
                values = [tuple((x / divisor for x in row)) for row in values]
            return values
        require(len(model['skins']) == 1, 'Invalid articulated export')
        joints = model['skins'][0]['joints']
        require(joints and len(set(joints)) == len(joints) and all(type(j) is int and 0 <= j < len(model['nodes']) for j in joints), 'Invalid skin joints')
        weighted, vertices = (set(), 0)
        for mesh in model['meshes']:
            for primitive in mesh['primitives']:
                attrs = primitive['attributes']
                weights, indices = (accessor(attrs['WEIGHTS_0']), accessor(attrs['JOINTS_0']))
                require(model['accessors'][attrs['WEIGHTS_0']]['type'] == 'VEC4' and model['accessors'][attrs['JOINTS_0']]['type'] == 'VEC4', 'Invalid skin attribute shape')
                require(model['accessors'][attrs['JOINTS_0']]['componentType'] in (5121, 5123) and not model['accessors'][attrs['JOINTS_0']].get('normalized'), 'Invalid joint indices')
                require(len(weights) == len(indices), 'Invalid articulated export')
                vertices += len(weights)
                for ws, js in zip(weights, indices):
                    require(all((math.isfinite(w) and 0 <= w <= 1 for w in ws)), 'Invalid articulated export')
                    require(abs(sum(ws) - 1) < 0.0001, 'Invalid articulated export')
                    for w, j in zip(ws, js):
                        require(0 <= j < len(joints), 'Invalid articulated export')
                        if w > 0.0001:
                            weighted.add(j)
        require(weighted == set(range(len(joints))), 'Unweighted joint')
        animations = model['animations']
        require(len(animations) == len(layout.clips) and {a['name'] for a in animations} == set(layout.clips), 'Invalid articulated export')
        for animation in animations:
            changed = False
            for channel in animation['channels']:
                require(type(channel['sampler']) is int and 0 <= channel['sampler'] < len(animation['samplers']), 'Invalid sampler')
                sampler = animation['samplers'][channel['sampler']]
                require(model['accessors'][sampler['input']]['type'] == 'SCALAR', 'Invalid animation time shape')
                times = [row[0] for row in accessor(sampler['input'])]
                require(len(times) >= 2 and all(math.isfinite(t) and t >= 0 for t in times) and all((a < b for a, b in zip(times, times[1:]))), 'Invalid articulated export')
                values = accessor(sampler['output'])
                interpolation = sampler.get('interpolation', 'LINEAR')
                require(interpolation in ('LINEAR', 'STEP', 'CUBICSPLINE'), 'Invalid interpolation')
                require(len(values) == len(times) * (3 if interpolation == 'CUBICSPLINE' else 1), 'Animation sample count mismatch')
                if interpolation == 'CUBICSPLINE':
                    values = values[1::3]
                require(all((math.isfinite(v) for row in values for v in row)), 'Invalid articulated export')
                if channel['target']['node'] in joints and len(set(values)) > 1:
                    changed = True
            require(changed, 'Clip has no changing joint')
        hashes = []
        for frame in range(layout.rows * layout.columns):
            with Image.open(safe_path(batch, layout.frame.format(id=name, frame=frame))) as im:
                require(im.size == (layout.frame_size, layout.frame_size), 'Invalid articulated export')
                alpha = im.convert('RGBA').getchannel('A')
                bounds = alpha.getbbox()
                require(bounds and min(bounds[:2]) >= layout.margin and max(bounds[2:]) <= layout.frame_size - layout.margin, (subject['id'], frame, bounds))
                hashes.append(im.tobytes())
        for start in range(0, layout.rows * layout.columns, layout.columns):
            require(len(set(hashes[start:start + layout.columns])) > 1, 'Static rendered clip')
        records.append(dict(id=subject['id'], bones=len(joints), exported_vertices=vertices, glb_bytes=len(raw), clips=len(layout.clips), normalized_weights=True, all_bones_weighted=True, transparent_margins=True))
    if report_path is not None:
        Path(report_path).write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return records
