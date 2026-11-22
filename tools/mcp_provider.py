"""Registry-routed local HTTP MCP transport, invoked by the GameCore hub.
Credentials remain in memory; arguments arrive on stdin, not command lines.
"""
import json,sys,urllib.request,urllib.parse
from mcp_registry import ROOT,resolve_http,_read_http_result,PROTOCOL_VERSION,CLIENT_INFO

def call(provider,operation,arguments):
    registry=json.loads((ROOT/'shared/ecosystem.json').read_text(encoding='utf-8'))
    server=next(s for s in registry['mcp']['servers'] if s['id']==provider)
    if operation!='tools/list' and operation not in server['tools']:raise ValueError('Unregistered provider operation')
    url,token,_,problem=resolve_http(server)
    if problem:raise ValueError(problem)
    parsed=urllib.parse.urlparse(url)
    if parsed.scheme!='http' or parsed.hostname not in ['127.0.0.1','localhost','::1']:raise ValueError('Only local HTTP providers are supported')
    headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
    if token:headers['Authorization']='Bearer '+token
    def post(payload,session=None):
        h=dict(headers)
        if session:h['Mcp-Session-Id']=session
        h['MCP-Protocol-Version']=PROTOCOL_VERSION
        req=urllib.request.Request(url,data=json.dumps(payload).encode('utf-8'),headers=h,method='POST')
        with urllib.request.urlopen(req,timeout=25) as response:return response.headers.get('Mcp-Session-Id') or session,_read_http_result(response)
    session,init=post({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':PROTOCOL_VERSION,'capabilities':{},'clientInfo':CLIENT_INFO}})
    if not init or 'result' not in init:raise ValueError('Provider initialization failed')
    post({'jsonrpc':'2.0','method':'notifications/initialized'},session)
    _,response=post({'jsonrpc':'2.0','id':2,'method':'tools/list' if operation=='tools/list' else 'tools/call','params':{} if operation=='tools/list' else {'name':operation,'arguments':arguments}},session)
    if not response or 'result' not in response:raise ValueError('Provider returned no result')
    return {'content':[{'type':'text','text':json.dumps(response['result'])}],'isError':False} if operation=='tools/list' else response['result']
if __name__=='__main__':
    try:result=call(sys.argv[1],sys.argv[2],json.load(sys.stdin))
    except Exception as error:result={'content':[{'type':'text','text':str(error)}],'isError':True}
    print(json.dumps(result))
