"""Checklist page for the apps the GameCore hub talks to over MCP.

  python tools/mcp_setup.py              # opens a local page: tick apps, see live status
  python tools/mcp_setup.py --no-browser # print the page URL instead of opening it

Each app's URL and token are found automatically (environment variables first, then the file
the app writes for local clients; see mcp_registry.discover). The page only ever sees status:
tokens stay in this process's memory and are never sent to the browser, printed or saved.
Ticked apps are remembered in .gamecore/mcp-selection.json (server ids only), which
`python tools/mcp_registry.py --probe --selected` also reads.

The page is served on 127.0.0.1 at a random port under a random per-launch path, and requests
from other origins are refused. Checks perform MCP initialize + tools/list only. Standard library only.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import secrets
import sys
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('mcp_registry', Path(__file__).with_name('mcp_registry.py'))
registry = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(registry)

SELECTION_PATH = Path('.gamecore/mcp-selection.json')


def load_ecosystem(root=ROOT):
    return json.loads((root / 'shared/ecosystem.json').read_text(encoding='utf-8'))


def load_selection(root, servers):
    """Saved ids, or every server when nothing has been saved yet."""
    ids = [s['id'] for s in servers]
    try:
        saved = json.loads((root / SELECTION_PATH).read_text(encoding='utf-8')).get('selected', [])
    except (OSError, ValueError):
        return ids
    return [i for i in saved if i in ids]


def save_selection(root, selected, servers):
    ids = {s['id'] for s in servers}
    clean = [i for i in selected if i in ids]
    path = root / SELECTION_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'selected': clean}, indent=2) + '\n', encoding='utf-8')
    return clean


def server_summary(server):
    return {
        'id': server['id'],
        'label': server.get('label', server['id']),
        'transport': server['transport'],
        'connection': server.get('connection', ''),
        'auto_discovery': bool(server.get('discovery')),
        'tools': server.get('tools', []),
        'write_tools': server.get('write_tools', []),
    }


def check(servers, components, ids):
    chosen = [s for s in servers if s['id'] in ids]
    with ThreadPoolExecutor(max_workers=max(1, len(chosen))) as pool:
        return list(pool.map(lambda s: registry.probe_server(s, components), chosen))


def make_handler(root, key):
    ecosystem = load_ecosystem(root)
    servers = ecosystem['mcp']['servers']
    components = {c['id']: c for c in ecosystem['components']}
    prefix = f'/s/{key}'

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _send(self, status, body, content_type='application/json'):
            data = body.encode('utf-8') if isinstance(body, str) else json.dumps(body).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', f'{content_type}; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'")
            self.end_headers()
            self.wfile.write(data)

        def _allowed(self):
            host = self.headers.get('Host', '')
            origin = self.headers.get('Origin')
            port = self.server.server_address[1]
            if host not in (f'127.0.0.1:{port}', f'localhost:{port}'):
                return False
            return origin is None or origin in (f'http://127.0.0.1:{port}', f'http://localhost:{port}')

        def _path(self):
            path = self.path.split('?', 1)[0]
            return path[len(prefix):] if path.startswith(prefix + '/') or path == prefix else None

        def do_GET(self):
            path = self._path()
            if path is None or not self._allowed():
                return self._send(404, {'error': 'not found'})
            if path in ('', '/'):
                return self._send(200, PAGE, 'text/html')
            if path == '/api/servers':
                return self._send(200, {'servers': [server_summary(s) for s in servers],
                                        'selected': load_selection(root, servers),
                                        'hub': ecosystem['mcp']['hub']['id']})
            return self._send(404, {'error': 'not found'})

        def do_POST(self):
            path = self._path()
            if path is None or not self._allowed():
                return self._send(404, {'error': 'not found'})
            try:
                body = json.loads(self.rfile.read(min(int(self.headers.get('Content-Length', 0)), 65536)) or b'{}')
                ids = [i for i in body.get('ids', []) if isinstance(i, str)]
            except (ValueError, AttributeError):
                return self._send(400, {'error': 'expected {"ids": [...]}'})
            if path == '/api/check':
                return self._send(200, {'results': check(servers, components, ids)})
            if path == '/api/selection':
                return self._send(200, {'selected': save_selection(root, ids, servers)})
            return self._send(404, {'error': 'not found'})

    return Handler


def serve(root=ROOT, port=0, open_browser=True):
    key = secrets.token_urlsafe(16)
    httpd = ThreadingHTTPServer(('127.0.0.1', port), make_handler(root, key))
    url = f'http://127.0.0.1:{httpd.server_address[1]}/s/{key}/'
    print(f'GameCore MCP setup: {url}\nPress Ctrl+C to stop.', flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GameCore MCP Apps</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--fg:#1b1f24;--muted:#5d6672;--line:#dde1e6;--ok:#1a7f37;--bad:#c62828;--warn:#9a6700;--idle:#6e7781;--accent:#2f5bd3}
@media (prefers-color-scheme:dark){:root{--bg:#121417;--card:#1b1e23;--fg:#e6e8eb;--muted:#9aa3ad;--line:#2c3138;--ok:#4ac26b;--bad:#ff6b6b;--warn:#d29922;--idle:#8b949e;--accent:#7aa2ff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:760px;margin:0 auto;padding:28px 16px 48px}h1{font-size:22px;margin:0 0 4px}p.lead{color:var(--muted);margin:0 0 20px}
.app{display:grid;grid-template-columns:auto 1fr auto;gap:4px 14px;align-items:start;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin-bottom:10px}
.app input{width:20px;height:20px;margin-top:2px;accent-color:var(--accent);cursor:pointer}
.name{font-weight:600}.meta{grid-column:2/4;color:var(--muted);font-size:13px}.detail{grid-column:2/4;font-size:13px}
.pill{font-size:12px;font-weight:600;padding:2px 9px;border-radius:999px;border:1px solid currentColor;white-space:nowrap}
.passed{color:var(--ok)}.failed{color:var(--bad)}.not_running,.not_configured,.not_installed{color:var(--warn)}.skipped,.checking{color:var(--idle)}
.bar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:18px 0 0}
button{font:inherit;padding:8px 16px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--fg);cursor:pointer}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff}button:disabled{opacity:.6;cursor:default}
#note{color:var(--muted);font-size:13px}
</style></head><body><main>
<h1>MCP apps for the GameCore hub</h1>
<p class="lead">Tick the apps the hub should use. Connections are found automatically; tokens never reach this page.</p>
<div id="apps"></div>
<div class="bar"><button class="primary" id="check">Check selected</button><button id="all">Select all</button><span id="note"></span></div>
</main><script>
const api = p => location.pathname.replace(/\/$/, '') + p;
const LABEL = {passed:'Connected',failed:'Missing tools',not_running:'Not running',not_configured:'Needs setup',not_installed:'Not installed',skipped:'Not used',checking:'Checking…'};
const HINT = {not_running:'Open the app, then check again.'};
let servers = [], selected = new Set();
const el = (t, c, txt) => { const e = document.createElement(t); if (c) e.className = c; if (txt != null) e.textContent = txt; return e; };
function render(results = {}) {
  const root = document.getElementById('apps'); root.replaceChildren();
  for (const s of servers) {
    const on = selected.has(s.id), r = !on ? {status: 'skipped'} : results[s.id] || {status: 'checking'};
    const row = el('label', 'app'), box = el('input'); box.type = 'checkbox'; box.checked = on;
    box.onchange = () => { box.checked ? selected.add(s.id) : selected.delete(s.id); save(); box.checked ? run([s.id]) : render(last); };
    row.append(box, el('span', 'name', s.label), el('span', 'pill ' + r.status, LABEL[r.status] || r.status));
    const n = s.write_tools.length, writes = n ? ` · ${n} write tool${n > 1 ? 's need' : ' needs'} confirmation` : '';
    row.append(el('span', 'meta', `${s.tools.length || 'discovered'} tools · ${s.auto_discovery ? 'auto-connect' : s.transport}${writes}`));
    let detail = '';
    if (r.status === 'passed') detail = `${r.server?.name || ''} ${r.server?.version || ''} · ${r.tools_found} tools available` + (r.connection_from === 'app' ? ' · connected using the app\'s saved details' : '');
    else if (r.status === 'failed') detail = r.missing_tools?.length ? 'Missing: ' + r.missing_tools.join(', ') : (r.detail || '');
    else if (r.status !== 'skipped' && r.status !== 'checking') detail = HINT[r.status] || r.detail || '';
    if (detail) row.append(el('span', 'detail', detail));
    if (r.status !== 'passed' && s.connection && on && r.status !== 'checking') row.append(el('span', 'meta', s.connection));
    root.append(row);
  }
}
let last = {};
async function run(ids) {
  ids = ids.filter(i => selected.has(i)); if (!ids.length) return render(last);
  ids.forEach(i => delete last[i]); render(last);
  const btn = document.getElementById('check'); btn.disabled = true;
  try {
    const res = await fetch(api('/api/check'), {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ids})});
    for (const r of (await res.json()).results) last[r.id] = r;
    const ok = Object.values(last).filter(r => r.status === 'passed').length;
    document.getElementById('note').textContent = `${ok} of ${selected.size} selected connected · checked ${new Date().toLocaleTimeString()}`;
  } catch (e) { document.getElementById('note').textContent = 'Check failed: is the setup script still running?'; }
  btn.disabled = false; render(last);
}
async function save() {
  await fetch(api('/api/selection'), {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ids:[...selected]})});
}
document.getElementById('check').onclick = () => run([...selected]);
document.getElementById('all').onclick = () => { servers.forEach(s => selected.add(s.id)); save(); run([...selected]); };
fetch(api('/api/servers')).then(r => r.json()).then(d => { servers = d.servers; selected = new Set(d.selected); run([...selected]); });
</script></body></html>
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--port', type=int, default=0, help='default: a free port')
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args(argv)
    serve(args.root, args.port, not args.no_browser)
    return 0


if __name__ == '__main__':
    sys.exit(main())
