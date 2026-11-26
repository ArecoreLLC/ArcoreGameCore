#!/usr/bin/env python3
"""Painted, animated companion pipeline: vendor the studio module into a game, list the stages,
and check a finished GLB. Standard library only. See workflows/painted-animated-companions/.

    python tools/companion_pipeline.py stages [--class frontier-model]
    python tools/companion_pipeline.py vendor --target <game folder for Blender scripts> [--godot <game addons folder>]
    python tools/companion_pipeline.py vendor --target <...> --check
    python tools/companion_pipeline.py validate-glb model.glb --clips Idle,Walk,Greet --loops Idle,Walk
"""
import argparse
import hashlib
import json
import math
import re
import shutil
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGES = ROOT / 'workflows/painted-animated-companions/stages.json'
MODULE = 'gamecore.blender.companion-studio'
BLENDER_FILES = ['painterly.py', 'motion.py', 'reference.py']
GODOT_FILES = ['painted_lighting.gdshaderinc']
BLENDER_SOURCE = ROOT / '3d/blender/companion_studio'
GODOT_SOURCE = ROOT / '3d/godot/painted_companion'
LOCK = 'gamecore_companion_studio.lock.json'
FORMATS = {5120: 'b', 5121: 'B', 5122: 'h', 5123: 'H', 5125: 'I', 5126: 'f'}
WIDTH = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def version_of(path):
    found = re.search(r"^VERSION\s*=\s*['\"]([^'\"]+)['\"]", Path(path).read_text(encoding='utf-8'), re.M)
    return found.group(1) if found else 'unknown'


# ---------- stages ----------
def load_stages():
    return json.loads(STAGES.read_text(encoding='utf-8'))

def stages(args):
    data = load_stages(); chosen = [s for s in data['stages'] if not args.automation or s['automation'] == args.automation]
    if args.json: print(json.dumps(chosen, indent=2)); return 0
    for s in chosen:
        extra = f" (first time: {s['first_time']})" if s.get('first_time') else (f" (else: {s['fallback']})" if s.get('fallback') else '')
        print(f"{s['id']:18s} {s['automation']}{extra}\n    {s['title']}: {s['why']}")
    return 0


