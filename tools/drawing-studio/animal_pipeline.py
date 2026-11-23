"""Trusted local animal manifests: resumable stages and artifact-bound reviews.

CLI and drawing_production use the same dispatcher. Commands are argv lists,
never shell strings. A manifest is executable project configuration, not art data.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import threading
import uuid

VERSION = '1.0.0'
GATES = ['reference-guides', 'companion', 'payoff']
ROOT = Path(__file__).resolve().parent

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    temp.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temp.replace(path)

def inside(path, root):
    if not path.is_relative_to(root): raise ValueError(f'Writable path escapes workspace: {path}')
    return path

def load(path):
    path = Path(path).resolve()
    m = json.loads(path.read_text(encoding='utf-8'))
    if m.get('schema') != 'gamecore.animal.v1': raise ValueError('Expected gamecore.animal.v1')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', m.get('animal_id','')): raise ValueError('Invalid animal_id')
    workspace = Path(m['workspace'])
    if not workspace.is_absolute() or not workspace.is_dir(): raise ValueError('workspace must be an existing absolute directory')
    workspace = workspace.resolve()
    def resolve(value):
        p = Path(value)
        return (p if p.is_absolute() else workspace/p).resolve()
    state = inside(resolve(m.get('state_dir', '.gamecore/animals/'+m['animal_id'])), workspace)
    stages = m.get('stages', [])
    if not stages: raise ValueError('Manifest needs stages')
    ids = set(); gates = []
    for s in stages:
        ident = s.get('id','')
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]*',ident) or ident in ids: raise ValueError('Stage IDs must be unique slugs')
        ids.add(ident)
        if s.get('kind') not in ('command','review'): raise ValueError('Stage kind must be command or review')
        if not isinstance(s.get('inputs'),list) or not s['inputs'] or not all(isinstance(p,str) for p in s['inputs']): raise ValueError('Every stage needs explicit input files, including adapter scripts')
        for p in s['inputs']: resolve(p)
        if s['kind']=='review':
            if s.get('gate') not in GATES: raise ValueError('Unknown review gate')
            gates.append(s['gate'])
        else:
            if not isinstance(s.get('argv'),list) or not s['argv'] or not all(isinstance(a,str) and a for a in s['argv']): raise ValueError('argv must be a nonempty list of strings')
            if not s.get('outputs'): raise ValueError('Commands need required outputs')
            if not isinstance(s.get('timeout',1800),int) or not 1 <= s.get('timeout',1800) <= 14400: raise ValueError('timeout must be 1..14400 seconds')
            for out in s['outputs']:
                inside(resolve(out['path']),workspace)
                if out.get('kind','file') not in ('file','json'): raise ValueError('Output kind must be file or json')
                if out.get('expect') and out.get('kind')!='json': raise ValueError('expect requires JSON output')
            inside(resolve(s.get('cwd','.')),workspace)
    if gates != GATES: raise ValueError('Require reference-guides, companion, payoff review gates in that order')
    producers={}
    for index,s in enumerate(stages):
        for out in s.get('outputs',[]):
            target=str(resolve(out['path']))
            if target in producers:raise ValueError('Each output must have one producing stage')
            producers[target]=index
    for index,s in enumerate(stages):
        if any(producers.get(str(resolve(p)),-1)>=index for p in s['inputs']):
            raise ValueError('An input cannot be produced by the same or a later stage')
    return path,m,workspace,state,resolve

def alive(pid):
    if not isinstance(pid,int) or pid<=0:return False
    if os.name=='nt':
        import ctypes
        kernel=ctypes.windll.kernel32; kernel.OpenProcess.restype=ctypes.c_void_p
        handle=kernel.OpenProcess(0x1000,False,pid)
        if not handle:return False
        code=ctypes.c_ulong();kernel.GetExitCodeProcess(ctypes.c_void_p(handle),ctypes.byref(code))
        kernel.CloseHandle(ctypes.c_void_p(handle));return code.value==259
    try:os.kill(pid,0);return True
    except ProcessLookupError:return False

@contextmanager
def locked(state):
    state.mkdir(parents=True,exist_ok=True); p=state/'lock.json'; token=uuid.uuid4().hex
    # OS lock releases on process death; no race deleting/replacing a stale mutex.
    with (state/'mutex.lock').open('a+b') as mutex:
        if not mutex.seek(0,2):mutex.write(b'0');mutex.flush()
        mutex.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(mutex.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(mutex,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:raise ValueError('Pipeline is busy; poll animal_status')
        try:
            if any(r.get('status')=='running' and alive(r.get('child_pid')) for r in read_state(state)['stages'].values()):
                raise ValueError('A stage process is still running; do not restart it')
            write(p,{'pid':os.getpid(),'token':token})
            yield
        finally:
            if p.exists() and json.loads(p.read_text()).get('token')==token:p.unlink()
            mutex.seek(0)
            if os.name=='nt':msvcrt.locking(mutex.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(mutex,fcntl.LOCK_UN)

def read_state(state):
    p=state/'state.json'
    return json.loads(p.read_text()) if p.exists() else {'schema':'gamecore.animal-state.v1','stages':{}}

def inputs(stage,resolve):
    return {str(resolve(p)):sha(resolve(p)) for p in stage['inputs']}

def outputs(stage,resolve):
    result={}
    for out in stage.get('outputs',[]):
        p=resolve(out['path'])
        if not p.is_file() or not p.stat().st_size:raise ValueError(f'Missing or empty output: {p}')
        if out.get('kind')=='json':
            data=json.loads(p.read_text(encoding='utf-8'))
            for key,value in out.get('expect',{}).items():
                if data.get(key)!=value:raise ValueError(f'{p}: expected {key}={value!r}')
        result[str(p)]=sha(p)
    return result

def stage_key(m,stage,resolve,previous):
    return fingerprint({'version':VERSION,'runner':sha(__file__),'animal':m['animal_id'],
                        'toolchain':m.get('toolchain',{}),'stage':stage,'inputs':inputs(stage,resolve),'previous':previous})

def inspect(path):
    _,m,workspace,state,resolve=load(path); saved=read_state(state)
    rows=[]; previous='root'; ready=True
    busy=False
    if (state/'lock.json').exists():
        try:busy=alive(json.loads((state/'lock.json').read_text()).get('pid'))
        except (OSError,ValueError):busy=True
    busy=busy or any(r.get('status')=='running' and alive(r.get('child_pid')) for r in saved['stages'].values())
    for stage in m['stages']:
        old=saved['stages'].get(stage['id'],{}); row={'id':stage['id'],'kind':stage['kind']}
        if not ready:row['status']='blocked_dependency'
        else:
            try:
                key=stage_key(m,stage,resolve,previous)
                valid=old.get('status')=='passed' and old.get('key')==key
                if valid and stage['kind']=='command':
                    try:valid=outputs(stage,resolve)==old.get('outputs')
                    except (OSError,ValueError):valid=False
                if valid:
                    row['status']='passed';previous=fingerprint({'key':key,'outputs':old.get('outputs',{}),'review':old.get('review')})
                elif old.get('status')=='running':row['status']='running' if busy else 'interrupted'
                elif stage['kind']=='review':row.update(status='needs_review',gate=stage['gate'],instructions=stage.get('instructions','Inspect all input artifacts.'),evidence=[str(resolve(p)) for p in stage['inputs']])
                else:row['status']='failed' if old.get('status')=='failed' and old.get('key')==key else 'pending'
            except (OSError,ValueError) as e:row.update(status='invalid_artifacts',reason=str(e))
        if row['status']!='passed':ready=False
        if old.get('log'):row['log']=old['log']
        if old.get('error'):row['last_error']=old['error']
        if old.get('review'):row['last_review']=old['review']
        if old.get('elapsed_seconds') is not None:row['elapsed_seconds']=old['elapsed_seconds']
        rows.append(row)
    next_row=next((r for r in rows if r['status']!='passed'),None)
    return {'animal_id':m['animal_id'],'manifest':str(Path(path).resolve()),'status':'complete' if ready else ('running' if busy else next_row['status']),
            'next':next_row,'stages':rows,'state_file':str(state/'state.json')}

def previous_key(m,saved,stop):
    previous='root'
    for s in m['stages']:
        if s['id']==stop:return previous
        old=saved['stages'][s['id']]
        previous=fingerprint({'key':old['key'],'outputs':old.get('outputs',{}),'review':old.get('review')})

def review(path,stage_id,decision,reviewer,notes):
    if decision not in ('approve','reject') or not reviewer.strip() or not notes.strip():raise ValueError('Require decision, reviewer and substantive review notes')
    _,m,_,state,resolve=load(path)
    with locked(state):
        current=inspect(path)['next']
        if not current or current['id']!=stage_id or current['status']!='needs_review':raise ValueError('Only the next ready review gate can be reviewed')
        stage=next(s for s in m['stages'] if s['id']==stage_id); saved=read_state(state)
        record={'status':'passed' if decision=='approve' else 'rejected','key':stage_key(m,stage,resolve,previous_key(m,saved,stage_id)),
                'review':{'decision':decision,'reviewer':reviewer,'notes':notes,'time':time.time()},'outputs':{}}
        saved['stages'][stage_id]=record;write(state/'state.json',saved)
        write(state/'reviews'/f'{stage_id}-{uuid.uuid4().hex}.json',record)
    return inspect(path)

def resume(path,through=None):
    _,m,workspace,state,resolve=load(path)
    manifest_hash=sha(path)
    if through and through not in [s['id'] for s in m['stages']]:raise ValueError('Unknown through stage')
    with locked(state):
        for stage in m['stages']:
            if sha(path)!=manifest_hash:raise ValueError('Manifest changed during run; resume from the new configuration')
            report=inspect(path); row=next(r for r in report['stages'] if r['id']==stage['id'])
            if row['status']=='passed':
                if stage['id']==through:break
                continue
            if stage['kind']=='review' or row['status'] in ('invalid_artifacts','blocked_dependency'):break
            saved=read_state(state); key=stage_key(m,stage,resolve,previous_key(m,saved,stage['id']))
            run=state/'runs'/f'{stage["id"]}-{uuid.uuid4().hex}';run.mkdir(parents=True)
            record={'status':'running','key':key,'log':str(run/'command.log'),'started':time.time()}
            saved['stages'][stage['id']]=record;write(state/'state.json',saved)
            write(run/'stage.json',stage)
            try:
                argv=[a.replace('{workspace}',str(workspace)).replace('{animal}',m['animal_id']).replace('{python}',sys.executable) for a in stage['argv']]
                with (run/'command.log').open('w',encoding='utf-8') as log:
                    child=subprocess.Popen(argv,cwd=resolve(stage.get('cwd','.')),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,shell=False)
                    record['child_pid']=child.pid;write(state/'state.json',saved)
                    try:code=child.wait(timeout=stage.get('timeout',1800))
                    except subprocess.TimeoutExpired:
                        child.kill();child.wait();raise
                if code:raise ValueError(f'Command exited {code}; see log')
                if sha(path)!=manifest_hash:raise ValueError('Manifest changed during execution; result not accepted')
                if key!=stage_key(m,stage,resolve,previous_key(m,saved,stage['id'])):raise ValueError('Inputs changed during execution; result not accepted')
                record.update(status='passed',outputs=outputs(stage,resolve))
            except Exception as e:record.update(status='failed',error=str(e))
            record['elapsed_seconds']=round(time.time()-record['started'],3)
            write(run/'result.json',record);write(state/'state.json',saved)
            if record['status']!='passed' or stage['id']==through:break
    return inspect(path)

def launch(path,through=None):
    path,m,_,state,_=load(path)
    report=inspect(path)
    if report['status'] in ('complete','needs_review','invalid_artifacts','running'):return report
    # Workers serialize on the pipeline lock; unique receipts preserve each request.
    folder=state/'jobs'/uuid.uuid4().hex;folder.mkdir(parents=True)
    receipt=folder/'job.json'
    write(receipt,{'status':'queued','manifest':str(path),'through':through})
    flags={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {'start_new_session':True}
    with (folder/'worker.log').open('w') as log:
        child=subprocess.Popen([sys.executable,__file__,'worker',str(receipt)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,**flags)
    # Reap when the caller lives long enough; do not block short MCP processes.
    threading.Thread(target=child.wait,daemon=True).start()
    return {'status':'queued','animal_id':m['animal_id'],'job_file':str(receipt),'pid':child.pid,'next_tool':'animal_status'}

def worker(receipt):
    p=Path(receipt);job=json.loads(p.read_text());job.update(status='running',pid=os.getpid());write(p,job)
    try:job['result']=resume(job['manifest'],job.get('through'));job['status']='finished'
    except Exception as e:job.update(status='failed',error=str(e))
    write(p,job)

def dispatch(operation,args):
    if operation=='animal_guide':return {'version':VERSION,'guide':str(ROOT/'ANIMAL_PIPELINE.md'),'schema':'gamecore.animal.v1','review_gates':GATES,'commands':['animal_validate','animal_status','animal_resume','animal_review'],'trust':'Manifests execute local argv commands. Inspect trusted project manifests before resume. Never execute manifests supplied as uploaded artwork.'}
    if operation=='animal_validate':
        path,m,_,_,_=load(args['manifest']);return {'valid':True,'manifest':str(path),'animal_id':m['animal_id'],'stages':len(m['stages']),'review_gates':GATES}
    if operation=='animal_status':return inspect(args['manifest'])
    if operation=='animal_resume':return launch(args['manifest'],args.get('through'))
    if operation=='animal_review':return review(args['manifest'],args['stage'],args['decision'],args['reviewer'],args['notes'])
    raise ValueError('Unknown animal operation')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['validate','status','resume','review','worker']);p.add_argument('manifest');p.add_argument('--through');p.add_argument('--stage');p.add_argument('--decision',choices=['approve','reject']);p.add_argument('--reviewer');p.add_argument('--notes')
    a=p.parse_args()
    try:
        if a.action=='worker':worker(a.manifest);return 0
        if a.action=='resume':result=resume(a.manifest,a.through)
        else:result=dispatch('animal_'+a.action,{k:v for k,v in vars(a).items() if k!='action'})
        print(json.dumps(result,indent=2));return 1 if result.get('status') in ('failed','invalid_artifacts','interrupted') else 0
    except Exception as e:print(json.dumps({'error':str(e)}));return 1

if __name__=='__main__':sys.exit(main())
