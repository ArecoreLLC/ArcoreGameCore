"""CPU Florence grounding benchmark; saves raw answers and resource evidence."""
import argparse,json,time,os,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--download',action='store_true')
    args=p.parse_args()
    from huggingface_hub import HfApi,snapshot_download
    repo='florence-community/Florence-2-base'
    manifest=ROOT/'.model-cache/florence-base.json'
    if args.download:
        manifest.parent.mkdir(parents=True,exist_ok=True)
        revision=HfApi().model_info(repo,token=False).sha
        path=snapshot_download(repo,revision=revision,cache_dir=str(ROOT/'.model-cache'),allow_patterns=['*.json','*.safetensors','*.txt'],token=False)
        manifest.write_text(json.dumps({'repo':repo,'revision':revision,'path':path}))
        print('Model cached',flush=True);return
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    started=time.perf_counter()
    from vision_metrics import ResourceMonitor
    monitor=ResourceMonitor().start()
    answers=[]
    (ROOT/'output').mkdir(parents=True,exist_ok=True)
    try:
        with monitor.measure('imports'):
            import torch,transformers
            from transformers import AutoProcessor,Florence2ForConditionalGeneration
            from PIL import Image,ImageDraw
        torch.set_num_threads(8)
        info=json.loads(manifest.read_text())
        with monitor.measure('load') as loading:
            processor=AutoProcessor.from_pretrained(info['path'],trust_remote_code=False,local_files_only=True)
            model=Florence2ForConditionalGeneration.from_pretrained(info['path'],torch_dtype=torch.float32,trust_remote_code=False,local_files_only=True).eval()
        source=ROOT/'assets/spider-reference.jpg'
        image=Image.open(source).convert('RGB')
        tasks=[('parts','<CAPTION_TO_PHRASE_GROUNDING>','The spider has a head, an abdomen, and legs.'),('head','<CAPTION_TO_PHRASE_GROUNDING>','The head of the spider.'),('abdomen','<CAPTION_TO_PHRASE_GROUNDING>','The abdomen of the spider.'),('legs','<CAPTION_TO_PHRASE_GROUNDING>','The legs of the spider.')]
        for name,task,text in tasks:
            with monitor.measure(name) as timing:
                inputs=processor(text=task+text,images=image,return_tensors='pt')
                with torch.inference_mode():output=model.generate(**inputs,max_new_tokens=128,num_beams=1,do_sample=False,max_time=28)
                raw=processor.batch_decode(output,skip_special_tokens=False)[0]
                parsed=processor.post_process_generation(raw,task=task,image_size=image.size)
            answer={'name':name,'prompt':task+text,'raw':raw,'parsed':parsed,'timing':timing,'under_30_seconds':timing['wall_seconds']<30}
            answers.append(answer);print(json.dumps(answer),flush=True)
            canvas=image.copy();draw=ImageDraw.Draw(canvas)
            result=parsed.get(task,{})
            for box,label in zip(result.get('bboxes',[]),result.get('labels',[])):
                draw.rectangle(box,outline='red',width=4);draw.text((box[0],box[1]),label,fill='red',stroke_width=1,stroke_fill='white')
            canvas.save(ROOT/f'output/florence-{name}.png')
        resources,samples=monitor.finish()
        report={'model':info,'image_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'torch':torch.__version__,'transformers':transformers.__version__,'threads':8,'device':'cpu','load':loading,'answers':answers,'resources':resources,'samples':samples,'total_seconds':time.perf_counter()-started,'limits':'max_time is a soft generation limit; one CPU run, no accuracy calibration; download excluded'}
        (ROOT/'output/florence-benchmark.json').write_text(json.dumps(report,indent=2))
    finally:
        if not monitor.stop_event.is_set():monitor.finish()

if __name__=='__main__':main()
