import React,{useEffect,useMemo,useRef,useState} from 'react';
import {convertFileSrc} from '@tauri-apps/api/core';
import {AlertTriangle,ArrowUpRight,Check,Headphones,Image as ImageIcon,Inbox,Music2,RotateCcw,Search,X} from 'lucide-react';
import type {Game,Media,MusicDesignRecord} from './types';
import {ARCHETYPE_IDS,ARCHETYPES,applyArchetypeToRecord} from './music';
import {iterationLabel} from './iteration';
import {
 type ApprovalEntry,type ApprovalItem,type ApprovalKind,type ApprovalState,type Decision,type HistoryDecision,
 KIND_LABELS,STATE_LABELS,IMAGE_KINDS,buildApprovalItems,sortApprovals,isOpen,itemKey,mediaBlockers,
 decideMusicDirection,decideMusicTake,decideMedia,reopenMusicDirection,reopenMusicTake,reopenMedia,pipelineLabel,
} from './approvals';

type StateFilter='open'|'approved'|'rejected'|'all';
type Snapshot={music:MusicDesignRecord[];media:Media[];items:ApprovalItem[]};
export type ApprovalsProps={
 records:MusicDesignRecord[]; media:Media[]; games:Game[]; history:ApprovalEntry[];
 native:boolean; busy:boolean;
 /** Runs one unit of work with the app's busy/error handling. Throwing aborts the unit. */
 run:(fn:()=>Promise<void>)=>Promise<void>;
 persistMusic:(r:MusicDesignRecord)=>Promise<MusicDesignRecord>;
 persistMedia:(m:Media)=>Promise<Media>;
 recordDecision:(e:{kind:ApprovalKind;subject_id:string;item_id:string;item_label:string;decision:HistoryDecision;note:string})=>Promise<void>;
 openGame:(gameId:string,tab:string)=>void;
};

