"""Generate review-only filmstrips; never alter source videos."""
import json, subprocess
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidence/marketing-2026-11-11'
names = ['improvements-showcase.mp4', 'FatMan-strike.mp4', 'sandbox-flythrough.mp4',
         'running-gear.mp4', 'Poofy-candy-ship-gameplay.mp4', 'Poofy-sails-to-meet-Plumpy.mp4',
         'character-abilities.mp4', 'Tsunami-full-songs-walkthrough.mp4']
items = []
for game in json.loads((OUT/'discovery.json').read_text()):
    for v in game.get('videos', []):
        p = Path(v['path'])
        if p.name not in names: continue
        if p.name == 'FatMan-strike.mp4' and '104214' not in str(p): continue
        if p.name == 'sandbox-flythrough.mp4' and '022853Z' not in str(p): continue
        probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)]))
        stream = next(s for s in probe['streams'] if s['codec_type']=='video')
        duration = float(probe['format']['duration'])
        i = len(items)
        board = Image.new('RGB',(1280,780),'#10151d'); draw=ImageDraw.Draw(board)
        for j,fraction in enumerate([.08,.25,.45,.65,.8,.93]):
            frame = OUT/f'video-{i}-{j}.jpg'
            subprocess.run(['ffmpeg','-v','error','-y','-ss',str(duration*fraction),'-i',str(p),'-frames:v','1','-vf','scale=640:340:force_original_aspect_ratio=decrease',str(frame)],check=True)
            im=Image.open(frame); x=(j%2)*640; y=(j//2)*260
            im.thumbnail((630,230));board.paste(im,(x,y));draw.text((x+5,y+232),f'{p.name} @ {duration*fraction:.1f}s',fill='white')
        board.save(OUT/f'video-{i}.jpg')
        result=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','NUL'],capture_output=True,text=True)
        items.append({**v,'project_id':game['id'],'game':game['name'],'width':stream['width'],'height':stream['height'],'duration_seconds':duration,'codec':stream['codec_name'],'audio_present':any(s['codec_type']=='audio' for s in probe['streams']),'decode_passed':result.returncode==0 and not result.stderr.strip(),'decode_errors':result.stderr[:2000],'review_index':i})
(OUT/'video-review.json').write_text(json.dumps(items,indent=2))
print(json.dumps([{'index':i['review_index'],'game':i['game'],'path':i['relative'],'seconds':i['duration_seconds'],'decode':i['decode_passed']} for i in items],indent=2))
