"""Validate GameCore wizard templates (the source of truth for hub wizards and ArcoreFlow nodes).

Standard library only. Enforces shared/wizard/wizard-template.schema.json (the JSON Schema subset it
uses) plus cross-reference rules a schema cannot express: unknown ids, stage order, artifact producers,
step coverage, defaults within bounds, and honest status/badge claims. Never executes adapters.
"""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = 'shared/wizard/wizard-template.schema.json'
ECOSYSTEM_PATH = 'shared/ecosystem.json'
TYPES = {'object': dict, 'array': list, 'string': str, 'boolean': bool, 'null': type(None)}


def _is_type(value, name):
    if name == 'integer':
        return isinstance(value, int) and not isinstance(value, bool)
    if name == 'number':
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, TYPES[name])


def check_schema(value, schema, root_schema, path, errors):
    """Validate the JSON Schema keywords used by the wizard schema."""
    if '$ref' in schema:
        node = root_schema
        for part in schema['$ref'].lstrip('#/').split('/'):
            node = node[part]
        schema = node
    if 'const' in schema and value != schema['const']:
        errors.append(f'{path}: expected {schema["const"]!r}')
        return
    if 'enum' in schema and value not in schema['enum']:
        errors.append(f'{path}: {value!r} not one of {schema["enum"]}')
        return
    expected = schema.get('type')
    if expected:
        names = expected if isinstance(expected, list) else [expected]
        if not any(_is_type(value, n) for n in names):
            errors.append(f'{path}: expected {"/".join(names)}')
            return
    if isinstance(value, str):
        if len(value) < schema.get('minLength', 0):
            errors.append(f'{path}: too short')
        if 'pattern' in schema and not re.search(schema['pattern'], value):
            errors.append(f'{path}: {value!r} does not match {schema["pattern"]}')
    if _is_type(value, 'number'):
        if 'minimum' in schema and value < schema['minimum']:
            errors.append(f'{path}: below minimum {schema["minimum"]}')
    if isinstance(value, list):
        if len(value) < schema.get('minItems', 0):
            errors.append(f'{path}: needs at least {schema["minItems"]} item(s)')
        if 'items' in schema:
            for i, item in enumerate(value):
                check_schema(item, schema['items'], root_schema, f'{path}[{i}]', errors)
    if isinstance(value, dict):
        for key in schema.get('required', []):
            if key not in value:
                errors.append(f'{path}: missing {key}')
        props = schema.get('properties', {})
        extra = schema.get('additionalProperties', True)
        for key, item in value.items():
            if 'propertyNames' in schema:
                check_schema(key, schema['propertyNames'], root_schema, f'{path}.<{key}>', errors)
            if key in props:
                check_schema(item, props[key], root_schema, f'{path}.{key}', errors)
            elif extra is False:
                errors.append(f'{path}: unknown property {key}')
            elif isinstance(extra, dict):
                check_schema(item, extra, root_schema, f'{path}.{key}', errors)


def check_field_value(name, field, value, where, errors):
    if field['type'] in ('enum', 'rational') and 'values' in field and value not in field['values']:
        errors.append(f'{where}: {name}={value!r} not in {field["values"]}')
    if field['type'] in ('integer', 'number'):
        if not _is_type(value, field['type']):
            errors.append(f'{where}: {name} must be {field["type"]}')
            return
        if 'minimum' in field and value < field['minimum'] or 'maximum' in field and value > field['maximum']:
            errors.append(f'{where}: {name}={value} outside {field.get("minimum")}..{field.get("maximum")}')
    if field['type'] in ('string', 'text') and isinstance(value, str) and len(value) > field.get('max_length', len(value)):
        errors.append(f'{where}: {name} longer than {field["max_length"]}')


def _references(value, path=''):
    """Yield (argument path, reference string) for field:/artifact: references at any depth."""
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _references(item, f'{path}.{key}' if path else key)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from _references(item, f'{path}[{i}]')
    elif isinstance(value, str) and (value.startswith('field:') or value.startswith('artifact:')):
        yield path, value


