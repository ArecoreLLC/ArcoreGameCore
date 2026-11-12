"""Fail-closed validation of an Unreal automation index.json; never proves rendering."""
import argparse
import json
from pathlib import Path


def validate(report, prefix):
    tests = report.get('tests')
    if not isinstance(tests, list):
        raise ValueError('Report has no tests array')
    selected = [t for t in tests if isinstance(t, dict) and str(t.get('fullTestPath', '')).startswith(prefix)]
    if not prefix or not selected:
        raise ValueError('No matching tests; an empty run is not a pass')
    failures = [t.get('fullTestPath') for t in selected if t.get('state') != 'Success' or t.get('errors', 0) != 0]
    if failures:
        raise ValueError('Unsuccessful tests: ' + ', '.join(failures))
    return {'status': 'passed', 'prefix': prefix, 'count': len(selected), 'tests': [t['fullTestPath'] for t in selected]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('--prefix', required=True)
    args = parser.parse_args()
    try:
        result = validate(json.loads(args.report.read_text(encoding='utf-8-sig')), args.prefix)
    except (ValueError, OSError) as error:
        parser.exit(1, f'Automation evidence rejected: {error}\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
