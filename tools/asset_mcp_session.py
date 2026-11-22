import json,subprocess,os
from pathlib import Path
class Session:
 def __init__(self, command, cwd=None):
  self.p=subprocess.Popen(command,cwd=cwd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0,text=True,encoding='utf-8');self.id=0
  self.request('initialize',{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'gamecore-art','version':'1'}})
 def request(self,method,params):
  self.id+=1;self.p.stdin.write(json.dumps({'jsonrpc':'2.0','id':self.id,'method':method,'params':params})+'\n');self.p.stdin.flush()
  while True:
   line=self.p.stdout.readline()
   if not line: raise RuntimeError('MCP process exited')
   result=json.loads(line)
   if result.get('id')==self.id:
    if 'error' in result:raise RuntimeError(result['error'])
    return result['result']
 def call(self,name,args):
  r=self.request('tools/call',{'name':name,'arguments':args})
  if r.get('isError'):raise RuntimeError(str(r))
  return r
 def close(self):
  self.p.stdin.close();self.p.wait(timeout=10)
def unpack(r):
 for c in r.get('content',[]):
  if c.get('type')=='text':
   try:return json.loads(c['text'])
   except ValueError:pass
 return r