def check_calls(tid, stage, servers, errors):
    """Downstream MCP calls must target registered servers/tools and reference the stage's own inputs."""
    sid = stage['id']
    fields = set(stage['inputs'].get('fields', []))
    artifacts = set(stage['inputs'].get('artifacts', []))
    for call in stage.get('calls', []):
        where = f'{tid}.{sid}.calls[{call["server"]}.{call["tool"]}]'
        server = servers.get(call['server']) if servers is not None else None
        if servers is not None:
            if server is None:
                errors.append(f'{where}: server is not in {ECOSYSTEM_PATH} mcp.servers')
                continue
            if server.get('tools') and call['tool'] not in server['tools']:
                errors.append(f'{where}: tool is not declared for server {call["server"]}')
            if call['tool'] in server.get('write_tools', []) and not call.get('writes'):
                errors.append(f'{where}: tool writes, so the call must declare writes: true')
        for name, value in _references(call['arguments']):
            if value.startswith('field:') and value[6:] not in fields:
                errors.append(f'{where}: argument {name} references field {value[6:]}, which is not a stage input')
            if value.startswith('artifact:') and value[9:] not in artifacts:
                errors.append(f'{where}: argument {name} references artifact {value[9:]}, which is not a stage input')
        for art in call.get('results', {}):
            if art not in stage['outputs']:
                errors.append(f'{where}: result {art} is not an output of the stage')


def check_references(t, errors, workflow_ids, servers=None):
    tid = t['template_id']
    fields, artifacts, caps = t['fields'], t['artifacts'], t['capabilities']
    if workflow_ids is not None and t['workflow'] not in workflow_ids:
        errors.append(f'{tid}: unknown workflow {t["workflow"]}')

    for name, field in fields.items():
        if 'default' in field:
            check_field_value(name, field, field['default'], f'{tid}.fields', errors)
        if field['type'] == 'enum' and 'values' not in field:
            errors.append(f'{tid}.fields.{name}: enum needs values')
        for other in field.get('visible_when', {}):
            if other not in fields:
                errors.append(f'{tid}.fields.{name}: visible_when references unknown field {other}')
    for pid, preset in t.get('presets', {}).items():
        for name, value in preset['values'].items():
            if name not in fields:
                errors.append(f'{tid}.presets.{pid}: unknown field {name}')
            else:
                check_field_value(name, fields[name], value, f'{tid}.presets.{pid}', errors)

    produced, stage_ids, check_ids, used_fields = {}, [], set(), set()
    for stage in t['stages']:
        sid = stage['id']
        if sid in stage_ids:
            errors.append(f'{tid}: duplicate stage {sid}')
        for cap in stage.get('requires', []):
            if cap not in caps:
                errors.append(f'{tid}.{sid}: unknown capability {cap}')
        for name in stage['inputs'].get('fields', []):
            used_fields.add(name)
            if name not in fields:
                errors.append(f'{tid}.{sid}: unknown input field {name}')
        for art in stage['inputs'].get('artifacts', []):
            if art not in artifacts:
                errors.append(f'{tid}.{sid}: unknown input artifact {art}')
            elif art not in produced:
                errors.append(f'{tid}.{sid}: input artifact {art} is not produced by an earlier stage')
        for art in stage['outputs']:
            if art not in artifacts:
                errors.append(f'{tid}.{sid}: unknown output artifact {art}')
            elif art in produced:
                errors.append(f'{tid}.{sid}: artifact {art} already produced by {produced[art]}')
            else:
                produced[art] = sid
        for check in stage.get('checks', []):
            if check['id'] in check_ids:
                errors.append(f'{tid}.{sid}: duplicate check id {check["id"]}')
            check_ids.add(check['id'])
        if not t['assistance']['ai_required'] and stage.get('assistance') == 'required':
            errors.append(f'{tid}.{sid}: requires AI but the template claims ai_required=false')
        check_calls(tid, stage, servers, errors)
        stage_ids.append(sid)
    for art in artifacts:
        if art not in produced:
            errors.append(f'{tid}: artifact {art} is never produced')

    step_ids, step_fields, step_stages = set(), set(), set()
    for step in t['wizard']['steps']:
        if step['id'] in step_ids:
            errors.append(f'{tid}: duplicate wizard step {step["id"]}')
        step_ids.add(step['id'])
        for name in step['fields']:
            if name not in fields:
                errors.append(f'{tid}.steps.{step["id"]}: unknown field {name}')
            elif name in step_fields:
                errors.append(f'{tid}.steps.{step["id"]}: field {name} already shown in an earlier step')
            step_fields.add(name)
        for sid in step['stages']:
            if sid not in stage_ids:
                errors.append(f'{tid}.steps.{step["id"]}: unknown stage {sid}')
            step_stages.add(sid)
        if 'preview' in step and step['preview'] not in step['stages']:
            errors.append(f'{tid}.steps.{step["id"]}: preview stage must be one of its stages')
    for name in sorted(set(fields) - step_fields):
        errors.append(f'{tid}: field {name} is not shown in any wizard step')
    for name in sorted(set(fields) - used_fields):
        errors.append(f'{tid}: field {name} is not consumed by any stage')
    for sid in stage_ids:
        if sid not in step_stages:
            errors.append(f'{tid}: stage {sid} is not reachable from any wizard step')

    # Honest claims: no badge or "implemented" status without evidence.
    acceptance = t['acceptance']
    passed = [k for k, v in acceptance.items() if v == 'passed']
    if passed and not acceptance.get('evidence'):
        errors.append(f'{tid}: acceptance {", ".join(passed)} passed without evidence')
    if t['implementation_status'] == 'implemented':
        if any(s['implementation'] != 'verified' for s in t['stages']):
            errors.append(f'{tid}: implemented status requires every stage verified')
        if acceptance['no_ai_run'] != 'passed' and not t['assistance']['ai_required']:
            errors.append(f'{tid}: implemented no-AI template requires a passed no_ai_run')
    elif t['implementation_status'] == 'proposed' and any(s['implementation'] in ('parameterized', 'verified') for s in t['stages']):
        errors.append(f'{tid}: proposed status but some stages are parameterized; use partial')


