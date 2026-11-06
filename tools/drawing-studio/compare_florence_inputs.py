"""Identify the subject, then compare three inputs within a 30-second worker budget."""
import json,os,re,subprocess,sys,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUTPUT=ROOT/'output/florence-input-comparison'
CONSTRUCTION='--construction' in sys.argv
if CONSTRUCTION:OUTPUT=ROOT/'output/florence-construction'
if '--output' in sys.argv:OUTPUT=Path(sys.argv[sys.argv.index('--output')+1]).resolve()


def iou(a,b):
    intersection=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
    union=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-intersection
    return intersection/union if union>0 else 0


def worker():
    started=time.perf_counter()
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    from vision_metrics import ResourceMonitor
    monitor=ResourceMonitor().start()
    try:
        with monitor.measure('imports'):
            import torch,transformers
            from transformers import AutoProcessor,Florence2ForConditionalGeneration
            from PIL import Image,ImageDraw,ImageFilter,ImageOps
        torch.set_num_threads(8)
        info=json.loads((ROOT/'.model-cache/florence-base.json').read_text())
        with monitor.measure('cached_load'):
            processor=AutoProcessor.from_pretrained(info['path'],trust_remote_code=False,local_files_only=True,use_fast=False)
            model=Florence2ForConditionalGeneration.from_pretrained(info['path'],dtype=torch.float32,local_files_only=True).eval()
        source=ROOT/'assets/spider-reference.jpg'
        image=ImageOps.exif_transpose(Image.open(source)).convert('RGB')
        def query(name,image,task,text=''):
            with monitor.measure(name) as timing:
                inputs=processor(text=task+text,images=image,return_tensors='pt')
                remaining=27-(time.perf_counter()-started)
                if remaining<=0:raise TimeoutError('Analysis budget exhausted')
                with torch.inference_mode():output=model.generate(**inputs,max_new_tokens=128,num_beams=1,do_sample=False,max_time=remaining)
                raw=processor.batch_decode(output,skip_special_tokens=False)[0]
                # The slow tokenizer can insert spaces between adjacent location tokens.
                # Native Florence's coordinate regex expects contiguous special tokens.
                parser_text=re.sub(r'>\s+<','><',raw)
                parsed=processor.post_process_generation(parser_text,task=task,image_size=image.size)
            return {'prompt':task+text,'raw':raw,'parser_text':parser_text,'parsed':parsed,'timing':timing}
        identification=query('identify_subject',image,'<DETAILED_CAPTION>')
        caption=identification['parsed'].get('<DETAILED_CAPTION>','')
        # Explicit profile selection from the model answer, never from the filename.
        if re.search(r'\bspider\b',caption,re.I):
            profile='arachnid';prompt='The spider has a head, an abdomen, and legs.'
        else:
            profile='generic';prompt=caption
        with monitor.measure('preprocessing'):
            gray=ImageOps.grayscale(image).convert('RGB')
            variants=[('color',image),('grayscale',gray),('smoothed_grayscale',gray.filter(ImageFilter.GaussianBlur(2)))]
            if CONSTRUCTION:variants=variants[:1]
        results={};panels=[];colors=['#e94630','#078449','#226ad0','#a846b0']
        try:face=__import__('PIL.ImageFont',fromlist=['truetype']).truetype('C:/Windows/Fonts/arial.ttf',17)
        except OSError:face=None
        for name,variant in variants:
            result=query(name,variant,'<CAPTION_TO_PHRASE_GROUNDING>',prompt);results[name]=result
            panel=variant.copy();draw=ImageDraw.Draw(panel)
            data=result['parsed']['<CAPTION_TO_PHRASE_GROUNDING>']
            for i,(box,label) in enumerate(zip(data.get('bboxes',[]),data.get('labels',[]))):
                color=colors[i%len(colors)];draw.rectangle(box,outline=color,width=4)
                draw.text((box[0]+4,box[1]+4),label,fill=color,font=face,stroke_width=2,stroke_fill='white')
            panel=panel.resize((640,349));tile=Image.new('RGB',(640,390),'#faf8f1');tile.paste(panel,(0,41))
            ImageDraw.Draw(tile).text((12,10),f'{name}: {result["timing"]["wall_seconds"]:.2f}s',fill='#243c38',font=face)
            panels.append(tile)
        agreement={};base=results['color']['parsed']['<CAPTION_TO_PHRASE_GROUNDING>']
        for name in (() if CONSTRUCTION else ('grayscale','smoothed_grayscale')):
            data=results[name]['parsed']['<CAPTION_TO_PHRASE_GROUNDING>'];agreement[name]=[]
            for box,label in zip(base['bboxes'],base['labels']):
                normalize=lambda s:re.sub(r'^(the|an|a)\s+','',s.casefold().strip())
                matches=[iou(box,b) for b,l in zip(data['bboxes'],data['labels']) if normalize(l)==normalize(label)]
                agreement[name].append({'label':label,'best_box_iou_vs_color':max(matches) if matches else None})
        sheet=Image.new('RGB',(1280,780),'#faf8f1')
        for panel,position in zip(panels,[(0,0),(640,0),(0,390)]):sheet.paste(panel,position)
        draw=ImageDraw.Draw(sheet)
        draw.text((660,420),'Subject first: '+profile,fill='#243c38',font=face)
        draw.text((660,455),'Same parts prompt for all variants.',fill='#243c38',font=face)
        draw.text((660,490),'Boxes are proposals, not segmentation masks.',fill='#243c38',font=face)
        sheet.save(OUTPUT.with_suffix('.png'))
        construction=None
        if CONSTRUCTION:
            palp_query=query('palp_grounding',image,'<CAPTION_TO_PHRASE_GROUNDING>','The spider has two short pedipalps beside its mouth and long walking legs.')
            results['palps']=palp_query
            with monitor.measure('construction_and_export'):
                from fit_detected_parts import construct
                construction=construct(image,base,OUTPUT,palp_query['parsed']['<CAPTION_TO_PHRASE_GROUNDING>'])
        resources,samples=monitor.finish()
        report={'model':info,'torch':torch.__version__,'transformers':transformers.__version__,'threads':8,'device':'cpu','image_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'identification':identification,'selected_profile':profile,'results':results,'agreement':agreement,'resources':resources,'samples':samples,'worker_seconds_before_report_write':time.perf_counter()-started,'limits':'Single fixed-order run. IoU measures agreement, not correctness. Smoothing radius 2 original pixels. No authored coordinates supplied.'}
        report['construction']=construction
        OUTPUT.with_suffix('.json').write_text(json.dumps(report,indent=2))
        print(json.dumps({'profile':profile,'caption':caption,'seconds':{k:v['timing']['wall_seconds'] for k,v in results.items()},'agreement':agreement}),flush=True)
    finally:
        if not monitor.stop_event.is_set():monitor.finish()


if __name__=='__main__':
    if '--worker' in sys.argv:worker()
    else:
        OUTPUT.parent.mkdir(parents=True,exist_ok=True)
        start=time.perf_counter()
        try:
            result=subprocess.run([sys.executable,__file__,'--worker','--output',str(OUTPUT)]+(['--construction'] if CONSTRUCTION else []),timeout=29)
            status='passed' if result.returncode==0 else 'failed'
        except subprocess.TimeoutExpired:status='timed_out'
        elapsed=time.perf_counter()-start
        receipt={'status':status,'total_wall_seconds':elapsed,'under_30_seconds':elapsed<30 and status=='passed','includes':'worker startup, imports, cached loading, classification, preprocessing, '+('color grounding, body fitting, appendage partition, lesson export' if CONSTRUCTION else 'all three queries')+', overlays, telemetry and report export','excludes':'one-time model download; parent receipt write'}
        OUTPUT.with_name(OUTPUT.name+'-receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt),flush=True)
        sys.exit(0 if receipt['under_30_seconds'] else 1)
