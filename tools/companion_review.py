#!/usr/bin/env python3
"""Image-side review tools for the painted, animated companion pipeline. Needs numpy and Pillow
(GameCore's tools/drawing-studio/.venv-vision has both). See workflows/painted-animated-companions/.

    sample   reference.png --points "muzzle=500,560 coat=480,230"      median colour at named points
    palette  reference.png [--clusters 6]                                dominant pigment clusters
    compare  reference.png render.png [--box x0,y0,x1,y1]                the same clusters in a render
    sheet    out.png --row "label=a.png,b.png,c.png" --row ...           contact sheet
    gif      frames_folder out.gif [--box x0,y0,x1,y1] [--size 300]      motion preview from stepped frames
    paper    colour.png reference.png [--seed 0]                         watercolour paper finish for a model render (reference.py)
"""
import argparse
import json
import sys
from pathlib import Path

PAPER = 232          # pixels brighter than this in every channel are treated as unpainted paper
NEAR = 34            # a render pixel belongs to a painting cluster within this RGB distance


def _np():
    import numpy as np
    return np

def _image(path):
    from PIL import Image
    return Image.open(path).convert('RGB')

def _box(text):
    return tuple(int(v) for v in text.split(',')) if text else None

def hexed(colour):
    return '#%02x%02x%02x' % tuple(int(round(v)) for v in colour)


def sample_points(path, points, radius=7):
    """Median colour and spread in a small window at each named point: [(name, hex, spread)]."""
    np = _np(); a = np.asarray(_image(path)).astype(float); out = []
    for name, (x, y) in points.items():
        window = a[max(0, y - radius):y + radius + 1, max(0, x - radius):x + radius + 1].reshape(-1, 3)
        out.append({'name': name, 'colour': hexed(np.median(window, 0)), 'spread': round(float(window.std(0).mean()), 1)})
    return out

def clusters(pixels, k, rounds=14, seed=3):
    """Plain k-means; returns centres and each centre's share of the pixels."""
    np = _np(); rng = np.random.default_rng(seed); centres = pixels[rng.choice(len(pixels), k, replace=False)].astype(float)
    for _ in range(rounds):
        label = np.argmin(((pixels[:, None, :] - centres[None]) ** 2).sum(2), 1)
        for i in range(k):
            if (label == i).any(): centres[i] = pixels[label == i].mean(0)
    return centres, np.bincount(label, minlength=k) / len(pixels)

def painting_palette(path, k=6, keep_paper=False):
    np = _np(); pixels = np.asarray(_image(path).resize((300, 330))).reshape(-1, 3).astype(float)
    if not keep_paper: pixels = pixels[pixels.min(1) < PAPER]
    centres, share = clusters(pixels, k); order = np.argsort(-share)
    return [{'colour': hexed(centres[i]), 'share': round(float(share[i]), 3)} for i in order], centres[order]

def compare(reference, render, k=6, box=None, keep_paper=False):
    """For each dominant pigment of the painting, the median of the render pixels nearest to it.
    A cluster the render never reaches is reported as not found. Pale clusters can be polluted by
    sky or sand in the crop; give a tight --box around the character."""
    np = _np(); palette, centres = painting_palette(reference, k, keep_paper)
    image = _image(render); pixels = np.asarray(image.crop(box) if box else image).reshape(-1, 3).astype(float)
    distance = ((pixels[:, None, :] - centres[None]) ** 2).sum(2); label = np.argmin(distance, 1); near = np.sqrt(distance.min(1)) < NEAR
    rows = []
    for i, entry in enumerate(palette):
        chosen = near & (label == i)
        if chosen.sum() < 150: rows.append({**entry, 'render': None, 'pixels': int(chosen.sum())}); continue
        median = np.median(pixels[chosen], 0)
        rows.append({**entry, 'render': hexed(median), 'difference': [int(v) for v in (median - centres[i]).round()], 'pixels': int(chosen.sum())})
    found = [r for r in rows if r['render']]
    worst = max((max(abs(v) for v in r['difference']) for r in found), default=None)
    return {'reference': str(reference), 'render': str(render), 'clusters': rows, 'found': len(found), 'worst_channel_difference': worst}

