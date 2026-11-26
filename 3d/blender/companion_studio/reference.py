"""Model-first painting reference: render a companion's Blender master as the picture a player paints.

One orthographic view of the rest pose gives three files in `out`:

  colour.png       the model on a transparent film, lit softly and almost without shadow
  regions.png      the same view with every part filled by its drawing-order region, so stroke
                   timing follows the real model instead of rectangles guessed on a picture
  projection.json  camera, bounds, the region of every part and the construction guides: each guide
                   is a group of parts (or a bone chain) projected through this camera, in
                   normalised picture coordinates (0..1 across, 0..1 down)

Because the picture is the model, the guides, the stroke regions and the palette cannot drift from the
character the way hand-placed guides on generated art can. `tools/companion_review.py paper` gives
colour.png a watercolour paper finish.

    from gamecore_companion_studio import reference
    reference.render('Lion_v001.blend', 'out/lion', spec)

spec (all optional except guides):
  guides     [{name, stage, match: [regex on object names], mode}]
               mode 'ellipse' (default): one outline around every matching part
               mode 'each': one outline per bone that carries matching parts (legs, ears, eyes);
                            by='side' groups by left/right of the body instead, by='part' per object
               mode 'bones': one outline per regex in `bones`, covering the vertices of the matching
                            parts that those bones carry (feet of a one-piece body, beads down a tail)
               mode 'chain': a smooth curve through the joints of the bones matching match[0] (tails,
                            wing spines); smooth=False joins the joints with straight lines
               mode 'axis': a line between the centres of the two groups in match
               mode 'cross': face cross-lines on the head in `match` (centre line and eye line, at the
                            height of the parts in `eyes`), curved over the head for a three-quarter view
             shape options: corners=N draws a wedge (hull cut to N corners: beak, fan, bat wing) instead
               of an ellipse; fit='area' (default, hugs the shape) or 'extent'; grow=1.0 scales it;
               under=[regex] + under_fraction keeps only what hangs below that group (legs under a body);
               light=True marks a guide to draw faintly; far_light=True (mode each) marks the far side
  regions    [(regex, region)] tested first, against "object name|material name|dominant bone"
  rules      [(regex, region)] tested next, against the object name; default REGION_RULES
  hide       [regex] objects to leave out (review floors, helper meshes)
  azimuth, elevation   degrees; the camera stands in front of a -Y facing model, turned toward +X
  sun, ambient         light strengths; size (width, height); fill (share of the frame the model takes)

The constants import without Blender; render() needs bpy.
"""
import json
import math
import re
from pathlib import Path

VERSION = '1.1.0'
REGIONS = ('ears', 'head', 'face', 'body', 'tail', 'paws')
# Drawing-order region of a part, first match wins, tested against the object name.
REGION_RULES = [
    (r'^(chest mane|chest pom)', 'body'),
    (r'ear', 'ears'),
    (r'eye|nose|muzzle|chin|smile|whisker|beak|brow', 'face'),
    (r'tail|plume|feather|wing|brush', 'tail'),
    (r'paw|leg|foot|toe|ankle|thigh', 'paws'),
    (r'head|cheek|mane|topknot|crest|bow', 'head'),
]
REGION_COLOURS = {'ears': (255, 0, 0), 'head': (0, 255, 0), 'face': (0, 0, 255), 'body': (255, 255, 0), 'tail': (255, 0, 255), 'paws': (0, 255, 255)}
DEFAULTS = dict(azimuth=35.0, elevation=8.0, sun=.55, ambient=.82, size=(1200, 1312), fill=.84)


def region_of(name, material, bone, custom=(), rules=REGION_RULES):
    """Region of one part. custom rules see "name|material|dominant bone"; rules see the name only."""
    key = f'{name}|{material}|{bone}'
    for pattern, region in custom:
        if re.search(pattern, key, re.I): return region
    for pattern, region in rules:
        if re.search(pattern, name, re.I): return region
    return 'body'


