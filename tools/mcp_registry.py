"""Check the MCP registry in shared/ecosystem.json and, optionally, probe the live servers.

The GameCore hub is the only MCP server agents register; it calls the downstream servers listed
under mcp.servers itself. This tool keeps that registry honest:

  python tools/mcp_registry.py            # structure only (no network, no processes)
  python tools/mcp_registry.py --probe    # also connect to each server and compare its tools

Probing performs MCP initialize + tools/list only; it never calls a tool. A server's URL and
bearer token come from the environment variables named in its auth block (e.g.
ARCORE_MCP_URL_SOUND_CORE), else from the local file the app itself writes, named in its
discovery block (e.g. SoundCore's service.json). Tokens stay in memory: they are never printed,
logged or written. Standard library only. For a checklist page instead of a CLI, see mcp_setup.py.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_VERSION = '2025-06-18'
TRANSPORTS = {'stdio', 'streamable-http'}
AUTH_TYPES = {'bearer', 'none', 'env'}
CLIENT_INFO = {'name': 'gamecore-mcp-registry', 'version': '0.1.0'}


def check_registry(ecosystem):
    """Structural rules for the mcp block. Returns a list of errors."""
    errors = []
    mcp = ecosystem.get('mcp')
    if not isinstance(mcp, dict):
        return ['ecosystem.json: missing mcp block']
    components = {c['id'] for c in ecosystem.get('components', [])}
    hub = mcp.get('hub')
    if not isinstance(hub, dict) or not hub.get('id') or not hub.get('tools'):
        errors.append('mcp.hub: needs an id and its tools (the hub is the single registered entry point)')
    elif len({t['name'] for t in hub['tools']}) != len(hub['tools']):
        errors.append('mcp.hub: duplicate tool names')
    seen = set()
    for server in mcp.get('servers', []):
        sid = server.get('id', '?')
        if sid in seen:
            errors.append(f'mcp.servers: duplicate id {sid}')
        seen.add(sid)
        if hub and sid == hub.get('id'):
            errors.append(f'mcp.servers.{sid}: the hub must not call itself')
        if server.get('component') not in components:
            errors.append(f'mcp.servers.{sid}: component {server.get("component")} is not in components')
        transport = server.get('transport')
        if transport not in TRANSPORTS:
            errors.append(f'mcp.servers.{sid}: transport must be one of {sorted(TRANSPORTS)}')
        if transport == 'streamable-http' and not str(server.get('url', '')).startswith('http://127.0.0.1'):
            errors.append(f'mcp.servers.{sid}: HTTP servers must be loopback (http://127.0.0.1...)')
        if transport == 'stdio' and not (isinstance(server.get('command'), list) and server['command']):
            errors.append(f'mcp.servers.{sid}: stdio servers need a command list')
        auth = server.get('auth', {})
        if auth.get('type') not in AUTH_TYPES:
            errors.append(f'mcp.servers.{sid}: auth.type must be one of {sorted(AUTH_TYPES)}')
        if auth.get('type') == 'bearer' and not auth.get('token_env'):
            errors.append(f'mcp.servers.{sid}: bearer auth must name token_env (tokens never live in the registry)')
        if any(k in json.dumps(auth).lower() for k in ('"token":', '"secret"', '"password"')):
            errors.append(f'mcp.servers.{sid}: auth must reference environment variables, not contain credentials')
        discovery = server.get('discovery')
        if discovery is not None:
            if not discovery.get('file') or not discovery.get('url') or not discovery.get('token_key'):
                errors.append(f'mcp.servers.{sid}: discovery needs file, url and token_key')
            elif not discovery['url'].startswith(('http://127.0.0.1', '{')):
                errors.append(f'mcp.servers.{sid}: discovery url must be loopback')
        tools = server.get('tools', [])
        extra = [t for t in server.get('write_tools', []) if tools and t not in tools]
        if extra:
            errors.append(f'mcp.servers.{sid}: write_tools not in tools: {", ".join(extra)}')
    return errors


# ---------------------------------------------------------------- transports

def _read_http_result(response):
    body = response.read().decode('utf-8')
    if 'text/event-stream' in response.headers.get('Content-Type', ''):
        for line in body.splitlines():
            if line.startswith('data:') and line[5:].strip():
                return json.loads(line[5:])
        raise ValueError('empty event stream')
    return json.loads(body) if body.strip() else None


def probe_http(url, token=None, timeout=5.0):
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
    if token:
        headers['Authorization'] = f'Bearer {token}'

    def post(payload, session=None):
        h = dict(headers)
        if session:
            h['Mcp-Session-Id'] = session
            h['MCP-Protocol-Version'] = PROTOCOL_VERSION
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=h, method='POST')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.headers.get('Mcp-Session-Id') or session, _read_http_result(response)

    session, init = post({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
        'protocolVersion': PROTOCOL_VERSION, 'capabilities': {}, 'clientInfo': CLIENT_INFO}})
    if not init or 'result' not in init:
        raise ValueError(f'initialize failed: {init}')
    post({'jsonrpc': '2.0', 'method': 'notifications/initialized'}, session)
    _, listed = post({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list', 'params': {}}, session)
    return init['result'], listed['result']['tools']


def probe_stdio(command, cwd, env, timeout=20.0):
    proc = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, encoding='utf-8')
    try:
        def send(payload):
            proc.stdin.write(json.dumps(payload) + '\n')
            proc.stdin.flush()

        def wait_for(msg_id):
            while True:
                line = proc.stdout.readline()
                if not line:
                    raise ValueError('server exited before answering')
                message = json.loads(line)
                if message.get('id') == msg_id:
                    return message

        send({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
            'protocolVersion': PROTOCOL_VERSION, 'capabilities': {}, 'clientInfo': CLIENT_INFO}})
        init = wait_for(1)
        send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
        send({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list', 'params': {}})
        listed = wait_for(2)
        return init['result'], listed['result']['tools']
    finally:
        proc.kill()
        proc.wait(timeout=timeout)
        for stream in (proc.stdin, proc.stdout):
            try:
                stream.close()
            except OSError:
                pass


def _expand(path, env):
    path = re.sub(r'%(\w+)%', lambda m: env.get(m.group(1), m.group(0)), path)
    return Path(os.path.expanduser(path))


def discover(server, env=os.environ):
    """Reads the URL and token the app wrote for local clients. Returns (url, token, problem)."""
    discovery = server.get('discovery')
    if not discovery:
        return None, None, None
    path = _expand(discovery['file'], env)
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return None, None, f'{path.name} not found: open the app once so it writes its connection details'
    except (OSError, ValueError) as exc:
        return None, None, f'could not read {path.name}: {exc}'
    if discovery.get('enabled_key') and not data.get(discovery['enabled_key']):
        return None, None, discovery.get('disabled_hint', 'the app has its agent API turned off')
    try:
        url = discovery['url'].format(**{k: v for k, v in data.items() if isinstance(v, (str, int))})
    except KeyError as exc:
        return None, None, f'{path.name} has no {exc}'
    token = data.get(discovery['token_key'])
    if not isinstance(token, str) or not token:
        return None, None, f'{path.name} has no {discovery["token_key"]}'
    if not url.startswith('http://127.0.0.1'):
        return None, None, f'{path.name} points at a non-loopback URL; refusing'
    return url.rstrip('/'), token, None


def resolve_http(server, env=os.environ):
    """URL and token for an HTTP server: environment first, then the app's discovery file."""
    auth = server.get('auth', {})
    bearer = auth.get('type') == 'bearer'
    url = env.get(auth.get('url_env', ''), '')
    token = env.get(auth.get('token_env', ''), '') if bearer else None
    source = 'environment'
    if not url or (bearer and not token):
        found_url, found_token, problem = discover(server, env)
        if problem and not url and '{port}' in server['url']:
            return None, None, None, problem
        url, token = url or found_url, token or found_token
        source = 'app' if found_url else source
    url = url or server['url']
    if '{port}' in url:
        return None, None, None, f'set {auth.get("url_env")} ({server.get("connection", "")})'
    if bearer and not token:
        return None, None, None, f'set {auth.get("token_env")}'
    return url, token, source, None


