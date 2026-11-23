"""Painted albedo atlas for vertex-coloured, part-built characters, written for Blender's Python.

Module: gamecore.blender.companion-studio (see README.md beside this file).

Every art part (one mesh object, one material, a POINT colour attribute named "Color") gets its
own chart in one atlas. Colour is evaluated per texel from the part's rest position, so markings
are as crisp as the texture rather than the mesh, and the pigment texture runs continuously across
parts. The consumer supplies `painter(T)`: its markings, in display sRGB, as a function of
position. Everything else here is generic: charts, packing, rasterising, pigment wash, contact
pooling, fibre handling and attaching the image to the materials.

Colours inside painters are display sRGB (0..1), exactly as sampled from the reference art.
The numpy helpers import without Blender; bake() needs bpy.
"""
import re, numpy as np
from types import SimpleNamespace

VERSION = '1.0.0'
SIZE = 2048   # default atlas edge in texels
PAD = 8       # painted margin around each chart, keeps mip levels clean


# ---------- colour helpers ----------
def H(h):
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])

def to_srgb(l):
    l = np.clip(l, 0, 1)
    return np.where(l < .0031308, l * 12.92, 1.055 * l ** (1 / 2.4) - .055)

def to_linear(s):
    s = np.clip(s, 0, 1)
    return np.where(s < .04045, s / 12.92, ((s + .055) / 1.055) ** 2.4)

def S(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)

def lerp(c, col, m):
    m = np.clip(m, 0, 1)[:, None]
    return c * (1 - m) + np.asarray(col) * m

def ellipse(u, v, cu, cv, ru, rv, rot=0.0, soft=.10):
    """1 inside a (rotated) ellipse, 0 outside, with a soft painted edge."""
    du, dv = u - cu, v - cv
    if rot:
        c, s = np.cos(rot), np.sin(rot)
        du, dv = du * c + dv * s, -du * s + dv * c
    return 1 - S(1 - soft, 1 + soft, np.hypot(du / ru, dv / rv))

def pool(c, m, amount=.16):
    """Pigment pools along the edge of a wash: darken where a mask crosses one half."""
    band = 4 * m * (1 - m)
    return np.clip(c, 1e-4, 1) ** (1 + amount * band)[:, None]


# ---------- noise ----------
def _hash(ix, iy, iz, seed):
    h = (ix * 374761393 + iy * 668265263 + iz * 1274126177 + seed * 974711) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFF) / 16777215.0

def vnoise(P, freq, seed=0):
    """Smooth value noise in 0..1; freq may be a 3-vector for combed (anisotropic) grain."""
    Q = P * np.asarray(freq, dtype=float)
    F = np.floor(Q); f = Q - F; f = f * f * (3 - 2 * f); I = F.astype(np.int64)
    x, y, z = I[:, 0], I[:, 1], I[:, 2]; fx, fy, fz = f[:, 0], f[:, 1], f[:, 2]
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (fx if dx else 1 - fx) * (fy if dy else 1 - fy) * (fz if dz else 1 - fz)
                out = out + w * _hash(x + dx, y + dy, z + dz, seed)
    return out

def jag(T, amp=.03, freq=34, seed=40):
    """Small signed offset for ragged fur-stroke edges on markings."""
    return (vnoise(T.P, (freq, freq, freq * .45), T.seed + seed) - .5) * 2 * amp

def wash(c, P, kind, seed, k=1.0):
    """Watercolour pigment: broad wash drift, soft dab blotches, paper tooth and combed fur grain.
    Less pigment lifts toward paper white; more pigment deepens and saturates."""
    big = (vnoise(P, 1.7, seed) + .5 * vnoise(P, 3.9, seed + 1)) / 1.5 - .5
    blot = S(.3, .7, vnoise(P, 11, seed + 2)) - .5
    grain = vnoise(P, 95, seed + 3) - .5
    fine = vnoise(P, 230, seed + 4) - .5
    d = .20 * big + .08 * blot + .08 * grain + .05 * fine
    if kind == 'fur':
        d = d + .12 * (vnoise(P, (70, 70, 13), seed + 5) - .5) + .06 * (vnoise(P, (150, 150, 30), seed + 6) - .5)
    return np.clip(c, 1e-4, 1) ** np.exp(-d * k)[:, None]