# ---------- vendor ----------
def vendor(args):
    """Copy the studio into a game with a SHA-256 lock, or check an existing copy against it."""
    plan = [(BLENDER_SOURCE / name, Path(args.target) / name) for name in BLENDER_FILES]
    if args.godot: plan += [(GODOT_SOURCE / name, Path(args.godot) / name) for name in GODOT_FILES]
    lock_path = Path(args.target) / LOCK
    if args.check:
        if not lock_path.is_file(): print(json.dumps({'ok': False, 'error': f'No lock at {lock_path}'})); return 1
        lock = json.loads(lock_path.read_text(encoding='utf-8')); problems = []
        for entry in lock['files']:
            copy = Path(entry['path'])
            if not copy.is_file(): problems.append({'file': entry['name'], 'problem': 'missing'})
            elif sha256(copy) != entry['sha256']: problems.append({'file': entry['name'], 'problem': 'changed since vendoring'})
            elif Path(ROOT.parent / entry['source']).is_file() and sha256(ROOT.parent / entry['source']) != entry['sha256']:
                problems.append({'file': entry['name'], 'problem': 'GameCore has a newer source', 'severity': 'info'})
        ok = not [p for p in problems if p.get('severity') != 'info']
        print(json.dumps({'ok': ok, 'module': lock['module'], 'problems': problems}, indent=2)); return 0 if ok else 1
    files = []
    for source, target in plan:
        if not source.is_file(): raise SystemExit(f'Missing module source: {source}')
        target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target)
        files.append({'name': source.name, 'source': str(source.relative_to(ROOT.parent)).replace('\\', '/'), 'path': str(target).replace('\\', '/'),
                      'sha256': sha256(target), 'version': version_of(source)})
    lock_path.write_text(json.dumps({'module': MODULE, 'version': version_of(BLENDER_SOURCE / 'motion.py'), 'files': files}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': True, 'lock': str(lock_path), 'files': [f['name'] for f in files]}, indent=2)); return 0


# ---------- validate-glb ----------
def read_glb(path):
    raw = Path(path).read_bytes()
    if raw[:4] != b'glTF': raise ValueError('Not a binary glTF file')
    length = struct.unpack('<I', raw[12:16])[0]
    return json.loads(raw[20:20 + length]), raw[28 + length:]

def accessor(doc, binary, index):
    """Rows of an accessor as tuples (normalised integers scaled to 0..1)."""
    acc = doc['accessors'][index]; view = doc['bufferViews'][acc['bufferView']]; code = FORMATS[acc['componentType']]; n = WIDTH[acc['type']]
    start = view.get('byteOffset', 0) + acc.get('byteOffset', 0); size = struct.calcsize('<' + code * n); stride = view.get('byteStride') or size
    rows = [struct.unpack_from('<' + code * n, binary, start + i * stride) for i in range(acc['count'])]
    if acc.get('normalized') and code != 'f':
        top = float(2 ** (8 * struct.calcsize(code)) - 1) if code.isupper() else float(2 ** (8 * struct.calcsize(code) - 1) - 1)
        rows = [tuple(v / top for v in row) for row in rows]
    return rows

def validate_glb(path, clips=(), loops=()):
    doc, binary = read_glb(path); issues = []
    def issue(severity, code, message): issues.append({'severity': severity, 'code': code, 'message': message})
    vertices = triangles = 0
    for mesh in doc.get('meshes', []):
        for prim in mesh['primitives']:
            a = prim['attributes']; position = accessor(doc, binary, a['POSITION']); vertices += len(position)
            if not all(math.isfinite(v) for row in position for v in row): issue('error', 'non_finite_position', f"{mesh.get('name')}: a vertex position is not finite.")
            if 'indices' in prim:
                index = accessor(doc, binary, prim['indices']); triangles += len(index) // 3
                if index and max(i[0] for i in index) >= len(position): issue('error', 'index_out_of_range', f"{mesh.get('name')}: an index points past the last vertex.")
            if 'WEIGHTS_0' in a:
                kind = doc['accessors'][a['WEIGHTS_0']]['componentType']; weights = accessor(doc, binary, a['WEIGHTS_0'])
                scale = 1.0 if kind == 5126 or doc['accessors'][a['WEIGHTS_0']].get('normalized') else float({5121: 255, 5123: 65535}.get(kind, 1))
                if any(abs(sum(row) / scale - 1) > .01 for row in weights): issue('error', 'weights_not_normalised', f"{mesh.get('name')}: skin weights do not sum to 1.")
            if 'TEXCOORD_0' in a:
                uv = accessor(doc, binary, a['TEXCOORD_0'])
                if any(v < -1e-4 or v > 1 + 1e-4 for row in uv for v in row): issue('warning', 'uv_outside_unit_square', f"{mesh.get('name')}: UVs leave the 0..1 square.")
            else: issue('warning', 'no_uvs', f"{mesh.get('name')}: no UVs.")
    untextured = [m.get('name', '?') for m in doc.get('materials', []) if 'baseColorTexture' not in m.get('pbrMetallicRoughness', {})]
    if untextured: issue('warning', 'material_without_texture', 'No base colour texture on: ' + ', '.join(untextured))
    report = {}
    for animation in doc.get('animations', []):
        seconds = 0.0; gap = 0.0; finite = True
        for channel in animation['channels']:
            sampler = animation['samplers'][channel['sampler']]; times = accessor(doc, binary, sampler['input']); values = accessor(doc, binary, sampler['output'])
            if sampler.get('interpolation') == 'CUBICSPLINE': values = values[1::3]
            seconds = max(seconds, times[-1][0]); finite &= all(math.isfinite(v) for row in values for v in row)
            first, last = values[0], values[-1]; direct = max(abs(a - b) for a, b in zip(first, last))
            # A quaternion and its negative are the same rotation.
            gap = max(gap, min(direct, max(abs(a + b) for a, b in zip(first, last))) if channel['target']['path'] == 'rotation' else direct)
        name = animation.get('name', ''); report[name] = {'seconds': round(seconds, 3), 'channels': len(animation['channels']), 'first_last_key_gap': round(gap, 5)}
        if not finite: issue('error', 'non_finite_keys', f'Clip "{name}" has keys that are not finite.')
        if name in loops and gap > 2e-3: issue('error', 'loop_does_not_close', f'Clip "{name}" should loop but its last key differs from its first by {gap:.4f}.')
    for name in clips:
        if name not in report: issue('error', 'missing_clip', f'Expected clip "{name}" is not in the file.')
    joints = sum(len(skin['joints']) for skin in doc.get('skins', []))
    errors = sum(1 for i in issues if i['severity'] == 'error')
    return {'file': str(path), 'sha256': sha256(path), 'ready': errors == 0, 'issues': issues,
            'stats': {'meshes': len(doc.get('meshes', [])), 'vertices': vertices, 'triangles': triangles, 'joints': joints,
                      'images': [i.get('name') for i in doc.get('images', [])], 'clips': report}}

def validate(args):
    result = validate_glb(args.glb, [c for c in args.clips.split(',') if c], [c for c in args.loops.split(',') if c])
    if args.out: Path(args.out).write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2)); return 0 if result['ready'] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0]); sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('stages', help='List pipeline stages and what kind of automation each one suits')
    p.add_argument('--class', dest='automation', help='Only this automation class'); p.add_argument('--json', action='store_true'); p.set_defaults(run=stages)
    p = sub.add_parser('vendor', help='Copy the studio module into a game with a hash lock')
    p.add_argument('--target', required=True, help='Folder for painterly.py and motion.py'); p.add_argument('--godot', help='Folder for the Godot shader include')
    p.add_argument('--check', action='store_true', help='Compare an existing copy with its lock instead of copying'); p.set_defaults(run=vendor)
    p = sub.add_parser('validate-glb', help='Structural and animation checks on a finished GLB')
    p.add_argument('glb'); p.add_argument('--clips', default='', help='Clips that must exist'); p.add_argument('--loops', default='', help='Clips that must loop')
    p.add_argument('--out', help='Write the JSON report here'); p.set_defaults(run=validate)
    args = parser.parse_args(argv); return args.run(args)


if __name__ == '__main__':
    sys.exit(main())
