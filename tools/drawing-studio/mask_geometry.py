"""Fast planar construction from foreground evidence; no anatomical certainty implied."""
import cv2
import numpy as np
from shape_geometry import ellipse_points, polygon_points


def foreground(image):
    rgb=np.asarray(image); small=cv2.resize(rgb,(640,349))
    lab=cv2.cvtColor(small,cv2.COLOR_RGB2LAB).astype(np.float32)
    # Sample all edges, including source background beside normalization padding.
    border=np.concatenate([lab[2,::8],lab[-3,::8],lab[::8,2],lab[::8,-3]])
    colors=np.unique((border/6).astype(int),axis=0)*6+3
    distance=np.full(lab.shape[:2],np.inf)
    for color in colors: distance=np.minimum(distance,np.linalg.norm(lab-color,axis=2))
    mask=(distance>18).astype(np.uint8)
    mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    n,labels,stats,_=cv2.connectedComponentsWithStats(mask)
    if n<2: return np.zeros(rgb.shape[:2],np.uint8),{'usable':False}
    largest=1+np.argmax(stats[1:,cv2.CC_STAT_AREA]); mask=(labels==largest).astype(np.uint8)
    fraction=float(mask.mean()); usable=.01<fraction<.8
    return cv2.resize(mask,(image.width,image.height),interpolation=cv2.INTER_NEAREST),{'usable':usable,'method':'border-color distance, largest component','foreground_fraction':fraction,'review_required':True}


def region(mask,box):
    x1,y1,x2,y2=np.rint(box).astype(int)
    h,w=mask.shape; x1,x2=np.clip([x1,x2],0,w); y1,y2=np.clip([y1,y2],0,h)
    out=np.zeros_like(mask); out[y1:y2,x1:x2]=mask[y1:y2,x1:x2]
    return out


def measure(points,mask):
    raster=np.zeros_like(mask); cv2.fillPoly(raster,[np.rint(points).astype(np.int32)],1)
    hit=np.count_nonzero((raster>0)&(mask>0)); area=np.count_nonzero(raster)
    target=np.count_nonzero(mask)
    return {'spill_fraction':round(1-hit/max(1,area),4),'coverage':round(hit/max(1,target),4),'iou':round(hit/max(1,area+target-hit),4)}


def primitive(mask,kind='ellipse'):
    yy,xx=np.nonzero(mask)
    if len(xx)<20:return None
    coords=np.column_stack((xx,yy)).astype(np.float32)
    center=coords.mean(axis=0); values,vectors=np.linalg.eigh(np.cov(coords.T))
    axis=vectors[:,-1]; angle=float(np.arctan2(axis[1],axis[0]))
    radii=2*np.sqrt(np.maximum(values[::-1],1))
    candidates=[]
    if kind=='triangle':
        hull=cv2.convexHull(coords)
        _,vertices=cv2.minEnclosingTriangle(hull)
        if vertices is None:return None
        vertices=vertices.reshape(-1,2)
        candidates=[polygon_points(center+(vertices-center)*scale,90) for scale in (.8,.9,1)]
    else:
        for scale in (.8,.9,1,1.1):
            candidates.append(ellipse_points([*center,*(radii*scale),angle],90))
    scored=[(measure(p,mask),p) for p in candidates]
    metrics,points=max(scored,key=lambda item:item[0]['iou']-.4*item[0]['spill_fraction'])
    points[:,0]=points[:,0].clip(0,mask.shape[1]-1); points[:,1]=points[:,1].clip(0,mask.shape[0]-1)
    metrics['uncertainty_reasons']=[reason for condition,reason in [(metrics['spill_fraction']>.14,'high_part_spill'),(metrics['iou']<.45,'low_part_overlap')] if condition]
    return {'points':points.tolist()+[points[0].tolist()],'primitive':kind,'metrics':metrics}