# ---------- charts ----------
def _kind(ob):
    label = ob.data.materials[0].name.split('|')[-1].lower()
    for kind in ('fur', 'eye', 'nose', 'silk'):
        if kind in label: return kind
    return 'skin'

def _coords(me):
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co)
    return co.reshape(-1, 3)

def _chart(ob):
    """Per-loop chart coordinates in 0..1 and the chart's size in model units."""
    me = ob.data; co = _coords(me); lo, hi = co.min(0), co.max(0); ext = np.maximum(hi - lo, 1e-5)
    nloops = len(me.loops); lv = np.empty(nloops, dtype=np.int32); me.loops.foreach_get('vertex_index', lv)
    if ob.get('chart') == 'sphere' and me.uv_layers:
        uv = np.empty(nloops * 2); me.uv_layers.active.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
        rh = (ext[0] + ext[1]) / 4; rz = ext[2] / 2
        return uv, 2 * np.pi * rh, np.pi * np.sqrt((rh * rh + rz * rz) / 2)
    # Everything else: a two-sided planar chart across its thinnest axis (front half, back half).
    axis = int(np.argmin(ext)); a, b = [i for i in range(3) if i != axis]
    normals = np.empty(len(me.polygons) * 3); me.polygons.foreach_get('normal', normals)
    back = normals.reshape(-1, 3)[:, axis] > 0
    totals = np.empty(len(me.polygons), dtype=np.int32); me.polygons.foreach_get('loop_total', totals)
    loop_back = np.repeat(back, totals)
    u = (co[lv, a] - lo[a]) / ext[a]; v = (co[lv, b] - lo[b]) / ext[b]
    uv = np.stack([np.where(loop_back, .52 + u * .48, u * .48), v], 1)
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    return uv, ext[a] * 2.08, ext[b]

def _pack(sizes, scale, size=SIZE):
    """Shelf packing; returns positions, or None when the atlas overflows."""
    order = sorted(range(len(sizes)), key=lambda i: -sizes[i][1]); pos = [None] * len(sizes)
    x = y = shelf = 0
    for i in order:
        w = max(6, int(round(sizes[i][0] * scale))) + 2 * PAD; h = max(6, int(round(sizes[i][1] * scale))) + 2 * PAD
        if w > size: return None
        if x + w > size: x = 0; y += shelf; shelf = 0
        if y + h > size: return None
        pos[i] = (x, y, w, h); x += w; shelf = max(shelf, h)
    return pos

def _raster(uv, att, w, h):
    """Scatter barycentric samples of every triangle into a w*h canvas."""
    canvas = np.zeros((h, w, att.shape[2])); mask = np.zeros((h, w), bool)
    edge = np.max(np.linalg.norm(uv - np.roll(uv, 1, axis=1), axis=2), axis=1)
    steps = np.clip(np.ceil(edge * 1.8).astype(int) + 1, 1, 400)
    for s in np.unique(steps):
        index = np.nonzero(steps == s)[0]
        i, j = np.meshgrid(np.arange(s + 1), np.arange(s + 1), indexing='ij'); keep = (i + j) <= s
        B = np.stack([i[keep], j[keep], s - i[keep] - j[keep]], 1) / s
        chunk = max(1, int(300000 / len(B)))
        for start in range(0, len(index), chunk):
            part = index[start:start + chunk]
            p = np.einsum('mk,tkc->tmc', B, uv[part]).reshape(-1, 2)
            value = np.einsum('mk,tkc->tmc', B, att[part]).reshape(-1, att.shape[2])
            x = np.clip(p[:, 0].astype(int), 0, w - 1); y = np.clip(p[:, 1].astype(int), 0, h - 1)
            canvas[y, x] = value; mask[y, x] = True
    return canvas, mask

def _dilate(canvas, mask, rounds):
    for _ in range(rounds):
        if mask.all(): break
        for shift in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            take = np.roll(mask, shift, (0, 1)) & ~mask
            canvas[take] = np.roll(canvas, shift, (0, 1))[take]; mask = mask | take
    return mask

