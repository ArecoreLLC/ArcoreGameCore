"""Image-only primitive proposals and explainable geometric support measurements.

Scores are heuristic evidence scores, not calibrated probabilities or part labels.
No authored spider guides or vision-model responses are imported here.
"""
from collections import defaultdict
import math

import cv2
import numpy as np


def ellipse_points(geometry,count=180):
    cx,cy,a,b,angle=geometry
    t=np.linspace(0,2*math.pi,count,endpoint=False)
    co,si=math.cos(angle),math.sin(angle)
    return np.column_stack((cx+a*np.cos(t)*co-b*np.sin(t)*si,cy+a*np.cos(t)*si+b*np.sin(t)*co)).astype(np.float32)


def polygon_points(vertices,count=180):
    vertices=np.asarray(vertices,dtype=np.float32).reshape(-1,2)
    lengths=np.linalg.norm(np.roll(vertices,-1,axis=0)-vertices,axis=1)
    if lengths.sum()==0:return np.repeat(vertices[:1],count,axis=0)
    samples=[]
    for i,length in enumerate(lengths):
        n=max(2,round(count*length/lengths.sum()))
        for t in np.linspace(0,1,n,endpoint=False):samples.append(vertices[i]*(1-t)+vertices[(i+1)%len(vertices)]*t)
    return np.asarray(samples,dtype=np.float32)


def edge_evidence(gray):
    smoothed=cv2.GaussianBlur(gray,(0,0),1.3)
    edges=cv2.Canny(smoothed,35,100)
    gx=cv2.Sobel(smoothed,cv2.CV_32F,1,0,ksize=3);gy=cv2.Sobel(smoothed,cv2.CV_32F,0,1,ksize=3)
    distance=cv2.distanceTransform(255-edges,cv2.DIST_L2,3)
    return {'edges':edges,'gx':gx,'gy':gy,'distance':distance}


def foreground_evidence(image):
    """Only suppress background gaps when the image border is nearly uniform."""
    lab=cv2.cvtColor(image,cv2.COLOR_RGB2LAB).astype(np.float32)
    border=np.concatenate((lab[:5].reshape(-1,3),lab[-5:].reshape(-1,3),lab[:,:5].reshape(-1,3),lab[:,-5:].reshape(-1,3)))
    background=np.median(border,axis=0)
    spread=float(np.percentile(np.linalg.norm(border-background,axis=1),95))
    reliable=spread<16
    threshold=max(10,spread+7)
    mask=np.linalg.norm(lab-background,axis=2)>threshold
    return mask,{'uniform_border_detected':reliable,'border_lab_distance_p95':round(spread,3),'foreground_lab_distance_threshold':round(threshold,3),'candidate_interior_min_foreground_fraction':.85}


def foreground_fraction(curve,foreground):
    x,y,w,h=cv2.boundingRect(np.asarray(curve,np.float32))
    hh,ww=foreground.shape;x=max(0,x);y=max(0,y);w=min(w,ww-x);h=min(h,hh-y)
    if min(w,h)<1:return 0.0
    mask=np.zeros((h,w),np.uint8)
    cv2.fillPoly(mask,[np.round(np.asarray(curve)-[x,y]).astype(np.int32)],255)
    selected=mask>0
    return float(np.mean(foreground[y:y+h,x:x+w][selected])) if np.any(selected) else 0.0