def sheet(out, rows, cell=300, box=None, label_height=26):
    from PIL import Image, ImageDraw, ImageFont
    try: font = ImageFont.truetype('segoeui.ttf', 17)
    except OSError: font = ImageFont.load_default()
    columns = max(len(files) for _, files in rows)
    page = Image.new('RGB', (cell * columns + 12, (cell + label_height) * len(rows) + 8), '#fbf8f1'); draw = ImageDraw.Draw(page)
    for r, (label, files) in enumerate(rows):
        y = r * (cell + label_height) + 4; draw.text((8, y + 2), label, fill='#33423a', font=font)
        for c, name in enumerate(files):
            tile = _image(name); tile = tile.crop(box) if box else tile
            tile.thumbnail((cell, cell), Image.LANCZOS); page.paste(tile, (6 + c * cell + (cell - tile.width) // 2, y + label_height + (cell - tile.height) // 2))
    Path(out).parent.mkdir(parents=True, exist_ok=True); page.save(out); return {'sheet': str(out), 'size': list(page.size)}

def gif(frames, out, box=None, size=300, milliseconds=67, colours=64, caption=None):
    from PIL import Image, ImageDraw, ImageFont
    try: font = ImageFont.truetype('segoeuib.ttf', 20)
    except OSError: font = ImageFont.load_default()
    images = []
    for path in sorted(Path(frames).glob('*.png')):
        frame = _image(path); frame = frame.crop(box) if box else frame; frame = frame.resize((size, size), Image.LANCZOS)
        text = caption(path) if caption else path.stem.split('_', 1)[-1]
        ImageDraw.Draw(frame).text((10, 8), text, fill='#22303a', font=font)
        images.append(frame.quantize(colors=colours, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
    if not images: raise SystemExit(f'No PNG frames in {frames}')
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    images[0].save(out, save_all=True, append_images=images[1:], duration=milliseconds, loop=0, optimize=True)
    return {'gif': str(out), 'frames': len(images), 'megabytes': round(Path(out).stat().st_size / 1e6, 2)}


def paper(render, out, seed=0, ivory=(244, 235, 214)):
    """Give a model render on a transparent film (reference.py's colour.png) a watercolour paper finish:
    hand-wobbled edges, pigment pooled along the silhouette, granulation, a paper-white ground.
    Pixels inside the model never go lighter than `ivory`, because palette builders read near-white as bare paper."""
    np = _np(); from PIL import Image, ImageFilter
    rng = np.random.default_rng(seed); limit = np.array(ivory) / 255
    def field(shape, cells):
        h, w = shape; small = rng.uniform(-1, 1, (max(2, round(cells * h / w)), cells)).astype(np.float32)
        return np.asarray(Image.fromarray(small).resize((w, h), Image.Resampling.BICUBIC))
    rgba = np.asarray(Image.open(render).convert('RGBA')).astype(np.float32) / 255; h, w = rgba.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    sx = np.clip(xx + field((h, w), 26) * 2.2, 0, w - 1).round().astype(int); sy = np.clip(yy + field((h, w), 26) * 2.2, 0, h - 1).round().astype(int)
    rgba = rgba[sy, sx]
    alpha = rgba[..., 3]; colour = np.minimum(rgba[..., :3] / np.maximum(alpha, 1e-4)[..., None], limit)
    blur = lambda a, r: np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255
    pooled = np.clip(alpha * (1 - blur(alpha, 7)) * 2.4, 0, 1)
    drift = 1 + .07 * field((h, w), 9) + .05 * field((h, w), 60) + .035 * rng.uniform(-1, 1, (h, w))
    colour = np.clip(colour, 1e-4, 1) ** ((1 + .30 * pooled) * drift)[..., None]
    colour = colour * .95 + .05
    soft = np.clip(blur(alpha, 1.6) * np.clip(1 + .25 * field((h, w), 40), .7, 1.2), 0, 1)[..., None]
    ground = 1 - .012 * (rng.uniform(0, 1, (h, w, 1)) > .5)
    image = Image.fromarray((np.clip(colour * soft + ground * (1 - soft), 0, 1) * 255).round().astype(np.uint8)).filter(ImageFilter.GaussianBlur(.6))
    Path(out).parent.mkdir(parents=True, exist_ok=True); image.save(out)
    return {'reference': str(out), 'size': list(image.size), 'seed': seed}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0]); sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('sample'); p.add_argument('reference'); p.add_argument('--points', required=True, help='"name=x,y name=x,y"')
    p = sub.add_parser('palette'); p.add_argument('reference'); p.add_argument('--clusters', type=int, default=6); p.add_argument('--keep-paper', action='store_true')
    p = sub.add_parser('compare'); p.add_argument('reference'); p.add_argument('render'); p.add_argument('--clusters', type=int, default=6)
    p.add_argument('--box'); p.add_argument('--keep-paper', action='store_true')
    p = sub.add_parser('sheet'); p.add_argument('out'); p.add_argument('--row', action='append', required=True, help='"label=a.png,b.png"'); p.add_argument('--cell', type=int, default=300); p.add_argument('--box')
    p = sub.add_parser('gif'); p.add_argument('frames'); p.add_argument('out'); p.add_argument('--box'); p.add_argument('--size', type=int, default=300)
    p = sub.add_parser('paper'); p.add_argument('render'); p.add_argument('out'); p.add_argument('--seed', type=int, default=0)
    args = parser.parse_args(argv)
    if args.command == 'sample':
        points = {}
        for item in args.points.split():
            name, xy = item.split('='); x, y = xy.split(','); points[name] = (int(x), int(y))
        result = sample_points(args.reference, points)
    elif args.command == 'palette': result = painting_palette(args.reference, args.clusters, args.keep_paper)[0]
    elif args.command == 'compare': result = compare(args.reference, args.render, args.clusters, _box(args.box), args.keep_paper)
    elif args.command == 'paper': result = paper(args.render, args.out, args.seed)
    elif args.command == 'sheet': result = sheet(args.out, [(r.split('=', 1)[0], r.split('=', 1)[1].split(',')) for r in args.row], args.cell, _box(args.box))
    else: result = gif(args.frames, args.out, _box(args.box), args.size)
    print(json.dumps(result, indent=2)); return 0


if __name__ == '__main__':
    sys.exit(main())
