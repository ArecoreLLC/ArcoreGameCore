"""Inventory external Unreal framework sources without importing or executing them.

The checked-in JSON pins every included file. --check detects additions, removals,
changed contents and generated-document drift. It never runs engines or repairs assets.
"""
import argparse
import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
CONFIG = Path('framework/inventory/unreal-sources.json')
CATALOG = Path('framework/inventory/unreal-inventory.json')
DOCUMENT = Path('framework/inventory/UNREAL_FILES.md')


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def collect_paths(source_root, spec, extensions, excluded):
    """Fail closed for missing declared scopes and symlinks escaping the source."""
    source_root = source_root.resolve()
    if not source_root.is_dir():
        raise ValueError(f'Missing source checkout: {source_root}')
    paths = set()

    def admit(path, markdown_only=False):
        relative = path.relative_to(source_root)
        if any(part in excluded for part in relative.parts):
            return
        if not path.resolve().is_relative_to(source_root):
            raise ValueError(f'Source path escapes its checkout: {path}')
        if path.is_file() and path.suffix.lower() in ({'.md'} if markdown_only else extensions):
            paths.add(path)

    for name in spec['root_files'] + spec.get('evidence_files', []):
        path = source_root / name
        if not path.is_file():
            raise ValueError(f'Missing declared source file: {path}')
        admit(path)
    for key, markdown_only in [('trees', False), ('documentation_trees', True)]:
        for name in spec[key]:
            base = source_root / name
            if not base.is_dir() or not base.resolve().is_relative_to(source_root):
                raise ValueError(f'Missing or escaped source scope: {base}')
            for current, directories, filenames in os.walk(base, followlinks=False):
                # Validate symlink directories even though os.walk will not follow them.
                for directory in directories:
                    p = Path(current) / directory
                    if directory not in excluded and not p.resolve().is_relative_to(source_root):
                        raise ValueError(f'Source directory escapes its checkout: {p}')
                directories[:] = [d for d in directories if d not in excluded]
                for filename in filenames:
                    admit(Path(current) / filename, markdown_only)
    return sorted(paths, key=lambda p: p.relative_to(source_root).as_posix())


def describe(source_id, relative, raw):
    """Extract declarations only; never import a scanned module, including tests."""
    text = raw.decode('utf-8-sig')
    suffix = Path(relative).suffix.lower()
    imports, arguments, tests, tools = [], [], [], []
    summary = ''
    if suffix == '.py':
        tree = ast.parse(text, filename=relative)
        summary = (ast.get_docstring(tree) or '').split('\n')[0]
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(n.name for n in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith('test_'):
                    tests.append(node.name)
                if any(isinstance(d, ast.Attribute) and d.attr == 'tool_call' for d in node.decorator_list):
                    tools.append({'name': node.name, 'summary': (ast.get_docstring(node) or '').split('\n')[0]})
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'add_argument':
                arguments.extend(a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str))
    elif suffix == '.cpp':
        tests = re.findall(r'IMPLEMENT_\w+_AUTOMATION_TEST\s*\(\s*\w+\s*,\s*"([^"]+)"', text)
        arguments = re.findall(r'FParse::Param\([^;\n]*?TEXT\("([^"]+)"\)', text)
    elif suffix == '.md':
        summary = next((line.lstrip('# ').strip() for line in text.splitlines() if line.startswith('# ')), '')
    elif suffix == '.ps1':
        arguments = re.findall(r'\[(?:string|switch|int|bool)\]\s*\$(\w+)', text, re.IGNORECASE)
    if source_id == 'world-framework':
        if relative.startswith('tests/'):
            role = 'framework regression tests'
        elif relative.startswith('Unreal/'):
            role = 'Unreal runtime plugin'
        elif '/profiles/' in relative:
            role = 'versioned rules and profiles'
        elif '/adapters/' in relative:
            role = 'engine adapter'
        elif '/terrain/' in relative or '/geometry/' in relative or '/assets/' in relative:
            role = 'procedural and portability helper'
        elif relative.startswith('src/'):
            role = 'validation core and probes'
        else:
            role = 'framework documentation and packaging'
    elif relative.startswith('Tools/'):
        name = Path(relative).stem
        role = ('project validation harness' if name.startswith(('audit_', 'verify_', 'validate_', 'inspect_', 'run_godot_', 'asset_integrity', 'model_review', 'analyze_')) else 'project procedural tool and launcher')
    elif relative.startswith('Plugins/'):
        role = 'native editor extension and adapters'
    elif relative.startswith('Source/'):
        role = 'project automation tests' if tests else 'project runtime and editor fixture'
    elif relative.startswith(('Assets/', 'Terrain/')) and suffix == '.json':
        role = 'project evidence and fixture manifest'
    else:
        role = 'project configuration and documentation'
    environment = 'inspect source prerequisites before execution'
    if 'unreal' in imports:
        environment = 'Unreal editor Python'
    elif 'bpy' in imports:
        environment = 'Blender Python'
    elif role == 'framework regression tests':
        environment = 'Python unittest with framework src on PYTHONPATH'
    elif suffix in {'.cpp', '.h', '.cs', '.uplugin', '.uproject'}:
        environment = 'Unreal build or runtime'
    elif suffix in {'.md', '.json', '.ini', '.txt', '.toml'}:
        environment = 'data or documentation'
    return {'role': role, 'summary': summary, 'execution_environment': environment,
            'imports': sorted(set(imports)), 'declared_arguments': sorted(set(arguments)),
            'declared_tests': sorted(set(tests)), 'native_mcp_tools': sorted(tools, key=lambda t: t['name'])}