def boundary_measure(points,evidence,tolerance=2.5):
    """Boundary support also requires image gradients normal to the proposed curve."""
    points=np.asarray(points,dtype=np.float32)
    h,w=evidence['edges'].shape
    if not np.any(evidence['edges']):return 0.0,float('inf')
    if np.any(points[:,0]<0) or np.any(points[:,0]>=w) or np.any(points[:,1]<0) or np.any(points[:,1]>=h):
        return 0.0,float('inf')
    tangent=np.roll(points,-1,axis=0)-np.roll(points,1,axis=0)
    normal=np.column_stack((-tangent[:,1],tangent[:,0]));normal/=np.maximum(1e-6,np.linalg.norm(normal,axis=1))[:,None]
    x=np.round(points[:,0]).astype(int).clip(0,w-1);y=np.round(points[:,1]).astype(int).clip(0,h-1)
    supported=np.zeros(len(points),dtype=bool)
    radius=math.ceil(tolerance)
    for dy in range(-radius,radius+1):
        for dx in range(-radius,radius+1):
            if dx*dx+dy*dy>tolerance*tolerance:continue
            xx=(x+dx).clip(0,w-1);yy=(y+dy).clip(0,h-1)
            gx=evidence['gx'][yy,xx];gy=evidence['gy'][yy,xx]
            aligned=np.abs(gx*normal[:,0]+gy*normal[:,1])/np.maximum(1e-6,np.hypot(gx,gy))>.72
            supported|=(evidence['edges'][yy,xx]>0)&aligned
    return float(supported.mean()),float(np.mean(evidence['distance'][y,x]))


def overlap_iou(contour,curve):
    all_points=np.concatenate((np.asarray(contour).reshape(-1,2),curve))
    x,y,w,h=cv2.boundingRect(all_points.astype(np.float32))
    if w*h>4_000_000 or min(w,h)<1:return 0.0
    offset=np.array([x,y]);a=np.zeros((h+2,w+2),np.uint8);b=a.copy()
    cv2.fillPoly(a,[np.round(np.asarray(contour).reshape(-1,2)-offset).astype(np.int32)],255)
    cv2.fillPoly(b,[np.round(curve-offset).astype(np.int32)],255)
    union=np.count_nonzero((a>0)|(b>0))
    return float(np.count_nonzero((a>0)&(b>0))/union) if union else 0.0


def ellipse_measure(contour,geometry,evidence):
    points=np.asarray(contour,dtype=np.float32).reshape(-1,2)
    cx,cy,a,b,angle=geometry
    curve=ellipse_points(geometry)
    # OpenCV's nearest ellipse points gives a geometric residual in image pixels.
    opencv=((float(cx),float(cy)),(float(a*2),float(b*2)),float(math.degrees(angle)))
    closest=cv2.getClosestEllipsePoints(opencv,points.reshape(-1,1,2)).reshape(-1,2)
    rms=float(np.sqrt(np.mean(np.sum((points-closest)**2,axis=1))))
    x=(points[:,0]-cx)*math.cos(angle)+(points[:,1]-cy)*math.sin(angle)
    y=-(points[:,0]-cx)*math.sin(angle)+(points[:,1]-cy)*math.cos(angle)
    bins=36 if b<18 else 72
    angles=(np.arctan2(y/b,x/a)+2*math.pi)%(2*math.pi)
    coverage=len(np.unique((angles/(2*math.pi)*bins).astype(int).clip(0,bins-1)))/bins
    support,boundary_error=boundary_measure(curve,evidence,tolerance=min(4,max(2,b*.025)))
    iou=overlap_iou(points,curve)
    fit=math.exp(-((rms/max(1,b))/.075)**2)
    base=.35*fit+.30*support+.15*coverage+.20*iou
    # An excellent algebraic fit without image evidence must not score highly.
    if support<.45:base*=support/.45
    return {'geometric_support_score':round(base,4),'rms_fit_error_px':round(rms,4),'normalized_rms_error':round(rms/b,5),'boundary_support_fraction':round(support,4),'mean_boundary_distance_px':round(boundary_error,4) if math.isfinite(boundary_error) else None,'trace_angular_coverage':round(coverage,4),'trace_fill_iou':round(iou,4),'fit_quality':round(fit,4)}


def canonical_ellipse(contour):
    (cx,cy),(width,height),angle=cv2.fitEllipseAMS(np.asarray(contour,dtype=np.float32).reshape(-1,1,2))
    if width<height:width,height=height,width;angle+=90
    return (float(cx),float(cy),float(width/2),float(height/2),math.radians(angle%180))


