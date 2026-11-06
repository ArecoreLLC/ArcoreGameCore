import copy
import importlib.util
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'mcp_registry.py'
spec = importlib.util.spec_from_file_location('mcp_registry', SCRIPT)
registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(registry)

ECOSYSTEM = json.loads((SCRIPT.parents[1] / 'shared/ecosystem.json').read_text(encoding='utf-8'))
TOOLS = ['list_categories', 'search_sounds', 'get_sound', 'collect_sounds']


def make_handler(token, sse=False, tools=TOOLS):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            if self.headers.get('Authorization') != f'Bearer {token}':
                self.send_response(401)
                self.end_headers()
                return
            message = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            if 'id' not in message:
                self.send_response(202)
                self.end_headers()
                return
            if message['method'] == 'initialize':
                result = {'protocolVersion': registry.PROTOCOL_VERSION, 'capabilities': {'tools': {}},
                          'serverInfo': {'name': 'fake-soundcore', 'version': '1'}}
            else:
                assert self.headers.get('Mcp-Session-Id') == 'session-1'
                result = {'tools': [{'name': n, 'inputSchema': {'type': 'object'}} for n in tools]}
            body = json.dumps({'jsonrpc': '2.0', 'id': message['id'], 'result': result})
            if sse:
                body = f'event: message\ndata: {body}\n\n'
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream' if sse else 'application/json')
            self.send_header('Mcp-Session-Id', 'session-1')
            self.end_headers()
            self.wfile.write(body.encode('utf-8'))
    return Handler


class FakeServer:
    def __init__(self, **kwargs):
        self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(**kwargs))
        self.url = f'http://127.0.0.1:{self.httpd.server_address[1]}/mcp'

    def __enter__(self):
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()


def sound_core():
    return copy.deepcopy(next(s for s in ECOSYSTEM['mcp']['servers'] if s['id'] == 'sound-core'))


class RegistryStructureTests(unittest.TestCase):
    def test_repository_registry_is_valid(self):
        self.assertEqual(registry.check_registry(ECOSYSTEM), [])

    def mutated(self, change):
        data = copy.deepcopy(ECOSYSTEM)
        change(data)
        return registry.check_registry(data)

    def test_hub_is_required(self):
        self.assertTrue(any('mcp.hub' in e for e in self.mutated(lambda d: d['mcp'].pop('hub'))))

    def test_inline_tokens_rejected(self):
        errors = self.mutated(lambda d: d['mcp']['servers'][1]['auth'].update(token='abc123'))
        self.assertTrue(any('not contain credentials' in e for e in errors))

    def test_http_servers_must_be_loopback(self):
        errors = self.mutated(lambda d: d['mcp']['servers'][0].update(url='http://example.com/mcp'))
        self.assertTrue(any('loopback' in e for e in errors))

    def test_write_tools_must_be_declared_tools(self):
        errors = self.mutated(lambda d: d['mcp']['servers'][0]['write_tools'].append('format_disk'))
        self.assertTrue(any('write_tools not in tools' in e for e in errors))

    def test_server_component_must_exist(self):
        errors = self.mutated(lambda d: d['mcp']['servers'][0].update(component='nowhere'))
        self.assertTrue(any('is not in components' in e for e in errors))


