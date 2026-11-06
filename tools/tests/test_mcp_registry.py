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


if __name__ == '__main__':
    unittest.main()