def valid_ellipse(geometry,shape):
    cx,cy,a,b,angle=geometry;h,w=shape
    return all(math.isfinite(v) for v in geometry) and 5<=b<=a and a/b<6 and a<max(w,h)*.55 and 0<=cx<w and 0<=cy<h


def fit_trace(contour,evidence,source='measured_trace'):
    """Measure a supplied trace as an ellipse/circle and/or a simple polygon."""
    points=np.asarray(contour,dtype=np.float32).reshape(-1,2)
    if len(points)<3 or not np.all(np.isfinite(points)):return []
    output=[]
    if len(points)>=5:
        try:
            geometry=canonical_ellipse(points)
            if valid_ellipse(geometry,evidence['edges'].shape):
                measured=ellipse_measure(points,geometry,evidence)
                kind='ellipse'
                if geometry[3]/geometry[2]>.91:
                    circle=(*geometry[:2],(geometry[2]+geometry[3])/2,(geometry[2]+geometry[3])/2,0)
                    circle_measure=ellipse_measure(points,circle,evidence)
                    if circle_measure['geometric_support_score']>=measured['geometric_support_score']-.025:
                        geometry,measured,kind=circle,circle_measure,'circle'
                output.append({'kind':kind,'geometry':list(geometry),'points':ellipse_points(geometry).tolist(),'measurements':measured,'sources':[source]})
        except cv2.error:pass
    perimeter=cv2.arcLength(points.reshape(-1,1,2),True)
    polygon=cv2.approxPolyDP(points.reshape(-1,1,2),perimeter*.025,True).reshape(-1,2)
    if len(polygon) in (3,4) and cv2.isContourConvex(polygon):
        kind='triangle'
        if len(polygon)==4:
            sides=np.roll(polygon,-1,axis=0)-polygon
            cosines=[abs(float(np.dot(sides[i],sides[(i+1)%4])))/max(1,float(np.linalg.norm(sides[i])*np.linalg.norm(sides[(i+1)%4]))) for i in range(4)]
            kind='rectangle' if max(cosines)<.25 else None
        if kind:
            curve=polygon_points(polygon);support,error=boundary_measure(curve,evidence)
            iou=overlap_iou(points,curve)
            measured={'geometric_support_score':round(.65*iou+.35*support,4),'trace_fill_iou':round(iou,4),'boundary_support_fraction':round(support,4),'mean_boundary_distance_px':round(error,4) if math.isfinite(error) else None,'vertices':len(polygon)}
            if support<.45:measured['geometric_support_score']*=support/.45
            output.append({'kind':kind,'vertices':polygon.tolist(),'points':curve.tolist(),'measurements':measured,'sources':[source]})
    return output


def similar(a,b):
    elliptical={'circle','ellipse'}
    if a['kind'] in elliptical and b['kind'] in elliptical:
        x,y,ra,rb,_=a['geometry'];xx,yy,sa,sb,_=b['geometry']
        return math.hypot(x-xx,y-yy)<max(3,min(rb,sb)*.25) and .67<ra/sa<1.5 and .67<rb/sb<1.5
    if a['kind']!=b['kind']:return False
    aa=np.mean(a['points'],axis=0);bb=np.mean(b['points'],axis=0)
    return np.linalg.norm(aa-bb)<4


