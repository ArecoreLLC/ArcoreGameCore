"""Propose image-driven primitives or measure user traces with explainable scores."""
import argparse
import base64
from collections import Counter
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import sys
import time
from xml.sax.saxutils import escape

import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageEnhance

from render_gif import ROOT,font,normalized_reference
from shape_geometry import detect_shapes,edge_evidence,fit_trace
from vision_metrics import ResourceMonitor


def draw_review(reference,candidates,path):
    rows=math.ceil(len(candidates)/3)
    canvas=Image.new('RGB',(1280,698+150+max(2,rows)*28),(250,248,241));draw=ImageDraw.Draw(canvas)
    draw.text((28,16),'IMAGE-DRIVEN SHAPE CANDIDATES',font=font(24,True),fill=(40,57,47))
    draw.text((28,48),'Geometry support / not semantic labels or calibrated probabilities',font=font(15),fill=(105,112,97))
    faded=Image.blend(reference.convert('RGB'),Image.new('RGB',(1280,698),(250,248,241)),.20)
    canvas.paste(faded,(0,80));draw=ImageDraw.Draw(canvas)
    occupied=[]
    for c in candidates:
        color=(29,135,91) if c['score_band']=='strong' else (49,104,166) if c['score_band']=='moderate' else (180,114,35)
        points=[(p[0],p[1]+80) for p in c['points']];draw.line(points+[points[0]],fill=color,width=2)
        cx=float(np.mean(c['points'],axis=0)[0]);cy=float(np.min(np.asarray(c['points'])[:,1]))+80
        label=f'{c["id"]} / {c["measurements"]["geometric_support_score"]*100:.0f}'
        width=draw.textlength(label,font=font(14))+12
        x=max(3,min(1277-width,cx-width/2));y=max(83,cy-25)
        for offset in range(10):
            box=(x,y,x+width,y+23)
            if not any(box[0]<b[2] and box[2]>b[0] and box[1]<b[3] and box[3]>b[1] for b in occupied):break
            y=max(83,min(750,y+25))
        occupied.append(box);draw.rounded_rectangle(box,radius=4,fill=(250,248,241),outline=color)
        draw.text((x+6,y+2),label,font=font(14),fill=color)
    y=798
    draw.text((28,y),'Scores out of 100. Fit error is RMS pixels. Small / nested details are marked *.',font=font(15),fill=(76,92,70))
    for i,c in enumerate(candidates):
        column=i%3;row=i//3
        error=c['measurements'].get('rms_fit_error_px')
        error_text=f'{error:.1f}px' if error is not None else 'polygon'
        label=f'{c["id"]} {c["kind"]}{"*" if c["detail_candidate"] else ""}   {c["measurements"]["geometric_support_score"]*100:.0f}/100   {error_text}'
        draw.text((28+column*418,y+31+row*28),label,font=font(16),fill=(40,57,47))
    canvas.save(path)


def export_lesson(reference,candidates,path):
    guides=[]
    for c in sorted(candidates,key=lambda c:cv2.contourArea(np.asarray(c['points'],np.float32)),reverse=True):
        if c['detail_candidate']:continue
        points=c['points']+[c['points'][0]]
        area=cv2.contourArea(np.asarray(c['points'],np.float32))
        guides.append({'type':'ellipse' if c['kind'] in ('ellipse','circle') else 'contour','stage':0 if area>1280*698*.06 else 1,'points':points,'candidate_id':c['id'],'geometric_support_score':c['measurements']['geometric_support_score']})
    buffer=io.BytesIO();reference.convert('RGB').save(buffer,format='JPEG',quality=94)
    lesson={'version':1,'name':'Automatic shape candidates - review before use','study':'custom','image':'data:image/jpeg;base64,'+base64.b64encode(buffer.getvalue()).decode('ascii'),'guides':guides,'review_required':True,'score_kind':'uncalibrated geometric support'}
    path.write_text(json.dumps(lesson,indent=2)+'\n',encoding='utf-8')
    return len(guides)


