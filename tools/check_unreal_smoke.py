"""Read-only Unreal smoke-log validation. A success marker alone is insufficient."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

ERROR = re.compile(r'\b(?:Error|Fatal):|Fatal error:|Assertion failed:|Ensure condition failed:|(?:\b|_)SMOKE FAIL\b', re.I)
PREFIX = re.compile(r'^(?:\[[^\]]+\]\[\s*\d+\])?\s*(?:[A-Za-z0-9_]+:\s*(?:(?:Display|Log):\s*)?)?')

def validate(log, marker, exit_code, started_at):
    if not math.isfinite(started_at) or started_at < 0:
        raise ValueError("Start time must be finite UTC Unix seconds")
    path = Path(log)
    if not marker or '\n' in marker or '\r' in marker:
        raise ValueError('A single-line success marker is required')
    if exit_code != 0:
        raise ValueError(f'Process exited with {exit_code}')
    if not path.is_file():
        raise ValueError('Smoke log is missing')
    if path.stat().st_mtime < started_at:
        raise ValueError('Smoke log predates this run')
    data = path.read_bytes()
    lines = data.decode('utf-8-sig', errors='replace').splitlines()
    errors = [line for line in lines if ERROR.search(line)]
    if errors:
        raise ValueError('Runtime errors found: ' + '\n'.join(errors[:5]))
    messages = [PREFIX.sub('', line, count=1) for line in lines]
    if not any(m == marker or m.startswith(marker + ' ') for m in messages):
        raise ValueError('Expected success marker not found as a log message')
    return {'status': 'passed', 'log': str(path.resolve()), 'sha256': hashlib.sha256(data).hexdigest(),
            'marker': marker, 'process_exit': exit_code,
            'scope': 'Fresh log, exit code and explicit marker; not a visual or coverage assessment'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--marker', required=True)
    parser.add_argument('--exit-code', type=int, required=True)
    parser.add_argument('--started-at', type=float, required=True, help='UTC Unix seconds recorded before launch')
    args = parser.parse_args()
    try:
        result = validate(args.log, args.marker, args.exit_code, args.started_at)
    except (ValueError, OSError) as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

