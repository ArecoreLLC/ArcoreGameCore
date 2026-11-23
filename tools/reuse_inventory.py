"""Read-only Godot procedure inventory. No imports, game execution or asset copying."""
import argparse,hashlib,json,re
from pathlib import Path

def scan(root):
    root=Path(root).resolve();files=[]
    for folder in ['scripts','addons']:
        for path in sorted((root/folder).rglob('*.gd')):
            if path.is_symlink():continue
            text=path.read_text(encoding='utf-8-sig')
            files.append({'path':path.relative_to(root).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'lines':len(text.splitlines()),'functions':re.findall(r'^(?:static )?func (\w+)\(',text,re.M),
                'resource_dependencies':sorted(set(re.findall(r'(?:preload|load)\("(res://[^"\n]+)"\)',text)))})
    return {'schema':'gamecore.reuse-inventory.v1','root':str(root),'scope':'GDScript scripts/ and addons/; source inspection only, not playtest proof','files':files,'file_count':len(files),'function_count':sum(len(f['functions']) for f in files)}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    report=scan(a.root);Path(a.out).write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='files'}))
