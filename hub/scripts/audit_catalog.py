"""Refresh filesystem evidence without changing editorial descriptions or any game.
Run from any working directory. Only known catalog roots are read. No game code runs.
"""
import hashlib
import json
import os
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data'
SKIP = {'.git', '.godot', 'node_modules', 'target', 'Binaries', 'Intermediate',
        'DerivedDataCache', 'builds', 'Builds', 'Packaged', 'Releases', '.publish-tickles',
        'tools', '.venv', '__pycache__', 'android', 'dist', 'vendor'}
ASSETS = {'.glb', '.gltf', '.blend', '.fbx', '.obj', '.uasset', '.umap', '.tscn',
          '.tres', '.gdshader', '.wav', '.ogg', '.mp3', '.png', '.jpg', '.webp', '.mp4', '.webm'}
CODE = {'.cpp', '.h', '.gd', '.ts', '.js', '.jsx', '.tsx', '.cs', '.py', '.ps1'}

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def text(p):
    return p.read_text(encoding='utf-8-sig', errors='replace')

def scan(root):
    errors = []
    paths = []
    def error(e):
        errors.append(str(e))
    for base, dirs, files in os.walk(root, onerror=error, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP and not (Path(base)/d).is_symlink()
                         and not (Path(base)/d).is_junction())
        for name in sorted(files):
            p = Path(base)/name
            if not p.is_symlink():
                paths.append(p)
    return paths, errors

def git(root):
    def run(*args):
        result = subprocess.run(['git','-C',str(root),*args], capture_output=True,text=True)
        return result.stdout.strip() if result.returncode == 0 else None
    return {'head': run('rev-parse','HEAD'), 'dirty': bool(run('status','--porcelain','--untracked-files=no')),
            'note': 'HEAD does not pin uncommitted files; see inspected-file SHA-256. Untracked assets may exist.'}

def main():
    catalog = json.loads((DATA/'catalog.json').read_text(encoding='utf-8'))
    assets_all = []
    for project in catalog:
        root = Path(project['path'])
        paths, errors = scan(root)
        rel = lambda p: p.relative_to(root).as_posix()
        source = [p for p in paths if p.suffix.lower() in CODE and 'Saved' not in p.parts
                  and 'Diagnostics' not in p.parts and not any(x.startswith('.') for x in p.relative_to(root).parts)]
        # Hash project-authored source; inventory binary assets without loading their contents.
        project['source_files'] = [{'path':rel(p),'sha256':digest(p),'bytes':p.stat().st_size} for p in source]
        evidence = [p for p in paths if p.suffix.lower() in {'.md','.json'} and
                    re.search(r'validation|verification|source.?pin|source.?snapshot|quality_pass|credits|license',p.name,re.I)
                    and 'Saved' not in p.parts]
        project['evidence_files'] = [{'path':rel(p),'sha256':digest(p)} for p in evidence]
        project['historical_checks'] = []
        for p in evidence:
            if p.name.upper() != 'VALIDATION.JSON':
                continue
            try:
                obj = json.loads(text(p))
                def visit(value, key=''):
                    if isinstance(value,dict):
                        if value.get('status') in ['passed','failed','blocked','not_run']:
                            project['historical_checks'].append({'id':value.get('id',key),'status':value['status'],
                                'command':value.get('command'), 'artifact':value.get('artifact',value.get('evidence',value.get('log'))),
                                'record':rel(p),'freshness':'historical, not rerun by catalog audit'})
                        for k,v in value.items():
                            if isinstance(v,(dict,list)): visit(v,k)
                    elif isinstance(value,list):
                        for i,v in enumerate(value): visit(v,f'{key}/{i}')
                visit(obj)
            except (ValueError,OSError):
                errors.append('Could not parse '+rel(p))
        project['asset_files'] = []
        media = []
        for p in paths:
            suffix = p.suffix.lower()
            if suffix not in ASSETS: continue
            if 'Saved' in p.parts:
                if suffix in {'.png','.jpg','.mp4','.webm'} and re.search(r'screenshot|capture|qa|validation',str(p),re.I):
                    media.append({'path':str(p),'name':p.name,'kind':'screenshot' if suffix in {'.png','.jpg'} else 'video'})
                continue
            row={'project_id':project['id'],'path':rel(p),'format':suffix[1:], 'bytes':p.stat().st_size,
                 'rights':'unreviewed','hash':None}
            assets_all.append(row)
            project['asset_files'].append(row)
        project['asset_counts']=dict(Counter(a['format'] for a in project['asset_files']))
        project['media_candidates']=media[:24]
        project['revision']=git(root)
        project['audit']={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'errors':errors,
                          'method':'Read-only filesystem/source audit; no builds, imports, playback or playtests executed'}
        old_commands=project.get('commands',[])
        project['commands']=[]
        for name in project.pop('command_names',[]):
            for p in paths:
                if p.name==name and p.suffix=='.ps1': project['commands'].append('./'+rel(p))
        # Preserve discovered commands during repeated refreshes.
        if not project['commands']:
            project['commands']=old_commands or ['./'+rel(p) for p in source if p.suffix=='.ps1' and p.name in
                                 ['Build.ps1','Play.ps1','Launch.ps1','Test.ps1','Build-Project.ps1','Build-Demo.ps1','build.ps1']]
        project['subgames']=[]
        arcade=root/'src/game/scenes/arcade/ArcadeHubScene.ts'
        if arcade.exists():
            for block in re.findall(r'\{\s*label:.*?\n\s*\}',text(arcade),re.S):
                def field(key):
                    match=re.search(key+r":\s*'((?:\\.|[^'])*)'",block)
                    return match.group(1).replace('\\n',' ').replace("\\'", "'") if match else ''
                key=field('key'); scene=arcade.parent/(key+'.ts')
                if not key or not field('gameId'):
                    continue
                project['subgames'].append({'name':field('label').title(),'id':field('gameId'),
                    'description':field('description'),'source':rel(scene),'source_present':scene.exists(),
                    'sha256':digest(scene) if scene.exists() else None,'validation':'source present; playtest not_run'})
        print(project['name'],len(source),'source files;',len(project['asset_files']),'asset files')
    files=[]
    for project in catalog:
        project['source_file_count']=len(project['source_files'])
        project['asset_file_count']=len(project['asset_files'])
        for kind,key in [('source','source_files'),('asset','asset_files')]:
            files.extend({'project_id':project['id'],'kind':kind,**f} for f in project.pop(key))
    (DATA/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
    (DATA/'files.jsonl').write_text('\n'.join(json.dumps(f,ensure_ascii=False) for f in files),encoding='utf-8')
    print('Catalog projects:',len(catalog),'Asset records:',len(assets_all))

if __name__=='__main__': main()