def region_lookup(regions_png):
    """region(u, v) for a rendered regions.png; a point off the model takes the nearest part's region.
    Needs numpy and Pillow, not Blender."""
    import numpy as np
    from PIL import Image
    ids = np.asarray(Image.open(regions_png).convert('RGBA')); names = list(REGION_COLOURS); centres = np.array([REGION_COLOURS[n] for n in names], float)
    solid = ids[..., 3] > 127; label = ((ids[..., :3].astype(float)[..., None, :] - centres) ** 2).sum(-1).argmin(-1)
    ys, xs = np.nonzero(solid)
    def region(u, v):
        x = min(ids.shape[1] - 1, max(0, int(u * ids.shape[1]))); y = min(ids.shape[0] - 1, max(0, int(v * ids.shape[0])))
        if not solid[y, x]:
            i = ((xs - x) ** 2 + (ys - y) ** 2).argmin(); x, y = xs[i], ys[i]
        return names[label[y, x]]
    return region


def hull(points):
    """Convex hull of 2D points, counter-clockwise, as a numpy array."""
    import numpy as np
    pts = sorted(set(map(tuple, np.round(np.asarray(points, dtype=float), 3))))
    if len(pts) < 3: return np.array(pts)
    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and (out[-1][0] - out[-2][0]) * (p[1] - out[-2][1]) - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0]) <= 0: out.pop()
            out.append(p)
        return out[:-1]
    return np.array(half(pts) + half(pts[::-1]))


def outline(points, count=72, fit='area', grow=1.0):
    """Closed outline of 2D points as an ellipse (numpy array in, list of [x, y] out).
    fit 'area': the ellipse with the same area moments as the points' convex hull; it hugs the shape
    (a torso, a pom) instead of reaching to its furthest corner. fit 'extent': principal-axis bounds."""
    import numpy as np
    points = np.asarray(points, dtype=float); t = np.linspace(0, math.tau, count + 1); ring = np.stack([np.cos(t), np.sin(t)], 1)
    h = hull(points) if fit == 'area' else None
    if h is not None and len(h) >= 3:
        c = h.mean(0); A = 0.0; first = np.zeros(2); second = np.zeros((2, 2))
        for i in range(len(h)):
            v = np.array([c, h[i], h[(i + 1) % len(h)]]); d1, d2 = v[1] - v[0], v[2] - v[0]; area = abs(d1[0] * d2[1] - d1[1] * d2[0]) / 2; total = v.sum(0)
            A += area; first += area * total / 3; second += area / 12 * (np.outer(total, total) + sum(np.outer(x, x) for x in v))
        if A > 1e-9:
            mean = first / A; values, vectors = np.linalg.eigh(second / A - np.outer(mean, mean))
            return (mean + (ring * 2 * np.sqrt(np.maximum(values, 1e-9)) * grow) @ vectors.T).tolist()
    centre = points.mean(0); _, _, axes = np.linalg.svd(points - centre, full_matrices=False)
    local = (points - centre) @ axes.T; lo, hi = local.min(0), local.max(0); mid = (lo + hi) / 2; rad = (hi - lo) / 2 * grow
    return (centre + (mid + ring * rad) @ axes).tolist()


def wedge(points, corners=3):
    """The convex hull cut down to `corners` points, closed: a beak triangle, a tail fan, a bat wing."""
    import numpy as np
    h = [tuple(p) for p in hull(points)]
    while len(h) > max(3, corners):
        areas = [abs((h[i - 1][0] - h[i][0]) * (h[(i + 1) % len(h)][1] - h[i][1]) - (h[i - 1][1] - h[i][1]) * (h[(i + 1) % len(h)][0] - h[i][0])) for i in range(len(h))]
        h.pop(int(np.argmin(areas)))
    return [list(p) for p in h] + [list(h[0])]