const KIND_ICON:Record<ApprovalKind,typeof Music2>={music_direction:Music2,music_take:Headphones,media:ImageIcon};
const toneFor=(s:ApprovalState)=>s==='approved'?'green':s==='rejected'?'':s==='changes_requested'?'warm':'accent';
function Pill({children,tone=''}:{children:React.ReactNode;tone?:string}){return <span className={'pill '+tone}>{children}</span>}
const when=(iso:string)=>{if(!iso)return '';const d=new Date(iso);return isNaN(d.getTime())?iso:d.toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'})};

export default function ApprovalsView(p:ApprovalsProps){
 const items=useMemo(()=>sortApprovals(buildApprovalItems(p.records,p.media,p.games,p.history)),[p.records,p.media,p.games,p.history]);
 const [kind,setKind]=useState<ApprovalKind|''>(''),[stateFilter,setStateFilter]=useState<StateFilter>('open');
 const [query,setQuery]=useState(''),[game,setGame]=useState('');
 const [selectedKey,setSelectedKey]=useState(''),[checked,setChecked]=useState<Set<string>>(new Set());
 const [confirm,setConfirm]=useState<ApprovalItem[]|null>(null);
 const [undo,setUndo]=useState<{label:string;snap:Snapshot}|null>(null);
 const listRef=useRef<HTMLDivElement>(null);

 const visible=items.filter(i=>(!kind||i.kind===kind)&&(!game||i.subjectId===game)
  &&(stateFilter==='all'||(stateFilter==='open'?isOpen(i.state):i.state===stateFilter))
  &&(!query||`${i.subjectName} ${i.title} ${i.summary}`.toLowerCase().includes(query.toLowerCase())));
 const openCount=(k?:ApprovalKind)=>items.filter(i=>isOpen(i.state)&&(!k||i.kind===k)).length;
 const selected=visible.find(i=>i.key===selectedKey)||visible[0];
 const subjects=useMemo(()=>[...new Map(items.map(i=>[i.subjectId,i.subjectName])).entries()].sort((a,b)=>a[1].localeCompare(b[1])),[items]);
 const bulk=visible.filter(i=>checked.has(i.key)&&isOpen(i.state));
 const bulkReady=bulk.filter(i=>!i.blockers.length);

 useEffect(()=>{setChecked(new Set())},[kind,stateFilter,game]);
 useEffect(()=>{if(!undo)return;const id=setTimeout(()=>setUndo(null),15000);return()=>clearTimeout(id)},[undo]);
 // j / k (or arrow keys) move through the queue when typing is not in progress.
 useEffect(()=>{
  const onKey=(e:KeyboardEvent)=>{
   if(e.target instanceof Element&&e.target.closest('input,textarea,select,[contenteditable="true"]'))return;
   if(confirm||e.ctrlKey||e.metaKey||e.altKey)return;
   const step=e.key==='j'||e.key==='ArrowDown'?1:e.key==='k'||e.key==='ArrowUp'?-1:0;
   if(!step||!visible.length)return;
   e.preventDefault();
   const idx=Math.max(0,visible.findIndex(i=>i.key===selected?.key));
   const next=visible[Math.min(visible.length-1,Math.max(0,idx+step))];
   setSelectedKey(next.key);
   listRef.current?.querySelector(`[data-key="${CSS.escape(next.key)}"]`)?.scrollIntoView({block:'nearest'});
  };
  window.addEventListener('keydown',onKey);return()=>window.removeEventListener('keydown',onKey);
 },[visible,selected?.key,confirm]);

 const recordOf=(gameId:string)=>{const r=p.records.find(x=>x.game_id===gameId);if(!r)throw new Error(`No music record for ${gameId}`);return r};
 const mediaOf=(id:string)=>{const m=p.media.find(x=>x.id===id);if(!m)throw new Error('Media item no longer exists');return m};

 /** Applies one decision to the source record, then appends history. Returns the pre-decision snapshot. */
 async function apply(item:ApprovalItem,d:Decision,note:string,draft?:{music?:MusicDesignRecord;media?:Media},cache?:Map<string,MusicDesignRecord>):Promise<Snapshot>{
  const snap:Snapshot={music:[],media:[],items:[item]};
  if(item.kind==='media'){
   const before=mediaOf(item.itemId);snap.media.push(before);
   await p.persistMedia(decideMedia(draft?.media||before,d,note));
  }else{
   // `cache` chains several decisions on one game's record within a bulk run.
   const before=cache?.get(item.subjectId)||recordOf(item.subjectId);snap.music.push(before);
   const base=draft?.music||before;
   const next=item.kind==='music_direction'?decideMusicDirection(base,d):decideMusicTake(base,item.itemId,d);
   if(next!==before){const saved=await p.persistMusic(next);cache?.set(item.subjectId,saved)}
  }
  await p.recordDecision({kind:item.kind,subject_id:item.subjectId,item_id:item.itemId,item_label:`${item.subjectName} — ${item.title}`,decision:d,note:note.trim()});
  return snap;
 }

 function nextOpenAfter(key:string){
  const idx=visible.findIndex(i=>i.key===key);
  return visible.slice(idx+1).find(i=>isOpen(i.state))||visible.slice(0,idx).find(i=>isOpen(i.state));
 }

 async function decide(item:ApprovalItem,d:Decision,note:string,draft?:{music?:MusicDesignRecord;media?:Media}){
  const next=nextOpenAfter(item.key);
  await p.run(async()=>{
   const snap=await apply(item,d,note,draft);
   setUndo({label:`${STATE_LABELS[d==='approved'?'approved':d==='rejected'?'rejected':'changes_requested']}: ${item.subjectName} — ${item.title}`,snap});
   if(stateFilter==='open'&&next)setSelectedKey(next.key);
  });
 }

 async function approveBulk(list:ApprovalItem[]){
  setConfirm(null);
  await p.run(async()=>{
   const snap:Snapshot={music:[],media:[],items:[]},cache=new Map<string,MusicDesignRecord>();
   // Music items for the same game must chain onto the previous save, so apply sequentially.
   for(const item of list){
    const s=await apply(item,'approved','',undefined,cache);
    for(const r of s.music)if(!snap.music.some(x=>x.game_id===r.game_id))snap.music.push(r);
    snap.media.push(...s.media);snap.items.push(item);
   }
   setChecked(new Set());
   setUndo({label:`Approved ${list.length} item${list.length===1?'':'s'}`,snap});
  });
 }

 async function restore(snap:Snapshot){
  setUndo(null);
  await p.run(async()=>{
   for(const r of snap.music)await p.persistMusic(r);
   for(const m of snap.media)await p.persistMedia(m);
   for(const i of snap.items)await p.recordDecision({kind:i.kind,subject_id:i.subjectId,item_id:i.itemId,item_label:`${i.subjectName} — ${i.title}`,decision:'reopened',note:'Undone'});
  });
 }

 async function reopen(item:ApprovalItem){
  await p.run(async()=>{
   if(item.kind==='media')await p.persistMedia(reopenMedia(mediaOf(item.itemId)));
   else{const r=recordOf(item.subjectId);await p.persistMusic(item.kind==='music_direction'?reopenMusicDirection(r):reopenMusicTake(r,item.itemId))}
   await p.recordDecision({kind:item.kind,subject_id:item.subjectId,item_id:item.itemId,item_label:`${item.subjectName} — ${item.title}`,decision:'reopened',note:''});
  });
 }

 return <div className="approvals-view">
  <div className="page-heading compact">
   <div><h1>Approvals</h1><p>Decisions waiting on a person: music direction, generated music takes and media for publication.</p></div>
   <div className="inline">
    {bulk.length>0&&<button className="primary" disabled={!p.native||p.busy||!bulkReady.length} onClick={()=>setConfirm(bulkReady)} title={bulkReady.length<bulk.length?`${bulk.length-bulkReady.length} selected item(s) have unresolved requirements and will be skipped`:''}><Check size={16}/> Approve selected ({bulkReady.length})</button>}
   </div>
  </div>

  <div className="chip-row" role="tablist" aria-label="Approval type">
   {([['','All'],['music_direction',KIND_LABELS.music_direction],['music_take',KIND_LABELS.music_take],['media',KIND_LABELS.media]] as [ApprovalKind|'',string][]).map(([k,l])=>
    <button key={k||'all'} role="tab" aria-selected={kind===k} className={'chip'+(kind===k?' selected':'')} onClick={()=>setKind(k)}>{l}<span>{openCount(k||undefined)}</span></button>)}
  </div>
  <div className="filterbar approvals-filters">
   <div className="search"><Search size={17}/><input aria-label="Search approvals" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search game, track or caption…"/></div>
   <select aria-label="Approval state" value={stateFilter} onChange={e=>setStateFilter(e.target.value as StateFilter)}>
    <option value="open">Needs decision</option><option value="approved">Approved</option><option value="rejected">Rejected</option><option value="all">All states</option>
   </select>
   <select aria-label="Approval game" value={game} onChange={e=>setGame(e.target.value)}>
    <option value="">All games & tracks</option>{subjects.map(([id,n])=><option key={id} value={id}>{n}</option>)}
   </select>
  </div>
  {!p.native&&<p className="muted small">Browser preview is read-only. Decisions are saved in the desktop app.</p>}

  {undo&&<div role="status" className="message success undo-bar"><Check size={16}/>{undo.label}<button className="link-button" disabled={p.busy} onClick={()=>void restore(undo.snap)}><RotateCcw size={14}/> Undo</button><button aria-label="Dismiss" onClick={()=>setUndo(null)}><X size={16}/></button></div>}

  {!visible.length?<div className="empty"><Inbox size={38}/><h2>{stateFilter==='open'?'Nothing waiting on you':'No matching items'}</h2><p>{stateFilter==='open'?'New music recommendations, generated takes and imported media appear here.':'Try another filter.'}</p></div>:
  <div className="approvals-layout">
   <div className="approval-list" ref={listRef} role="listbox" aria-label="Approval queue">
    <div className="approval-list-head">
     <label className="inline"><input type="checkbox" aria-label="Select all open items" checked={visible.some(i=>isOpen(i.state))&&visible.filter(i=>isOpen(i.state)).every(i=>checked.has(i.key))} onChange={e=>setChecked(e.target.checked?new Set(visible.filter(i=>isOpen(i.state)).map(i=>i.key)):new Set())} disabled={!visible.some(i=>isOpen(i.state))}/><small>{visible.length} item{visible.length===1?'':'s'}</small></label>
     <small className="muted">j / k to move</small>
    </div>
    {visible.map(i=>{const I=KIND_ICON[i.kind];return <div key={i.key} data-key={i.key} role="option" aria-selected={selected?.key===i.key} className={'approval-row'+(selected?.key===i.key?' selected':'')} onClick={()=>setSelectedKey(i.key)}>
     {isOpen(i.state)?<input type="checkbox" aria-label={`Select ${i.subjectName} ${i.title}`} checked={checked.has(i.key)} onClick={e=>e.stopPropagation()} onChange={e=>{const n=new Set(checked);e.target.checked?n.add(i.key):n.delete(i.key);setChecked(n)}}/>:<span className="check-spacer"/>}
     <I size={16} className="approval-kind-icon"/>
     <div className="approval-row-body"><strong>{i.subjectName}</strong><span>{KIND_LABELS[i.kind]} · {i.title}</span></div>
     <div className="approval-row-meta">{i.blockers.length>0&&isOpen(i.state)&&<AlertTriangle size={14} aria-label={`${i.blockers.length} requirement(s) missing`}/>}{i.state!=='pending'&&<Pill tone={toneFor(i.state)}>{STATE_LABELS[i.state]}</Pill>}</div>
    </div>})}
   </div>
   {selected&&<ApprovalDetail key={selected.key} item={selected} {...p} history={p.history.filter(h=>itemKey(h.kind,h.item_id)===selected.key).sort((a,b)=>b.decided_at.localeCompare(a.decided_at))} onDecide={decide} onReopen={reopen}/>}
  </div>}

  {confirm&&<div className="overlay"><section className="modal compact" role="dialog" aria-modal="true" aria-label="Confirm approvals">
   <h2>Approve {confirm.length} item{confirm.length===1?'':'s'}?</h2>
   <p className="muted">Each item is saved to its own record and logged in the approval history. You can undo right after.</p>
   <ul className="confirm-list">{confirm.map(i=><li key={i.key}><strong>{i.subjectName}</strong> — {KIND_LABELS[i.kind]}: {i.title}</li>)}</ul>
   {bulk.length>bulkReady.length&&<p className="muted small">{bulk.length-bulkReady.length} selected item(s) with missing requirements are skipped.</p>}
   <div className="modal-actions"><button onClick={()=>setConfirm(null)}>Cancel</button><button className="primary" autoFocus onClick={()=>void approveBulk(confirm)}><Check size={16}/> Approve {confirm.length}</button></div>
  </section></div>}
 </div>;
}

function ApprovalDetail({item,records,media,games,history,native,busy,run,persistMusic,persistMedia,openGame,onDecide,onReopen}:ApprovalsProps&{item:ApprovalItem;onDecide:(i:ApprovalItem,d:Decision,note:string,draft?:{music?:MusicDesignRecord;media?:Media})=>Promise<void>;onReopen:(i:ApprovalItem)=>Promise<void>}){
 const record=records.find(r=>r.game_id===item.subjectId);
 const mediaItem=item.kind==='media'?media.find(m=>m.id===item.itemId):undefined;
 const [note,setNote]=useState('');
 const [arch,setArch]=useState(record?.archetype||record?.recommended_archetype||'');
 const [setting,setSetting]=useState(record?.setting||record?.recommended_setting||'');
 const [mDraft,setMDraft]=useState<Media|undefined>(mediaItem&&structuredClone(mediaItem));
 const isCatalog=games.some(g=>g.id===item.subjectId);
 const open=isOpen(item.state);

 const dirChanged=item.kind==='music_direction'&&record&&(arch!==(record.archetype||record.recommended_archetype||'')||setting!==(record.setting||record.recommended_setting||''));
 const mediaChanged=Boolean(mediaItem&&mDraft&&(['title','caption','alt_text','rights'] as const).some(k=>mDraft[k]!==mediaItem[k]));
 const blockers=item.kind==='media'&&mDraft?mediaBlockers(mDraft):item.kind==='music_direction'&&!arch?['Choose an archetype']:item.blockers;
 const draft=item.kind==='music_direction'&&record&&dirChanged&&arch?{music:applyArchetypeToRecord(record,arch,setting,false)}:item.kind==='media'&&mDraft?{media:mDraft}:undefined;

 const track=item.kind==='music_take'?record?.tracks.find(t=>t.track_id===item.itemId):undefined;
 const field=(k:'title'|'caption'|'alt_text'|'rights',label:string,multi=false)=>mDraft&&<label className="field"><span>{label}</span>{multi?<textarea rows={3} value={mDraft[k]} onChange={e=>setMDraft({...mDraft,[k]:e.target.value})}/>:<input value={mDraft[k]} onChange={e=>setMDraft({...mDraft,[k]:e.target.value})}/>}</label>;

 return <section className="panel approval-detail" aria-label="Approval detail">
  <div className="eyebrow">{KIND_LABELS[item.kind].toUpperCase()} · {item.scope==='roadmap'?'ROADMAP TRACK':'CATALOG GAME'}</div>
  <div className="section-heading"><div><h2>{item.subjectName}</h2><p className="muted">{item.title}</p></div><div className="inline"><Pill tone={toneFor(item.state)}>{STATE_LABELS[item.state]}</Pill>{isCatalog&&<button onClick={()=>openGame(item.subjectId,item.kind==='media'?'Media':'Music')}>Open game <ArrowUpRight size={14}/></button>}</div></div>
  {item.lastDecision?.decision==='changes_requested'&&open&&<div className="callout warm"><strong>Changes requested {when(item.lastDecision.decided_at)}</strong><p>{item.lastDecision.note}</p></div>}

  {item.kind==='music_direction'&&record&&<>
   {record.recommendation_reason&&<p>{record.recommendation_reason}</p>}
   <div className="tag-list"><Pill>Production: {pipelineLabel(record)}</Pill>{record.recommended_archetype&&<Pill>Recommended: {record.recommended_archetype}</Pill>}<Pill>{record.tracks.length} track slot{record.tracks.length===1?'':'s'}</Pill></div>
   <div className="form-row">
    <label className="field"><span>Archetype</span><select aria-label="Archetype" value={arch} onChange={e=>setArch(e.target.value)}><option value="">Choose…</option>{ARCHETYPE_IDS.map(a=><option key={a} value={a}>{a} · {ARCHETYPES[a].bpm} BPM · {ARCHETYPES[a].genre}</option>)}</select></label>
    <label className="field"><span>Atmosphere / setting</span><input aria-label="Atmosphere / setting" value={setting} onChange={e=>setSetting(e.target.value)} placeholder={record.recommended_setting}/></label>
   </div>
   {dirChanged&&<div className="inline"><small className="muted">Changing the archetype regenerates the prompt templates; recorded Suno URLs are kept.</small><button disabled={!native||busy||!arch} onClick={()=>void run(async()=>{await persistMusic(applyArchetypeToRecord(record,arch,setting,false))})}>Save without deciding</button></div>}
  </>}

  {item.kind==='music_take'&&track&&<>
   <p className="muted">{item.summary}</p>
   <details><summary>Style prompt</summary><p className="small prewrap">{track.style_prompt}</p></details>
   {(track.suno.candidates||[]).length?<div className="take-list">{track.suno.candidates!.map(c=><div className="take-row" key={c.clip_id}>
    <strong>Take {c.take}</strong>
    <div className="tag-list">{c.used_in_game&&<Pill tone="green">Used in game</Pill>}{c.take===track.suno.recommended_take&&<Pill>Recommended</Pill>}<Pill>Score {c.quality_score}</Pill><Pill tone={c.listen_rating?'green':'warm'}>{c.listen_rating?`Rated ${c.listen_rating}/5`:'Unrated'}</Pill>{c.liked&&<Pill tone="warm">Liked</Pill>}</div>
    <small className="muted">{c.duration_s}s · {c.bpm_detected} BPM · {c.key_detected}{c.listen_notes?` · “${c.listen_notes}”`:''}</small>
    {c.url&&<a className="button" href={c.url} target="_blank" rel="noreferrer">Listen <ArrowUpRight size={13}/></a>}
   </div>)}</div>:track.suno.url?<a className="button" href={track.suno.url} target="_blank" rel="noreferrer">Listen in Suno <ArrowUpRight size={13}/></a>:null}
   {isCatalog&&<p className="muted small">Rate takes and choose the in-game take on the game's Music tab.</p>}
  </>}

  {item.kind==='media'&&mediaItem&&mDraft&&<div className="approval-media">
   <div className="media-preview">{!native?<div className="video-placeholder"><ImageIcon size={30}/></div>:IMAGE_KINDS.includes(mediaItem.kind)?<img src={convertFileSrc(mediaItem.stored_path)} alt={mDraft.alt_text||mDraft.title}/>:['music','sfx'].includes(mediaItem.kind)?<audio controls src={convertFileSrc(mediaItem.stored_path)}/>:<video controls src={convertFileSrc(mediaItem.stored_path)}/>}
    {mediaItem.kind==='screenshot'&&<small>{iterationLabel(mediaItem)}</small>}</div>
   <div>{field('title','Title')}{field('caption','Caption',true)}{IMAGE_KINDS.includes(mediaItem.kind)&&field('alt_text','Alt text')}{field('rights','Rights / license clearance')}
    {mediaChanged&&<button disabled={!native||busy} onClick={()=>void run(async()=>{await persistMedia(mDraft)})}>Save fields without deciding</button>}</div>
  </div>}

  {open?<div className="decision-box">
   {blockers.length>0&&<div className="callout"><strong>Before approving</strong><ul>{blockers.map(b=><li key={b}>{b}</li>)}</ul></div>}
   {item.hints.map(h=><p key={h} className="muted small"><AlertTriangle size={12}/> {h}</p>)}
   <label className="field"><span>Note (required to request changes)</span><textarea rows={2} value={note} onChange={e=>setNote(e.target.value)} placeholder="What should change, or why this was approved / rejected"/></label>
   <div className="inline decision-actions">
    <button className="primary" disabled={!native||busy||blockers.length>0} onClick={()=>void onDecide(item,'approved',note,draft)}><Check size={16}/> Approve</button>
    <button disabled={!native||busy||!note.trim()} title={note.trim()?'':'Write a note first'} onClick={()=>void onDecide(item,'changes_requested',note,draft)}>Request changes</button>
    <button className="danger" disabled={!native||busy} onClick={()=>void onDecide(item,'rejected',note,draft)}><X size={16}/> Reject</button>
   </div>
   <small className="muted">{item.kind==='music_direction'?'Reject clears the recommendation so a new one can be made.':item.kind==='media'?'Reject retires the item; the original file is kept.':'Reject marks this track rejected; its takes stay recorded.'}</small>
  </div>:<div className="decision-box"><button disabled={!native||busy} onClick={()=>void onReopen(item)}><RotateCcw size={15}/> Reopen for review</button></div>}

  {history.length>0&&<div className="approval-history"><h3>History</h3>{history.map(h=><div key={h.id}><Pill tone={h.decision==='approved'?'green':h.decision==='rejected'?'':'warm'}>{h.decision.replace('_',' ')}</Pill><small>{when(h.decided_at)}</small>{h.note&&<p>{h.note}</p>}</div>)}</div>}
 </section>;
}
