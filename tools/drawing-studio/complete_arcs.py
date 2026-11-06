"""Complete large construction circles from partial, smoothed image edges."""
import argparse
import json
import math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
from render_gif import ROOT, normalized_reference, font
from shape_geometry import ellipse_points, foreground_evidence, foreground_fraction
from measure_shapes import export_lesson
from vision_metrics import ResourceMonitor


def complete(pixels):
    candidates=circle_candidates(pixels)
    stretched=cv2.resize(pixels,None,fx=1,fy=1.35)
    for c in circle_candidates(stretched):
        cx,cy,a,b,angle=c['geometry']
        c['geometry']=[cx,cy/1.35,a,b/1.35,angle]
        c['points']=ellipse_points(c['geometry']).tolist()
        c['kind']='ellipse'
        candidates.append(c)
    for i,c in enumerate(candidates):c['id']=f'C{i+1:02d}'
    return candidates


def circle_candidates(pixels):
    cv2.setNumThreads(4)
    small=cv2.resize(pixels,None,fx=.5,fy=.5)
    gray=cv2.cvtColor(small,cv2.COLOR_RGB2GRAY)
    foreground,background=foreground_evidence(pixels)
    proposals=[]
    for sigma in (2,4,6):
        smooth=cv2.GaussianBlur(gray,(0,0),sigma)
        edges=cv2.Canny(smooth,15,40)
        gx=cv2.Sobel(smooth,cv2.CV_32F,1,0);gy=cv2.Sobel(smooth,cv2.CV_32F,0,1)
        circles=cv2.HoughCircles(smooth,cv2.HOUGH_GRADIENT,1.5,35,param1=40,param2=22,minRadius=45,maxRadius=125)
        if circles is None:continue
        for cx,cy,r in circles[0]:
            angles=np.linspace(0,2*math.pi,180,endpoint=False)
            supported=np.zeros(180,bool)
            for offset in np.linspace(-4,4,17):
                x=np.round(cx+(r+offset)*np.cos(angles)).astype(int);y=np.round(cy+(r+offset)*np.sin(angles)).astype(int)
                valid=(x>=0)&(x<gray.shape[1])&(y>=0)&(y<gray.shape[0]);x=x.clip(0,gray.shape[1]-1);y=y.clip(0,gray.shape[0]-1)
                alignment=np.abs(gx[y,x]*np.cos(angles)+gy[y,x]*np.sin(angles))/np.maximum(1e-6,np.hypot(gx[y,x],gy[y,x]))
                supported|=valid&(edges[y,x]>0)&(alignment>.8)
            # Spread across sectors prevents one short arc driving a full circle.
            sectors=supported.reshape(12,15).mean(axis=1)>.2
            coverage=float(supported.mean());spread=float(sectors.mean())
            geometry=[float(cx*2),float(cy*2),float(r*2),float(r*2),0]
            points=ellipse_points(geometry).tolist()
            interior=foreground_fraction(points,foreground)
            if coverage<.25 or spread<.5 or (background['uniform_border_detected'] and interior<.8):continue
            score=.7*coverage+.3*spread
            proposals.append({'kind':'circle','geometry':geometry,'points':points,'detail_candidate':False,'supported_angles':supported.tolist(),'measurements':{'geometric_support_score':score,'supported_perimeter_fraction':coverage,'supported_sector_fraction':spread,'foreground_fraction':interior},'sigma':sigma,'review_required':True,'semantic_confidence':None})
    selected=[]
    for p in sorted(proposals,key=lambda p:p['measurements']['geometric_support_score'],reverse=True):
        x,y,r,_,_=p['geometry']
        if any(math.hypot(x-q['geometry'][0],y-q['geometry'][1])<min(r,q['geometry'][2])*.6 for q in selected):continue
        p['id']=f'C{len(selected)+1:02d}';selected.append(p)
        if len(selected)==6:break
    return selected


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=ROOT/'assets/spider-reference.jpg')
    parser.add_argument('--output',type=Path,default=ROOT/'output/spider-arcs.json')
    args=parser.parse_args()
    paths=[args.output,args.output.with_suffix('.png'),args.output.with_name(args.output.stem+'-lesson.json')]
    if args.output.suffix!='.json' or args.input.resolve() in [p.resolve() for p in paths]:parser.error('Use a distinct JSON output path')
    reference,_,_=normalized_reference(argparse.Namespace(input=args.input,lesson=None))
    monitor=ResourceMonitor().start()
    try:
        with monitor.measure('arc_completion') as timing: candidates=complete(np.array(reference.convert('RGB')))
    finally:resources,samples=monitor.finish()
    canvas=Image.new('RGB',(1280,808),'#faf8f1');canvas.paste(reference,(0,110));draw=ImageDraw.Draw(canvas)
    draw.text((25,15),'PARTIAL ARCS / CONSTRUCTION SHAPES',font=font(26,True),fill='#243c38')
    draw.text((25,55),'Green: supported curve. Orange dashes: inferred completion. No authored positions.',font=font(18),fill='#243c38')
    for c in candidates:
        points=c['points'];supported=c['supported_angles']
        for i in range(len(points)):
            if supported[i] or i%4<2:
                p=points[i];q=points[(i+1)%len(points)];draw.line([(p[0],p[1]+110),(q[0],q[1]+110)],fill='#008b64' if supported[i] else '#ed761c',width=4)
        x,y=c['geometry'][:2];draw.text((x,y+110),c['id'],font=font(22,True),fill='#193e32',stroke_width=2,stroke_fill='white')
    args.output.parent.mkdir(parents=True,exist_ok=True);canvas.save(paths[1]);export_lesson(reference,candidates,paths[2])
    report={'method':'multiscale gradient Hough circles with partial perimeter support','authored_guides_used':False,'semantic_labels_inferred':False,'score_kind':'uncalibrated geometric evidence','candidates':candidates,'timing':timing,'resources':resources,'samples':samples}
    args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'candidates':[{k:c[k] for k in ('id','geometry','measurements')} for c in candidates],'timing':timing},indent=2))


if __name__=='__main__':main()
