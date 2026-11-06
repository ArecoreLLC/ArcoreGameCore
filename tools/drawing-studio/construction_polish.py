"""Display-only overlap hierarchy and conservative image-supported muzzle orientation."""
import cv2
import numpy as np
from shape_geometry import ellipse_points
from mask_geometry import measure


def polish_guides(guides):
    """Fade torso arcs inside limbs. Leave all painting polygons intact."""
    limbs=[np.asarray(g['points'],np.float32) for g in guides if g.get('canonical_part')=='part.leg']
    for guide in guides:
        points=guide['points']; weights=[]
        for a,b in zip(points[:-1],points[1:]):
            midpoint=((a[0]+b[0])/2,(a[1]+b[1])/2)
            behind=guide.get('canonical_part')=='part.torso' and any(cv2.pointPolygonTest(p,midpoint,False)>=0 for p in limbs)
            weights.append(.22 if behind else 1.0)
        guide['segment_opacity']=weights
    return guides


def align_muzzle(image,mask,shape):
    """Use a long upper-muzzle edge as a cue, only if silhouette fit is preserved."""
    yy,xx=np.nonzero(mask)
    evidence={'applied':False,'method':'upper-region line cue; not verified nose bridge'}
    if len(xx)<30:return shape,evidence
    x1,x2=int(xx.min()),int(xx.max()+1); y1,y2=int(yy.min()),int(yy.max()+1)
    gray=cv2.cvtColor(np.asarray(image)[y1:y2,x1:x2],cv2.COLOR_RGB2GRAY)
    edge=cv2.Canny(gray,45,110); edge[int(edge.shape[0]*.65):]=0
    lines=cv2.HoughLinesP(edge,1,np.pi/180,threshold=10,minLineLength=max(8,(x2-x1)*.25),maxLineGap=4)
    if lines is None:return shape,evidence
    coords=np.column_stack((xx,yy)); center=coords.mean(axis=0)
    old=measure(shape['points'],mask); best=None
    for a,b,c,d in lines[:,0]:
        angle=float(np.arctan2(d-b,c-a)); axis=np.array([np.cos(angle),np.sin(angle)])
        normal=np.array([-axis[1],axis[0]])
        radii=2*np.sqrt([np.var((coords-center)@axis),np.var((coords-center)@normal)])
        if radii[0]<radii[1]:continue
        for scale in (.8,.9,1):
            points=ellipse_points([*center,*(radii*scale),angle],90)
            metrics=measure(points,mask)
            if metrics['iou']>=old['iou']-.025 and metrics['spill_fraction']<=old['spill_fraction']+.02:
                score=np.hypot(c-a,d-b)+metrics['iou']*10
                if best is None or score>best[0]:best=(score,points,metrics,angle)
    if best:
        _,points,metrics,angle=best
        shape={**shape,'points':points.tolist()+[points[0].tolist()],'metrics':metrics}
        evidence.update(applied=True,angle_degrees=round(float(np.degrees(angle)),2))
    return shape,evidence
