import React,{useEffect,useState} from 'react';
import {invoke,isTauri} from '@tauri-apps/api/core';
import {open} from '@tauri-apps/plugin-dialog';
import {ArrowRight,Check,Copy,Download,FolderOpen,GitBranch,Plus,Save,Search} from 'lucide-react';
import seedPipelines from '../data/pipelines.json';

const native = isTauri();

export type PipelineHandoff = {from:string; to:string; artifact:string; contract:string};
export type PipelineStage = {step:string; owner:string; tool_or_guide:string; acceptance:string};
export type PipelineRecord = {
 id:string; title:string; status:string; kind:string;
 source_component:string; target_component:string; summary:string;
 guide_path?:string; tool_path?:string; updated_at?:string;
 handoffs:PipelineHandoff[]; stages:PipelineStage[];
};

function slugify(text:string):string{
 return text.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,80);
}

export function renderPipelineMarkdown(p:PipelineRecord):string{
 const handoffRows = p.handoffs.map(h=>`| ${h.from} | ${h.to} | ${h.artifact} | \`${h.contract}\` |`).join('\n');
 const stageRows = p.stages.map(s=>`| ${s.step} | ${s.owner} | \`${s.tool_or_guide}\` | ${s.acceptance} |`).join('\n');
 return [
  `# ${p.title}`,
  '',
  `- **ID:** \`${p.id}\``,
  `- **Status:** \`${p.status}\``,
  `- **Flow:** ${p.source_component} -> ${p.target_component}`,
  p.guide_path ? `- **Guide:** \`${p.guide_path}\`` : '',
  p.tool_path ? `- **Tool / Spec:** \`${p.tool_path}\`` : '',
  '',
  '## Summary',
  '',
  p.summary,
  '',
  '## Handoffs',
  '',
  '| From | To | Artifact | Contract |',
  '|---|---|---|---|',
  handoffRows || '| - | - | - | - |',
  '',
  '## Stages',
  '',
  '| Step | Owner | Tool / Guide | Acceptance |',
  '|---|---|---|---|',
  stageRows || '| - | - | - | - |',
  '',
 ].filter(x=>x!==undefined).join('\n');
}

const emptyDraft = ():PipelineRecord => ({
 id: '',
 title: '',
 status: 'draft',
 kind: 'proposal',
 source_component: '',
 target_component: '',
 summary: '',
 handoffs: [{from:'', to:'', artifact:'', contract:'shared/pipeline-contract.md'}],
 stages: [{step:'1. ', owner:'', tool_or_guide:'', acceptance:''}],
});