def _crease(P, own, ellipsoids, skip=('muzzle',)):
    """Soft pigment pooled where another large form meets this one (painted contact line)."""
    out = np.zeros(len(P))
    for ob, centre, radii, name in ellipsoids:
        if ob is own or min(radii) < .1 or any(word in name.lower() for word in skip): continue
        q = (P - np.asarray(centre)) / np.asarray(radii); length = np.linalg.norm(q, axis=1) + 1e-9
        distance = (length - 1) * length / (np.linalg.norm(q / np.asarray(radii), axis=1) + 1e-9)
        out = np.maximum(out, 1 - S(0, .07, distance))
    return out


# ---------- bake ----------
def bake(name, version, parts, out_dir, painter=None, fibers=None, ellipsoids=(), seed=7, size=SIZE, detail=None, crease_skip=('muzzle',)):
    """Paint one albedo atlas for `parts`, attach it to their materials and return its stats.

    parts: mesh objects, each with one material and a POINT colour attribute "Color"; objects
    flagged ob['chart'] = 'sphere' use their own UVs, everything else gets a two-sided planar chart.
    painter(T): returns sRGB colour per texel or None to keep the authored colour. T carries name,
    kind (fur/skin/eye/nose/silk from the material name), P/x/y/z, N/nx/ny/nz, base (authored colour),
    c and r (the part's bounding centre and half-size), seed, and k (set it to scale the wash).
    fibers maps a combed-fibre object name to the surface object it grows on (or None); fibres
    keep vertex colour (painted from that surface) and point at a white texel, so
    texture * colour is right for both.
    ellipsoids: (object, centre, radii, name) for large forms; pigment pools where they meet, except
    forms whose name contains a word in crease_skip.
    detail(object) -> texel-density multiplier; default favours eyes, heads and wings.
    """
    import bpy
    fibers = fibers or {}
    surfaces = [ob for ob in parts if ob.name not in fibers]
    charts = [_chart(ob) for ob in surfaces]
    weigh = detail or (lambda ob: 2.2 if _kind(ob) == 'eye' else 1.45 if ('head' in ob.name.lower() or 'wing' in ob.name.lower()) else 1.0)
    detail = [weigh(ob) for ob in surfaces]
    sizes = [(w * d, h * d) for (_, w, h), d in zip(charts, detail)] + [(1e-6, 1e-6)]  # last: white texel block
    lo, hi = 1.0, 4000.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if _pack(sizes, mid, size): lo = mid
        else: hi = mid
    places = _pack(sizes, lo, size)
    atlas = np.zeros((size, size, 3)); used = np.zeros((size, size), bool)
    for ob, (uv, _, _), (x0, y0, w, h) in zip(surfaces, charts, places):
        me = ob.data; me.calc_loop_triangles(); iw, ih = w - 2 * PAD, h - 2 * PAD
        count = len(me.loop_triangles)
        tl = np.empty(count * 3, dtype=np.int32); me.loop_triangles.foreach_get('loops', tl)
        tv = np.empty(count * 3, dtype=np.int32); me.loop_triangles.foreach_get('vertices', tv)
        co = _coords(me); normal = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('normal', normal)
        colour = np.empty(len(me.vertices) * 4); me.color_attributes['Color'].data.foreach_get('color', colour)
        att = np.concatenate([co, normal.reshape(-1, 3), colour.reshape(-1, 4)[:, :3]], 1)[tv].reshape(-1, 3, 9)
        local = (uv[tl] * np.array([iw, ih]) + PAD).reshape(-1, 3, 2)
        canvas, mask = _raster(local, att, w, h); mask = _dilate(canvas, mask, PAD + 3)
        flat = canvas[mask]; P = flat[:, :3]; N = flat[:, 3:6]
        N = N / (np.linalg.norm(N, axis=1, keepdims=True) + 1e-9)
        kind = _kind(ob); box_lo, box_hi = co.min(0), co.max(0)
        T = SimpleNamespace(name=re.sub(r'\.\d{3}$', '', ob.name), kind=kind, P=P, x=P[:, 0], y=P[:, 1], z=P[:, 2], N=N, nx=N[:, 0], ny=N[:, 1], nz=N[:, 2],
                            base=to_srgb(flat[:, 6:9]), c=(box_lo + box_hi) / 2, r=np.maximum((box_hi - box_lo) / 2, 1e-5), seed=seed, k=1.0)
        col = T.base if painter is None else painter(T)
        if col is None: col = T.base
        if kind in ('fur', 'skin', 'silk') and min(T.r) > .03:
            col = np.clip(col, 1e-4, 1) ** (1 + .30 * _crease(P, ob, ellipsoids, crease_skip))[:, None]
        strength = T.k * {'eye': .2, 'nose': .45}.get(kind, 1.0)
        col = wash(col, P, kind, seed, strength)
        region = atlas[y0:y0 + h, x0:x0 + w]; region[mask] = col; used[y0:y0 + h, x0:x0 + w] |= mask
        # Final atlas UVs; the surface itself becomes white so texture * vertex colour = texture.
        final = (uv * np.array([iw, ih]) + PAD + np.array([x0, y0])) / size
        me.uv_layers.active.data.foreach_set('uv', final.ravel())
        me.color_attributes['Color'].data.foreach_set('color', np.ones(len(me.vertices) * 4))
    wx, wy, ww, wh = places[-1]; atlas[wy:wy + wh, wx:wx + ww] = 1; used[wy:wy + wh, wx:wx + ww] = True
    atlas[~used] = atlas[used].mean(0)
    white = ((wx + ww / 2) / size, (wy + wh / 2) / size)
    by_ell = {ob.name: (c, r) for ob, c, r, _ in ellipsoids}
    for ob in parts:
        if ob.name not in fibers: continue
        me = ob.data; co = _coords(me)
        centroid = np.repeat(co.reshape(-1, 3, 3).mean(1), 3, axis=0)
        colour = np.empty(len(me.vertices) * 4); me.color_attributes['Color'].data.foreach_get('color', colour)
        colour = colour.reshape(-1, 4); parent = fibers[ob.name]; col = to_srgb(colour[:, :3])
        if parent is not None and painter is not None:
            centre, radii = by_ell.get(parent.name, (co.mean(0), np.ones(3)))
            N = (centroid - np.asarray(centre)) / np.asarray(radii) ** 2; N = N / (np.linalg.norm(N, axis=1, keepdims=True) + 1e-9)
            T = SimpleNamespace(name=re.sub(r'\.\d{3}$', '', parent.name), kind='fur', P=centroid, x=centroid[:, 0], y=centroid[:, 1], z=centroid[:, 2], N=N,
                                nx=N[:, 0], ny=N[:, 1], nz=N[:, 2], base=col, c=np.asarray(centre), r=np.asarray(radii), seed=seed, k=1.0)
            painted = painter(T)
            if painted is not None: col = painted
        col = wash(col, centroid, 'fur', seed, .8)
        colour[:, :3] = to_linear(col); me.color_attributes['Color'].data.foreach_set('color', colour.ravel())
        if not me.uv_layers: me.uv_layers.new(name='UVMap')
        me.uv_layers.active.data.foreach_set('uv', np.tile(white, len(me.loops)))
    # File and datablock share one short name: the glTF exporter may use either, and Godot prefixes
    # extracted textures with the GLB name (-> <Name>_<version>_painted_albedo.png in the game).
    image_name = 'painted_albedo'
    for stale in [i for i in bpy.data.images if i.name.startswith('painted_albedo')]: bpy.data.images.remove(stale)
    image = bpy.data.images.new('painted_albedo', size, size, alpha=False)
    rgba = np.ones((size, size, 4), dtype=np.float32); rgba[:, :, :3] = np.clip(atlas, 0, 1)
    image.pixels.foreach_set(rgba.ravel()); image.file_format = 'PNG'
    image.filepath_raw = str(out_dir / (image_name + '.png')); image.save(); image.pack()
    for material in {ob.data.materials[0] for ob in parts}:
        tree = material.node_tree; shader = tree.nodes.get('Principled BSDF')
        vertex = next(n for n in tree.nodes if n.type == 'VERTEX_COLOR')
        texture = tree.nodes.new('ShaderNodeTexImage'); texture.image = image
        mix = tree.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = 1
        tree.links.new(texture.outputs['Color'], mix.inputs[6]); tree.links.new(vertex.outputs['Color'], mix.inputs[7])
        tree.links.new(mix.outputs[2], shader.inputs['Base Color'])
    return {'image': image_name + '.png', 'size': size, 'charts': len(surfaces), 'texels_per_unit': round(lo, 1),
            'coverage': round(float(used.mean()), 3)}
