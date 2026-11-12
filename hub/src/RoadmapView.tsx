import {useEffect,useState} from 'react';

import {invoke,isTauri} from '@tauri-apps/api/core';

import {open} from '@tauri-apps/plugin-dialog';

import {roadmapReviewExport} from './roadmapExport';

import {ArrowLeft,ArrowUpRight,FolderOpen,Save,Search} from 'lucide-react';

import type {Game,Library,FileRecord} from './types';

import {accepted,progress,unmet,previewRoadmap,type RoadmapGame,type TargetProgress} from './roadmap';

import seed from '../data/capability-roadmap.json';

const native=isTauri();

const states=['planned','in_progress','blocked','implemented','verified','reused'];

function Field({label,value,onChange,multi=false}:{label:string;value:string;onChange:(s:string)=>void;multi?:boolean}){return <label className="field"><span>{label}</span>{multi?<textarea value={value} rows={3} onChange={e=>onChange(e.target.value)}/>:<input value={value} onChange={e=>onChange(e.target.value)}/>}</label>}

export default function Roadmap({lib,onDirty,onBusy,openGame}:{lib:Library;onDirty:(v:boolean)=>void;onBusy:(v:boolean)=>void;openGame:(g:Game)=>void}){

 const [rows,setRows]=useState<RoadmapGame[]>([]),[draft,setDraft]=useState<RoadmapGame|null>(null),[dirty,setDirty]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');

 const [exportText,setExportText]=useState(''),[exportMessage,setExportMessage]=useState('');

 const [query,setQuery]=useState(''),[wave,setWave]=useState(''),[filter,setFilter]=useState(''),[target,setTarget]=useState('');

 const [donor,setDonor]=useState(''),[kind,setKind]=useState('source'),[fileQuery,setFileQuery]=useState(''),[files,setFiles]=useState<FileRecord[]>([]);

 const label=(id:string)=>lib.taxonomy.find(t=>t.id===id)?.label||id;

 async function load(){try{setRows(native?await invoke<RoadmapGame[]>('roadmap'):previewRoadmap(seed.projects));setError('')}catch(e){setError(String(e))}}

 useEffect(()=>{void load()},[]);

 useEffect(()=>{onDirty(dirty)},[dirty,onDirty]);

 useEffect(()=>{onBusy(busy)},[busy,onBusy]);

 useEffect(()=>{let active=true;setFiles([]);if(!native||!donor)return;const id=setTimeout(()=>invoke<FileRecord[]>('list_files',{projectId:donor,kind,query:fileQuery}).then(f=>{if(active)setFiles(f)}).catch(e=>{if(active)setError(String(e))}),180);return()=>{active=false;clearTimeout(id)}},[donor,kind,fileQuery]);

 function leave(){return !busy&&(!dirty||window.confirm('Discard unsaved roadmap changes?'))}

 function select(g:RoadmapGame){if(!leave())return;setDraft(structuredClone(g));setDirty(false);setTarget(g.capability_ids[0]);setDonor(g.donors[0]?.project_id||'');setFileQuery('');setNotice('');setError('');window.scrollTo(0,0)}

 function change(patch:Partial<RoadmapGame>){if(draft){setDraft({...draft,...patch});setDirty(true)}}

 function editTarget(patch:Partial<TargetProgress>){if(draft)change({target_progress:{...draft.target_progress,[target]:{...draft.target_progress[target],...patch}}})}

 async function save(){if(!draft)return;setBusy(true);setError('');try{const saved=await invoke<RoadmapGame>('save_roadmap',{project:draft});setRows(rows.map(g=>g.id===saved.id?saved:g));setDraft(saved);setDirty(false);setNotice('Roadmap saved to SQLite')}catch(e){setError(String(e))}finally{setBusy(false)}}

 async function reveal(projectId:string,fileKind:string,path:string){try{await invoke('reveal_indexed_file',{projectId,kind:fileKind,path})}catch(e){setError(String(e))}}

 async function folder(projectId:string,provider:string|null=null){try{await invoke('open_project_folder',{projectId,provider})}catch(e){setError(String(e))}}

 async function reviewJson(){setBusy(true);setError('');try{const [latest,library]=native?await Promise.all([invoke<RoadmapGame[]>('roadmap'),invoke<Library>('library')]):[rows,lib];const snapshot=dirty&&draft?latest.map(g=>g.id===draft.id?draft:g):latest;const doc=roadmapReviewExport(snapshot,library,{unsavedGameId:dirty?draft?.id:undefined,preview:!native});setExportText(JSON.stringify({...doc,review_context:{feedback_review:seed.feedback_review,validation:seed.validation,waves:seed.waves,prioritization:seed.prioritization,audit_first:seed.audit_first,larger_game_combinations:seed.larger_game_combinations}},null,2));setExportMessage('')}catch(e){setError(String(e))}finally{setBusy(false)}}

 async function copyJson(){try{await navigator.clipboard.writeText(exportText);setExportMessage('JSON copied to clipboard')}catch{const area=document.getElementById('roadmap-json') as HTMLTextAreaElement|null;area?.focus();area?.select();setExportMessage('Clipboard unavailable. JSON selected — press Ctrl+C to copy.')}}

 async function saveJson(){try{if(native){const directory=await open({directory:true,multiple:false,title:'Export roadmap JSON'});if(typeof directory==='string'){const path=await invoke<string>('export_roadmap_json',{directory,document:JSON.parse(exportText)});setExportMessage('Exported: '+path)}}else{const url=URL.createObjectURL(new Blob([exportText+'\n'],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='gamecore-roadmap-review.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);setExportMessage('JSON download started')}}catch(e){setExportMessage(String(e))}}

 const sorted=[...rows].sort((a,b)=>a.priority-b.priority||a.title.localeCompare(b.title));

 const visible=sorted.filter(g=>(!wave||g.wave===Number(wave))&&(!filter||(filter==='ready'?unmet(g,rows).length===0:filter==='waiting'?unmet(g,rows).length>0:filter==='blocked'?g.status==='blocked'||progress(g).blocked>0:g.status===filter))&&[g.title,g.pitch,g.owner,...g.capability_ids.map(label)].join(' ').toLowerCase().includes(query.toLowerCase()));

 const unique=new Set(rows.flatMap(g=>g.capability_ids)),acceptedUnique=new Set(rows.flatMap(g=>g.capability_ids.filter(id=>accepted(g.target_progress[id]))));

 const current= draft?.target_progress[target];const selectedDonor=lib.projects.find(g=>g.id===donor);

 return <div className="roadmap-view">

  {error&&<div role="alert" className="message error">{error}</div>}{notice&&<div role="status" className="message success">{notice}</div>}

  {draft?<>

   <button className="back" onClick={()=>{if(leave()){setDraft(null);setDirty(false)}}}><ArrowLeft size={16}/> All roadmap games</button>

   <div className="page-heading"><div><div className="eyebrow">WAVE {draft.wave} · PRIORITY {draft.priority}</div><h1>{draft.title}</h1><p>{draft.pitch}</p></div><div className="inline"><button disabled={busy} onClick={reviewJson}>Export JSON</button><button className="primary" disabled={!native||busy||!dirty} onClick={save}><Save size={16}/> Save roadmap</button></div></div>

   <div className="roadmap-summary"><span>{progress(draft).accepted}/{progress(draft).total} accepted targets</span><span>{progress(draft).first}/{draft.first_slice_capabilities.length} first-slice targets</span><span>{unmet(draft,rows).length} first-slice gates · {unmet(draft,rows,'later').length} later gates</span><span>{draft.technical_risk} technical risk</span></div>

   <section className="panel"><h2>Creative direction</h2><p>{draft.creative_direction}</p><h3>Visual identity</h3><p>{draft.visual_direction}</p><small>{draft.creative_scope}</small><details><summary>Review changes{draft.previous_title?' · formerly '+draft.previous_title:''}</summary>{draft.review_changes?.map((s,i)=><p key={i}>{s}</p>)}{!!Object.keys(draft.archived_target_progress||{}).length&&<p>Retired target evidence is retained in the JSON export and SQLite history.</p>}</details></section>

   <div className="two-col"><section className="panel"><h2>Plan and ownership</h2><fieldset disabled={!native||busy}><div className="form-row"><label className="field"><span>Priority</span><input type="number" min="1" max="999" value={draft.priority} onChange={e=>change({priority:Number(e.target.value)})}/></label><label className="field"><span>Game status</span><select value={draft.status} onChange={e=>change({status:e.target.value})}>{['planned','active','blocked','paused','completed'].map(s=><option key={s}>{s}</option>)}</select></label></div><Field label="Owner" value={draft.owner} onChange={v=>change({owner:v})}/><Field label="Game notes / blockers" value={draft.notes} onChange={v=>change({notes:v})} multi/></fieldset><p>{draft.priority_reason}</p><small>{draft.preferred_runtime}</small><h3>Reusable outputs</h3><ul>{draft.reusable_outputs.map(s=><li key={s}>{s}</li>)}</ul></section>

   <section className="panel"><h2>Prerequisite milestones</h2><p className="muted">First-slice gates determine readiness. Later gates apply only when that milestone starts.</p>{Object.entries(draft.dependency_requirements).map(([id,targets])=>{const dep=rows.find(g=>g.id===id);return <div className="dependency" key={id}><button className="back" onClick={()=>dep&&select(dep)}>{dep?.title||id}<ArrowUpRight size={14}/></button><p className="muted">{draft.dependency_contracts?.[id]?.mode.replaceAll('_',' ')} · {draft.dependency_contracts?.[id]?.adapter}</p><small>{targets.filter(t=>accepted(dep?.target_progress[t])).length}/{targets.length} required targets accepted</small><fieldset disabled={!native||busy}>{dep?.capability_ids.map(cap=><div className="check-option" key={cap}><label><input type="checkbox" checked={targets.includes(cap)} onChange={e=>{const next={...draft.dependency_requirements};next[id]=e.target.checked?[...targets,cap]:targets.filter(x=>x!==cap);if(!next[id].length)delete next[id];change({dependency_requirements:next})}}/>{label(cap)}</label>{targets.includes(cap)&&<select aria-label={'Dependency stage '+id+' '+cap} value={draft.dependency_stages?.[id]?.[cap]||'first_slice'} onChange={e=>change({dependency_stages:{...draft.dependency_stages,[id]:{...draft.dependency_stages?.[id],[cap]:e.target.value}}})}><option value="first_slice">First slice</option><option value="later">Later milestone</option></select>}</div>)}</fieldset><button disabled={!native||busy} onClick={()=>{const next={...draft.dependency_requirements};delete next[id];change({dependency_requirements:next})}}>Remove prerequisite</button></div>})}<select aria-label="Add prerequisite game" disabled={!native||busy} value="" onChange={e=>{const g=rows.find(x=>x.id===e.target.value);if(g)change({dependency_requirements:{...draft.dependency_requirements,[g.id]:g.first_slice_capabilities}})}}><option value="">Add prerequisite game…</option>{sorted.filter(g=>g.id!==draft.id&&!draft.dependency_requirements[g.id]).map(g=><option key={g.id} value={g.id}>{g.title}</option>)}</select><h3>Feeds into</h3><div className="tag-list">{rows.filter(g=>g.dependency_requirements[draft.id]).map(g=><button key={g.id} onClick={()=>select(g)}>{g.title}</button>)}</div></section></div>

   <section className="panel"><h2>Capability targets</h2><p>Implementation, acceptance and second-consumer reuse are separate. Planned targets do not change the capability atlas.</p><div className="target-layout"><div className="target-list">{draft.capability_ids.map(id=><button key={id} className={id===target?'target-row active':'target-row'} onClick={()=>setTarget(id)}><strong>{label(id)}</strong><small>{draft.first_slice_capabilities.includes(id)?'FIRST SLICE':'LATER MILESTONE'} · {draft.target_progress[id].state.replaceAll('_',' ')}</small></button>)}</div>{current&&<div className="target-editor"><h2>{label(target)}</h2><p>{lib.taxonomy.find(t=>t.id===target)?.description}</p><fieldset disabled={!native||busy}><label className="field"><span>Target state</span><select value={current.state} onChange={e=>editTarget({state:e.target.value})}>{states.map(s=><option key={s} value={s}>{s.replaceAll('_',' ')}</option>)}</select></label><Field label="Target notes / blockers" value={current.notes} onChange={v=>editTarget({notes:v})} multi/><div className="form-row"><Field label="Revision / build" value={current.revision} onChange={v=>editTarget({revision:v})}/><Field label="Platform / hardware" value={current.platform} onChange={v=>editTarget({platform:v})}/></div><Field label="Test command or procedure" value={current.procedure} onChange={v=>editTarget({procedure:v})} multi/><Field label="Evidence path / result" value={current.evidence} onChange={v=>editTarget({evidence:v})} multi/><Field label="Second consumer and acceptance evidence" value={current.second_consumer} onChange={v=>editTarget({second_consumer:v})}/></fieldset><h3>Pinned code and asset references</h3>{current.reuse_links.length?current.reuse_links.map((l,i)=><div className="pinned-ref" key={l.project_id+l.path}><strong>{lib.projects.find(g=>g.id===l.project_id)?.name} · {l.kind}</strong><button className="file-link" disabled={!native} onClick={()=>reveal(l.project_id,l.kind,l.path)}>{l.path}<FolderOpen size={14}/></button><fieldset disabled={!native||busy}><Field label={'Reference version '+(i+1)} value={l.version} onChange={v=>editTarget({reuse_links:current.reuse_links.map((x,j)=>j===i?{...x,version:v}:x)})}/><Field label={'Reference notes '+(i+1)} value={l.notes} onChange={v=>editTarget({reuse_links:current.reuse_links.map((x,j)=>j===i?{...x,notes:v}:x)})}/><button onClick={()=>editTarget({reuse_links:current.reuse_links.filter((_,j)=>i!==j)})}>Unpin reference</button></fieldset></div>):<p className="muted">Search a donor below and pin a file to this target.</p>}</div>}</div><details><summary>Game acceptance scope</summary><p>{draft.acceptance}</p></details></section>

   <section className="panel"><h2>Reusable code and assets</h2><div className="donor-cards">{draft.donors.map(d=>{const g=lib.projects.find(g=>g.id===d.project_id);return <article key={d.project_id}><h3>{d.name}</h3><p>{d.source_entry_points}</p><strong>{d.reuse_mode?.replaceAll('_',' ')}</strong><p className="muted">{d.admission}</p>{!!d.code_links?.length&&<details><summary>Indexed code entry points ({d.code_links.length})</summary>{d.code_links.map(f=><div key={f.path}><button className="file-link" disabled={!native} onClick={()=>reveal(d.project_id,'source',f.path)}>{f.path}<FolderOpen size={14}/></button><small className="muted">Catalog source snapshot · {f.sha256?.slice(0,12)}</small></div>)}</details>}<p className="muted">{d.asset_overview}</p><div className="inline"><button onClick={()=>{setDonor(d.project_id);setFileQuery('');setKind('source')}}>Browse indexed files</button><button onClick={()=>{setDonor(d.project_id);setFileQuery('');setKind('asset')}}>Browse assets</button>{g&&<button onClick={()=>openGame(g)}>Open game record<ArrowUpRight size={14}/></button>}<button disabled={!native} onClick={()=>folder(d.project_id)}>Source folder</button></div></article>})}</div><h3>Find a reference for {label(target)}</h3><div className="filterbar"><select aria-label="Reference donor" value={donor} onChange={e=>setDonor(e.target.value)}>{lib.projects.map(g=><option key={g.id} value={g.id}>{g.name}</option>)}</select><select aria-label="Reference kind" value={kind} onChange={e=>setKind(e.target.value)}><option value="source">Source code</option><option value="asset">Assets</option></select><div className="search"><Search size={16}/><input aria-label="Search donor files" placeholder="Filename, folder, model, sound…" value={fileQuery} onChange={e=>setFileQuery(e.target.value)}/></div></div>{!native&&<p>Indexed file search and pinning are available in the desktop app.</p>}<div className="reference-files">{files.map(f=><div key={f.path}><button className="file-link" onClick={()=>reveal(donor,kind,f.path)}>{f.path}<FolderOpen size={14}/></button><small>{f.sha256?'Source hash recorded':'Version / rights need review'}</small><button disabled={!native||busy||!current||current.reuse_links.some(l=>l.project_id===donor&&l.path===f.path&&l.kind===kind)} onClick={()=>current&&editTarget({reuse_links:[...current.reuse_links,{project_id:donor,kind,path:f.path,version:f.sha256||'',notes:''}]})}>Pin to target</button></div>)}</div><p className="muted small">Up to 100 indexed results. Reveal opens the file location without executing it. Index hashes are snapshots; recheck current files before reuse.</p>{selectedDonor&&<div className="provider-grid">{selectedDonor.provider_links.map(p=><article className="panel" key={p.provider}><h3>{p.provider}</h3><p>{p.description}</p><small>{p.asset_id||'Exact provider asset not linked'} · {p.version||'Version unpinned'}</small><button disabled={!native} onClick={()=>folder(selectedDonor.id,p.provider)}>Open provider folder</button></article>)}</div>}</section>

  <div className="roadmap-savebar"><span>{dirty?'Unsaved roadmap changes':'Roadmap saved'} · {draft.title}</span><button className="primary" disabled={!native||busy||!dirty} onClick={save}><Save size={16}/> Save target changes</button></div>

  </>:<>

   <div className="page-heading"><div><div className="eyebrow">FROM SMALL GAMES TO SHARED FOUNDATIONS</div><h1>Game roadmap</h1><p>{rows.length} game tracks · Priorities, prerequisite milestones and evidence-backed progress.</p></div><div className="inline"><button disabled={busy||!rows.length} onClick={reviewJson}>Export JSON</button><button disabled={busy} onClick={load}>Refresh roadmap</button></div></div>

   <div className="stats"><div><strong>{rows.length}</strong><span>Planned game tracks</span></div><div><strong>{unique.size}</strong><span>Unique capability targets</span></div><div><strong>{acceptedUnique.size}</strong><span>With accepted roadmap evidence</span></div><div><strong>{rows.reduce((n,g)=>n+progress(g).accepted,0)}/{rows.reduce((n,g)=>n+g.capability_ids.length,0)}</strong><span>Accepted game–capability targets</span></div></div>

   <section className="panel"><p>All 143 original gaps plus 3 failure-case capabilities have at least two planned consumers across 50 games. Assignments do not imply implementation. Readiness uses first-slice gates; later dependencies are tracked separately.</p><details><summary>Incorporated review</summary>{seed.feedback_review.accepted.map(s=><p key={s}>{s}</p>)}<h3>Corrections to reviewer claims</h3>{seed.feedback_review.corrected.map(s=><p key={s}>{s}</p>)}</details><details><summary>Audit existing candidates before building</summary>{seed.audit_first.map(a=><p key={a.project_id}><strong>{lib.projects.find(g=>g.id===a.project_id)?.name}</strong> · {a.capabilities.join(', ')}</p>)}</details></section>

   <div className="filterbar"><div className="search"><Search size={18}/><input aria-label="Search roadmap" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Game, capability or owner…"/></div><select aria-label="Roadmap wave" value={wave} onChange={e=>setWave(e.target.value)}><option value="">All waves</option>{seed.waves.map(w=><option key={w.wave} value={w.wave}>{w.wave}. {w.title}</option>)}</select><select aria-label="Roadmap status" value={filter} onChange={e=>setFilter(e.target.value)}><option value="">All states</option><option value="ready">Prerequisites met</option><option value="waiting">Waiting on prerequisites</option>{['planned','active','blocked','paused','completed'].map(s=><option key={s}>{s}</option>)}</select></div><p className="muted">{visible.length} game tracks · Lower priority number comes first.</p>

   <div className="roadmap-grid">{visible.map(g=>{const p=progress(g),pending=unmet(g,rows).length;return <button className="roadmap-card panel" key={g.id} onClick={()=>select(g)}><div className="inline"><span className="priority-number">{String(g.priority).padStart(2,'0')}</span><span className="pill">Wave {g.wave} · {g.status}</span></div><h2>{g.title}</h2><p>{g.pitch}</p><progress max={p.total} value={p.accepted} aria-label={g.title+' accepted targets'}/><div className="roadmap-card-footer"><span>{p.accepted}/{p.total} accepted · {p.implemented} implemented</span><span>{pending?`${pending} prerequisites pending`:'Prerequisites met'}</span></div><small>{g.owner||'Unassigned'} · {g.technical_risk} risk</small></button>})}</div>{!visible.length&&<p>No roadmap games match these filters.</p>}

   <section className="panel"><h2>Larger-game combinations</h2><div className="donor-cards">{seed.larger_game_combinations.map(g=><article key={g.id}><h3>{g.name}</h3><p>{g.core}</p><p>{g.creative_direction}</p><p className="muted">{g.visual_direction}</p><div className="tag-list">{g.combine.map(id=><button key={id} onClick={()=>{const game=rows.find(g=>g.id===id);if(game)select(game)}}>{rows.find(g=>g.id===id)?.title}</button>)}</div><p className="muted">{g.first_combined_slice}</p></article>)}</div></section>

  </>}

 {exportText&&<div className="overlay"><section className="modal roadmap-export" role="dialog" aria-modal="true" aria-label="Export roadmap JSON"><div className="section-heading"><div><h2>Roadmap JSON for feedback</h2><p>All games, regardless of filters. Includes priorities, dependencies, progress, donor references and review questions.</p></div><button onClick={()=>setExportText('')}>Close export</button></div><p className="muted">Includes notes, evidence and local reference paths; no source-code or media file contents. Any unsaved game edits are explicitly marked in snapshot.unsaved_game_ids.</p><label className="field"><span>Review JSON · {(new Blob([exportText]).size/1024).toFixed(0)} KB</span><textarea id="roadmap-json" aria-label="Roadmap JSON" readOnly value={exportText} spellCheck={false}/></label>{exportMessage&&<p role="status">{exportMessage}</p>}<div className="modal-actions"><button onClick={()=>{const t=document.getElementById('roadmap-json') as HTMLTextAreaElement;t.focus();t.select()}}>Select all JSON</button><button onClick={saveJson}>Save JSON file</button><button className="primary" onClick={copyJson}>Copy JSON</button></div></section></div>}

 </div>

}