def build_inventory(repo_root, config):
    if config.get('schema_version') != 1:
        raise ValueError('Unsupported inventory configuration version')
    sources, entries = [], []
    for spec in config['sources']:
        source_root = (repo_root / spec['root']).resolve()
        files = collect_paths(source_root, spec, set(config['extensions']), set(config['excluded_directories']))
        records = []
        for path in files:
            raw = path.read_bytes()
            relative = path.relative_to(source_root).as_posix()
            entry = {'source': spec['id'], 'path': relative, 'sha256': sha256(raw), 'bytes': len(raw),
                     **describe(spec['id'], relative, raw)}
            entry.update(config.get('entry_notes', {}).get(spec['id'] + ':' + relative, {}))
            records.append(entry)
        # Digest includes names and contents, so renames and additions change the baseline.
        pin = ''.join(f"{e['path']}\0{e['sha256']}\n" for e in records).encode('utf-8')
        sources.append({'id': spec['id'], 'root': spec['root'], 'ownership': spec['ownership'],
                        'files': len(records), 'snapshot_sha256': sha256(pin)})
        entries.extend(records)
    return {'schema_version': 1, 'reviewed_on': config['reviewed_on'], 'engine': config['engine'],
            'framework_version': config['framework_version'], 'revision_note': config['revision_note'],
            'execution_status': 'inventory_only; no engine or asset operations executed',
            'scope': {'source_config': CONFIG.as_posix(), 'binary_assets_included': False,
                      'saved_evidence_copied': False, 'declarations_are_not_execution_results': True},
            'sources': sources, 'entries': entries}


def render_document(inventory, config):
    roots = {s['id']: s['root'] for s in config['sources']}
    lines = ['# Unreal framework file inventory', '',
             'Generated by `tools/inventory_unreal.py`. This catalogs external source files; it does not copy implementation or execute any listed script. Source roots are relative to GameCore. Hashes, dependencies, declared CLI flags, test names and native MCP operations are in [the JSON inventory](unreal-inventory.json).', '',
             f"Reviewed {inventory['reviewed_on']}; framework {inventory['framework_version']}; Unreal {inventory['engine']['version']} / Win64. {inventory['revision_note']}", '',
             'All Tools, Source, Plugins and Config text files in ArcoreOpenWorld are covered, along with root launchers, Assets/Terrain Markdown guides and explicitly selected evidence pointers, receipts and sandbox manifests. The framework includes src, Unreal, tests, docs and package metadata. Engine binaries, generated caches, asset binaries and historical capture trees are excluded. See [scope configuration](unreal-sources.json) and the [integration guide](../UNREAL_INTEGRATION.md).', '']
    for source in inventory['sources']:
        lines.extend([f"## {source['id']}", '', f"Root `{source['root']}`; {source['files']} files; snapshot SHA-256 `{source['snapshot_sha256']}`.", ''])
        own_entries = [e for e in inventory['entries'] if e['source'] == source['id']]
        for role in sorted({e['role'] for e in own_entries}):
            lines.extend([f'### {role}', '', '| Source file | Purpose or declarations |', '|---|---|'])
            for e in own_entries:
                if e['role'] != role:
                    continue
                # This generated document is two directories below GameCore's root.
                link = quote('../../' + roots[e['source']] + '/' + e['path'], safe='/.-_')
                details = e['summary'] or e['execution_environment']
                if e.get('limitation'):
                    details += '; ' + e['operational_status'] + ': ' + e['limitation']
                if e['declared_tests']:
                    details += '; tests: ' + ', '.join(e['declared_tests'])
                if e['native_mcp_tools']:
                    details += '; native MCP: ' + ', '.join(t['name'] for t in e['native_mcp_tools'])
                details = details.replace('|', '\\|').replace('\n', ' ')
                lines.append(f"| [{e['path']}]({link}) | {details} |")
            lines.append('')
    return '\n'.join(lines)


def check_catalog(expected, actual):
    """Report source drift without accepting it or rewriting the stored baseline."""
    def keyed(doc):
        return {(e['source'], e['path']): e for e in doc['entries']}
    old, new = keyed(expected), keyed(actual)
    problems = []
    for key in sorted(old.keys() | new.keys()):
        label = ':'.join(key)
        if key not in old:
            problems.append('uncataloged: ' + label)
        elif key not in new:
            problems.append('missing: ' + label)
        elif old[key] != new[key]:
            problems.append('changed: ' + label)
    if not problems and expected != actual:
        problems.append('inventory metadata or source snapshot changed')
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT, help='GameCore checkout; source roots resolve relative to it')
    parser.add_argument('--check', action='store_true', help='Report drift without writing files')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        config = json.loads((root / CONFIG).read_text(encoding='utf-8'))
        inventory = build_inventory(root, config)
        markdown = render_document(inventory, config)
        if args.check:
            expected = json.loads((root / CATALOG).read_text(encoding='utf-8'))
            errors = check_catalog(expected, inventory)
            if (root / DOCUMENT).read_text(encoding='utf-8') != markdown:
                errors.append('generated Markdown differs; review and regenerate the inventory')
        else:
            (root / CATALOG).write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            (root / DOCUMENT).write_text(markdown, encoding='utf-8')
            errors = []
        print(json.dumps({'status': 'failed' if errors else 'passed', 'errors': errors,
                          'files': len(inventory['entries']),
                          'roles': dict(sorted(Counter(e['role'] for e in inventory['entries']).items()))}, indent=2))
        return int(bool(errors))
    except (OSError, ValueError, KeyError, SyntaxError) as exc:
        print(json.dumps({'status': 'failed', 'errors': [str(exc)]}, indent=2))
        return 1


if __name__ == '__main__':
    sys.exit(main())
