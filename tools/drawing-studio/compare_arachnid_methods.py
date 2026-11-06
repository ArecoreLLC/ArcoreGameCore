"""Fresh sequential legacy/generic/profile runs with shared analysis+GIF deadlines."""
import json,time,sys,hashlib
from pathlib import Path
from collections import Counter
from PIL import Image,ImageDraw
from benchmark_construction import run_bounded,ROOT,REPO

out=ROOT/'output/arachnid-method-comparison';out.mkdir(parents=True,exist_ok=True)
python=str(ROOT/'.venv-vision/Scripts/python.exe');source=ROOT/'assets/spider-reference.jpg'
selected=sys.argv[sys.argv.index('--only')+1:] if '--only' in sys.argv else []
rows=json.loads((out/'comparison.json').read_text()) if selected and (out/'comparison.json').exists() else []
for method in ('generic','legacy','profile'):
    if selected and method not in selected:continue
    target=out/method
    command=([python,str(ROOT/'compare_florence_inputs.py'),'--worker','--construction','--output',str(target)] if method=='legacy' else [python,str(ROOT/'resolve_sketch_parts.py'),'--input',str(source),'--output',str(target.with_suffix('.json')),'--arachnid-mode',method])
    lesson=out/f'{method}-lesson.json'
    render=[sys.executable,str(ROOT/'render_gif.py'),'--lesson',str(lesson),'--advanced','--width','640','--fps','4','--duration','12','--output',str(target.with_suffix('.gif'))]
    row={'method':method,'commands':[command,render],'status':'passed','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
    start=time.perf_counter()
    try:
        for i,cmd in enumerate((command,render)):
            code=run_bounded(cmd,30-(time.perf_counter()-start),out/f'{method}-{i}.log')
            if code:raise RuntimeError(f'phase {i} exited {code}')
        report=json.loads(target.with_suffix('.json').read_text())
        if method=='legacy':
            raw=report['results']['color']['parsed']['<CAPTION_TO_PHRASE_GROUNDING>']
            parts=report['construction']['appendage_candidates']
            row['candidate_roles']=dict(Counter(p['proposed_role'] for p in parts))
            row['body_regions']=len(report['construction']['body_parts'])
        else:
            raw=report['queries'][1]['parsed'];row['candidate_roles']=dict(Counter(p['raw_label'] for p in report['parts']))
            row['audit']=report['detection_audit']
        row['model']=report['model'];row['raw_grounded_labels']=dict(Counter(raw['labels']))
        resources=report['resources'];row['cpu_machine_mean']=resources['process_cpu_percent_machine_mean'];row['gpu_process_peak']=resources.get('gpu_process_busiest_engine_percent_sampled',{}).get('peak')
        row['guide_count']=len(json.loads(lesson.read_text())['guides'])
    except Exception as exc:row.update(status='failed',error=str(exc))
    row['total_seconds']=round(time.perf_counter()-start,3);row['within_30_seconds']=row['total_seconds']<30
    rows=[r for r in rows if r['method']!=method]+[row]
    rows.sort(key=lambda r:('generic','legacy','profile').index(r['method']))
    (out/'comparison.json').write_text(json.dumps(rows,indent=2))
    print(json.dumps({k:v for k,v in row.items() if k not in ('commands','model','audit')}),flush=True)
sheet=Image.new('RGB',(1280,3*440),'#faf8f1');draw=ImageDraw.Draw(sheet)
for i,row in enumerate(rows):
    path=out/f'{row["method"]}.png'
    if path.exists():
        im=Image.open(path);im.thumbnail((1200,400));sheet.paste(im,((1280-im.width)//2,i*440+30))
    draw.text((20,i*440+8),f'{row["method"]} | {row["status"]} | {row["total_seconds"]}s',fill='black')
sheet.save(out/'comparison.png')
