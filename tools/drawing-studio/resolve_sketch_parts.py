"""Identify an image, ground taxonomy parts, and export construction lessons on CPU."""
import argparse, base64, io, json, os, re, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from subject_taxonomy import load_catalog, candidate_profiles, resolve_part


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--arachnid-mode',choices=('profile','generic'),default='profile')
    args = parser.parse_args()
    started = time.perf_counter()
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    from vision_metrics import ResourceMonitor
    monitor = ResourceMonitor().start()
    try:
        import torch
        from transformers import AutoProcessor, Florence2ForConditionalGeneration
        from PIL import ImageDraw
        from render_gif import normalized_reference
        from shape_geometry import ellipse_points
        torch.set_num_threads(8)
        reference, _, _ = normalized_reference(argparse.Namespace(input=args.input, lesson=None))
        image = reference.convert('RGB')
        info = json.loads((ROOT / '.model-cache/florence-base.json').read_text())
        with monitor.measure('model_load'):
            processor = AutoProcessor.from_pretrained(info['path'], local_files_only=True, trust_remote_code=False, use_fast=False)
            model = Florence2ForConditionalGeneration.from_pretrained(info['path'], local_files_only=True, dtype=torch.float32).eval()
        queries = []
        def query(task, text='', query_image=None):
            query_image = image if query_image is None else query_image
            remaining = 25 - (time.perf_counter() - started)
            if remaining < 1: raise TimeoutError('Part analysis budget exhausted')
            with monitor.measure(task):
                inputs = processor(text=task+text, images=query_image, return_tensors='pt')
                with torch.inference_mode():
                    tokens = model.generate(**inputs, max_new_tokens=256, num_beams=1, do_sample=False, max_time=remaining)
                raw = processor.batch_decode(tokens, skip_special_tokens=False)[0]
                parsed = processor.post_process_generation(re.sub(r'>\s+<', '><', raw), task=task, image_size=query_image.size)[task]
            queries.append({'task':task, 'prompt':text, 'raw':raw, 'parsed':parsed})
            return parsed
        caption = query('<DETAILED_CAPTION>')
        catalog = load_catalog()
        candidates = candidate_profiles(caption, catalog)
        # Common caption nouns are profile-selection evidence, never image filenames.
        noun_profiles = {r'\b(wolf|dog|cat|horse|deer|lion|tiger|bear)\b':'profile.quadruped', r'\b(robot|android)\b':'profile.humanoid_robot', r'\b(man|woman|boy|girl)\b':'profile.humanoid_biped'}
        noun_profiles.update({r'\b(eagle|bird|parrot|owl)\b':'profile.avian',r'\b(iguana|lizard|crocodile)\b':'profile.reptile'})
        for pattern, candidate in noun_profiles.items():
            if re.search(pattern, caption, re.I) and not any(c['profile']==candidate for c in candidates):
                candidates.append({'profile':candidate,'alias_score':.8,'raw_label':caption,'source':'caption_noun'})
        # Generic words do not establish a useful anatomical profile.
        candidates = [c for c in candidates if c['profile'] != 'profile.generic_object']
        # Caption order is a heuristic for primary subject versus supporting props.
        def first_mention(candidate):
            aliases=catalog['profiles'][candidate['profile']].get('aliases',[])
            patterns=[r'\b'+re.escape(alias)+r'\b' for alias in aliases]
            patterns += [pattern for pattern,pid in noun_profiles.items() if pid==candidate['profile']]
            matches=[m.start() for pattern in patterns if (m:=re.search(pattern,caption,re.I))]
            return min(matches,default=len(caption))
        candidates.sort(key=first_mention)
        profile_id = candidates[0]['profile'] if candidates else None
        profile = catalog['profiles'][profile_id] if profile_id else None
        if profile:
            labels = [('body' if p['part']=='part.torso' else catalog['parts'][p['part']]['label']) for p in profile['parts']][:12]
            prompt = 'The subject has ' + ', '.join(labels) + '.'
        else:
            prompt = caption
        from arachnid_profile import eligible, BODY_PROMPT, PALP_PROMPT, adapt
        use_arachnid=eligible(profile_id,caption) and args.arachnid_mode=='profile'
        taxonomy_prompt=prompt
        if use_arachnid:prompt=BODY_PROMPT
        grounded = query('<CAPTION_TO_PHRASE_GROUNDING>', prompt)
        construction=None
        if use_arachnid:
            palp_grounded=query('<CAPTION_TO_PHRASE_GROUNDING>',PALP_PROMPT)
            args.output.parent.mkdir(parents=True,exist_ok=True)
            with monitor.measure('arachnid_construction'):
                from fit_detected_parts import construct
                construction=construct(image,grounded,args.output.with_name(args.output.stem+'-regional'),palp_grounded)
        from part_geometry import fit_geometry, torso_box, individual_detections
        detections = list(zip(grounded.get('labels', []), grounded.get('bboxes', [])))
        if use_arachnid:
            detections=[(re.sub(r'^(the|an|a)\s+','',label.lower()),box) for label,box in detections]
            # Preserve the generic pass's individual eye proposals; a head crop can
            # instead return one aggregate eye-cluster box on stylized spiders.
            eye_grounding=query('<CAPTION_TO_PHRASE_GROUNDING>',taxonomy_prompt)
            detections += [(label,box) for label,box in zip(eye_grounding.get('labels',[]),eye_grounding.get('bboxes',[])) if label.lower()=='eye']
        # Magnify the head for small composition landmarks; do not invent hidden eyes.
        heads = [b for label,b in detections if label.lower()=='head']
        if heads and not use_arachnid and time.perf_counter()-started < 20:
            hx,hy,hr,hb = map(int, heads[0])
            face = image.crop((hx,hy,hr,hb)).resize((640,640))
            eyes = query('<CAPTION_TO_PHRASE_GROUNDING>', 'The face has eyes.', face)
            for label,b in zip(eyes.get('labels',[]),eyes.get('bboxes',[])):
                if label.lower() in ('eye','eyes'):
                    detections.append(('eye',[hx+b[0]*(hr-hx)/640,hy+b[1]*(hb-hy)/640,hx+b[2]*(hr-hx)/640,hy+b[3]*(hb-hy)/640]))
        detections = individual_detections(detections)
        torso = torso_box(detections) if profile_id=='profile.quadruped' else None
        from mask_geometry import foreground, region, fit_part, remainder_candidates, measure
        from construction_polish import polish_guides, align_muzzle
        import numpy as np
        with monitor.measure('foreground_mask'):
            mask,mask_info=foreground(image)
        covered=np.zeros_like(mask)
        guides, parts = [], []
        overlay = image.copy(); draw = ImageDraw.Draw(overlay)
        detection_audit=[]
        def add_shape(shape,label,canonical,box,raw_box,source):
            points=shape['points']; identifier=f'part-{len(parts)+1}'
            guides.append({'type':'ellipse' if shape['primitive']=='ellipse' else 'contour','closed':True,'primitive':shape['primitive'],'stage':0 if canonical in ('part.head','part.torso','part.neck') else 1,'points':points,'part_id':identifier,'canonical_part':canonical,'proposed_role':label})
            parts.append({'id':identifier,'raw_label':label,'canonical_part':canonical,'box':box,'raw_box':raw_box,'geometry_source':source,'fit_metrics':shape.get('metrics'),'orientation_evidence':shape.get('orientation_evidence'),'confidence':None,'review_required':True})
            color='#ba7615' if canonical=='part.unknown' else '#008b64'
            draw.line([tuple(p) for p in points],fill=color,width=3)
            draw.text(tuple(points[0]),label,fill=color,stroke_width=1,stroke_fill='white')

        if construction:
            for candidate in adapt(construction):
                add_shape(candidate['shape'],candidate['role'],candidate['canonical'],candidate['box'],candidate['raw_box'],'arachnid profile; '+candidate['evidence'])
                parts[-1]['walking_segment_candidate']=candidate['walking_segment_candidate']
                guides[-1]['stage']=0 if candidate['canonical'] in ('part.cephalothorax','part.abdomen') else 1
            detection_audit.append({'action':'regional_decomposition','note':'Body proposals grounded by model; exposed appendages from geometry, not individual model detections','body_regions':len(construction['body_parts']),'appendage_regions':len(construction['appendage_candidates'])})
            detections=[(label,box) for label,box in detections if label=='eye']
        for label, raw_box in detections:
            box=list(raw_box)
            geometry_source='edge-fitted semantic region'
            if label.lower()=='body' and profile_id=='profile.quadruped':
                if torso is None: continue
                box=torso
                geometry_source='side-view torso prior from neck, tail and leg anchors; edge fitted'
            if label.lower()=='head':
                ears=[b for l,b in detections if l.lower()=='ear']
                if ears: box[1]=max(box[1],min(b[3]-.15*(b[3]-b[1]) for b in ears))
            x1,y1,x2,y2 = map(float, box)
            if x2-x1 < 6 or y2-y1 < 6:
                detection_audit.append({'label':label,'box':raw_box,'action':'rejected','reason':'too_small'});continue
            resolved = resolve_part('torso' if label.strip().lower()=='body' and profile and any(p['part']=='part.torso' for p in profile['parts']) else label, catalog, None if label=='eye' else profile_id)
            if resolved['part'] in ('part.unknown', 'part.ambiguous'):
                detection_audit.append({'label':label,'box':raw_box,'action':'rejected','reason':'unresolved_taxonomy_label'});continue
            # Reject whole-image detections and duplicate boxes returned for multiple terms.
            if (x2-x1)*(y2-y1) > image.width*image.height*.65:
                detection_audit.append({'label':label,'box':raw_box,'action':'rejected','reason':'whole_image_box'});continue
            if any(sum(abs(a-b) for a,b in zip(box,p['box'])) < 12 for p in parts):
                detection_audit.append({'label':label,'box':raw_box,'action':'rejected','reason':'duplicate_box'});continue
            detection_audit.append({'label':label,'box':raw_box,'action':'accepted','canonical':resolved['part']})
            triangle=resolved['part']=='part.ear' and profile_id=='profile.quadruped'
            points,support = fit_geometry(image,box,triangle)
            points = [[max(0,min(1279,x)),max(0,min(697,y))] for x,y in points]
            part_mask=region(mask,box)
            # Remove appendage detections from the estimated torso, not from landmarks.
            if label=='body':
                for other,b in detections:
                    if other in ('leg','tail','foot'):
                        part_mask[region(mask,b)>0]=0
            covered|=part_mask
            # Eyes are interior landmarks: a foreground silhouette cannot isolate them.
            fitted=fit_part(part_mask,label.lower()) if mask_info['usable'] and label!='eye' else []
            if fitted:
                for shape in fitted:
                    if label=='muzzle':
                        shape,evidence=align_muzzle(image,part_mask,shape)
                        shape['orientation_evidence']=evidence
                    shape['metrics']['foreground_spill_fraction']=measure(shape['points'],mask)['spill_fraction']
                    shape['metrics']['previous_foreground_spill_fraction']=measure(points,mask)['spill_fraction']
                    add_shape(shape,'torso mass' if label=='body' else label,resolved['part'],box,raw_box,geometry_source+'; foreground pixel fit')
            else:
                add_shape({'points':points,'primitive':'triangle' if triangle else 'ellipse'},label,resolved['part'],box,raw_box,geometry_source+'; edge fallback')
        unresolved=[]
        if mask_info['usable'] and torso is not None:
            for candidate in remainder_candidates(mask,covered,torso[3]):
                yy,xx=np.nonzero(candidate); box=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]
                import cv2
                expanded=cv2.dilate(candidate,np.ones((9,9),np.uint8))
                evidence={'touches_detected_foot':any(np.any(expanded & region(mask,b)) for l,b in detections if l=='foot'),'height_width_ratio':round((box[3]-box[1])/max(1,box[2]-box[0]),3),'area_fraction_of_subject':round(float(candidate.sum()/max(1,mask.sum())),4)}
                unresolved.append({'box':box,'hypothesis':'unresolved appendage','evidence':evidence,'review_required':True})
                for shape in fit_part(candidate,'unresolved appendage'):
                    add_shape(shape,'unresolved appendage','part.unknown',box,None,'unclaimed foreground; not semantic detection')
        # Unknown subjects get measured geometry rather than a fixed surrounding oval.
        if len(guides)<2:
            from mask_geometry import unknown_masses
            if mask_info['usable']:
                for shape in unknown_masses(mask):
                    pts=np.asarray(shape['points']);box=[float(pts[:,0].min()),float(pts[:,1].min()),float(pts[:,0].max()),float(pts[:,1].max())]
                    add_shape(shape,'Unresolved mass','part.unknown',box,None,'foreground distance peaks; no semantic identity')
            if not guides:raise ValueError('No supported construction regions; foreground segmentation needs review')
        polish_guides(guides)
        # Render the same faded arcs used by the GIF, retaining full polygons for paint.
        overlay=image.copy(); draw=ImageDraw.Draw(overlay)
        for guide in guides:
            points=guide['points']; color=(186,118,21) if guide.get('canonical_part')=='part.unknown' else (0,139,100)
            for i,(a,b) in enumerate(zip(points[:-1],points[1:])):
                opacity=guide['segment_opacity'][i]
                midpoint=(int((a[0]+b[0])/2),int((a[1]+b[1])/2))
                background=image.getpixel((max(0,min(image.width-1,midpoint[0])),max(0,min(image.height-1,midpoint[1]))))
                ink=tuple(round(c*opacity+base*(1-opacity)) for c,base in zip(color,background))
                draw.line([tuple(a),tuple(b)],fill=ink,width=2 if opacity<1 else 3)
            label=guide.get('proposed_role','')
            if label=='walking-leg segment candidate':label='segment '+guide['part_id'].split('-')[-1]
            elif label=='unresolved mouth appendage':label='mouth candidate'
            draw.text(tuple(points[0]),label,fill=color,stroke_width=1,stroke_fill='white')
        stream = io.BytesIO(); image.save(stream,format='PNG')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        lesson = {'version':1,'name':'Detected part study','study':'custom','image':'data:image/png;base64,'+base64.b64encode(stream.getvalue()).decode(),'guides':guides,'profile':profile_id,'review_required':True}
        args.output.with_name(args.output.stem+'-lesson.json').write_text(json.dumps(lesson),encoding='utf-8')
        overlay.save(args.output.with_suffix('.png'))
        from PIL import Image
        Image.fromarray(mask*255).save(args.output.with_name(args.output.stem+'-mask.png'))
    finally:
        resources,samples = monitor.finish()
    report = {'caption':caption,'profile':profile_id,'profile_candidates':candidates,'parts':parts,'guide_count':len(guides),'mask':mask_info,'unresolved_candidates':unresolved,'queries':queries,'resources':resources,'samples':samples,'elapsed_seconds':time.perf_counter()-started,'model':info,'review_required':True,'arachnid_method':'regional_profile' if use_arachnid else 'generic','detection_audit':detection_audit}
    args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('caption','profile','guide_count','elapsed_seconds')}))


if __name__ == '__main__': main()