def detect_shapes(image,min_score=.72,max_shapes=24):
    """Propose and measure primitives from multi-threshold/multi-scale contours."""
    cv2.setNumThreads(4);cv2.setRNGSeed(0)
    image=np.asarray(image,dtype=np.uint8)
    gray=cv2.cvtColor(image,cv2.COLOR_RGB2GRAY);evidence=edge_evidence(gray)
    foreground,background=foreground_evidence(image)
    h,w=gray.shape;proposals=[];traces=0
    def consume(binary,source):
        nonlocal traces
        contours,_=cv2.findContours(binary,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
        for contour in contours:
            area=abs(cv2.contourArea(contour))
            if len(contour)<15 or area<100 or area>w*h*.55:continue
            x,y,ww,hh=cv2.boundingRect(contour)
            if min(ww,hh)<11 or max(ww,hh)>min(ww,hh)*7 or x<2 or y<2 or x+ww>=w-2 or y+hh>=h-2:continue
            traces+=1
            measured=fit_trace(contour,evidence,source)
            proposals.extend(c for c in measured if c['measurements']['geometric_support_score']>=max(.4,min_score-.15))
    for sigma in (1.0,2.3,4.0):
        blurred=cv2.GaussianBlur(gray,(0,0),sigma)
        consume(cv2.Canny(blurred,35,100),f'edge_blur_{sigma}')
        for threshold in (35,55,75,95,120,145,170):
            binary=np.uint8(blurred<threshold)*255
            consume(binary,f'dark_{threshold}_blur_{sigma}')
    # Stable color regions can expose forms that grayscale merges together.
    low=cv2.resize(image,(max(1,w//3),max(1,h//3)),interpolation=cv2.INTER_AREA)
    lab=cv2.cvtColor(low,cv2.COLOR_RGB2LAB).astype(np.float32)
    _,labels,centers=cv2.kmeans(lab.reshape(-1,3),8,None,(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,25,.3),1,cv2.KMEANS_PP_CENTERS)
    labels=labels.reshape(low.shape[:2])
    for i in range(len(centers)):
        mask=cv2.resize(np.uint8(labels==i)*255,(w,h),interpolation=cv2.INTER_NEAREST)
        mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
        consume(mask,f'color_region_{i}')
    # Merge near-identical threshold/scale proposals; retain independent source evidence.
    proposals.sort(key=lambda c:c['measurements']['geometric_support_score'],reverse=True)
    merged=[]
    for candidate in proposals:
        duplicate=next((c for c in merged if similar(c,candidate)),None)
        if duplicate:duplicate['sources']=sorted(set(duplicate['sources']+candidate['sources']))
        else:merged.append(candidate)
    accepted=[]
    for c in merged:
        fraction=foreground_fraction(c['points'],foreground)
        c['foreground_fraction']=round(fraction,4) if background['uniform_border_detected'] else None
        if background['uniform_border_detected'] and fraction<.85:continue
        base=c['measurements']['geometric_support_score'];agreement=min(1,(len(c['sources'])-1)/4)
        c['measurements']['repeatability']=round(agreement,4)
        c['measurements']['geometric_support_score']=round(base*(.95+.05*agreement),4)
        if c['measurements']['geometric_support_score']>=min_score:accepted.append(c)
    accepted.sort(key=lambda c:c['measurements']['geometric_support_score'],reverse=True)
    accepted=accepted[:max_shapes]
    for i,c in enumerate(accepted):
        c['id']=f'A{i+1:02}';c['semantic_label']=None;c['review_required']=True
        c['score_band']='strong' if c['measurements']['geometric_support_score']>=.85 else 'moderate' if c['measurements']['geometric_support_score']>=.72 else 'weak'
        c['detail_candidate']=cv2.contourArea(np.asarray(c['points'],np.float32))<w*h*.0003
        if c['kind'] in ('circle','ellipse'):
            x,y,a,b,angle=c['geometry']
            for other in accepted:
                if other is c or other['kind'] not in ('circle','ellipse'):continue
                xx,yy,aa,bb,rotation=other['geometry']
                if a*b>aa*bb*.2:continue
                dx=(x-xx)*math.cos(rotation)+(y-yy)*math.sin(rotation)
                dy=-(x-xx)*math.sin(rotation)+(y-yy)*math.cos(rotation)
                if (dx/aa)**2+(dy/bb)**2<.6:c['detail_candidate']=True
    return {'candidates':accepted,'trace_count':traces,'raw_proposals':len(proposals),'merged_proposals':len(merged),'edge_map':evidence['edges'],'background_test':background}
