"""Experimental silhouette-based part proposals; semantic assignments require review."""
import argparse
import json
import math
import heapq
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
from render_gif import ROOT, normalized_reference, font
from shape_geometry import foreground_evidence, ellipse_points
from measure_shapes import export_lesson
from vision_metrics import ResourceMonitor


def propose(pixels):
    cv2.setNumThreads(4)
    mask, background = foreground_evidence(pixels)
    if not background['uniform_border_detected']:
        raise ValueError('This experimental pass requires a plain background.')
    mask = mask.astype('uint8') * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9,9),np.uint8))
    contours,_ = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    mask[:] = 0
    if not contours: return [],[],background
    cv2.drawContours(mask,[max(contours,key=cv2.contourArea)],-1,255,-1)
    distance = cv2.distanceTransform(mask,cv2.DIST_L2,5)
    # Scale-independent local width maxima propose thick masses and limb lobes.
    radius = max(7,round(min(mask.shape)*.012))
    maxima = (distance >= cv2.dilate(distance,np.ones((radius*2+1,radius*2+1),np.uint8))-.01) & (distance>10)
    n, labels, stats, centers = cv2.connectedComponentsWithStats(maxima.astype('uint8'))
    seeds = sorted([(float(distance[int(y),int(x)]),int(x),int(y)) for x,y in centers[1:]],reverse=True)[:32]
    markers = np.zeros(mask.shape,np.int32); markers[mask==0]=1
    for i,(_,x,y) in enumerate(seeds): cv2.circle(markers,(x,y),2,i+2,-1)
    queue=[]
    for i,(_,x,y) in enumerate(seeds):
        heapq.heappush(queue,(-float(distance[y,x]),y,x,i+2))
    markers[:]=0
    while queue:
        cost,y,x,label=heapq.heappop(queue)
        if markers[y,x]: continue
        markers[y,x]=label
        for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
            ny,nx=y+dy,x+dx
            if 0<=ny<mask.shape[0] and 0<=nx<mask.shape[1] and mask[ny,nx] and not markers[ny,nx]:
                heapq.heappush(queue,(max(cost,-float(distance[ny,nx])),ny,nx,label))
    parts=[]
    for i,(width,x,y) in enumerate(seeds):
        region=(markers==i+2)&(mask>0)
        yy,xx=np.nonzero(region)
        if len(xx)<150: continue
        pts=np.column_stack((xx,yy)).astype(float)
        center=pts.mean(axis=0); values,vectors=np.linalg.eigh(np.cov(pts.T)); order=np.argsort(values)[::-1]
        axes=2*np.sqrt(values[order]); axis=vectors[:,order[0]]
        angle=math.atan2(axis[1],axis[0]); geometry=[*center,*axes,angle]
        outline=ellipse_points(geometry).tolist()
        fitted=np.zeros(mask.shape,np.uint8); cv2.fillPoly(fitted,[np.round(outline).astype(np.int32)],1)
        overlap=float(np.count_nonzero((fitted>0)&region)/max(1,np.count_nonzero((fitted>0)|region)))
        role='body mass candidate' if width>distance.max()*.55 else 'limb segment candidate'
        parts.append({'id':f'P{len(parts)+1:02d}','kind':'ellipse','geometry':[float(v) for v in geometry], 'points':outline,'detail_candidate':False,'proposed_role':role,'semantic_confidence':None,'visibility_confidence':None,'review_required':True,'measurements':{'geometric_support_score':overlap,'region_ellipse_iou':overlap},'seed_label':i+2})
    connections=[]
    for a in parts:
        expanded=cv2.dilate((markers==a['seed_label']).astype('uint8'),np.ones((7,7),np.uint8))>0
        for b in parts:
            if a['id']<b['id'] and np.any(expanded & (markers==b['seed_label'])):
                connections.append({'from':a['id'],'to':b['id'],'kind':'region adjacency; anatomical connection unverified'})
    return parts,connections,background


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=ROOT/'assets/spider-reference.jpg')
    parser.add_argument('--output',type=Path,default=ROOT/'output/spider-parts.json')
    args=parser.parse_args()
    if args.output.suffix!='.json': parser.error('Output must end in .json')
    outputs=[args.output,args.output.with_suffix('.png'),args.output.with_name(args.output.stem+'-lesson.json')]
    if args.input.resolve() in [p.resolve() for p in outputs]: parser.error('Output would overwrite input')
    reference,_,_=normalized_reference(argparse.Namespace(input=args.input,lesson=None))
    monitor=ResourceMonitor().start()
    try:
        with monitor.measure('part_proposals') as timing: parts,connections,background=propose(np.array(reference.convert('RGB')))
    finally: resources,samples=monitor.finish()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    canvas=Image.new('RGB',(1280,798),'#faf8f1');canvas.paste(reference,(0,100));draw=ImageDraw.Draw(canvas)
    draw.text((25,15),'EXPERIMENTAL BODY / LIMB CONSTRUCTION',font=font(25,True),fill='#243c38')
    draw.text((25,53),'Image-derived regions. Labels and connections are hypotheses; review required.',font=font(18),fill='#243c38')
    for part in parts:
        color='#e85730' if part['proposed_role'].startswith('body') else '#0085ba'
        points=[(x,y+100) for x,y in part['points']];draw.line(points+[points[0]],fill=color,width=3)
        x,y=part['geometry'][:2];draw.text((x,y+100),part['id'],font=font(20,True),fill=color,stroke_width=2,stroke_fill='white')
    canvas.save(outputs[1]);export_lesson(reference,parts,outputs[2])
    report={'method':'silhouette distance maxima, watershed, moment ellipses','subject_prior':'spider (user selected); body masses and articulated limbs','authored_guides_used':False,'model_used':None,'score_kind':'region ellipse IoU; uncalibrated','parts':parts,'connections':connections,'background':background,'timing':timing,'resources':resources,'samples':samples,'review_required':True}
    args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'parts':len(parts),'connections':len(connections),'timing':timing,'overlay':str(outputs[1])},indent=2))


if __name__=='__main__': main()