def probe_server(server, components, env=os.environ):
    sid = server['id']
    auth = server.get('auth', {})
    source = None
    try:
        if server['transport'] == 'streamable-http':
            url, token, source, problem = resolve_http(server, env)
            if problem:
                return {'id': sid, 'status': 'not_configured', 'detail': problem}
            info, tools = probe_http(url, token)
        else:
            root = (ROOT / components[server['component']]['root']).resolve()
            child_env = {**env, **auth.get('env', {})}
            command = [sys.executable if c == 'python' else c for c in server['command']]
            if not (root / command[-1]).exists() and len(command) > 1:
                return {'id': sid, 'status': 'not_installed', 'detail': f'{command[-1]} not found in {root}'}
            info, tools = probe_stdio(command, str(root), child_env)
    except (urllib.error.URLError, ConnectionError, TimeoutError) as exc:
        return {'id': sid, 'status': 'not_running', 'detail': str(getattr(exc, 'reason', exc))}
    except (OSError, ValueError, KeyError) as exc:
        return {'id': sid, 'status': 'failed', 'detail': str(exc)}
    names = {t['name'] for t in tools}
    missing = [t for t in server.get('tools', []) if t not in names]
    return {
        'id': sid,
        'status': 'failed' if missing else 'passed',
        'server': info.get('serverInfo', {}),
        'protocol': info.get('protocolVersion'),
        'tools_found': len(names),
        'missing_tools': missing,
        **({'connection_from': source} if source else {})
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--probe', action='store_true', help='connect to each server (initialize + tools/list only)')
    parser.add_argument('--server', action='append', help='limit probing to these server ids')
    parser.add_argument('--selected', action='store_true',
                        help='limit probing to the apps ticked in mcp_setup.py (.gamecore/mcp-selection.json)')
    parser.add_argument('--strict', action='store_true', help='treat not_running/not_configured as failures')
    args = parser.parse_args(argv)
    ecosystem = json.loads((args.root / 'shared/ecosystem.json').read_text(encoding='utf-8'))
    errors = check_registry(ecosystem)
    result = {'status': 'failed' if errors else 'passed', 'errors': errors,
              'hub': ecosystem.get('mcp', {}).get('hub', {}).get('id'),
              'scope': 'registry structure' + (' and live tools/list' if args.probe else '')}
    if args.probe and not errors:
        components = {c['id']: c for c in ecosystem['components']}
        wanted = set(args.server) if args.server else None
        if args.selected:
            try:
                saved = json.loads((args.root / '.gamecore/mcp-selection.json').read_text(encoding='utf-8'))
                wanted = (wanted or set()) | set(saved.get('selected', []))
            except (OSError, ValueError):
                pass  # nothing saved yet: probe every server
        servers = [s for s in ecosystem['mcp']['servers'] if wanted is None or s['id'] in wanted]
        result['servers'] = [probe_server(s, components) for s in servers]
        bad = {'failed'} | ({'not_running', 'not_configured', 'not_installed'} if args.strict else set())
        if any(s['status'] in bad for s in result['servers']):
            result['status'] = 'failed'
    print(json.dumps(result, indent=2))
    return 1 if result['status'] == 'failed' else 0


if __name__ == '__main__':
    sys.exit(main())
