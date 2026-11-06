"""Sequential CPU benchmark with a shared 30-second analysis/export deadline per image."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent.parent


def run_bounded(command,remaining,log):
    with log.open('w',encoding='utf-8') as output:
        process=subprocess.Popen(command,cwd=REPO,stdout=output,stderr=subprocess.STDOUT)
        try:return process.wait(timeout=max(.01,remaining))
        except subprocess.TimeoutExpired:
            if sys.platform=='win32':subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True)
            else:process.kill()
            process.wait()
            raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'output/polish-benchmark')
    parser.add_argument('--only',nargs='+',help='Run selected cases; preserve other recorded rows')
    args=parser.parse_args(); out=args.output.resolve(); out.mkdir(parents=True,exist_ok=True)
    sheet=Image.open(REPO/'shared/subject-taxonomy/unclassified/batch-001-sheet.png')
    w,h=sheet.size
    # Extract existing panel assets; do not synthesize or alter their content.
    for name,box in [('lamp',(8,h//2+8,w//2-8,h-8)),('mushrooms',(w//2+8,h//2+8,w-8,h-8))]:
        sheet.crop(box).save(out/f'{name}-input.png')
    cases=[('wolf-standing',REPO/'shared/subject-taxonomy/samples/quadruped.jpg'),('eagle-perched',REPO/'shared/subject-taxonomy/samples/avian.jpg'),('bat-spread-wings',REPO/'shared/subject-taxonomy/samples/bat.jpg'),('iguana-crouched',REPO/'shared/subject-taxonomy/samples/reptile.jpg'),('spider',ROOT/'assets/spider-reference.jpg'),('lamp-unclassified',out/'lamp-input.png'),('mushrooms-unclassified',out/'mushrooms-input.png')]
    rows=json.loads((out/'comparison.json').read_text()) if args.only and (out/'comparison.json').exists() else []
    for name,source in cases:
        if args.only and name not in args.only:continue
        started=time.perf_counter(); report=out/f'{name}.json'
        commands=[[str(ROOT/'.venv-vision/Scripts/python.exe'),str(ROOT/'resolve_sketch_parts.py'),'--input',str(source),'--output',str(report)], [sys.executable,str(ROOT/'render_gif.py'),'--lesson',str(out/f'{name}-lesson.json'),'--advanced','--width','640','--fps','4','--duration','12','--output',str(out/f'{name}.gif'),'--sheet',str(out/f'{name}-sheet.png')]]
        row={'name':name,'input':str(source),'commands':commands,'status':'passed','budget_seconds':30}
        try:
            for index,command in enumerate(commands):
                elapsed=time.perf_counter()-started
                if elapsed>=30:raise subprocess.TimeoutExpired(command,30)
                code=run_bounded(command,30-elapsed,out/f'{name}-{index}.log')
                if code:raise RuntimeError(f'Phase {index} exit {code}; see log')
            analysis=json.loads(report.read_text(encoding='utf-8'))
            row.update(profile=analysis['profile'],guides=analysis['guide_count'],unresolved=len(analysis['unresolved_candidates']),analysis_seconds=analysis['elapsed_seconds'],cpu_machine_mean=analysis['resources']['process_cpu_percent_machine_mean'],gpu_process_peak=analysis['resources'].get('gpu_process_busiest_engine_percent_sampled',{}).get('peak'),peak_ram_mib=analysis['resources'].get('process_rss_mib_sampled',{}).get('peak'))
            lesson=json.loads((out/f'{name}-lesson.json').read_text())
            row['faded_segments']=sum(a<1 for g in lesson['guides'] for a in g.get('segment_opacity',[]))
            row['muzzle_cue_applied']=any((p.get('orientation_evidence') or {}).get('applied') for p in analysis['parts'])
        except subprocess.TimeoutExpired:row.update(status='timed_out',error='Shared 30-second deadline reached; process tree terminated')
        except Exception as exc:row.update(status='failed',error=str(exc))
        row['total_seconds']=round(time.perf_counter()-started,3)
        row['within_budget']=row['total_seconds']<30
        rows=[r for r in rows if r['name']!=name]+[row]
        rows.sort(key=lambda r:[c[0] for c in cases].index(r['name']))
        (out/'comparison.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
        print(json.dumps({k:row[k] for k in ('name','status','total_seconds')}),flush=True)
    gallery=Image.new('RGB',(1280,4*390),'#f5f2eb'); draw=ImageDraw.Draw(gallery)
    for i,row in enumerate(rows):
        path=out/(row['name']+'.png'); x=(i%2)*640;y=(i//2)*390
        if path.exists():
            im=Image.open(path); im.thumbnail((640,349));gallery.paste(im,(x,y+30))
        draw.text((x+10,y+8),f"{row['name']} | {row['status']} | {row['total_seconds']}s",fill='black')
    gallery.save(out/'comparison.png')


if __name__=='__main__':main()
