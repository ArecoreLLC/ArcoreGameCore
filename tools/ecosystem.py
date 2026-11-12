"""Read-only Arcore dependency checks. No service startup or credential access."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inspect(root=ROOT, project=None):
    root = Path(root).resolve()
    errors, checks = [], []
    registry = json.loads((root / 'shared/ecosystem.json').read_text(encoding='utf-8'))
    if registry.get('schema_version') != 1:
        raise ValueError('Unsupported registry schema')
    seen = set()
    for entry in registry['components']:
        ident = entry['id']
        if ident in seen:
            errors.append('Duplicate integration: ' + ident)
        seen.add(ident)
        base = (root / entry['root']).resolve()
        missing = []
        for name in entry['required_files']:
            target = (base / name).resolve()
            if not target.is_relative_to(base) or not target.is_file():
                missing.append(name)
        checks.append({'id': ident, 'status': 'failed' if missing else 'passed', 'root': str(base), 'missing': missing})
        if missing:
            errors.append(ident + ': required files missing')
    if project:
        path = Path(project).resolve()
        config = json.loads(path.read_text(encoding='utf-8'))
        if config.get('schema_version') != 1:
            errors.append('Unsupported project schema')
        if config.get('dimension') not in ('2d', '3d'):
            errors.append('Invalid dimension')
        engine = config.get('engine', {})
        engine_id = engine.get('id')
        if engine_id not in ('unreal', 'godot') or not engine.get('version'):
            errors.append('Declare engine id and version')
        if not config.get('project_id') or not config.get('platforms'):
            errors.append('Declare project id and target platforms')
        for ident in config.get('integrations', []):
            if ident not in seen:
                errors.append('Unknown integration: ' + ident)
        base = path.parent.parent
        name = engine.get('project_file', '')
        target = (base / name).resolve()
        expected = '.uproject' if engine_id == 'unreal' else '.godot'
        if not name or not target.is_relative_to(base) or not target.is_file() or target.suffix != expected:
            errors.append('Engine project must exist inside consumer with the correct extension')
        if engine_id == 'unreal' and target.is_file() and config.get('runtime_plugins'):
            from unreal_runtime_plugins import inspect_runtime_plugins
            runtime = inspect_runtime_plugins(target, config['runtime_plugins'])
            checks.append({'id': 'runtime_plugins', **runtime})
            errors.extend(runtime['errors'])
        checks.append({'id': 'consumer', 'project': config.get('project_id'), 'engine': engine_id})
    return {'status': 'failed' if errors else 'passed', 'scope': 'file-level integration only; live services and engine behavior not checked', 'checks': checks, 'errors': errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path)
    parser.add_argument('--review', choices=['asset-sandbox', 'model-history', 'nature-walk'])
    args = parser.parse_args()
    try:
        report = inspect(project=args.project)
        if args.review:
            registry = json.loads((ROOT / 'shared/review-environments.json').read_text(encoding='utf-8'))
            mode = next(m for m in registry['modes'] if m['id'] == args.review)
            provider = next(c for c in report['checks'] if c['id'] == registry['provider'])
            base = Path(provider['root'])
            report['review'] = dict(mode)
            for field in ('guide', 'launcher'):
                target = (base / mode[field]).resolve()
                if not target.is_relative_to(base) or not target.is_file():
                    report['errors'].append('Missing or invalid review ' + field)
                    report['status'] = 'failed'
                report['review'][field] = str(target)
            report['review']['execution'] = 'not_run; discovery only'
    except (OSError, ValueError, KeyError, TypeError) as exc:
        report = {'status': 'failed', 'errors': [str(exc)]}
    print(json.dumps(report, indent=2))
    return int(report['status'] != 'passed')


if __name__ == '__main__':
    raise SystemExit(main())