def run(args):
    if not 0<=args.min_score<=1 or not 1<=args.max_shapes<=64:
        raise ValueError('Use a score threshold between 0 and 1 and 1-64 shapes.')
    if args.output.suffix.lower()!='.json':raise ValueError('--output must end in .json.')
    overlay=args.output.with_suffix('.png');svg=args.output.with_suffix('.svg')
    lesson_path=args.output.with_name(args.output.stem+'-lesson.json')
    telemetry_path=args.output.with_name(args.output.stem+'-telemetry.json')
    sources={path.resolve() for path in (args.input,args.traces) if path is not None}
    if any(path.resolve() in sources for path in (args.output,overlay,svg,lesson_path,telemetry_path)):
        raise ValueError('Choose an output name that cannot overwrite the input image or trace file.')
    reference,name,study=normalized_reference(argparse.Namespace(input=args.input,lesson=None))
    pixels=np.array(reference.convert('RGB'))
    start=time.perf_counter();monitor=ResourceMonitor().start()
    try:
        with monitor.measure('shape_detection') as detection_metrics:
            result=detect_shapes(pixels,args.min_score,args.max_shapes)
        trace_results=[]
        if args.traces:
            if args.traces.stat().st_size>18_000_000:raise ValueError('Trace file must be under 18 MB.')
            data=json.loads(args.traces.read_text(encoding='utf-8'))
            if not isinstance(data,dict):raise ValueError('Expected a trace object containing guides or traces.')
            traces=data.get('guides',data.get('traces',[]))
            if not isinstance(traces,list) or len(traces)>500:raise ValueError('Expected up to 500 traces or lesson guides.')
            evidence=edge_evidence(cv2.cvtColor(pixels,cv2.COLOR_RGB2GRAY))
            for i,trace in enumerate(traces):
                if not isinstance(trace,dict):raise ValueError(f'Expected an object for trace {i}.')
                points=np.asarray(trace.get('points',[]),dtype=np.float32)
                if points.ndim!=2 or points.shape[1:]!=(2,) or len(points)>10000 or not np.all(np.isfinite(points)):
                    raise ValueError(f'Invalid points in trace {i}.')
                fits=fit_trace(points,evidence,source='supplied_trace')
                trace_results.append({'trace_index':i,'fits':fits,'review_required':True})
        resources,samples=monitor.finish()
    finally:
        if not monitor.stop_event.is_set():monitor.finish()
    elapsed=time.perf_counter()-start
    args.output.parent.mkdir(parents=True,exist_ok=True)
    candidates=result['candidates']
    draw_review(reference,candidates,overlay)
    lines=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 698">','<title>Measured geometry candidates; manual review required</title>']
    for c in candidates:
        if c['kind'] in ('circle','ellipse'):
            cx,cy,a,b,angle=c['geometry']
            element='circle' if c['kind']=='circle' else 'ellipse'
            geometry=f'cx="{cx:.3f}" cy="{cy:.3f}" '+(f'r="{a:.3f}"' if element=='circle' else f'rx="{a:.3f}" ry="{b:.3f}" transform="rotate({math.degrees(angle):.3f} {cx:.3f} {cy:.3f})"')
        else:
            element='polygon';coordinates=' '.join(f'{x:.2f},{y:.2f}' for x,y in c['vertices']);geometry=f'points="{coordinates}"'
        lines.append(f'<{element} id="{c["id"]}" {geometry} fill="none" stroke="#21875b" stroke-width="2"><title>{escape(c["id"]+" "+c["kind"])} score {c["measurements"]["geometric_support_score"]:.3f}</title></{element}>')
    lines.append('</svg>');svg.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    guide_count=export_lesson(reference,candidates,lesson_path)
    report={'schema_version':1,'status':'candidates_for_review','created_with':{'python':platform.python_version(),'opencv':cv2.__version__,'numpy':np.__version__},'image':{'sha256':hashlib.sha256(args.input.read_bytes()).hexdigest(),'normalized_size':[1280,698]},'parameters':{'min_score':args.min_score,'max_shapes':args.max_shapes,'opencv_threads':4},'score_definition':{'kind':'uncalibrated geometric support, not probability','ellipse_base':'.35 * exp(-(normalized_rms/.075)^2) + .30 * gradient_aligned_boundary_support + .15 * angular_coverage + .20 * trace_fill_iou','repeatability':'base score multiplied by .95 + .05 * min(1,(source_count-1)/4)','weak_boundary_penalty':'base score multiplied by boundary_support/.45 when support < .45','semantic_confidence':None,'note':'Strong geometric support does not identify an eye, leg, or body; partial/occluded construction masses may be missed.'},'automatic_detection_uses_authored_guides':False,'candidate_count':len(candidates),'counts_by_kind':dict(Counter(c['kind'] for c in candidates)),'trace_count':result['trace_count'],'raw_proposals':result['raw_proposals'],'merged_proposals':result['merged_proposals'],'background_test':result['background_test'],'candidates':candidates,'measured_supplied_traces':trace_results,'detection_wall_seconds':round(detection_metrics['wall_seconds'],4),'analysis_and_monitor_setup_seconds':round(elapsed,4),'resources':resources,'draft_guide_count':guide_count,'outputs':{'overlay':overlay.name,'svg':svg.name,'draft_lesson':lesson_path.name},'review_required':True}
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    telemetry_path.write_text(json.dumps({'samples':samples},indent=2)+'\n',encoding='utf-8')
    summary={k:report[k] for k in ['candidate_count','counts_by_kind','trace_count','raw_proposals','detection_wall_seconds','draft_guide_count']}
    summary.update({'report':str(args.output.resolve()),'overlay':str(overlay.resolve()),'lesson':str(lesson_path.resolve())})
    print(json.dumps(summary,indent=2),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=ROOT/'assets'/'spider-reference.jpg')
    p.add_argument('--output',type=Path,default=ROOT/'output'/'spider-shapes.json')
    p.add_argument('--min-score',type=float,default=.72)
    p.add_argument('--max-shapes',type=int,default=24)
    p.add_argument('--traces',type=Path,help='Optional JSON {traces:[{points:[[x,y],...]}]} or saved lesson guides in normalized 1280 x 698 coordinates')
    try:run(p.parse_args())
    except (ValueError,OSError,cv2.error) as error:
        print(f'Shape measurement failed: {error}',file=sys.stderr);sys.exit(1)
