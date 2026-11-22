"""Convert solid-color SVG paths/circles into layered relief OBJ geometry.
Requires svgpathtools and shapely. Deliberately rejects unsupported transforms/images.
This produces editable 2.5D relief, not inferred full-volume character anatomy.
"""
import argparse, json, math, hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
from svgpathtools import parse_path, Line
from shapely.geometry import Polygon, LineString
from shapely import constrained_delaunay_triangles

def build(source, destination):
    source, destination = Path(source), Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    root = ET.parse(source).getroot()
    view = [float(v) for v in root.attrib.get('viewBox', '0 0 512 512').split()]
    if len(view) != 4 or view[2] <= 0 or view[3] <= 0: raise ValueError('Invalid viewBox')
    vertices, faces, materials = [], [], {}
    layer = 0
    def emit(geometry, color, depth, alpha=1.0):
        if color == 'none' or geometry.is_empty: return
        if not color.startswith('#') or len(color) not in [4, 7]: raise ValueError('Only solid hex colors supported: ' + color)
        if len(color) == 4: color = '#' + ''.join(c*2 for c in color[1:])
        name = 'ink_' + color[1:] + ('_a%03d'%round(alpha*1000) if alpha < 1 else '')
        materials[name] = [int(color[i:i+2], 16)/255 for i in [1,3,5]] + [alpha]
        polygons = list(geometry.geoms) if geometry.geom_type == 'MultiPolygon' else [geometry]
        for poly in polygons:
            if poly.geom_type != 'Polygon': continue
            # Unconstrained Delaunay + filtering can leave holes in concave
            # ribbons and curved outlines. Preserve the polygon boundary itself.
            triangles = list(constrained_delaunay_triangles(poly).geoms)
            if not math.isclose(sum(t.area for t in triangles), poly.area, rel_tol=1e-7, abs_tol=1e-7):
                raise ValueError('Triangulation did not preserve the polygon area')
            for tri in triangles:
                face=[]
                for x,y in list(tri.exterior.coords)[:3]:
                    vertices.append(((x-view[0]-view[2]/2)/view[2]*4, (view[1]+view[3]/2-y)/view[3]*4, depth))
                    face.append(len(vertices))
                faces.append((name, face))
    def walk(node, inherited):
        nonlocal layer
        attrs = dict(inherited);attrs.update(node.attrib)
        tag=node.tag.split('}')[-1]
        if tag == 'defs': return
        if 'transform' in node.attrib: raise ValueError('Flatten transforms before relief conversion')
        if tag in ['svg','g']:
            for child in node: walk(child,attrs)
            return
        if tag not in ['path','circle']: raise ValueError('Unsupported SVG element: '+tag)
        contours=[]
        if tag=='circle':
            x,y,r=[float(attrs.get(k,0)) for k in ['cx','cy','r']]
            contours=[[(x+math.cos(i*math.tau/48)*r,y+math.sin(i*math.tau/48)*r) for i in range(49)]]
        else:
            for sub in parse_path(attrs['d']).continuous_subpaths():
                pts=[]
                for seg in sub:
                    n=1 if isinstance(seg,Line) else 16
                    pts.extend((seg.point(i/n).real,seg.point(i/n).imag) for i in range(n))
                pts.append((sub[-1].end.real,sub[-1].end.imag))
                contours.append(pts)
        fill=attrs.get('fill','#000000');stroke=attrs.get('stroke','none');alpha=float(attrs.get('opacity',1))
        for pts in contours:
            if len(pts)>=3 and fill!='none':emit(Polygon(pts).buffer(0),fill,layer*0.008,alpha*float(attrs.get("fill-opacity",1)))
            if len(pts)>=2 and stroke!='none':emit(LineString(pts).buffer(float(attrs.get('stroke-width',1))/2, quad_segs=3),stroke,layer*0.008+0.003,alpha*float(attrs.get("stroke-opacity",1)))
        layer+=1
    walk(root,{})
    destination.parent.mkdir(parents=True,exist_ok=True)
    lines=['# Original source: '+source.name]
    lines.extend('v %.6f %.6f %.6f'%v for v in vertices)
    previous=None
    for material, face in faces:
        if material != previous:lines.append('usemtl '+material);previous=material
        lines.append('f '+' '.join(map(str,face)))
    destination.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    metadata={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'geometry_version':2,'materials':materials,'triangles':len(faces),'layers':layer,'units':'4-unit normalized relief','dimension':'2.5d'}
    destination.with_suffix('.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    return metadata
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source');parser.add_argument('output')
    a=parser.parse_args(); print(json.dumps(build(a.source,a.output)))
