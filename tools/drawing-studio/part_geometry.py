"""Constrained, image-supported construction geometry (scores are not probabilities)."""
import cv2
import numpy as np
from shape_geometry import ellipse_points, polygon_points


def individual_detections(detections):
    """Discard group boxes containing two separate detections of the same part."""
    result=[]
    for label,box in detections:
        contained=0
        for other,b in detections:
            if other!=label or b is box: continue
            area=(b[2]-b[0])*(b[3]-b[1])
            if area >= .7*(box[2]-box[0])*(box[3]-box[1]): continue
            intersection=max(0,min(box[2],b[2])-max(box[0],b[0]))*max(0,min(box[3],b[3])-max(box[1],b[1]))
            if intersection/max(1,area)>.85: contained+=1
        if contained<2: result.append((label,box))
    return result


def torso_box(detections):
    """Side-view quadruped prior; abstain without neck, tail and leg anchors."""
    def boxes(name): return [b for label,b in detections if label.lower()==name]
    neck,tail,legs=boxes('neck'),boxes('tail'),boxes('leg')
    if not neck or not tail or not legs: return None
    n,t=neck[0],tail[0]
    nc=(n[0]+n[2])/2; tc=(t[0]+t[2])/2
    left,right=(nc,t[0]) if tc>nc else (t[2],nc)
    top=n[1]+.12*(n[3]-n[1])
    bottom=float(np.median([b[1] for b in legs]))+.10*(n[3]-n[1])
    if right-left<30 or bottom-top<30: return None
    return [left,top,right,bottom]


def fit_geometry(image, box, triangle=False):
    """Search near a semantic box for edge-supported size, tilt and position."""
    x1,y1,x2,y2=box; w=x2-x1; h=y2-y1
    gray=cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2GRAY)
    edges=cv2.Canny(gray,45,110)
    distance=cv2.distanceTransform(255-edges,cv2.DIST_L2,3)
    best=None
    for dx in (-.06,0,.06):
        for dy in (-.06,0,.06):
            for sx in (.82,.94,1.04):
                for sy in (.82,.94,1.04):
                    for angle in (-.3,0,.3):
                        cx=(x1+x2)/2+dx*w; cy=(y1+y2)/2+dy*h
                        if triangle:
                            vertices=np.array([[0,-h*sy/2],[-w*sx/2,h*sy/2],[w*sx/2,h*sy/2]])
                            rot=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
                            points=polygon_points(vertices@rot.T+[cx,cy],90)
                        else: points=ellipse_points([cx,cy,w*sx/2,h*sy/2,angle],90)
                        xx=np.rint(points[:,0]).astype(int).clip(0,image.width-1)
                        yy=np.rint(points[:,1]).astype(int).clip(0,image.height-1)
                        distances=distance[yy,xx]
                        support=float(np.mean(np.exp(-distances/3)))
                        score=support-.07*(abs(sx-1)+abs(sy-1))-.1*(abs(dx)+abs(dy))
                        if best is None or score>best[0]: best=(score,points,support)
    points=best[1]; points[:,0]=points[:,0].clip(0,image.width-1); points[:,1]=points[:,1].clip(0,image.height-1)
    return points.tolist()+[points[0].tolist()],round(best[2],3)
