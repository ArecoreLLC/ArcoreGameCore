import importlib.util
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

SCRIPT = Path(__file__).resolve().parents[1] / 'mcp_setup.py'
spec = importlib.util.spec_from_file_location('mcp_setup', SCRIPT)
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)
REPO = SCRIPT.parents[1]


class SetupPageTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        shutil.copytree(REPO / 'shared', self.root / 'shared')
        self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), setup.make_handler(self.root, 'k3y'))
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.addCleanup(self.httpd.server_close)
        self.addCleanup(self.httpd.shutdown)
        self.base = f'http://127.0.0.1:{self.httpd.server_address[1]}'

    def request(self, path, body=None, headers=None):
        data = json.dumps(body).encode('utf-8') if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, headers={'Content-Type': 'application/json', **(headers or {})})
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8')

    def test_page_and_server_list(self):
        self.assertIn('MCP apps for the GameCore hub', self.request('/s/k3y/'))
        listed = json.loads(self.request('/s/k3y/api/servers'))
        ids = [s['id'] for s in listed['servers']]
        self.assertIn('sound-core', ids)
        self.assertEqual(listed['selected'], ids)  # nothing saved yet: all ticked
        self.assertNotIn('token_env', json.dumps(listed))

    def test_selection_saved_ids_only(self):
        saved = json.loads(self.request('/s/k3y/api/selection', {'ids': ['sound-core', 'bogus']}))
        self.assertEqual(saved['selected'], ['sound-core'])
        on_disk = json.loads((self.root / '.gamecore/mcp-selection.json').read_text(encoding='utf-8'))
        self.assertEqual(on_disk, {'selected': ['sound-core']})
        self.assertEqual(json.loads(self.request('/s/k3y/api/servers'))['selected'], ['sound-core'])

    def test_check_only_probes_requested_ids(self):
        results = json.loads(self.request('/s/k3y/api/check', {'ids': ['unreal-editor']}))['results']
        self.assertEqual([r['id'] for r in results], ['unreal-editor'])
        self.assertIn(results[0]['status'], {'passed', 'failed', 'not_running'})

    def test_wrong_key_and_foreign_origin_refused(self):
        for path, headers in (('/s/wrong/api/servers', {}), ('/s/k3y/api/servers', {'Origin': 'http://evil.example'})):
            with self.assertRaises(urllib.error.HTTPError) as caught:
                self.request(path, headers=headers)
            self.assertEqual(caught.exception.code, 404)


if __name__ == '__main__':
    unittest.main()
