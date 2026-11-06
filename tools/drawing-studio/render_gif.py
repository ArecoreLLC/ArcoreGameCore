"""Headless Drawing Atelier exporter. Requires Python/Pillow and Node, no browser."""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import math
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import time

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps, __version__ as pillow_version

ROOT = Path(__file__).resolve().parent
PAPER = (250, 248, 241)


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    source = p.add_mutually_exclusive_group()
    source.add_argument('--input', type=Path, help='JPEG, PNG or WebP reference; defaults to the spider sample')
    source.add_argument('--lesson', type=Path, help='Editable JSON lesson saved by Drawing Atelier')
    p.add_argument('--output', type=Path, default=ROOT / 'output' / 'spider-study.gif')
    p.add_argument('--sheet', type=Path, help='Also export a six-step PNG teaching sheet')
    p.add_argument('--width', type=int, default=960, help='GIF width, 320-1600 (default: 960)')
    p.add_argument('--fps', type=int, default=12, help='Frames per second, 1-30 (default: 12)')
    p.add_argument('--duration', type=float, default=24, help='Drawing duration in seconds, 6-120 (default: 24)')
    p.add_argument('--hold', type=float, default=2, help='Hold the finished painting for 0-10 seconds')
    p.add_argument('--no-cursor', action='store_true', help='Hide the animated pencil/brush tip')
    p.add_argument('--advanced', action='store_true', help='Finish each construction part before painting the next; generate six stock colors and recipes')
    p.add_argument('--mixing-output', type=Path, help='Export a separate color-mixing GIF (also generates palette JSON and PNG)')
    p.add_argument('--mixing-only', action='store_true', help='Export the palette and mixing GIF without rendering the drawing GIF')
    p.add_argument('--palette-output', type=Path, help='Recipe JSON path; defaults to OUTPUT-palette.json')
    return p


