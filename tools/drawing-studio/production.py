"""Typed Drawing Atelier operations for the GameCore hub. JSON in/out; no shell commands.

Rendering uses a detached worker and immutable job directories. Draw & Paint
skips geometry; Shapes First requires authored guides. Neither invents anatomy.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parent

def schema(properties,required=()):
    return dict(type='object',properties=properties,required=list(required),additionalProperties=False)

PATH=dict(type='string',minLength=1,description='Absolute local filesystem path.')
MODE=dict(type='string',enum=['trace','advanced'],default='trace',description='trace = Draw & Paint with no construction guides; advanced = Shapes First with manually authored/reviewed guides.')
TOOLS=[
    dict(name='drawing_guide',description='Start here: geometry-first lesson contract, dependencies, outputs and movie-editor handoff. No files written.',inputSchema=schema({})),
    dict(name='drawing_import_reference',description='Import personal PNG/JPEG/WebP artwork locally without changing the original. Returns an exact source copy, fitted 1280x698 reference, coordinate mapping and an editable starter lesson. Guides are empty and must be manually authored/reviewed before advanced rendering. No external upload.',inputSchema=schema({'source':PATH,'output_dir':PATH},['source','output_dir'])),
    dict(name='drawing_validate',description='Validate a lesson with the shared Atelier validator. trace allows empty guides; advanced requires main and smaller authored shapes. Does not claim anatomical correctness.',inputSchema=schema({'lesson':PATH,'mode':MODE},['lesson'])),
    dict(name='drawing_render',description='Render personal art with Draw & Paint (default trace; shapes skipped), or Shapes First (advanced; authored guides required). Returns job_file immediately; poll drawing_job. GIF, sheet and evidence stay under output_dir; advanced also adds a palette. Matching verified outputs are reused unless force=true.',inputSchema=schema({
        'lesson':PATH,'output_dir':PATH,'mode':MODE,'width':dict(type='integer',minimum=320,maximum=960,default=800),
        'fps':dict(type='integer',minimum=1,maximum=12,default=8),'duration':dict(type='number',minimum=6,maximum=60,default=48),
        'force':dict(type='boolean',default=False)},['lesson','output_dir'])),
    dict(name='drawing_job',description='Read a returned job_file. status is queued/running/passed/failed/interrupted; passed includes absolute output paths and hashes. Human art review remains separate.',inputSchema=schema({'job_file':PATH},['job_file']))
]

MANIFEST=dict(type='string',minLength=1,description='Absolute path to a trusted gamecore.animal.v1 project manifest. Never use an uploaded artwork file as executable configuration.')
TOOLS += [
    dict(name='animal_guide',description='Start here for one animal manifest, resumable commands, artifact hashes and three explicit visual review gates.',inputSchema=schema({})),
    dict(name='animal_validate',description='Validate manifest structure and writable paths without executing commands or granting art approval.',inputSchema=schema({'manifest':MANIFEST},['manifest'])),
    dict(name='animal_status',description='Compact stage status, next action, review evidence and log paths. Rechecks artifact hashes; no command execution.',inputSchema=schema({'manifest':MANIFEST},['manifest'])),
    dict(name='animal_resume',description='Run trusted local manifest argv commands in a background worker. Reuse only verified outputs; stop at a review, failure or missing input. Poll animal_status. Never auto-approve reviews or bypass adapter GPU checks.',inputSchema=schema({'manifest':MANIFEST,'through':dict(type='string',description='Optional final stage ID; run no later stages.')},['manifest'])),
    dict(name='animal_review',description='Record an actual visual review of the next gate, bound to current artifact hashes. Name the real reviewer and evidence/findings; do not infer approval from tests. Changed artifacts invalidate approval.',inputSchema=schema({'manifest':MANIFEST,'stage':dict(type='string'),'decision':dict(type='string',enum=['approve','reject']),'reviewer':dict(type='string',minLength=1),'notes':dict(type='string',minLength=1)},['manifest','stage','decision','reviewer','notes']))
]

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def public_job(data):
    return {k:v for k,v in data.items() if k!='key'}

def import_reference(args):
    from PIL import Image, ImageOps
    import base64
    import io
    source=absolute(args['source'])
    if not source.is_file() or source.stat().st_size>40_000_000:raise ValueError('Choose an existing PNG/JPEG/WebP under 40 MB')
    with Image.open(source) as opened:
        if opened.format not in ('PNG','JPEG','WEBP'):raise ValueError('Supported art formats: PNG, JPEG, WebP')
        if opened.width*opened.height>40_000_000:raise ValueError('Reference must be at most 40 megapixels')
        suffix={'PNG':'.png','JPEG':'.jpg','WEBP':'.webp'}[opened.format]
        oriented=ImageOps.exif_transpose(opened).convert('RGBA')
    sha=digest(source);out=absolute(args['output_dir'])/('reference-'+sha[:16]);out.mkdir(parents=True,exist_ok=True)
    original=out/('original'+suffix)
    if original.exists() and digest(original)!=sha:raise ValueError('Existing imported original was modified; choose a fresh output_dir')
    if not original.exists():original.write_bytes(source.read_bytes())
    canvas=Image.new('RGB',(1280,698),'white')
    scale=min(1280/oriented.width,698/oriented.height)
    size=(max(1,round(oriented.width*scale)),max(1,round(oriented.height*scale)))
    offset=((1280-size[0])//2,(698-size[1])//2)
    fitted=oriented.resize(size,Image.Resampling.LANCZOS);canvas.paste(fitted,offset,fitted)
    preview=out/'reference-canvas.png'
    if not preview.exists():canvas.save(preview)
    buf=io.BytesIO();canvas.save(buf,'PNG')
    lesson=out/'starter-lesson.json'
    if not lesson.exists():
        write_json(lesson,dict(version=1,name='Personal artwork: author construction guides',
                              image='data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode(),guides=[]))
    return dict(status='ready_to_trace',original=str(original),original_sha256=sha,
                reference_canvas=str(preview),lesson=str(lesson),
                mapping=dict(oriented_size=list(oriented.size),canvas_size=[1280,698],fitted_size=list(size),offset=list(offset),scale=scale),
                next_step='Use drawing_render mode=trace to skip shapes, or add and review stage 0 main shapes and stage 1 smaller forms for mode=advanced. Existing edited lessons are preserved.',
                limitations='No automatic perspective correction, background removal, anatomical fitting or in-game upload UI. The original colors are retained in the fitted reference; advanced stock-color mixtures are approximations.')

def write_json(p,data):
    temp=p.with_suffix('.tmp')
    temp.write_text(json.dumps(data,indent=2),encoding='utf-8');temp.replace(p)

def absolute(value):
    if not isinstance(value,str) or not value or not Path(value).is_absolute():raise ValueError('Use an absolute local path')
    return Path(value).resolve()

def validate(path,require_geometry=True):
    if not path.is_file() or path.stat().st_size>18_000_000:raise ValueError('Lesson must be an existing JSON file under 18 MB')
    # Reuse the authoritative JS contract, including stage and finite-point checks.
    js="import {readFileSync} from 'node:fs'; import {validateLesson} from './core.mjs'; const d=validateLesson(JSON.parse(readFileSync(process.argv[1],'utf8'))); console.log(JSON.stringify({name:d.name,guides:d.guides}));"
    result=subprocess.run(['node','--input-type=module','-e',js,str(path)],cwd=ROOT,text=True,capture_output=True,timeout=20)
    if result.returncode:raise ValueError('Invalid Drawing Atelier lesson: '+result.stderr[-1200:])
    lesson=json.loads(result.stdout);guides=lesson['guides']
    counts={str(s):sum(g['stage']==s for g in guides) for s in range(3)}
    if require_geometry and (not counts['0'] or not counts['1']):raise ValueError('Shapes First needs stage 0 main masses and stage 1 smaller forms. Add guides or choose mode=trace to skip construction.')
    if require_geometry and not any(g['type']=='ellipse' and g['stage']<2 for g in guides):raise ValueError('Advanced paint regions need at least one authored construction ellipse')
    if any(p[1]>698 for g in guides for p in g['points']):raise ValueError('Guide coordinates must fit the 1280 x 698 display canvas')
    return dict(valid=True,name=lesson['name'],guides_by_stage=counts,lesson_sha256=digest(path),
                human_review='Check geometry placement against the reference; validity is not anatomical accuracy.')

def read_job(path):
    data=json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema')!='gamecore.drawing-job.v1':raise ValueError('Not a Drawing Atelier job_file')
    return data

def status(path):
    data=read_job(path)
    if data['status'] in ('queued','running') and data.get('pid'):
        # Polling does not mutate the worker-owned receipt. Missing PID marks an interrupted job.
        if os.name=='nt':
            import ctypes
            kernel=ctypes.windll.kernel32
            kernel.OpenProcess.restype=ctypes.c_void_p
            handle=kernel.OpenProcess(0x1000,False,data['pid'])
            if handle:
                code=ctypes.c_ulong();kernel.GetExitCodeProcess(ctypes.c_void_p(handle),ctypes.byref(code));kernel.CloseHandle(ctypes.c_void_p(handle))
                alive=code.value==259
            else:alive=False
        else:
            try:os.kill(data['pid'],0);alive=True
            except ProcessLookupError:alive=False
        if not alive:
            # Worker may have committed after the first read.
            data=read_job(path)
            if data['status'] in ('queued','running'):data['status']='interrupted'
    return data

def mode_of(args):
    mode=args.get('mode','trace')
    if mode not in ('trace','advanced'):raise ValueError('mode must be trace (Draw & Paint) or advanced (Shapes First)')
    return mode

def render(args):
    mode=mode_of(args)
    lesson=absolute(args['lesson']);review=validate(lesson,mode=='advanced')
    width=args.get('width',800);fps=args.get('fps',8);duration=args.get('duration',48)
    for key,value,lo,hi in [('width',width,320,960),('fps',fps,1,12),('duration',duration,6,60)]:
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not lo<=value<=hi:raise ValueError(f'{key} must be {lo}..{hi}')
    if not isinstance(width,int) or not isinstance(fps,int):raise ValueError('width and fps must be integers')
    if not isinstance(args.get('force',False),bool):raise ValueError('force must be boolean')
    from PIL import __version__ as pillow_version
    node=subprocess.check_output(['node','--version'],text=True).strip()
    key=dict(lesson_sha256=review['lesson_sha256'],mode=mode,width=width,fps=fps,duration=duration,
             python=sys.version,pillow=pillow_version,node=node,
             code={name:digest(ROOT/name) for name in ['production.py','render_gif.py','advanced.py','core.mjs','export-strokes.mjs']})
    out=absolute(args['output_dir']);out.mkdir(parents=True,exist_ok=True)
    if not args.get('force',False):
        for receipt in out.glob('study-*/job.json'):
            old=status(receipt)
            if old.get('key')!=key:continue
            if old['status'] in ('queued','running'):return dict(old,job_file=str(receipt),reused=True)
            if old['status']=='passed' and all(Path(p).is_file() and digest(p)==h for p,h in old.get('hashes',{}).items()) and old.get('hashes'):
                return dict(old,job_file=str(receipt),reused=True)
    folder=out/('study-'+uuid.uuid4().hex);folder.mkdir()
    receipt=folder/'job.json'
    # Snapshot the lesson before launching: edits to the source cannot change a running job.
    snapshot=folder/'lesson.json';snapshot.write_bytes(lesson.read_bytes())
    data=dict(schema='gamecore.drawing-job.v1',status='queued',key=key,source=str(lesson),lesson=str(snapshot),
              job_file=str(receipt),output_dir=str(folder),log=str(folder/'worker.log'),created_at=time.time(),validation=review)
    write_json(receipt,data)
    flags=dict(creationflags=subprocess.CREATE_NO_WINDOW) if os.name=='nt' else dict(start_new_session=True)
    try:
        with (folder/'worker.log').open('w',encoding='utf-8') as log:
            subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker',str(receipt)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,**flags)
    except Exception as error:
        data.update(status='failed',error=str(error));write_json(receipt,data);raise
    return data

def worker(receipt):
    data=read_job(receipt);data.update(status='running',pid=os.getpid());write_json(receipt,data)
    folder=receipt.parent;key=data['key']
    try:
        subprocess.run([sys.executable,str(ROOT/'render_gif.py'),'--lesson',data['lesson'],'--advanced' if key['mode']=='advanced' else '--skip-construction',
            '--width',str(key['width']),'--fps',str(key['fps']),'--duration',str(key['duration']),'--hold','3',
            '--output',str(folder/'study.gif'),'--sheet',str(folder/'sheet.png')],check=True,timeout=600)
        names=['study.gif','sheet.png','study.evidence.json']
        if key['mode']=='advanced':names+=['study-palette.json','study-palette.png']
        outputs={name:str(folder/name) for name in names}
        data.update(status='passed',outputs=outputs,hashes={p:digest(p) for p in outputs.values()},finished_at=time.time())
    except Exception as error:data.update(status='failed',error=str(error),finished_at=time.time())
    write_json(receipt,data)

def dispatch(operation,args):
    if operation=='tools/list':return dict(tools=TOOLS)
    definition=next((t for t in TOOLS if t['name']==operation),None)
    if not definition:raise ValueError('Unknown drawing operation; call tools/list first')
    spec=definition['inputSchema']
    if not isinstance(args,dict) or set(args)-set(spec['properties']):raise ValueError('Unexpected arguments; use the discovered inputSchema')
    if any(k not in args for k in spec['required']):raise ValueError('Missing required arguments: '+', '.join(spec['required']))
    if operation.startswith('animal_'):
        import animal_pipeline
        return animal_pipeline.dispatch(operation,args)
    if operation=='drawing_guide':return dict(
        guide=str(ROOT/'MCP.md'),workflow=str(ROOT.parents[1]/'workflows/game-music-video/drawing.md'),
        order=['drawing_import_reference preserves personal art and creates a fitted lesson','Choose trace (default Draw & Paint) to skip shapes, or advanced (Shapes First) with user-authored stage 0 masses and stage 1 smaller forms','drawing_validate with the same mode; visually review any authored geometry','drawing_render with the chosen mode, then poll drawing_job','Consumer retimes exported strokes to music and captures clean engine footage','video_production imports the finished mix into ArcoreCut; edit captions and export'],
        canvas=dict(width=1280,height=698),guide_types=['ellipse','line','contour'],
        lesson_fields=dict(version=1,name='Your study name',image='data:image/png;base64,...',guides=[dict(type='ellipse',stage=0,name='main mass',points='At least two [x,y] points; sample the full ellipse'),dict(type='line',stage=1,name='feature axis',points=[[500,200],[500,350]])]),
        dependencies=['Python 3 with Pillow','Node.js','No browser or model weights needed'],
        boundaries=['No automatic anatomical guide authoring','No image generation','No song retiming or game capture in drawing_render','No publication','Geometric validity is not human art approval'])
    if operation=='drawing_validate':return validate(absolute(args['lesson']),mode_of(args)=='advanced')
    if operation=='drawing_import_reference':return import_reference(args)
    if operation=='drawing_render':return public_job(render(args))
    return public_job(status(absolute(args['job_file'])))

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker':worker(absolute(sys.argv[2]))
    else:
        try:
            request=json.load(sys.stdin);print(json.dumps(dict(ok=True,result=dispatch(request['operation'],request.get('arguments',{})))))
        except Exception as error:print(json.dumps(dict(ok=False,error=str(error))))
