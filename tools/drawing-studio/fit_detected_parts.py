"""Refine grounded body boxes and propose exposed appendage regions."""
import math
import heapq
import cv2
import numpy as np
from PIL import Image,ImageDraw
from shape_geometry import ellipse_points,foreground_evidence
from measure_shapes import export_lesson
from render_gif import font


def body_fit(pixels,box):
    x1,y1,x2,y2=box;cx=(x1+x2)/2;cy=(y1+y2)/2;a=(x2-x1)/2;b=(y2-y1)/2
    gray=cv2.GaussianBlur(cv2.cvtColor(pixels,cv2.COLOR_RGB2GRAY),(0,0),3)
    edges=cv2.Canny(gray,18,45)
    distance=cv2.distanceTransform(255-edges,cv2.DIST_L2,3)
    gx=cv2.Sobel(gray,cv2.CV_32F,1,0);gy=cv2.Sobel(gray,cv2.CV_32F,0,1)
    best=None
    for dx in (-.04,0,.04):
        for dy in (-.04,0,.04):
            for sx in (.9,1,1.08):
                for sy in (.9,1,1.08):
                    for angle in (-.15,0,.15):
                        geometry=[cx+dx*a,cy+dy*b,a*sx,b*sy,angle]
                        points=ellipse_points(geometry)
                        xx=points[:,0].round().astype(int).clip(0,pixels.shape[1]-1);yy=points[:,1].round().astype(int).clip(0,pixels.shape[0]-1)
                        tangent=np.roll(points,-1,axis=0)-np.roll(points,1,axis=0)
                        normal=np.column_stack((-tangent[:,1],tangent[:,0]));normal/=np.maximum(1e-6,np.linalg.norm(normal,axis=1))[:,None]
                        alignment=np.abs(gx[yy,xx]*normal[:,0]+gy[yy,xx]*normal[:,1])/np.maximum(1e-6,np.hypot(gx[yy,xx],gy[yy,xx]))
                        supported=(distance[yy,xx]<7)&(alignment>.6)
                        score=float(supported.mean())-.2*(abs(sx-1)+abs(sy-1))
                        if best is None or score>best[0]:best=(score,geometry,points,supported)
    score,geometry,points,supported=best
    return {'kind':'ellipse','geometry':geometry,'points':points.tolist(),'supported_angles':supported.tolist(),'detail_candidate':False,'measurements':{'geometric_support_score':float(supported.mean())},'detected_box':box,'review_required':True}


def classify_appendage(geometry,head,palp_boxes):
    """Conservative exclusion: unresolved mouth-side parts are not walking-leg evidence."""
    x,y=geometry[:2];hx,hy,a,b,_=head
    near_mouth=abs(x-hx)<a*.8 and hy+b*.45<y<hy+b*1.55
    for box in palp_boxes:
        x1,y1,x2,y2=box
        # Reject whole-subject/group boxes masquerading as a palp detection.
        if 0<x2-x1<a*1.4 and 0<y2-y1<b*1.7 and x1<=x<=x2 and y1<=y<=y2 and near_mouth:
            return 'palp candidate','model box plus mouth-region prior'
    if near_mouth:return 'unresolved mouth appendage','mouth-region prior only; may include a front leg'
    return 'walking-leg segment candidate','outside mouth-region exclusion; anatomy unverified'