class ProbeTests(unittest.TestCase):
    components = {c['id']: c for c in ECOSYSTEM['components']}

    def probe(self, server, env):
        return registry.probe_server(server, self.components, env)

    def test_http_probe_passes_with_json_and_sse(self):
        for sse in (False, True):
            with FakeServer(token='t0k', sse=sse) as fake:
                env = {'ARCORE_MCP_URL_SOUND_CORE': fake.url, 'ARCORE_MCP_TOKEN_SOUND_CORE': 't0k'}
                result = self.probe(sound_core(), env)
                self.assertEqual(result['status'], 'passed', result)
                self.assertEqual(result['tools_found'], 4)

    def test_missing_tool_fails(self):
        with FakeServer(token='t0k', tools=TOOLS[:2]) as fake:
            env = {'ARCORE_MCP_URL_SOUND_CORE': fake.url, 'ARCORE_MCP_TOKEN_SOUND_CORE': 't0k'}
            result = self.probe(sound_core(), env)
            self.assertEqual(result['status'], 'failed')
            self.assertEqual(result['missing_tools'], ['get_sound', 'collect_sounds'])

    def test_unconfigured_and_unreachable(self):
        self.assertEqual(self.probe(sound_core(), {})['status'], 'not_configured')
        env = {'ARCORE_MCP_URL_SOUND_CORE': 'http://127.0.0.1:9/mcp', 'ARCORE_MCP_TOKEN_SOUND_CORE': 'x'}
        self.assertEqual(self.probe(sound_core(), env)['status'], 'not_running')

    def test_stdio_probe(self):
        with tempfile.TemporaryDirectory() as temp:
            script = Path(temp) / 'fake_mcp.py'
            script.write_text(
                'import json, sys\n'
                'for line in sys.stdin:\n'
                '    m = json.loads(line)\n'
                '    if "id" not in m: continue\n'
                '    r = {"protocolVersion": "2025-06-18", "serverInfo": {"name": "fake"}} if m["method"] == "initialize" '
                'else {"tools": [{"name": "list_nodes"}]}\n'
                '    print(json.dumps({"jsonrpc": "2.0", "id": m["id"], "result": r}), flush=True)\n',
                encoding='utf-8')
            info, tools = registry.probe_stdio([sys.executable, str(script)], temp, None)
            self.assertEqual(info['serverInfo']['name'], 'fake')
            self.assertEqual([t['name'] for t in tools], ['list_nodes'])


def model_forge():
    return copy.deepcopy(next(s for s in ECOSYSTEM['mcp']['servers'] if s['id'] == 'model-forge'))


class DiscoveryTests(unittest.TestCase):
    """Connection details read from the file each app writes for local clients."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)

    def server(self, data, enabled_key=None):
        (self.dir / 'service.json').write_text(json.dumps(data), encoding='utf-8')
        server = sound_core()
        server['discovery'] = {'file': '%FAKEDATA%/service.json', 'url': '{url}/mcp', 'token_key': 'token'}
        if enabled_key:
            server['discovery']['enabled_key'] = enabled_key
        return server

    def env(self, **extra):
        return {'FAKEDATA': str(self.dir), **extra}

    def test_probe_connects_from_app_file(self):
        with FakeServer(token='app-token-123') as fake:
            server = self.server({'url': fake.url[:-len('/mcp')], 'token': 'app-token-123'})
            result = registry.probe_server(server, ProbeTests.components, self.env())
            self.assertEqual(result['status'], 'passed', result)
            self.assertEqual(result['connection_from'], 'app')
            self.assertNotIn('app-token-123', json.dumps(result))

    def test_environment_overrides_app_file(self):
        with FakeServer(token='env-token') as fake:
            server = self.server({'url': 'http://127.0.0.1:9', 'token': 'stale'})
            env = self.env(ARCORE_MCP_URL_SOUND_CORE=fake.url, ARCORE_MCP_TOKEN_SOUND_CORE='env-token')
            result = registry.probe_server(server, ProbeTests.components, env)
            self.assertEqual(result['status'], 'passed', result)
            self.assertEqual(result['connection_from'], 'environment')

    def test_missing_file_is_not_configured(self):
        server = sound_core()
        server['discovery']['file'] = str(self.dir / 'absent.json')
        result = registry.probe_server(server, ProbeTests.components, {})
        self.assertEqual(result['status'], 'not_configured')
        self.assertIn('open the app once', result['detail'])

    def test_disabled_agent_api_reported(self):
        server = self.server({'url': 'http://127.0.0.1:1', 'token': 'x', 'on': False}, enabled_key='on')
        self.assertEqual(registry.discover(server, self.env())[2], 'the app has its agent API turned off')

    def test_non_loopback_url_refused(self):
        server = self.server({'url': 'http://evil.example', 'token': 'x'})
        self.assertIn('non-loopback', registry.discover(server, self.env())[2])

    def test_model_forge_port_template(self):
        (self.dir / 'settings.json').write_text(json.dumps(
            {'agentEnabled': True, 'agentPort': 7879, 'agentToken': 'abc'}), encoding='utf-8')
        server = model_forge()
        server['discovery']['file'] = '%FAKEDATA%/settings.json'
        self.assertEqual(registry.discover(server, self.env()), ('http://127.0.0.1:7879/mcp', 'abc', None))

    def test_registry_rejects_incomplete_discovery(self):
        data = copy.deepcopy(ECOSYSTEM)
        del data['mcp']['servers'][0]['discovery']['token_key']
        self.assertTrue(any('discovery needs' in e for e in registry.check_registry(data)))


if __name__ == '__main__':
    unittest.main()