export default function PipelinesView(){
 const [proposals,setProposals] = useState<PipelineRecord[]>([]);
 const [selected,setSelected] = useState<PipelineRecord | null>(seedPipelines.pipelines[0] as PipelineRecord);
 const [draft,setDraft] = useState<PipelineRecord | null>(null);
 const [query,setQuery] = useState('');
 const [statusFilter,setStatusFilter] = useState('');
 const [notice,setNotice] = useState('');
 const [error,setError] = useState('');
 const [copied,setCopied] = useState('');
 const [busy,setBusy] = useState(false);

 async function loadProposals(){
  if(!native) return;
  try{
   const rows = await invoke<PipelineRecord[]>('pipeline_proposals');
   setProposals(rows);
  }catch(e){setError(String(e))}
 }

 useEffect(()=>{void loadProposals()},[]);

 const allPipelines:PipelineRecord[] = [...proposals, ...(seedPipelines.pipelines as PipelineRecord[])];
 const visible = allPipelines.filter(p =>
  (!statusFilter || p.status === statusFilter) &&
  [p.id, p.title, p.source_component, p.target_component, p.summary].join(' ').toLowerCase().includes(query.toLowerCase())
 );

 async function copyText(key:string, value:string){
  try{
   await navigator.clipboard.writeText(value);
   setCopied(key);
   setTimeout(()=>setCopied(''),1600);
  }catch{setNotice('Clipboard unavailable — use Export .json + .md instead.')}
 }

 async function saveProposal(){
  if(!draft) return;
  setBusy(true); setError(''); setNotice('');
  try{
   const payload:PipelineRecord = {
    ...draft,
    id: draft.id.trim() || slugify(draft.title),
   };
   const saved = native
    ? await invoke<PipelineRecord>('save_pipeline_proposal', {proposal: payload})
    : {...payload, updated_at: new Date().toISOString()};
   setProposals(prev => [saved, ...prev.filter(x=>x.id!==saved.id)]);
   setSelected(saved);
   setDraft(null);
   setNotice(`Saved ${saved.status}: ${saved.title}`);
  }catch(e){setError(String(e))}
  finally{setBusy(false)}
 }

 async function exportProposal(p:PipelineRecord){
  setError('');
  const md = renderPipelineMarkdown(p);
  if(native){
   try{
    const directory = await open({directory:true, multiple:false, title:'Export pipeline .json and .md'});
    if(typeof directory === 'string'){
     const path = await invoke<string>('export_pipeline_proposal', {directory, proposal: p, markdown: md});
     setNotice(`Exported: ${path}`);
    }
   }catch(e){setError(String(e))}
  }else{
   await copyText(`md-${p.id}`, md);
   setNotice('Copied standardized Markdown to clipboard.');
  }
 }

 return (
  <div>
   <div className="page-heading compact">
    <div>
     <h1>Pipelines & handoffs</h1>
     <p>Standardized pipeline metadata ({seedPipelines.contract}). Existing pipelines are read-only; create proposals or drafts for new pipelines.</p>
    </div>
    <div className="inline">
     <button className="primary" onClick={()=>{setDraft(emptyDraft()); setError(''); setNotice('')}}><Plus size={16}/> New proposal / draft</button>
    </div>
   </div>

   {error && <div role="alert" className="message error">{error}</div>}
   {notice && <div role="status" className="message success">{notice}</div>}

   {draft && (
    <section className="panel" style={{marginBottom:16}}>
     <div className="section-heading">
      <div>
       <div className="eyebrow">NEW PIPELINE PROPOSAL / DRAFT</div>
       <h2>Create standardized pipeline metadata</h2>
      </div>
      <div className="inline">
       <button onClick={()=>setDraft(null)}>Cancel</button>
       <button className="primary" disabled={busy || !draft.title.trim()} onClick={()=>void saveProposal()}><Save size={15}/> Save {draft.status}</button>
      </div>
     </div>
     <div className="form-row">
      <label className="field"><span>Title</span><input value={draft.title} placeholder="e.g. Critter SFX & Foley Pipeline" onChange={e=>{const t=e.target.value; setDraft({...draft, title:t, id: draft.id || slugify(t)})}}/></label>
      <label className="field"><span>ID (kebab-case)</span><input value={draft.id} placeholder="critter-sfx-foley" onChange={e=>setDraft({...draft, id:slugify(e.target.value)})}/></label>
      <label className="field"><span>Status</span><select value={draft.status} onChange={e=>setDraft({...draft, status:e.target.value})}><option value="draft">draft</option><option value="proposal">proposal</option></select></label>
     </div>
     <div className="form-row">
      <label className="field"><span>Source component</span><input value={draft.source_component} placeholder="ArcoreSoundCore" onChange={e=>setDraft({...draft, source_component:e.target.value})}/></label>
      <label className="field"><span>Target component</span><input value={draft.target_component} placeholder="Unreal 5.8.4" onChange={e=>setDraft({...draft, target_component:e.target.value})}/></label>
     </div>
     <label className="field"><span>Summary</span><textarea rows={2} value={draft.summary} placeholder="Concise scope and acceptance goal…" onChange={e=>setDraft({...draft, summary:e.target.value})}/></label>

     <div className="section-heading" style={{marginTop:10}}>
      <h3>Handoffs ({draft.handoffs.length})</h3>
      <button onClick={()=>setDraft({...draft, handoffs:[...draft.handoffs, {from:'', to:'', artifact:'', contract:'shared/pipeline-contract.md'}]})}>+ Add handoff</button>
     </div>
     {draft.handoffs.map((h,i)=>(
      <div className="form-row" key={i}>
       <label className="field"><span>From</span><input value={h.from} onChange={e=>setDraft({...draft, handoffs:draft.handoffs.map((x,j)=>j===i?{...x,from:e.target.value}:x)})}/></label>
       <label className="field"><span>To</span><input value={h.to} onChange={e=>setDraft({...draft, handoffs:draft.handoffs.map((x,j)=>j===i?{...x,to:e.target.value}:x)})}/></label>
       <label className="field"><span>Artifact</span><input value={h.artifact} onChange={e=>setDraft({...draft, handoffs:draft.handoffs.map((x,j)=>j===i?{...x,artifact:e.target.value}:x)})}/></label>
       <label className="field"><span>Contract</span><input value={h.contract} onChange={e=>setDraft({...draft, handoffs:draft.handoffs.map((x,j)=>j===i?{...x,contract:e.target.value}:x)})}/></label>
      </div>
     ))}

     <div className="section-heading" style={{marginTop:10}}>
      <h3>Stages ({draft.stages.length})</h3>
      <button onClick={()=>setDraft({...draft, stages:[...draft.stages, {step:`${draft.stages.length+1}. `, owner:'', tool_or_guide:'', acceptance:''}]})}>+ Add stage</button>
     </div>
     {draft.stages.map((s,i)=>(
      <div className="form-row" key={i}>
       <label className="field"><span>Step</span><input value={s.step} onChange={e=>setDraft({...draft, stages:draft.stages.map((x,j)=>j===i?{...x,step:e.target.value}:x)})}/></label>
       <label className="field"><span>Owner</span><input value={s.owner} onChange={e=>setDraft({...draft, stages:draft.stages.map((x,j)=>j===i?{...x,owner:e.target.value}:x)})}/></label>
       <label className="field"><span>Tool / Guide</span><input value={s.tool_or_guide} onChange={e=>setDraft({...draft, stages:draft.stages.map((x,j)=>j===i?{...x,tool_or_guide:e.target.value}:x)})}/></label>
       <label className="field"><span>Acceptance</span><input value={s.acceptance} onChange={e=>setDraft({...draft, stages:draft.stages.map((x,j)=>j===i?{...x,acceptance:e.target.value}:x)})}/></label>
      </div>
     ))}
    </section>
   )}

   <div className="filterbar">
    <div className="search"><Search size={18}/><input aria-label="Search pipelines" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Filter pipelines, components, artifacts…"/></div>
    <select aria-label="Pipeline status" value={statusFilter} onChange={e=>setStatusFilter(e.target.value)}>
     <option value="">All statuses ({allPipelines.length})</option>
     {['scaffold','exploratory','active','proposal','draft'].map(s=><option key={s} value={s}>{s}</option>)}
    </select>
   </div>

   <div className="two-col">
    <div>
     {visible.map(p=>(
      <button key={p.id} className="panel" style={{width:'100%',textAlign:'left',marginBottom:10,borderColor:selected?.id===p.id?'var(--accent, #4f8cff)':undefined}} onClick={()=>setSelected(p)}>
       <div className="inline">
        <GitBranch size={15}/>
        <strong>{p.title}</strong>
        <span className="pill">{p.status}</span>
        {p.kind==='proposal' && <span className="pill warm">proposal/draft</span>}
       </div>
       <p className="muted small" style={{marginTop:4}}>{p.source_component} → {p.target_component}</p>
       <p className="small">{p.summary}</p>
      </button>
     ))}
    </div>

    {selected && (
     <section className="panel">
      <div className="section-heading">
       <div>
        <div className="eyebrow">{selected.kind === 'proposal' ? 'PROPOSAL / DRAFT' : 'EXISTING PIPELINE (READ-ONLY)'} · {selected.status.toUpperCase()}</div>
        <h2>{selected.title}</h2>
       </div>
       <div className="inline">
        <button onClick={()=>void copyText(`md-${selected.id}`, renderPipelineMarkdown(selected))}>
         {copied===`md-${selected.id}`?<Check size={14}/>:<Copy size={14}/>} Copy .md
        </button>
        <button onClick={()=>void exportProposal(selected)}>
         <Download size={14}/> Export .json + .md
        </button>
       </div>
      </div>
      <p>{selected.summary}</p>
      <p className="muted small"><strong>Flow:</strong> {selected.source_component} <ArrowRight size={12} style={{verticalAlign:'middle'}}/> {selected.target_component}</p>
      {(selected.guide_path || selected.tool_path) && (
       <div className="inline" style={{marginTop:8}}>
        {selected.guide_path && <button className="file-link" disabled={!native} onClick={()=>void invoke('open_folder_for_path',{path:`X:/Projects/ArcoreGameCore/${selected.guide_path}`})}>{selected.guide_path}<FolderOpen size={12}/></button>}
        {selected.tool_path && <button className="file-link" disabled={!native} onClick={()=>void invoke('open_folder_for_path',{path:`X:/Projects/ArcoreGameCore/${selected.tool_path}`})}>{selected.tool_path}<FolderOpen size={12}/></button>}
       </div>
      )}

      <h3 style={{marginTop:14}}>Handoffs ({selected.handoffs.length})</h3>
      {selected.handoffs.map((h,i)=>(
       <div key={i} className="check-row" style={{marginTop:6}}>
        <span className="pill">{i+1}</span>
        <div>
         <strong>{h.from} → {h.to}</strong>
         <div className="small">{h.artifact} · <code>{h.contract}</code></div>
        </div>
       </div>
      ))}

      <h3 style={{marginTop:14}}>Stages ({selected.stages.length})</h3>
      {selected.stages.map((s,i)=>(
       <div key={i} className="check-row" style={{marginTop:6}}>
        <span className="pill green">{s.owner}</span>
        <div>
         <strong>{s.step}</strong>
         <div className="small"><code>{s.tool_or_guide}</code> · {s.acceptance}</div>
        </div>
       </div>
      ))}

      <details style={{marginTop:14}}>
       <summary>Standardized JSON & Markdown metadata</summary>
       <pre style={{whiteSpace:'pre-wrap',fontSize:11,marginTop:8}}>{JSON.stringify(selected, null, 2)}</pre>
      </details>
     </section>
    )}
   </div>
  </div>
 );
}
