import React,{useMemo,useState} from 'react';
import {invoke,isTauri} from '@tauri-apps/api/core';
import {open} from '@tauri-apps/plugin-dialog';
import {Copy,Download,X} from 'lucide-react';
import {exportFileName,type ExportSource} from './gameExport';

export type ExportScope='filtered'|'all'|'selected';

/** Shared export modal for the game catalog and the pipeline (roadmap): preview, copy or save JSON. */
export default function GameExportDialog({source,heading,filteredCount,totalCount,selectedName,initialScope,build,onClose}:{
 source:ExportSource; heading:string; filteredCount:number; totalCount:number; selectedName?:string; initialScope?:ExportScope;
 build:(scope:ExportScope)=>unknown; onClose:()=>void;
}){
 const [scope,setScope]=useState<ExportScope>(initialScope||(selectedName?'selected':'filtered'));
 const [message,setMessage]=useState('');
 const text=useMemo(()=>{try{return JSON.stringify(build(scope),null,2)}catch(e){return `// Export failed: ${String(e)}`}},[scope,build]);
 const fileName=exportFileName(source,scope);

 async function copy(){
  try{await navigator.clipboard.writeText(text);setMessage('JSON copied to clipboard')}
  catch{const area=document.getElementById('game-export-json') as HTMLTextAreaElement|null;area?.focus();area?.select();setMessage('Clipboard unavailable. JSON selected — press Ctrl+C to copy.')}
 }
 async function save(){
  try{
   if(isTauri()){
    const directory=await open({directory:true,multiple:false,title:'Export games JSON'});
    if(typeof directory==='string'){const path=await invoke<string>('export_games_json',{directory,document:JSON.parse(text),fileName});setMessage('Exported: '+path)}
   }else{
    const url=URL.createObjectURL(new Blob([text+'\n'],{type:'application/json'}));
    const a=document.createElement('a');a.href=url;a.download=fileName;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    setMessage(`Download started: ${fileName}`);
   }
  }catch(e){setMessage(String(e))}
 }

 const options:[ExportScope,string][]=[
  ...(selectedName?[['selected',`This game · ${selectedName}`] as [ExportScope,string]]:[]),
  ['filtered',`Filtered · ${filteredCount}`],
  ['all',`All · ${totalCount}`],
 ];
 return <div className="overlay"><section className="modal roadmap-export game-export" role="dialog" aria-modal="true" aria-label={heading}>
  <div className="section-heading"><div><h2>{heading}</h2><p>Overview, genre, main mechanics, classification facets, full capability taxonomy and flat <code>namespace:value</code> tags for each game.</p></div><button aria-label="Close export" onClick={onClose}><X size={18}/></button></div>
  <div className="tabs" role="radiogroup" aria-label="Export scope">{options.map(([id,lbl])=><button key={id} role="radio" aria-checked={scope===id} className={scope===id?'selected':''} onClick={()=>{setScope(id);setMessage('')}}>{lbl}</button>)}</div>
  <label className="field"><span><code style={{textTransform:'none'}}>{fileName}</code> · {(new Blob([text]).size/1024).toFixed(1)} KB</span><textarea id="game-export-json" aria-label="Games export JSON" readOnly value={text} spellCheck={false}/></label>
  {message&&<p role="status">{message}</p>}
  <div className="modal-actions"><button onClick={onClose}>Close</button><button onClick={copy}><Copy size={16}/> Copy JSON</button><button className="primary" onClick={save}><Download size={16}/> Save file</button></div>
 </section></div>;
}