def chain_masks(mask):
    """Estimate a centerline from transverse pixel medians, split at measured bends."""
    yy,xx=np.nonzero(mask)
    if len(xx)<40:return [mask]
    xy=np.column_stack((xx,yy)); center=xy.mean(axis=0)
    _,vectors=np.linalg.eigh(np.cov(xy.T)); axis=vectors[:,-1]
    along=(xy-center)@axis; edges=np.linspace(along.min(),along.max()+1,13)
    centers=[]
    for lo,hi in zip(edges[:-1],edges[1:]):
        selected=xy[(along>=lo)&(along<hi)]
        if len(selected):centers.append(np.median(selected,axis=0))
    curve=np.array(centers,np.float32)
    path=cv2.approxPolyDP(curve.reshape(-1,1,2),max(3,np.ptp(along)*.035),False).reshape(-1,2)
    if len(path)<2:return [mask]
    # Assign pixels to nearest polyline segment, preserving orientation and bends.
    distances=[]
    for a,b in zip(path[:-1],path[1:]):
        v=b-a; t=np.clip((xy-a)@v/max(1,float(v@v)),0,1)
        distances.append(np.sum((xy-(a+t[:,None]*v))**2,axis=1))
    owners=np.argmin(distances,axis=0); result=[]
    for i in range(len(distances)):
        sub=np.zeros_like(mask); pts=xy[owners==i]; sub[pts[:,1],pts[:,0]]=1
        if len(pts)>25:result.append(sub)
    return result or [mask]


def fit_part(mask,label):
    masks=chain_masks(mask) if label in ('leg','tail','unresolved appendage') else [mask]
    if label=='body':
        # Two geometric core masses, deliberately not asserted to be ribcage/pelvis.
        dist=cv2.distanceTransform(mask,cv2.DIST_L2,5)
        _,radius,_,first=cv2.minMaxLoc(dist)
        suppressed=dist.copy(); cv2.circle(suppressed,first,int(radius*1.3),0,-1)
        _,second_radius,_,second=cv2.minMaxLoc(suppressed)
        if second_radius>radius*.45:
            yy,xx=np.indices(mask.shape)
            a=(xx-first[0])**2+(yy-first[1])**2
            b=(xx-second[0])**2+(yy-second[1])**2
            masks=[(mask*(a<=b+radius**2*.25)).astype(np.uint8),(mask*(b<=a+second_radius**2*.25)).astype(np.uint8)]
    kind='triangle' if label=='ear' else 'ellipse'
    return [p for m in masks if (p:=primitive(m,kind)) is not None]


def remainder_candidates(mask,covered,minimum_y):
    remainder=((mask>0)&(covered==0)).astype(np.uint8); remainder[:int(minimum_y)]=0
    count,labels,stats,_=cv2.connectedComponentsWithStats(remainder)
    result=[]
    for i in range(1,count):
        x,y,w,h,area=stats[i]
        if area>120 and h>30 and h/max(1,w)>1.4:
            result.append((labels==i).astype(np.uint8))
    return result[:4]


def unknown_masses(mask,limit=16):
    """Unlabeled distance-peak regions; never assign anatomy to generic geometry."""
    distance=cv2.distanceTransform(mask,cv2.DIST_L2,5); remaining=distance.copy(); seeds=[]
    for _ in range(limit):
        _,radius,_,center=cv2.minMaxLoc(remaining)
        if radius<7:break
        seeds.append(center);cv2.circle(remaining,center,max(14,int(radius*1.5)),0,-1)
    yy,xx=np.nonzero(mask)
    if not seeds:return []
    xy=np.column_stack((xx,yy)); owners=np.argmin(np.sum((xy[:,None]-np.asarray(seeds)[None])**2,axis=2),axis=1)
    shapes=[]
    for i in range(len(seeds)):
        sub=np.zeros_like(mask); pts=xy[owners==i];sub[pts[:,1],pts[:,0]]=1
        shape=primitive(sub)
        if shape:shapes.append(shape)
    return shapes
