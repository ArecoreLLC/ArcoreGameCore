"""Read-only module discovery against the standalone MCP binary and isolated library."""
import json, os, subprocess, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
requests=[{'jsonrpc':'2.0','id':0,'method':'tools/list'}]
cases=[('module_search',{'query':'terrain clearance'}),('module_search',{'key':'portable:buoyancy','details':True}),
       ('module_search',{'language':'csharp'}),('module_search',{'language':'gdscript','limit':1}),
       ('module_search',{'language':'gdscript','limit':1,'offset':1}),
       ('module_search',{'capability':'cap-terrain-height-sampling'}),
       ('reusable_modules',{'id':'reef-clearance'}),('reusable_modules',{'id':'lyric-world-cues'}),
       ('reusable_modules',{'id':'save-rotation'}),('module_search',{'limit':101})]
for i,(name,args) in enumerate(cases,1):requests.append({'jsonrpc':'2.0','id':i,'method':'tools/call','params':{'name':name,'arguments':args}})
with tempfile.TemporaryDirectory(prefix='gamecore-module-mcp-') as temp:
    result=subprocess.run([str(ROOT/'src-tauri/target/release/gamecore-library.exe'),'--mcp'],
        input=''.join(json.dumps(r)+'\n' for r in requests),capture_output=True,text=True,timeout=30,
        env={**os.environ,'GAMECORE_DATA_DIR':temp})
    assert result.returncode==0,result.stderr
    rows=[json.loads(line) for line in result.stdout.splitlines()]
assert len(rows)==len(requests)
assert {'module_search','reusable_modules'}<={r['name'] for r in rows[0]['result']['tools']}
for row in rows[1:-1]:assert row['result']['isError'] is False,row
bodies=[json.loads(row['result']['content'][0]['text']) for row in rows[1:-1]]
assert bodies[0]['entries'][0]['key']=='procedures:reef-clearance'
assert bodies[1]['entries'][0]['source_entry']['language']=='cpp'
assert bodies[2]['total']==3
assert bodies[3]['entries'][0]['key']!=bodies[4]['entries'][0]['key']
assert bodies[5]['entries'][0]['key']=='procedures:reef-clearance'
assert bodies[6]['entries'][0]['status']==bodies[7]['entries'][0]['status']=='extracted'
assert bodies[8]['entries'][0]['disposition']=='game-owned'
assert rows[-1]['result']['isError'] is True
print(json.dumps({'status':'passed','checks':len(requests),'responses':rows},indent=2))
