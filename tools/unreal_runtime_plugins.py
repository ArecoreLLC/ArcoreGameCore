"""Validate explicitly declared Unreal runtime plugins without loading them."""
from pathlib import Path
import json

def inspect_runtime_plugins(project_file, declarations):
    project_file = Path(project_file).resolve()
    project = json.loads(project_file.read_text(encoding='utf-8-sig'))
    enabled = {p.get('Name') for p in project.get('Plugins', []) if p.get('Enabled') is True}
    roots = [project_file.parent / 'Plugins']
    roots += [(project_file.parent / p).resolve() for p in project.get('AdditionalPluginDirectories', [])]
    errors, checks = [], []
    for name in declarations:
        if not isinstance(name, str) or not name or not name.replace('_', '').isalnum():
            errors.append('Invalid runtime plugin name: ' + str(name))
            continue
        candidates = [r / name / (name + '.uplugin') for r in roots]
        candidates += [r / (name + '.uplugin') for r in roots]
        descriptor = next((p for p in candidates if p.is_file()), None)
        if name not in enabled:
            errors.append('Runtime plugin is not explicitly enabled: ' + name)
        if descriptor is None:
            errors.append('Runtime plugin descriptor not found: ' + name)
        else:
            try:
                data = json.loads(descriptor.read_text(encoding='utf-8-sig'))
                if not any(m.get('Type') == 'Runtime' for m in data.get('Modules', [])):
                    errors.append('Plugin has no Runtime module: ' + name)
            except (ValueError, OSError) as exc:
                errors.append('Invalid plugin descriptor: ' + str(exc))
        checks.append({'id': name, 'enabled': name in enabled, 'descriptor': str(descriptor) if descriptor else None})
    return {'checks': checks, 'errors': errors, 'scope': 'declaration and descriptor only; does not establish build, loading or packaging'}
