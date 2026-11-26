"""Run ModelForge work from a shell through the GameCore hub, and wait for it.

One command instead of a per-character run_forge.ps1 / hub.py / request-json trio:

  python forge_job.py run <model_id> <script.py> [args...] [--timeout 1800] [--save] [--out status.json]
      Queues the script in headless Blender (blender_run script_path), polls until it ends, prints the
      script's log and result. Exit code 1 when the job failed.
  python forge_job.py call <operation> <json | @file.json> [--out result.json]
      Any model_production operation (check_file, import_files, blender_review, diff_versions ...).
      Blender operations that answer with a job id are waited for.

The scripts see FORGE_PARAMS (path, args) and FORGE_RESULT as before.
"""
import argparse, json, subprocess, sys, time
from pathlib import Path

HUB = Path(__file__).resolve().parents[1] / 'hub/src-tauri/target/release/gamecore-library.exe'


def hub_call(tool, arguments, timeout=180):
    req = [{'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2024-11-05', 'capabilities': {},
                                                                          'clientInfo': {'name': 'forge-job', 'version': '1'}}},
           {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
           {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {'name': tool, 'arguments': arguments}}]
    r = subprocess.run([str(HUB), '--mcp'], input='\n'.join(map(json.dumps, req)) + '\n', text=True, capture_output=True,
                       timeout=timeout, encoding='utf-8')
    out = next((x for x in (json.loads(l) for l in r.stdout.splitlines() if l.startswith('{')) if x.get('id') == 2), None)
    if out is None:
        raise RuntimeError('no answer from the hub: ' + r.stderr[-800:])
    if 'error' in out:
        raise RuntimeError(json.dumps(out['error']))
    result = out['result']
    for c in result.get('content', []):
        if c.get('type') == 'text':
            try:
                return json.loads(c['text'])
            except ValueError:
                return {'text': c['text']}
    return result


def forge(operation, arguments):
    r = hub_call('model_production', {'operation': operation, 'arguments': arguments})
    if isinstance(r, dict) and r.get('error'):
        raise RuntimeError(json.dumps(r['error']))
    return r.get('result', r) if isinstance(r, dict) else r


def wait(job, timeout):
    """Polls a Blender job until it is no longer queued or running. Returns the finished job's result with
    status 'done' added, or {'status': 'failed', 'error': ...}: ModelForge answers a failed job with an error."""
    started = time.time()
    while True:
        try:
            st = forge('blender_status', {'job_id': job})
        except RuntimeError as e:
            try:
                return {'status': 'failed', 'job_id': job, 'error': json.loads(str(e))}
            except ValueError:
                return {'status': 'failed', 'job_id': job, 'error': str(e)}
        if st.get('status') not in ('queued', 'running'):
            st.setdefault('status', 'done')
            return st
        if time.time() - started > timeout + 90:
            raise RuntimeError(f'gave up waiting for job {job}')
        time.sleep(3)


def finish(r, timeout):
    if isinstance(r, dict) and r.get('job_id') and r.get('status') in ('queued', 'running'):
        print('job', r['job_id'], flush=True)
        r = wait(r['job_id'], timeout)
    return r


def report(st, out):
    if out:
        Path(out).write_text(json.dumps(st, indent=2), encoding='utf-8')
    status = st.get('status', 'done')
    print('status', status, *(('after', st['elapsed_seconds'], 's') if st.get('elapsed_seconds') is not None else ()))
    inner = st
    for line in (inner.get('log') or [])[-80:]:
        print(line)
    if inner.get('stdout'):                      # what the script printed (scripts written before log() existed)
        print(str(inner['stdout'])[-3000:].rstrip())
    for w in inner.get('warnings') or []:
        print('warning:', w)
    if st.get('error'):
        e = st['error']
        print('error:', (e if isinstance(e, str) else json.dumps(e, indent=1))[-6000:])
    if inner.get('result'):
        print('result:', json.dumps(inner['result'])[:4000])
    return 0 if status in ('done', 'passed', 'finished', 'succeeded') and not st.get('error') else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    run = sub.add_parser('run')
    run.add_argument('model_id'); run.add_argument('script'); run.add_argument('args', nargs='*')
    run.add_argument('--timeout', type=int, default=1800); run.add_argument('--save', action='store_true'); run.add_argument('--out')
    call = sub.add_parser('call')
    call.add_argument('operation'); call.add_argument('arguments'); call.add_argument('--timeout', type=int, default=1800); call.add_argument('--out')
    a = ap.parse_args()
    if a.cmd == 'run':
        r = forge('blender_run', {'model_id': a.model_id, 'script_path': str(Path(a.script).resolve()), 'args': a.args, 'save': a.save,
                                  'wait_seconds': 0, 'timeout_seconds': a.timeout})
        sys.exit(report(finish(r, a.timeout), a.out))
    text = Path(a.arguments[1:]).read_text(encoding='utf-8-sig') if a.arguments.startswith('@') else a.arguments
    r = finish(forge(a.operation, json.loads(text)), a.timeout)
    if a.out:
        Path(a.out).write_text(json.dumps(r, indent=2), encoding='utf-8')
    if isinstance(r, dict) and r.get('status') == 'failed':
        sys.exit(report(r, None))
    if isinstance(r, dict) and 'changes' in r:          # a Blender job: the per-object change list is long and rarely wanted
        r = {k: v for k, v in r.items() if k != 'changes'}
    print(json.dumps(r, indent=1))


if __name__ == '__main__':
    main()
