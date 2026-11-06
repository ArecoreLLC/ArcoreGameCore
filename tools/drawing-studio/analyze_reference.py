"""Run a small local VLM on a reference without using the authored drawing lesson."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

ROOT=Path(__file__).resolve().parent
QUESTIONS=[
    ('subject','Describe the main subject of this image in one sentence.'),
    ('composition','Is this image primarily a single isolated subject, multiple separate subjects, or an environmental scene? Choose one and briefly describe the background.'),
    ('visible_parts','List the main visible parts of the subject. Mention only parts you can see.'),
    ('construction','Describe the largest basic shapes that could be used to sketch this image. Do not guess hidden parts.'),
]


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=ROOT/'assets'/'spider-reference.jpg')
    p.add_argument('--output',type=Path,default=ROOT/'output'/'vision-analysis.json')
    p.add_argument('--model',choices=['HuggingFaceTB/SmolVLM-500M-Instruct','HuggingFaceTB/SmolVLM-256M-Instruct'],default='HuggingFaceTB/SmolVLM-500M-Instruct')
    p.add_argument('--revision',help='Exact Hugging Face commit; otherwise resolve and record the current commit')
    p.add_argument('--longest-edge',type=int,choices=[512,1024],default=1024)
    p.add_argument('--max-new-tokens',type=int,default=128)
    p.add_argument('--threads',type=int,default=min(8,os.cpu_count() or 1))
    p.add_argument('--offline',action='store_true',help='Use a previously cached exact --revision without network access')
    p.add_argument('--device',choices=['cpu','cuda'],default='cpu',help='Execution backend; explicit CUDA requires a compatible installed PyTorch build and GPU')
    p.add_argument('--sample-interval',type=float,default=.25,help='CPU/RAM/Windows GPU sample interval, 0.1-2 seconds')
    return p


def write_metrics_csv(report,path):
    fields=['phase','wall_seconds','cpu_seconds','cpu_percent_machine_mean','cpu_percent_one_core_mean','rss_mib_peak_observed','gpu_system_percent_mean','gpu_system_percent_peak','gpu_process_percent_mean','gpu_process_percent_peak','gpu_process_dedicated_mib_peak','time_to_first_token_seconds','time_to_complete_answer_seconds']
    with path.open('w',newline='',encoding='utf-8') as file:
        writer=csv.DictWriter(file,fieldnames=fields);writer.writeheader()
        by_id={answer['id']:answer for answer in report['answers']}
        for phase in report['resources']['phases']:
            answer=by_id.get(phase['name'].split('.')[0],{}) if phase['name'].endswith('.generate') else {}
            writer.writerow({'phase':phase['name'],'wall_seconds':phase['wall_seconds'],'cpu_seconds':phase['cpu_seconds'],'cpu_percent_machine_mean':phase['process_cpu_percent_machine_mean'],'cpu_percent_one_core_mean':phase['process_cpu_percent_one_core_mean'],'rss_mib_peak_observed':phase['process_rss_mib_peak_observed'],'gpu_system_percent_mean':phase['gpu_system_busiest_engine_percent_sampled']['mean'],'gpu_system_percent_peak':phase['gpu_system_busiest_engine_percent_sampled']['peak'],'gpu_process_percent_mean':phase['gpu_process_busiest_engine_percent_sampled']['mean'],'gpu_process_percent_peak':phase['gpu_process_busiest_engine_percent_sampled']['peak'],'gpu_process_dedicated_mib_peak':phase['gpu_process_dedicated_mib_sampled']['peak'],'time_to_first_token_seconds':answer.get('time_to_first_token_seconds'),'time_to_complete_answer_seconds':answer.get('time_to_complete_answer_seconds')})


def analyze(args):
    if not 32<=args.max_new_tokens<=256 or not 1<=args.threads<=32:
        raise ValueError('Use 32-256 output tokens and 1-32 CPU threads.')
    if args.offline and not args.revision:
        raise ValueError('--offline requires the exact --revision recorded by an earlier run.')
    if args.input.resolve()==args.output.resolve():
        raise ValueError('Input and output paths must differ.')
    if not .1<=args.sample_interval<=2:
        raise ValueError('Use a sample interval between 0.1 and 2 seconds.')
    if args.offline:
        # Some processor sub-loads in Transformers 4.x do not propagate all kwargs.
        # Enforce offline behavior before importing the Hub/Transformers modules.
        os.environ['HF_HUB_OFFLINE']='1'
        os.environ['TRANSFORMERS_OFFLINE']='1'
    # Imports are optional: the standard drawing exporter does not depend on this stack.
    from vision_metrics import ResourceMonitor,FirstTokenClock
    monitor=ResourceMonitor(args.sample_interval).start()
    try:
        return _analyze(args,monitor)
    finally:
        if not monitor.stop_event.is_set():monitor.finish()


def _analyze(args,monitor):
    from vision_metrics import FirstTokenClock
    with monitor.measure('runtime_imports'):
        import torch
        import transformers
        import huggingface_hub
        from huggingface_hub import HfApi
        from PIL import Image, ImageOps, __version__ as pillow_version
        from transformers import AutoProcessor, AutoModelForVision2Seq

    torch.set_num_threads(args.threads)
    torch.manual_seed(0)
    start=monitor.started
    if args.device=='cuda' and not torch.cuda.is_available():
        monitor.finish()
        raise ValueError('CUDA execution is unavailable in this PyTorch build/hardware. CPU monitoring still supports Windows AMD GPU counters.')
    cache=ROOT/'.model-cache';cache.mkdir(exist_ok=True)
    with monitor.measure('model_resolution_and_image'):
        revision=args.revision or HfApi(token=False).model_info(args.model).sha
        print(f'Model: {args.model}\nRevision: {revision}\nDevice: {args.device}, float32, {args.threads} threads',flush=True)
        with Image.open(args.input) as original:
            if original.width*original.height>40_000_000:
                raise ValueError('Choose an image smaller than 40 megapixels.')
            image=ImageOps.exif_transpose(original).convert('RGB')
    kwargs={'revision':revision,'cache_dir':str(cache),'token':False,'trust_remote_code':False,'local_files_only':args.offline}
    with monitor.measure('model_load') as load_metrics:
        processor=AutoProcessor.from_pretrained(args.model,**kwargs)
        # Use the processor's supported resize control to bound the vision workload.
        processor.image_processor.size={'longest_edge':args.longest_edge}
        model=AutoModelForVision2Seq.from_pretrained(args.model,torch_dtype=torch.float32,attn_implementation='eager',use_safetensors=True,**kwargs).to(args.device).eval()
        if args.device=='cuda':torch.cuda.synchronize()
    loaded=time.perf_counter()
    print(f'Model load: {load_metrics["wall_seconds"]:.2f}s; ready at {loaded-start:.2f}s including imports. Running neutral prompts ...',flush=True)
    answers=[]
    for identifier,question in QUESTIONS:
        prompt_started=time.perf_counter()
        with monitor.measure(identifier+'.preprocess') as preprocess_metrics:
            messages=[{'role':'user','content':[{'type':'image'},{'type':'text','text':question}]}]
            prompt=processor.apply_chat_template(messages,add_generation_prompt=True)
            inputs=processor(text=prompt,images=[image],return_tensors='pt').to(args.device)
            prompt_length=inputs['input_ids'].shape[1]
            if args.device=='cuda':torch.cuda.synchronize()
        streamer=FirstTokenClock()
        with monitor.measure(identifier+'.generate') as generation_metrics:
            with torch.inference_mode():
                generated=model.generate(**inputs,max_new_tokens=args.max_new_tokens,do_sample=False,use_cache=True,streamer=streamer)
            if args.device=='cuda':torch.cuda.synchronize()
        with monitor.measure(identifier+'.decode'):
            output_ids=generated[:,prompt_length:]
            answer=processor.batch_decode(output_ids,skip_special_tokens=True)[0].strip()
        tokens=output_ids.shape[1]
        item={'id':identifier,'prompt':question,'answer':answer,'output_tokens':tokens,'hit_token_limit':tokens>=args.max_new_tokens,'inference_seconds':round(generation_metrics['wall_seconds'],3),'preprocess_seconds':preprocess_metrics['wall_seconds'],'time_to_first_token_seconds':round(streamer.first_token_seconds,6) if streamer.first_token_seconds is not None else None,'time_to_complete_answer_seconds':round(time.perf_counter()-prompt_started,6),'tokens_per_second_including_prefill':round(tokens/generation_metrics['wall_seconds'],3),'resources':generation_metrics}
        answers.append(item)
        print(json.dumps(item,ensure_ascii=True),flush=True)
    resources,samples=monitor.finish()
    resources['model_device']=args.device
    resources['cuda_execution_available']=torch.cuda.is_available()
    resources['cuda_build']=torch.version.cuda
    resources['cuda_peak_allocated_mib']=round(torch.cuda.max_memory_allocated()/2**20,3) if args.device=='cuda' else None
    resources['run_condition']='Cached weights only / no network' if args.offline else 'May include model downloads or network metadata checks'
    telemetry_path=args.output.with_suffix('.telemetry.json')
    report={
        'status':'inference_completed','created_at':datetime.now(timezone.utc).isoformat(),
        'model':args.model,'revision':revision,'model_license':'Apache-2.0',
        'image':{'name':args.input.name,'sha256':hashlib.sha256(args.input.read_bytes()).hexdigest(),'size':list(image.size)},
        'runtime':{'python':platform.python_version(),'torch':torch.__version__,'transformers':transformers.__version__,'huggingface_hub':huggingface_hub.__version__,'pillow':pillow_version,'platform':platform.platform(),'device':args.device,'dtype':'float32','threads':args.threads,'model_parameters':sum(p.numel() for p in model.parameters()),'longest_edge':args.longest_edge,'do_sample':False,'max_new_tokens':args.max_new_tokens},
        'model_load_and_download_seconds':load_metrics['wall_seconds'],'ready_after_imports_and_load_seconds':round(loaded-start,3),'total_seconds':round(time.perf_counter()-start,3),'resources':resources,'telemetry_file':telemetry_path.name,
        'test_design':{'authored_guides_used':False,'subject_name_in_prompts':False,'image_filename_passed_to_model':False,'manual_review_required':True},
        'answers':answers,
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    telemetry_path.write_text(json.dumps({'interval_seconds_requested':args.sample_interval,'samples':samples},indent=2)+'\n',encoding='utf-8')
    csv_path=args.output.with_suffix('.metrics.csv')
    write_metrics_csv(report,csv_path)
    report['metrics_csv_file']=csv_path.name
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
    print(f'Saved raw model responses: {args.output.resolve()}',flush=True)
    return report


if __name__=='__main__':
    try:
        analyze(parser().parse_args())
    except (ValueError,OSError,ImportError) as error:
        print(f'Vision test failed: {error}',file=sys.stderr)
        sys.exit(1)
