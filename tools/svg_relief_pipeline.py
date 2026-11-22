"""GameCore CLI: SVG relief -> ModelForge Blender -> PhotoMaster -> sprite atlases.
One shared recipe is applied to every manifest subject. Originals are never overwritten.
"""
import argparse, base64, hashlib, json, time
from pathlib import Path
from PIL import Image
from svg_relief import build
from mcp_provider import call
from asset_mcp_session import Session, unpack
ROOT=Path(__file__).resolve().parents[1]
def model_call(operation, args):
 r=call('model-forge', operation, args)
 if r.get('isError'):raise RuntimeError(r)
 return r.get('structuredContent') or unpack(r)
def job(model, script, params, save):
 r=model_call('blender_run',{'model_id':model,'version':1,'script':script,'params':params,'format':'blend','save':save,'wait_seconds':0,'timeout_seconds':1200})
 job_id=r['job_id'];print('ModelForge job',job_id,flush=True)
 while r.get('status')=='running':
  time.sleep(1);r=model_call('blender_status',{'job_id':job_id})
 if r.get('status')!='done' or r.get('error'):raise RuntimeError(r)
 return r

def run(manifest_path, output):
 manifest_path=Path(manifest_path).resolve();manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
 output=Path(output).resolve()
 if output.exists():raise FileExistsError('Use a fresh version directory: '+str(output))
 output.mkdir(parents=True);(output/'final').mkdir();(output/'recipes').mkdir()
 receipt={'pipeline':'svg-relief-v1','subjects':[], 'status':'running'}
 photo_command=next(x['command'] for x in json.loads((ROOT/'shared/ecosystem.json').read_text())['mcp']['servers'] if x['id']=='photo-master')
 photo_root=next(x['root'] for x in json.loads((ROOT/'shared/ecosystem.json').read_text())['components'] if x['id']=='photo-master')
 photo=Session([str((ROOT/photo_root/photo_command[0]).resolve()),'--workspace',str(output)])
 try:
  photo.call('studio_state',{})
  def finish(raw, name, adjustments):
   photo.call('open_image',{'path':str(raw)})
   photo.call('set_adjustments',{'adjustments':adjustments})
   preview=photo.call('preview',{'max_edge':768})
   for item in preview['content']:
    if item['type']=='image':(output/(name+'_preview.png')).write_bytes(base64.b64decode(item['data']))
   photo.call('save_project',{'path':str(output/'recipes'/(name+'.json'))})
   target=output/'final'/(name+'.png');photo.call('export_image',{'path':str(target)})
   # Retain the saved project/export, releasing this document before the next
   # subject so large rosters do not exhaust PhotoMaster's open-document limit.
   photo.call('close_document',{})
   return hashlib.sha256(target.read_bytes()).hexdigest()
  for asset in manifest['subjects']:
   name=asset['id']
   if not name.replace('_','').replace('-','').isalnum():raise ValueError('Invalid asset ID')
   source=(manifest_path.parent/asset['svg']).resolve();obj=output/(name+'.obj')
   geometry=build(source,obj)
   imported=model_call('import_files',{'paths':[str(obj)],'note':'Original SVG relief seed; common GameCore pipeline v1'})
   if imported.get('errors'):raise RuntimeError(imported)
   mid=imported['imported'][0]['model_id']
   render=job(mid,(ROOT/'tools/relief_render.py').read_text(),{'output':str(output/name),'palette':str(obj.with_suffix('.json'))},True)
   atlas=Image.new('RGBA',(1536,1536))
   for frame in range(16):
    with Image.open(output/name/('frame_%02d.png'%frame)) as image:
     if image.size!=(384,384):raise ValueError('Unexpected frame size')
     atlas.alpha_composite(image.convert('RGBA'),((frame%4)*384,(frame//4)*384))
   raw=output/(name+'_raw.png');atlas.save(raw)
   digest=finish(raw,name,manifest['character_finish'])
   receipt['subjects'].append({'id':name,'model_id':mid,'source_sha256':geometry['source_sha256'],'geometry_version':geometry.get('geometry_version',1),'job_id':render['job_id'],'model_result':render.get('result',{}).get('saved'),'sha256':digest,'frame_size':384,'columns':4,'rows':4,'clips':{'idle':[0,4],'cast':[4,4],'guard':[8,4],'hit':[12,4]}})
   (output/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
   print('Finished',name,flush=True)
  if manifest.get('environment',False):
   result=job(receipt['subjects'][0]['model_id'],(ROOT/'tools/relief_environment.py').read_text(),{'output':str(output/'environment')},False)
   imported=model_call('import_files',{'paths':[str(output/'environment/editable.blend')],'note':'Original procedural relief arena; no seed geometry retained'})
   digest=finish(output/'environment/environment_raw.png','environment',manifest['environment_finish'])
   receipt['environment']={'job_id':result['job_id'],'sha256':digest,'model_import':imported}
  receipt['status']='complete'
 finally:
  photo.close();(output/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
 return receipt
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');p.add_argument('output');a=p.parse_args();run(a.manifest,a.output)