def construct(image,grounding,output,palp_grounding=None):
    pixels=np.array(image);cv2.setNumThreads(4)
    parts=[]
    for label,box in zip(grounding['labels'],grounding['bboxes']):
        role='head' if 'head' in label.lower() else 'abdomen' if 'abdomen' in label.lower() else None
        if role:
            part=body_fit(pixels,box);part.update(id=role,proposed_role=role);parts.append(part)
    foreground,bg=foreground_evidence(pixels)
    if not bg['uniform_border_detected']:raise ValueError('Appendage pass currently requires a plain background')
    mask=foreground.astype('uint8')*255
    lab=cv2.cvtColor(pixels,cv2.COLOR_RGB2LAB).astype(float)
    bodymask=np.zeros(mask.shape,np.uint8)
    for part in parts:cv2.fillPoly(bodymask,[np.round(part['points']).astype(np.int32)],1)
    if not parts:raise ValueError('No grounded body regions; cannot separate appendages')
    stock=np.median(lab[bodymask>0,1:],axis=0)
    background=np.median(lab[:5,:,1:].reshape(-1,2),axis=0)
    mask[np.linalg.norm(lab[:,:,1:]-stock,axis=2)>=np.linalg.norm(lab[:,:,1:]-background,axis=2)]=0
    mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    # Remove only inferred body interiors; exposed appendages remain uncertain.
    for part in parts:
        geometry=part['geometry'].copy();geometry[2]*=1.07;geometry[3]*=1.07
        cv2.fillPoly(mask,[np.round(ellipse_points(geometry)).astype(np.int32)],0)
    mask[:int(min(p['geometry'][1] for p in parts))]=0
    distance=cv2.distanceTransform(mask,cv2.DIST_L2,5)
    maxima=(distance>=cv2.dilate(distance,np.ones((35,35),np.uint8))-.01)&(distance>10)
    _,seeds,_,centers=cv2.connectedComponentsWithStats(maxima.astype('uint8'))
    labels=np.zeros(mask.shape,np.int32);queue=[]
    for i,(x,y) in enumerate(centers[1:],1):heapq.heappush(queue,(0,int(y),int(x),i))
    # Geodesic nearest-seed assignment follows foreground and cannot cross background gaps.
    while queue:
        cost,y,x,label=heapq.heappop(queue)
        if labels[y,x]:continue
        labels[y,x]=label
        for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
            ny,nx=y+dy,x+dx
            if 0<=ny<mask.shape[0] and 0<=nx<mask.shape[1] and mask[ny,nx] and not labels[ny,nx]:heapq.heappush(queue,(cost+1,ny,nx,label))
    count=len(centers)
    limbs=[]
    for i in range(1,count):
        if np.count_nonzero(labels==i)<700:continue
        yy,xx=np.nonzero(labels==i);points=np.column_stack((xx,yy))
        values,vectors=np.linalg.eigh(np.cov(points.T));order=np.argsort(values)[::-1]
        axes=2*np.sqrt(values[order]);direction=vectors[:,order[0]]
        if axes[0]/max(1,axes[1])<1.15:continue
        center=points.mean(axis=0);geometry=[*center,*axes,math.atan2(direction[1],direction[0])]
        contour=max(cv2.findContours((labels==i).astype('uint8'),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0],key=cv2.contourArea).reshape(-1,2)
        fitted=np.zeros(mask.shape,np.uint8);curve=ellipse_points(geometry);cv2.fillPoly(fitted,[np.round(curve).astype(np.int32)],1)
        region=labels==i;iou=float(np.count_nonzero(region&(fitted>0))/np.count_nonzero(region|(fitted>0)))
        limbs.append({'id':f'L{len(limbs)+1}','proposed_role':'exposed appendage candidate','kind':'ellipse','geometry':[float(v) for v in geometry],'points':curve.tolist(),'contour':contour.tolist(),'detail_candidate':False,'measurements':{'geometric_support_score':iou},'review_required':True,'anatomical_identity':None})
    head=next((p['geometry'] for p in parts if p['id']=='head'),None)
    palp_grounding=palp_grounding or {'labels':[],'bboxes':[]}
    palp_boxes=[b for b,l in zip(palp_grounding['bboxes'],palp_grounding['labels']) if 'palp' in l.lower()]
    for p in limbs:
        role,evidence=classify_appendage(p['geometry'],head,palp_boxes) if head else ('unresolved appendage','no head location')
        p['proposed_role']=role;p['role_evidence']=evidence
        p['eligible_for_walking_leg_grouping']=role=='walking-leg segment candidate'
    canvas=Image.new('RGB',(1280,798),'#faf8f1');canvas.paste(image,(0,100));draw=ImageDraw.Draw(canvas)
    draw.text((20,12),'GROUNDED BODY FITS AND EXPOSED APPENDAGES',font=font(25,True),fill='#243c38')
    draw.text((20,50),'Blue: leg candidates. Purple: palp candidates. Amber: unresolved mouth appendages.',font=font(17),fill='#243c38')
    for p in parts:
        pts=p['points']
        for i in range(len(pts)):
            if p['supported_angles'][i] or i%4<2:
                a=pts[i];b=pts[(i+1)%len(pts)];draw.line([(a[0],a[1]+100),(b[0],b[1]+100)],fill='#008b64' if p['supported_angles'][i] else '#ea721e',width=4)
        x,y=p['geometry'][:2];draw.text((x,y+100),p['id'],font=font(19,True),fill='#243c38',stroke_width=2,stroke_fill='white')
    for p in limbs:
        color='#167fc0' if p['eligible_for_walking_leg_grouping'] else '#9443b3' if p['proposed_role']=='palp candidate' else '#ba7615'
        pts=[(x,y+100) for x,y in p['contour']];draw.line(pts+[pts[0]],fill=color,width=3)
        pts=[(x,y+100) for x,y in p['points']];draw.line(pts+[pts[0]],fill=color,width=2)
        x,y=p['geometry'][:2];draw.text((x,y+100),p['id'],font=font(20,True),fill=color,stroke_width=2,stroke_fill='white')
    canvas.save(output.with_suffix('.png'))
    export_lesson(image,parts+limbs,output.with_name(output.name+'-lesson.json'))
    import json
    lesson_path=output.with_name(output.name+'-lesson.json')
    lesson=json.loads(lesson_path.read_text())
    roles={p['id']:p for p in parts+limbs}
    for guide in lesson['guides']:
        part=roles[guide['candidate_id']]
        guide['proposed_role']=part['proposed_role']
        guide['eligible_for_walking_leg_grouping']=part.get('eligible_for_walking_leg_grouping',False)
    lesson_path.write_text(json.dumps(lesson,indent=2))
    return {'body_parts':parts,'appendage_candidates':limbs,'background':bg,'method':'box-constrained edge-supported ellipse search, chroma foreground gate, expanded body subtraction, local thickness seeds, geodesic partition and moment ellipses','limitations':'Exposed regions can merge multiple legs or split one leg. No occluded roots inferred; no verified eight-leg topology. Scores are uncalibrated.'}