def _dominant_bone(ob):
    totals = {}
    for v in ob.data.vertices:
        for g in v.groups: totals[g.group] = totals.get(g.group, 0) + g.weight
    return ob.vertex_groups[max(totals, key=totals.get)].name if totals else ''


def render(blend, out, spec, label=None):
    """Open `blend`, render colour.png and regions.png into `out`, write projection.json and return its summary."""
    import bpy
    import numpy as np
    from mathutils import Vector
    s = {**DEFAULTS, **{k: v for k, v in spec.items() if v is not None}}; W, H = s['size']; azimuth, elevation = s['azimuth'], s['elevation']
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    scene = bpy.context.scene; scene.frame_set(1)
    rig = next((o for o in scene.objects if o.type == 'ARMATURE'), None)
    if rig and rig.animation_data:                      # rest pose: no clip may leak into the picture
        rig.animation_data.action = None
        for track in rig.animation_data.nla_tracks: track.mute = True
        for pb in rig.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
    custom = s.get('regions', []); rules = s.get('rules', REGION_RULES)
    hidden = [re.compile(p, re.I) for p in s.get('hide', [])]
    meshes = []
    for o in scene.objects:
        if o.type != 'MESH': continue
        if o.hide_render or any(p.search(o.name) for p in hidden): o.hide_render = True; continue
        meshes.append(o)
    bpy.context.view_layer.update(); deps = bpy.context.evaluated_depsgraph_get()
    def world_points(ob):
        me = ob.evaluated_get(deps).to_mesh(); co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co)
        m = np.array(ob.matrix_world); return co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
    az, el = math.radians(azimuth), math.radians(elevation)
    forward = Vector((-math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), -math.sin(el)))     # camera sits in front (-Y) and to +X
    right = forward.cross(Vector((0, 0, 1))).normalized(); up = right.cross(forward).normalized()
    R, U = np.array(right), np.array(up)
    cloud = {o.name: world_points(o) for o in meshes}
    everything = np.concatenate(list(cloud.values()))
    a, b = everything @ R, everything @ U; amid, bmid = (a.min() + a.max()) / 2, (b.min() + b.max()) / 2
    scale = max(b.max() - b.min(), (a.max() - a.min()) * H / W) / s['fill']                         # ortho_scale spans the taller side
    def project(points):
        p = np.asarray(points, dtype=float).reshape(-1, 3)
        return np.stack([(.5 + (p @ R - amid) / (scale * W / H)) * W, (.5 - (p @ U - bmid) / scale) * H], 1)
    cam_data = bpy.data.cameras.new('Reference camera'); cam_data.type = 'ORTHO'; cam_data.ortho_scale = scale; cam_data.clip_end = 100
    cam = bpy.data.objects.new('Reference camera', cam_data); scene.collection.objects.link(cam); scene.camera = cam
    depth = float((everything @ np.array(forward)).mean())
    cam.location = Vector(R * amid + U * bmid) + forward * (depth - 20)
    cam.rotation_euler = forward.to_track_quat('-Z', 'Y').to_euler()
    for o in list(scene.objects):
        if o.type == 'LIGHT': bpy.data.objects.remove(o, do_unlink=True)
    sun = bpy.data.objects.new('Soft key', bpy.data.lights.new('Soft key', 'SUN')); scene.collection.objects.link(sun)
    sun.data.energy = s['sun']; sun.data.angle = math.radians(40)
    sun.rotation_euler = (forward + right * -.5 + Vector((0, 0, -.75))).normalized().to_track_quat('-Z', 'Y').to_euler()
    world = bpy.data.worlds.new('Paper light'); world.use_nodes = True; scene.world = world
    world.node_tree.nodes['Background'].inputs[0].default_value = (1, 1, 1, 1); world.node_tree.nodes['Background'].inputs[1].default_value = s['ambient']
    r = scene.render; r.engine = 'BLENDER_EEVEE'; r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
    r.film_transparent = True; r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGBA'
    scene.view_settings.view_transform = 'Standard'; scene.view_settings.look = 'None'; scene.view_settings.exposure = 0; scene.view_settings.gamma = 1
    r.filepath = str(out / 'colour.png'); bpy.ops.render.render(write_still=True)

    # Region pass: flat emission per part, one sample, no filtering.
    flat = {}
    for region, colour in REGION_COLOURS.items():
        m = bpy.data.materials.new('REGION ' + region); m.use_nodes = True; nodes = m.node_tree.nodes; nodes.clear()
        e = nodes.new('ShaderNodeEmission'); e.inputs[0].default_value = (*[(c / 255) ** 2.2 for c in colour], 1); o_ = nodes.new('ShaderNodeOutputMaterial')
        m.node_tree.links.new(e.outputs[0], o_.inputs[0]); flat[region] = m
    parts = {}
    for o in meshes:
        region = region_of(o.name, o.data.materials[0].name if o.data.materials else '', _dominant_bone(o), custom, rules); parts[o.name] = region
        o.data = o.data.copy(); o.data.materials.clear(); o.data.materials.append(flat[region])
        for p in o.data.polygons: p.material_index = 0
    try: scene.eevee.taa_render_samples = 1
    except Exception: pass
    r.filter_size = .01; r.filepath = str(out / 'regions.png'); bpy.ops.render.render(write_still=True)

    # Guides: outlines of part groups, wedges, lines along bone chains, face cross-lines; normalised picture coordinates.
    def norm(pixels): return [[round(x / W, 5), round(y / H, 5)] for x, y in pixels]
    def group(patterns): return [n for n in cloud if any(re.search(p, n, re.I) for p in patterns)]
    bone_of = {}
    def vertex_bones(name):
        """Dominant bone name of every vertex of one part."""
        if name not in bone_of:
            ob = bpy.data.objects[name]; names = [g.name for g in ob.vertex_groups]
            bone_of[name] = np.array([names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in ob.data.vertices])
        return bone_of[name]
    def gather(names, g):
        """World points of parts, optionally only the stretch that hangs below another group (legs under a body)."""
        pts = np.concatenate([cloud[n] for n in names])
        if g.get('under') and group(g['under']):
            ref = np.concatenate([cloud[n] for n in group(g['under'])]); cut = ref[:, 2].min() + g.get('under_fraction', .3) * (ref[:, 2].max() - ref[:, 2].min())
            kept = pts[pts[:, 2] < cut]; pts = kept if len(kept) >= 8 else pts
        return pts
    def shape(points3d, g):
        flat2 = project(points3d)
        if g.get('corners'): return dict(type='line', points=norm(wedge(flat2, g['corners'])))
        return dict(type='ellipse', points=norm(outline(flat2, fit=g.get('fit', 'area'), grow=g.get('grow', 1.0))))
    guides = []
    def add(name, g, points3d=None, **made):
        entry = dict(name=name, stage=g['stage'], **(made or shape(points3d, g)))
        if g.get('light'): entry['light'] = True
        guides.append(entry); return entry
    for g in s['guides']:
        mode = g.get('mode', 'ellipse')
        if mode == 'ellipse':
            names = group(g['match'])
            if names: add(g['name'], g, gather(names, g))
        elif mode == 'each':
            # One shape per bone that carries matching parts (legs, ears), per side of the body, or per part.
            names = group(g['match']); by = g.get('by', 'bone'); sets = {}
            for n in names:
                key = _dominant_bone(bpy.data.objects[n]) if by == 'bone' else ('L' if cloud[n][:, 0].mean() < 0 else 'R') if by == 'side' else n
                sets.setdefault(key, []).append(n)
            if by == 'bone' and len(sets) == 1 and len(names) > 1: sets = {n: [n] for n in names}      # both sides on one bone: one outline per part
            made = [gather(members, g) for members in sets.values()]
            near_side = 1.0 if math.sin(az) >= 0 else -1.0                         # the camera stands toward +X when azimuth is positive
            lateral = [float(p[:, 0].mean()) * near_side for p in made]
            order = sorted(range(len(made)), key=lambda i: project(made[i])[:, 0].mean())
            for rank, i in enumerate(order):
                entry = add(f"{g['name']} {rank + 1}", g, made[i])
                if g.get('far_light') and len(made) > 1 and lateral[i] < -1e-3: entry['light'] = True      # limbs on the side away from the camera read lighter
        elif mode == 'bones':
            # One shape per bone group: match picks the parts, every regex in `bones` picks the vertices one shape covers.
            names = group(g['match'])
            for i, pattern in enumerate(g['bones']):
                chosen = [cloud[n][np.array([bool(re.search(pattern, b, re.I)) for b in vertex_bones(n)], dtype=bool)] for n in names]
                pts = np.concatenate(chosen) if chosen else np.zeros((0, 3))
                if len(pts) >= 8: add(g['name'] if len(g['bones']) == 1 else f"{g['name']} {i + 1}", g, pts)
        elif mode == 'chain' and rig:
            bones = [b for b in rig.data.bones if re.search(g['match'][0], b.name, re.I)]
            if bones:
                m = rig.matrix_world; pts = np.array([tuple(m @ bones[0].head_local)] + [tuple(m @ b.tail_local) for b in bones])
                if len(pts) > 2 and g.get('smooth', True):          # one drawn curve through the joints (Catmull-Rom)
                    curve = []
                    for i in range(len(pts) - 1):
                        p0, p1, p2, p3 = pts[max(0, i - 1)], pts[i], pts[i + 1], pts[min(len(pts) - 1, i + 2)]
                        for t in np.linspace(0, 1, 8, endpoint=False):
                            curve.append(.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3))
                    pts = np.array(curve + [pts[-1]])
                add(g['name'], g, type='line', points=norm(project(pts)))
        elif mode == 'axis':
            ends = [project(np.concatenate([cloud[n] for n in group([p])])).mean(0) for p in g['match'] if group([p])]
            if len(ends) == 2: add(g['name'], g, type='line', points=norm(ends))
        elif mode == 'cross':
            # Face cross-lines on a -Y facing head: the centre line down the front and the eye line across it,
            # both drawn on the head's bounding ellipsoid so they bend with the three-quarter view.
            names = group(g['match'])
            if not names: continue
            pts = np.concatenate([cloud[n] for n in names]); lo, hi = pts.min(0), pts.max(0); c = (lo + hi) / 2; rad = (hi - lo) / 2
            eyes = group(g.get('eyes', [])); eye_z = float(np.concatenate([cloud[n] for n in eyes])[:, 2].mean()) if eyes else float(c[2])
            sweep = np.radians(np.linspace(72, -72, 25))
            centre_line = [(c[0], c[1] - rad[1] * math.cos(a), c[2] + rad[2] * math.sin(a)) for a in sweep]
            k = math.sqrt(max(.05, 1 - ((eye_z - c[2]) / rad[2]) ** 2))
            eye_line = [(c[0] + rad[0] * k * math.sin(a), c[1] - rad[1] * k * math.cos(a), eye_z) for a in sweep]
            add(g['name'] + ' centre line', g, type='line', points=norm(project(centre_line)))
            add(g['name'] + ' eye line', g, type='line', points=norm(project(eye_line)))
    result = dict(animal=label, blend=str(blend), size=[W, H], azimuth=azimuth, elevation=elevation, ortho_scale=scale,
                  model_height=float(everything[:, 2].max() - everything[:, 2].min()), model_top=float(everything[:, 2].max()),
                  model_radius=float(np.hypot(everything[:, 0], everything[:, 1]).max()), parts=parts, guides=guides)
    (out / 'projection.json').write_text(json.dumps(result, indent=1), encoding='utf-8')
    return {'guides': len(guides), 'parts': len(parts), 'height': result['model_height'], 'top': result['model_top'], 'radius': result['model_radius']}
