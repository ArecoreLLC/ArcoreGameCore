"""Blind Florence task comparison: no supplied subject or part vocabulary."""
import os,json,time,sys,subprocess,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUTPUT=ROOT/'output/florence-part-discovery'


def worker():
    start=time.perf_counter()
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    from vision_metrics import ResourceMonitor
    monitor=ResourceMonitor().start()
    try:
        with monitor.measure('imports'):
            import torch,transformers
            from transformers import AutoProcessor,Florence2ForConditionalGeneration
            from PIL import Image,ImageDraw,ImageFont
        torch.set_num_threads(8)
        info=json.loads((ROOT/'.model-cache/florence-base.json').read_text())
        with monitor.measure('load'):
            processor=AutoProcessor.from_pretrained(info['path'],local_files_only=True,trust_remote_code=False,use_fast=False)
            model=Florence2ForConditionalGeneration.from_pretrained(info['path'],local_files_only=True,dtype=torch.float32).eval()
        source=ROOT/'assets/spider-reference.jpg';image=Image.open(source).convert('RGB')
        answers=[]
        tasks=['<DETAILED_CAPTION>','<MORE_DETAILED_CAPTION>','<DENSE_REGION_CAPTION>','<OD>','<CAPTION_TO_PHRASE_GROUNDING>']
        for task in tasks:
            text=answers[1]['parsed']['<MORE_DETAILED_CAPTION>'] if task=='<CAPTION_TO_PHRASE_GROUNDING>' else ''
            with monitor.measure(task) as timing:
                remaining=26-(time.perf_counter()-start)
                if remaining<=0:raise TimeoutError('Worker budget exhausted')
                inputs=processor(text=task+text,images=image,return_tensors='pt')
                with torch.inference_mode():tokens=model.generate(**inputs,max_new_tokens=256,num_beams=1,do_sample=False,max_time=remaining)
                raw=processor.batch_decode(tokens,skip_special_tokens=False)[0]
                parsed=processor.post_process_generation(re.sub(r'>\s+<','><',raw),task=task,image_size=image.size)
            answer={'task':task,'prompt':task+text,'raw':raw,'parsed':parsed,'timing':timing,'output_tokens':tokens.shape[-1]}
            answers.append(answer);print(json.dumps({'task':task,'parsed':parsed,'seconds':timing['wall_seconds']}),flush=True)
        font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
        sheet=Image.new('RGB',(1280,780),'#faf8f1')
        for i,answer in enumerate(answers[2:]):
            panel=image.copy();draw=ImageDraw.Draw(panel);data=answer['parsed'][answer['task']]
            for box,label in zip(data.get('bboxes',[]),data.get('labels',[])):
                draw.rectangle(box,outline='#167fc0',width=4);draw.text((box[0]+3,box[1]+3),label[:90],font=font,fill='#167fc0',stroke_width=2,stroke_fill='white')
            x=(i%2)*640;y=(i//2)*390;sheet.paste(panel.resize((640,349)),(x,y+41))
            ImageDraw.Draw(sheet).text((x+10,y+10),answer['task'],font=font,fill='#243c38')
        sheet.save(OUTPUT.with_suffix('.png'))
        resources,samples=monitor.finish()
        report={'model':info,'image_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'torch':torch.__version__,'transformers':transformers.__version__,'threads':8,'answers':answers,'resources':resources,'samples':samples,'subject_or_parts_supplied':False,'self_grounding_text_source':'verbatim MORE_DETAILED_CAPTION output','limits':'One image, greedy decoding, up to 256 new tokens, fixed task order. No profile, authored coordinates or filename supplied to model.'}
        OUTPUT.with_suffix('.json').write_text(json.dumps(report,indent=2))
    finally:
        if not monitor.stop_event.is_set():monitor.finish()


if __name__=='__main__':
    if '--worker' in sys.argv:worker()
    else:
        OUTPUT.parent.mkdir(parents=True,exist_ok=True);start=time.perf_counter()
        try:status='passed' if subprocess.run([sys.executable,__file__,'--worker'],timeout=29).returncode==0 else 'failed'
        except subprocess.TimeoutExpired:status='timed_out'
        elapsed=time.perf_counter()-start
        receipt={'status':status,'full_seconds':elapsed,'under_30_seconds':status=='passed' and elapsed<30,'includes':'startup, imports, cached load, five queries, overlay and report export','excludes':'download and parent receipt serialization'}
        OUTPUT.with_name(OUTPUT.name+'-receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
        sys.exit(0 if receipt['under_30_seconds'] else 1)