def validate_template(path, schema, workflow_ids=None, servers=None):
    errors = []
    try:
        template = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        return [f'{path}: {exc}']
    check_schema(template, schema, schema, Path(path).name, errors)
    if errors:
        return errors
    check_references(template, errors, workflow_ids, servers)
    return errors


def load_servers(ecosystem):
    """Downstream MCP servers the hub may call, keyed by id (the hub itself is not callable)."""
    return {s['id']: s for s in ecosystem.get('mcp', {}).get('servers', [])}


def validate(root):
    root = Path(root).resolve()
    try:
        schema = json.loads((root / SCHEMA_PATH).read_text(encoding='utf-8'))
        index = json.loads((root / 'workflows/index.json').read_text(encoding='utf-8'))
        ecosystem = json.loads((root / ECOSYSTEM_PATH).read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        return [str(exc)], 0
    servers = load_servers(ecosystem)
    ids = {w.get('id') for w in index.get('workflows', [])}
    errors, count = [], 0
    for entry in index.get('workflows', []):
        rel = entry.get('wizard')
        if not rel:
            continue
        count += 1
        path = root / rel
        if not path.is_file():
            errors.append(f'{entry.get("id")}: missing wizard file {rel}')
            continue
        errs = validate_template(path, schema, ids, servers)
        if not errs:
            template = json.loads(path.read_text(encoding='utf-8'))
            if template['workflow'] != entry.get('id'):
                errs.append(f'{rel}: workflow {template["workflow"]!r} does not match index id {entry.get("id")!r}')
        errors.extend(f'{rel}: {e}' if not e.startswith(rel) else e for e in errs)
    return errors, count


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--root', type=Path, default=ROOT)
    errors, count = validate(parser.parse_args().root)
    print(json.dumps({'status': 'failed' if errors else 'passed', 'templates': count, 'errors': errors}, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