def font(size, serif=False):
    for name in (['C:/Windows/Fonts/georgia.ttf', 'DejaVuSerif.ttf'] if serif else ['C:/Windows/Fonts/segoeui.ttf', 'DejaVuSans.ttf']):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def normalized_reference(args):
    lesson = None
    if args.lesson:
        if args.lesson.stat().st_size > 18_000_000:
            raise ValueError('Lesson file must be under 18 MB.')
        lesson = json.loads(args.lesson.read_text(encoding='utf-8'))
        image_url = lesson.get('image', '')
        if not image_url.startswith(('data:image/jpeg;base64,', 'data:image/png;base64,', 'data:image/webp;base64,')):
            raise ValueError('Lesson must contain an embedded JPEG, PNG or WebP reference.')
        source = io.BytesIO(base64.b64decode(image_url.split(',', 1)[1], validate=True))
        name = str(lesson.get('name', 'Drawing study'))[:150]
        study = 'spider' if lesson.get('study') == 'spider' else 'custom'
    else:
        source = args.input or ROOT / 'assets' / 'spider-reference.jpg'
        name = args.input.stem if args.input else 'Little woodland spider'
        study = 'custom' if args.input else 'spider'
    with Image.open(source) as image:
        if image.width * image.height > 40_000_000:
            raise ValueError('Choose a reference smaller than 40 megapixels.')
        image = ImageOps.exif_transpose(image).convert('RGBA')
        fit=min(1280/image.width,698/image.height)
        image=image.resize((round(image.width*fit),round(image.height*fit)),Image.Resampling.LANCZOS)
        fitted = Image.new('RGBA', (1280, 698), PAPER + (255,))
        fitted.alpha_composite(image, ((1280-image.width)//2, (698-image.height)//2))
    return fitted, name, study


def extract_strokes(reference, study, lesson_path):
    node = shutil.which('node')
    if not node:
        raise ValueError('Node.js is required to reuse the Drawing Atelier stroke engine.')
    # Explicit workspace temporary directory also works in restricted environments.
    with tempfile.TemporaryDirectory(prefix='.gif-render-', dir=ROOT) as temp:
        pixels = Path(temp) / 'reference.rgba'
        output = Path(temp) / 'strokes.json'
        pixels.write_bytes(reference.resize((640, 349), Image.Resampling.LANCZOS).tobytes())
        command = [node, str(ROOT / 'export-strokes.mjs'), str(pixels), str(output), study]
        if lesson_path:
            command.append(str(lesson_path.resolve()))
        subprocess.run(command, check=True, capture_output=True, text=True)
        return json.loads(output.read_text(encoding='utf-8'))


class Renderer:
    def __init__(self, data, width, regions=None):
        self.data, self.width = data, width
        self.scale = width * 2 / 1280
        self.size = (width * 2, round(698 * self.scale))
        self.height = round(self.size[1] / 2)
        self.paper = Image.new('RGBA', self.size, PAPER + (255,))
        rng = random.Random(18)
        draw = ImageDraw.Draw(self.paper)
        for _ in range(round(width * 55)):
            x, y = rng.randrange(self.size[0]), rng.randrange(self.size[1])
            v = rng.randrange(232, 250)
            draw.point((x, y), fill=(v, v-1, v-5, 255))
        self.layers = [Image.new('RGBA', self.size) for _ in range(6)]
        self.counts = [0] * 6
        self.cursor = (0, 0)
        self.complete = []
        self.region_masks={}
        self.active_part=None
        self.paint_fraction=0
        if regions is not None:
            for i,part in enumerate(data['parts']):
                mask=regions.point(lambda value:255 if value==i else 0).resize(self.size,Image.Resampling.NEAREST)
                self.region_masks[part['id']]=mask

    def stroke(self, layer, op, index):
        s = self.scale
        draw = ImageDraw.Draw(layer)
        if op.get('kind') == 'pencil':
            ax, ay = op['a']; bx, by = op['b']
            jitter = math.sin(index * 17.71) * .55
            construction = op['construction']
            opacity=max(0,min(1,op.get('opacity',1)))
            draw.line([(int((ax+jitter)*s), int(ay*s)), (int(bx*s), int((by+jitter)*s))], fill=(112,107,87,round(110*opacity)) if construction else (63,59,50,round(145*opacity)), width=max(1, round((.85 if construction else 1.05)*s)))
            draw.line([(int((ax+1)*s), int((ay-1)*s)), (int((bx+1.3)*s), int((by-.5)*s))], fill=(100,95,77,round(35*opacity)), width=max(1, round(.5*s)))
            self.cursor = (bx*s, by*s)
        else:
            x,y,dx,dy = (op[k]*s for k in ('x','y','dx','dy'))
            color = op['color']
            rgb = tuple(int(color[j:j+2],16) for j in (1,3,5)) if color.startswith('#') else tuple(map(int,color[4:-1].split(',')))
            fill = rgb + (round(op['alpha']*255),)
            width = max(1,round(op['width']*s))
            a,b = (round(x-dx/2),round(y-dy/2)), (round(x+dx/2),round(y+dy/2))
            # Clip the brush footprint to its assigned construction region, not just
            # its center, so a neighboring unpainted part stays pencil-only.
            stamp=None
            if 'part_id' in op:
                margin=math.ceil(width/2)+2
                left=max(0,min(a[0],b[0])-margin);top=max(0,min(a[1],b[1])-margin)
                right=min(layer.width,max(a[0],b[0])+margin+1);bottom=min(layer.height,max(a[1],b[1])+margin+1)
                if right<=left or bottom<=top:return
                stamp=Image.new('RGBA',(right-left,bottom-top))
                draw=ImageDraw.Draw(stamp)
                a=(a[0]-left,a[1]-top);b=(b[0]-left,b[1]-top)
            draw.line([a,b],fill=fill,width=width)
            if width>2:
                radius=width/2
                for px,py in (a,b):
                    draw.ellipse((px-radius,py-radius,px+radius,py+radius),fill=fill)
            if stamp is not None:
                mask=self.region_masks[op['part_id']].crop((left,top,right,bottom))
                stamp.putalpha(ImageChops.multiply(stamp.getchannel('A'),mask))
                layer.alpha_composite(stamp,(left,top))
                self.cursor=(b[0]+left,b[1]+top)
            else:
                self.cursor=b

    def advance(self, stage, count):
        operations = self.data['stages'][stage]
        if count<self.counts[stage]:
            self.layers[stage]=Image.new('RGBA',self.size)
            self.counts[stage]=0
        for i in range(self.counts[stage], count):
            self.stroke(self.layers[stage], operations[i], i)
        self.counts[stage] = count

    def frame(self, progress, cursor=True, label_stage=None):
        stage = min(5, int(progress*6)) if label_stage is None else label_stage
        for i, operations in enumerate(self.data['stages']):
            fraction=max(0,min(1,progress*6-i))
            if self.data.get('advanced') and i in (2,3) and self.data.get('sketch_schedules'):
                from advanced import schedule_count
                count,part,local=schedule_count(self.data['sketch_schedules'][i-2],fraction)
                if i==stage:
                    self.active_part=part;self.paint_fraction=local
            elif self.data.get('advanced') and i>=4:
                from advanced import schedule_count
                count,part,local=schedule_count(self.data['paint_schedules'][i-4],fraction)
                if i==stage:
                    self.active_part=part;self.paint_fraction=local
            else:
                count = int(fraction*len(operations))
            self.advance(i,count)
        result = self.paper.copy()
        for i,layer in enumerate(self.layers):
            alpha = 1
            if i<2 and progress>2/6:
                alpha=max(.2,1-(progress-2/6)*1.6)
            if i==2 and progress>4/6:
                alpha=1-(progress-4/6)*2.1
            if alpha<1:
                layer=layer.copy();layer.putalpha(layer.getchannel('A').point(lambda a:round(a*alpha)))
            result.alpha_composite(layer)
        if cursor and 0<progress<1:
            x,y = self.cursor
            s=self.scale
            points=[(x,y),(x+5*s,y-15*s),(x+34*s,y-65*s),(x+28*s,y-69*s),(x-3*s,y-17*s)]
            draw=ImageDraw.Draw(result)
            draw.polygon(points,fill=(186,153,106,255) if stage<4 else (84,115,102,255))
            draw.line(points+[points[0]],fill=(87,73,55,255),width=max(1,round(s*.7)))
            draw.polygon([(x,y),(x+2*s,y-8*s),(x-2*s,y-8*s)],fill=(65,62,51,255))
        result=result.convert('RGB').resize((self.width,self.height),Image.Resampling.LANCZOS)
        output=Image.new('RGB',(self.width,self.height+(112 if self.data.get('advanced') else 76)),PAPER)
        output.paste(result,(0,0))
        draw=ImageDraw.Draw(output)
        draw.line((20,self.height+2,self.width-20,self.height+2),fill=(221,220,210))
        title=f'{stage+1:02} / {self.data["instructions"][stage]["title"]}'
        if stage in (2,3) and self.active_part and self.data.get('sketch_schedules'):
            title=f'{self.active_part["name"]} / Lines & graphite'
        elif stage>=4 and self.active_part:
            part=self.active_part;count=int(self.paint_fraction*len(part['operations']))
            title=f'{part["name"]} / '+('Base coat' if count<part['broad_count'] else 'Refine & finish')
        draw.text((22,self.height+12),title,font=font(max(12,min(19,self.width//34)),True),fill=(51,77,61))
        draw.text((22,self.height+43),'DRAWING ATELIER  /  pencil to paint',font=font(12),fill=(116,123,112))
        draw.line((self.width-152,self.height+53,self.width-22,self.height+53),fill=(218,222,210),width=3)
        draw.line((self.width-152,self.height+53,self.width-152+round(130*progress),self.height+53),fill=(62,92,71),width=3)
        if self.data.get('advanced'):
            for i,base in enumerate(self.data['base_colors']):
                x=22+i*min(95,(self.width-44)//6)
                draw.rounded_rectangle((x,self.height+71,x+23,self.height+92),radius=3,fill=tuple(base['rgb']))
                draw.text((x+28,self.height+72),base['id'],font=font(11),fill=(80,96,76))
        return output


def make_palette(reference):
    # One palette for the entire animation prevents frame-to-frame color flicker.
    colors=reference.convert('RGB').quantize(colors=190).getpalette()[:570]
    for i in range(60):
        v=round(35+i*(220/59));colors.extend((v,max(0,v-2),max(0,v-8)))
    for color in (PAPER,(51,77,61),(116,123,112),(186,153,106),(84,115,102),(221,220,210)):
        colors.extend(color)
    palette=Image.new('P',(1,1));palette.putpalette(colors)
    return palette


def wrap(draw,text,x,y,width,face,line_height):
    row=''
    for word in text.split():
        trial=(row+' '+word).strip()
        if row and draw.textlength(trial,font=face)>width:
            draw.text((x,y),row,font=face,fill=(105,112,97));y+=line_height;row=word
        else:
            row=trial
    draw.text((x,y),row,font=face,fill=(105,112,97))


def make_sheet(frames,instructions,name,path):
    sheet=Image.new('RGB',(1800,2240),PAPER);draw=ImageDraw.Draw(sheet)
    draw.text((65,35),'DRAWING ATELIER / SIX-STEP STUDY',font=font(18),fill=(62,92,71))
    draw.text((65,78),name[:65],font=font(40,True),fill=(51,77,61))
    for i,frame in enumerate(frames):
        x,y=65+(i%2)*850,160+(i//2)*680
        fitted=frame.resize((800,round(frame.height*800/frame.width)),Image.Resampling.LANCZOS)
        sheet.paste(fitted,(x,y))
        wrap(draw,instructions[i]['text'],x,y+fitted.height+18,790,font(21),30)
    path.parent.mkdir(parents=True,exist_ok=True);sheet.save(path)


def run(args):
    if not 320<=args.width<=1600 or not 1<=args.fps<=30 or not math.isfinite(args.duration) or not 6<=args.duration<=120 or not math.isfinite(args.hold) or not 0<=args.hold<=10:
        raise ValueError('Use width 320-1600, fps 1-30, duration 6-120, and hold 0-10.')
    if args.output.suffix.lower()!='.gif':
        raise ValueError('--output must end in .gif.')
    if args.sheet and args.sheet.suffix.lower()!='.png':
        raise ValueError('--sheet must end in .png.')
    advanced=getattr(args,'advanced',False)
    mixing_only=getattr(args,'mixing_only',False)
    mixing_output=getattr(args,'mixing_output',None)
    if mixing_only and mixing_output is None:
        mixing_output=args.output.with_name(args.output.stem+'-mixing.gif')
    if mixing_output and mixing_output.suffix.lower()!='.gif':
        raise ValueError('--mixing-output must end in .gif.')
    palette_output=getattr(args,'palette_output',None)
    if palette_output and palette_output.suffix.lower()!='.json':
        raise ValueError('--palette-output must end in .json.')
    destinations=[p.resolve() for p in [args.output,args.sheet,mixing_output,palette_output] if p is not None]
    if len(set(destinations))!=len(destinations):
        raise ValueError('Drawing, sheet, mixing and palette outputs need distinct paths.')
    # Indexed frames are retained for encoding; bound the requested memory footprint.
    frame_count=round(args.duration*args.fps)+1
    if args.width*(round(args.width*698/1280)+(112 if advanced else 76))*frame_count>450_000_000:
        raise ValueError('This export exceeds the 450 MB frame budget. Reduce width, fps or duration.')
    start=time.perf_counter();reference,name,study=normalized_reference(args)
    print(f'Analyzing {name} ...',flush=True)
    data=extract_strokes(reference,study,args.lesson)
    print('Stroke counts: '+', '.join(str(len(s)) for s in data['stages']),flush=True)
    manifest=None;regions=None;mixing_report=None
    if advanced or mixing_output or palette_output:
        from advanced import build_advanced, export_mixing, palette_sheet
        planned,manifest,regions=build_advanced(data)
        if advanced:
            data=planned;data['parts']=manifest['parts'];data['base_colors']=manifest['base_colors']
        elif not mixing_only:
            # Planning operates on a copy to preserve the standard drawing mode.
            data=extract_strokes(reference,study,args.lesson)
            regions=None
        palette_output=palette_output or args.output.with_name(args.output.stem+'-palette.json')
        palette_output.parent.mkdir(parents=True,exist_ok=True)
        palette_output.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        palette_sheet(manifest,palette_output.with_suffix('.png'),font)
        print(f'Six-color palette: {palette_output}; {len(manifest["recipes"])} mixtures; mean RGB error {manifest["mean_rgb_rmse"]}/255',flush=True)
        if mixing_output:
            print('Rendering the separate color-mixing animation ...',flush=True)
            mixing_report=export_mixing(manifest,mixing_output,args.width,args.fps,font)
            mixing_report['palette']=str(palette_output.resolve())
            mixing_output.with_suffix('.evidence.json').write_text(json.dumps(mixing_report,indent=2)+'\n',encoding='utf-8')
            print(json.dumps(mixing_report,indent=2),flush=True)
        if mixing_only:return mixing_report
    renderer=Renderer(data,args.width,regions);palette=make_palette(reference)
    # Include every stage boundary exactly, irrespective of fps/duration.
    sheet_times=[.1,.2,.3,.4,.7,1] if advanced else [i/6 for i in range(1,7)]
    samples=sorted(set([i/(frame_count-1) for i in range(frame_count)]+sheet_times))
    frames=[];durations=[];completed=[];last_stage=-1
    for index,progress in enumerate(samples):
        # Give region-based painting 60% of the movie; construction/graphite use 40%.
        drawing_progress=(progress/.4*4/6 if progress<.4 else 4/6+(progress-.4)/.6*2/6) if advanced else progress
        frame=renderer.frame(drawing_progress,cursor=not args.no_cursor)
        frames.append(frame.quantize(palette=palette,dither=Image.Dither.NONE))
        next_time=samples[index+1] if index+1<len(samples) else progress
        # GIF timings are centiseconds; clamp tiny added boundary frames to 10 ms.
        durations.append(max(10,(round(next_time*args.duration*100)-round(progress*args.duration*100))*10))
        if progress in sheet_times:
            # Stage labels describe the completed stage rather than the next stage.
            completed.append(renderer.frame(drawing_progress,cursor=False,label_stage=sheet_times.index(progress)))
        current=min(5,int(progress*6))
        if current!=last_stage:
            print(f'Rendering {current+1}/6: {data["instructions"][current]["title"]}',flush=True);last_stage=current
    durations[-1]=max(10,round(args.hold*100)*10)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    print(f'Encoding {len(frames)} frames ...',flush=True)
    frames[0].save(args.output,save_all=True,append_images=frames[1:],duration=durations,loop=0,disposal=1,optimize=False)
    if args.sheet:
        make_sheet(completed,data['instructions'],name,args.sheet)
    # Decode the actual GIF, checking all frames and recorded duration.
    with Image.open(args.output) as saved:
        duration=0
        for i in range(saved.n_frames):
            saved.seek(i);saved.load();duration+=saved.info.get('duration',0)
        report={'status':'passed','output':str(args.output.resolve()),'size':list(saved.size),'frames':saved.n_frames,'duration_ms':duration,'loop':saved.info.get('loop'),'bytes':args.output.stat().st_size,'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),'python':sys.version.split()[0],'pillow':pillow_version,'elapsed_seconds':round(time.perf_counter()-start,2),'stroke_counts':[len(s) for s in data['stages']],'advanced':advanced}
        if manifest:
            report['palette']=str(palette_output.resolve());report['mixture_count']=len(manifest['recipes']);report['part_count']=len(manifest['paint_order'])
        if saved.n_frames<7 or saved.info.get('loop')!=0:
            raise ValueError('Export validation failed: expected a looping animation with at least seven frames.')
    evidence=args.output.with_suffix('.evidence.json');evidence.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    if args.sheet:
        print(f'Teaching sheet: {args.sheet.resolve()}')
    return report


if __name__=='__main__':
    try:
        run(parser().parse_args())
    except (ValueError,OSError,subprocess.CalledProcessError) as error:
        print(f'Export failed: {error}',file=sys.stderr)
        if isinstance(error,subprocess.CalledProcessError) and error.stderr:
            print(error.stderr,file=sys.stderr)
        sys.exit(1)
