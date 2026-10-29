"""Validate scaffold manifests and local Markdown links; never execute game code."""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_IDS = {'phaser-to-godot', 'godot-windows-to-android', 'godot-to-unreal'}


def validate(root):
    root = Path(root).resolve()
    errors = []

    def local_file(value, owner):
        if not isinstance(value, str) or not value:
            errors.append(f'{owner}: expected nonempty relative path')
            return
        candidate = (root / value).resolve()
        if Path(value).is_absolute() or not candidate.is_relative_to(root):
            errors.append(f'{owner}: path must stay inside repository: {value}')
        elif not candidate.is_file():
            errors.append(f'{owner}: missing file: {value}')

    try:
        index = json.loads((root / 'workflows/index.json').read_text())
    except (OSError, ValueError) as exc:
        return [f'workflows/index.json: {exc}']
    if not isinstance(index, dict) or index.get('schema_version') != 1:
        return ['workflows/index.json: expected object with schema_version 1']
    entries = index.get('workflows')
    if not isinstance(entries, list):
        return ['workflows/index.json: workflows must be a list']
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append('workflow entry must be an object')
            continue
        ident = entry.get('id')
        if not isinstance(ident, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', ident):
            errors.append('workflow id must be a lowercase slug')
            continue
        if ident in seen:
            errors.append(f'duplicate workflow id: {ident}')
        seen.add(ident)
        if entry.get('status') not in ('scaffold', 'exploratory'):
            errors.append(f'{ident}: invalid scaffold status')
        dims = entry.get('dimensions')
        if not isinstance(dims, list) or not dims or any(d not in ('2d', '3d') for d in dims):
            errors.append(f'{ident}: dimensions must contain 2d and/or 3d')
        for field in ('guide', 'example'):
            local_file(entry.get(field), f'{ident}.{field}')
        shared = entry.get('shared')
        if not isinstance(shared, list) or not shared:
            errors.append(f'{ident}: shared must be a nonempty path list')
        else:
            for path in shared:
                local_file(path, f'{ident}.shared')
    if not REQUIRED_IDS <= seen:
        errors.append('missing required workflows: ' + ', '.join(sorted(REQUIRED_IDS - seen)))
    docs = [root / 'AGENTS.md', root / 'README.md']
    for directory in ('2d', '3d', 'shared', 'workflows', 'tools'):
        base = root / directory
        if not base.is_dir():
            errors.append(f'missing directory: {directory}')
        docs.extend(base.rglob('*.md'))
    for doc in docs:
        if not doc.is_file():
            errors.append(f'missing document: {doc.relative_to(root)}')
            continue
        for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)\)', doc.read_text()):
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target) or target.startswith('#'):
                continue
            path = (doc.parent / target.split('#', 1)[0]).resolve()
            if not path.is_relative_to(root) or not path.exists():
                errors.append(f'{doc.relative_to(root)}: broken local link: {target}')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    errors = validate(parser.parse_args().root)
    print(json.dumps({'status': 'failed' if errors else 'passed', 'errors': errors}, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
