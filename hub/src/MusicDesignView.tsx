import React,{useState,useEffect} from 'react';
import {invoke,isTauri} from '@tauri-apps/api/core';
import {Check,Copy,FolderOpen,ArrowUpRight,Plus,Save,Sparkles,X,Star} from 'lucide-react';
import type {Game,MusicDesignRecord,MusicTrack,SunoCandidate,ProviderCatalogs} from './types';
import {ARCHETYPE_IDS,ARCHETYPES,SUNO_STANDARD_OPTIONS,SUNO_BETA_OPTIONS,applyArchetypeToRecord,generateTracksForArchetype,pipelineStage} from './music';
import seedRecords from '../data/music-design/index.json';
import {LibraryMatches} from './MusicLibraryView';
import {libraryTracksForArchetype} from './musicLibrary';

const native = isTauri();
const GAME_STATUSES = ['unassigned','recommended','excluded','planned','in_progress','approved'];
const TRACK_STATUSES = ['prompt_ready','generated','stems_split','approved','rejected'];
const IN_GAME_STATUSES = ['not_integrated','stems_downloaded','sonic_alchemist_sliced','wired_in_engine'];
const VOCALS = ['none','wordless','sung'];
const STANDARD_FAMILIES = ARCHETYPE_IDS.filter(a=>!('parent_archetype' in ARCHETYPES[a]));
const BIOME_STYLES = ARCHETYPE_IDS.filter(a=>'parent_archetype' in ARCHETYPES[a]);
const human = (s:string)=>s.replaceAll('_',' ');

type Section = 'overview'|'tracks'|'matches';
type TrackPane = 'prompt'|'stems'|'takes'|'files';

function Pill({children,tone=''}:{children:React.ReactNode;tone?:string}){return <span className={'pill '+tone}>{children}</span>}
const keepList = (inst:MusicTrack['instruments'])=>[...new Set(inst.filter(x=>x.keep).map(x=>x.stem))].sort();

export function GameMusicPanel({
 game, record, providerCatalogs, onSaveRecord, onUpdateGameLink, onOpenFolder, onOpenLibrary, busy
}:{
 game:Game;
 record:MusicDesignRecord;
 providerCatalogs:ProviderCatalogs;
 onSaveRecord:(rec:MusicDesignRecord)=>Promise<void>;
 onUpdateGameLink:(provider:string, assetId:string)=>Promise<void>;
 onOpenFolder:(provider:string|null)=>void;
 onOpenLibrary?:()=>void;
 busy:boolean;
}){
 const [draft,setDraft] = useState<MusicDesignRecord>(()=>structuredClone(record));
 const [dirty,setDirty] = useState(false);
 const [copied,setCopied] = useState('');
 const [section,setSection] = useState<Section>('overview');
 const [trackIdx,setTrackIdx] = useState(0);
 const [pane,setPane] = useState<TrackPane>('takes');

 useEffect(()=>{setDraft(structuredClone(record));setDirty(false)},[record]);
 useEffect(()=>{setSection('overview');selectTrack(0,record.tracks)},[record.game_id]);
 function selectTrack(i:number,tracks=draft.tracks){setTrackIdx(i);setPane(tracks[i]?.suno.candidates?.length?'takes':'prompt')}

 function openFolderForPath(path?:string){
  if(!path || !native) return;
  void invoke('open_folder_for_path', { path });
 }
 function update(patch:Partial<MusicDesignRecord>){setDraft(prev=>({...prev,...patch}));setDirty(true)}
 function updateTrack(idx:number, patch:Partial<MusicTrack>){
  setDraft(prev=>({...prev,tracks:prev.tracks.map((t,i)=>i===idx?{...t,...patch}:t)}));
  setDirty(true);
 }
 async function copyText(key:string, text:string){
  try{await navigator.clipboard.writeText(text);setCopied(key);setTimeout(()=>setCopied(''),2000)}catch{setCopied('')}
 }
 function addTrack(arch:string, label?:string){
  const letter = String.fromCharCode(65 + draft.tracks.length);
  const extra = generateTracksForArchetype(draft.game_id, draft.name, arch, activeSetting, [], 1)[0];
  if(!extra) return;
  update({tracks:[...draft.tracks,{...extra, track_id:`${draft.game_id}-${letter}`, title:`${draft.name} - ${label||'Track '+letter}`}]});
  setTrackIdx(draft.tracks.length);setSection('tracks');setPane('prompt');
 }

 const activeArch = draft.archetype || draft.recommended_archetype || 'cozy';
 const activeSetting = draft.setting || draft.recommended_setting || '';
 const links = [
  {provider:'ArcoreSonicAlchemist',label:'Sonic Alchemist',field:'sonic_alchemist_project' as const,list:providerCatalogs['ArcoreSonicAlchemist']?.projects||[],own:{value:game.id,label:`Create / link '${game.id}'`}},
  {provider:'ArcoreSoundCore',label:'SoundCore',field:'soundcore_project' as const,list:providerCatalogs['ArcoreSoundCore']?.projects||[],own:{value:game.id,label:`Project: ${game.id}`}},
  {provider:'ArcoreModelForge',label:'ModelForge',field:'modelforge_project' as const,list:providerCatalogs['ArcoreModelForge']?.projects||[],own:{value:game.name,label:`Project: ${game.name}`}},
 ];
 const activeTrackIdx = Math.max(0, draft.tracks.findIndex(t=>t.suno.candidates?.some(c=>c.used_in_game)));
 const activeTrack = draft.tracks[activeTrackIdx];
 const activeSuno = activeTrack?.suno;
 const activeCand = activeSuno?.candidates?.find(c=>c.used_in_game) || activeSuno?.candidates?.find(c=>c.clip_id===activeSuno.clip_id);
 const activeStage = pipelineStage(draft);
 const dbFilePath = `hub/data/music-design/${draft.game_id}.json`;
 const matches = (draft.related_suno_tracks || []).filter(r=>!r.dismissed);
 const takesTotal = draft.tracks.reduce((n,t)=>n+(t.suno.candidates?.length||0),0);
 const tIdx = Math.min(trackIdx, Math.max(0,draft.tracks.length-1));
 const track = draft.tracks[tIdx];

 const sections:[Section,string,number|null][] = [['overview','Overview',null],['tracks','Tracks',draft.tracks.length],...(matches.length?[['matches','Suno matches',matches.length] as [Section,string,number]]:[])];

 return <div className="music-tab">
  <div className="music-bar">
   <div className="music-bar-tabs" role="tablist" aria-label="Music sections">
    {sections.map(([id,lbl,n])=><button key={id} role="tab" aria-selected={section===id} className={section===id?'selected':''} onClick={()=>setSection(id)}>{lbl}{n!==null&&<span>{n}</span>}</button>)}
   </div>
   <div className="inline music-bar-status">
    <Pill tone={activeStage==='wired_in_engine'||draft.status==='approved'?'green':'warm'}>{human(activeStage)}</Pill>
    <Pill tone={draft.status==='approved'||draft.status==='planned'?'green':'warm'}>{human(draft.status)}</Pill>
    {dirty&&<span className="unsaved">Unsaved changes</span>}
    <button className="primary" disabled={!native||busy||!dirty} onClick={()=>onSaveRecord(draft)}><Save size={15}/> Save music design</button>
   </div>
  </div>

  {section==='overview'&&<>
   <div className="music-overview">
    <section className="panel">
     <div className="eyebrow">MUSIC DIRECTION</div>
     <div className="section-heading tight">
      <div>
       <h2>{draft.recommended_archetype || 'Unassigned'}{draft.recommended_setting ? ` · ${draft.recommended_setting}` : ''}</h2>
       <p className="muted">{draft.recommendation_reason || 'Select an archetype and setting to generate 2–3 adaptive tracks with locked instrumentation.'}</p>
      </div>
      {draft.recommended_archetype && draft.status !== 'excluded' && !['approved','in_progress'].includes(draft.status) && (
       <button className="primary" disabled={!native||busy} onClick={()=>{
        const next = applyArchetypeToRecord(draft, draft.recommended_archetype!, draft.recommended_setting || draft.setting, true);
        setDraft(next);void onSaveRecord(next);
       }}><Check size={16}/> Approve recommendation</button>
      )}
     </div>
     <div className="form-row">
      <label className="field"><span>Music status</span>
       <select aria-label="Music status" value={draft.status} onChange={e=>update({status:e.target.value})}>
        {GAME_STATUSES.map(s=><option key={s} value={s}>{human(s)}</option>)}
       </select>
      </label>
      <label className="field"><span>Selected archetype</span>
       <select aria-label="Selected archetype" value={draft.archetype||''} onChange={e=>{
        const arch = e.target.value || null;
        if(arch){setDraft(prev=>applyArchetypeToRecord(prev, arch, prev.setting || prev.recommended_setting, false));setDirty(true)}
        else update({archetype:null});
       }}>
        <option value="">(Use recommendation: {draft.recommended_archetype||'none'})</option>
        <optgroup label="Standard families">{STANDARD_FAMILIES.map(a=><option key={a} value={a}>{a} — {ARCHETYPES[a].genre} ({ARCHETYPES[a].bpm} BPM)</option>)}</optgroup>
        <optgroup label="Biome / theme styles">{BIOME_STYLES.map(a=><option key={a} value={a}>{a} [{(ARCHETYPES[a] as {parent_archetype?:string}).parent_archetype}] — {ARCHETYPES[a].genre} ({ARCHETYPES[a].bpm} BPM)</option>)}</optgroup>
       </select>
      </label>
      <label className="field"><span>Biome / atmosphere setting</span>
       <input aria-label="Biome / atmosphere setting" value={draft.setting} placeholder={draft.recommended_setting||'e.g. neon grid, sunken crypt, breezy harbor'} onChange={e=>update({setting:e.target.value})}/>
      </label>
      <label className="field"><span>Exclusion note (if already scored)</span>
       <input aria-label="Exclusion note" value={draft.exclusion_reason} placeholder="Leave blank unless game already has music" onChange={e=>update({exclusion_reason:e.target.value})}/>
      </label>
     </div>
    </section>

    <section className="panel">
     <div className="eyebrow">IN-GAME MUSIC</div>
     {activeTrack ? <>
      <div className="section-heading tight">
       <div>
        <h2>{activeTrack.title}</h2>
        <div className="tag-list">
         {activeCand && <Pill tone="green">Take {activeCand.take}{activeCand.used_in_game ? ' · used in game' : ''}</Pill>}
         {activeSuno?.analysis && <><Pill>{activeSuno.analysis.bpm_detected} BPM</Pill><Pill>{activeSuno.analysis.key_detected}</Pill><Pill>{activeSuno.analysis.bars_detected} bars</Pill></>}
         {activeSuno?.stem_group_id && <Pill>Stems: {activeSuno.stem_group_id}</Pill>}
        </div>
       </div>
       <div className="inline">
        {activeSuno?.url && <a className="button" href={activeSuno.url} target="_blank" rel="noreferrer">Suno <ArrowUpRight size={14}/></a>}
        <button onClick={()=>{selectTrack(activeTrackIdx);setSection('tracks')}}>View takes</button>
       </div>
      </div>
      <div className="form-row three">
       <label className="field"><span>Integration status</span>
        <select aria-label="In-game integration status" value={activeSuno?.in_game_status || 'not_integrated'} onChange={e=>updateTrack(activeTrackIdx,{suno:{...activeTrack.suno, in_game_status:e.target.value}})}>
         {IN_GAME_STATUSES.map(s=><option key={s} value={s}>{human(s)}</option>)}
        </select>
       </label>
       <label className="field"><span>Engine audio path</span>
        <input aria-label="Engine audio path" value={activeSuno?.engine_asset_path || ''} placeholder="/Game/Audio/Music" onChange={e=>updateTrack(activeTrackIdx,{suno:{...activeTrack.suno, engine_asset_path:e.target.value}})}/>
       </label>
       <label className="field"><span>Loop length (s)</span>
        <input aria-label="In-game loop length" type="number" step="0.01" value={activeSuno?.in_game_loop_s ?? ''} placeholder="e.g. 54.86" onChange={e=>updateTrack(activeTrackIdx,{suno:{...activeTrack.suno, in_game_loop_s:e.target.value?Number(e.target.value):undefined}})}/>
       </label>
      </div>
      <p className="small muted kv">
       {(()=>{const stems=activeSuno?.in_game_stems?.length?activeSuno.in_game_stems:activeTrack.stems_requested;return stems.length?<><strong>Stems:</strong> {stems.join(', ')}<br/></>:null})()}
       <strong>DB file:</strong> <code>{dbFilePath}</code> <button className="link-button" onClick={()=>void copyText('db-file', dbFilePath)}>{copied==='db-file'?'Copied':'Copy'}</button>
      </p>
     </> : <p className="muted">No tracks yet. Open Tracks to generate prompt templates.</p>}
    </section>
   </div>

   <LibraryMatches archetype={activeArch} tracks={libraryTracksForArchetype(activeArch)} native={native} onBrowse={onOpenLibrary}/>

   <section className="panel music-links">
    <div className="eyebrow">ECOSYSTEM LINKS</div>
    <div className="music-links-grid">
     {links.map(l=>{
      const value = game.provider_links.find(p=>p.provider===l.provider)?.asset_id || draft[l.field] || '';
      return <div className="music-link" key={l.provider}>
       <label className="field"><span>{l.label}</span>
        <select aria-label={`${l.label} project`} value={value} onChange={e=>{const val=e.target.value;update({[l.field]:val} as Partial<MusicDesignRecord>);void onUpdateGameLink(l.provider,val)}}>
         <option value="">Not linked</option>
         {l.list.map(p=><option key={p.id} value={p.id}>{p.label}</option>)}
         <option value={l.own.value}>{l.own.label}</option>
        </select>
       </label>
       <button className="icon-button" aria-label={`Open ${l.label}`} title={`Open ${l.label}`} disabled={!native} onClick={()=>onOpenFolder(l.provider)}><FolderOpen size={15}/></button>
      </div>;
     })}
    </div>
   </section>
  </>}

  {section==='tracks'&&<div className="music-tracks">
   <aside className="track-picker" aria-label="Tracks">
    {draft.tracks.map((t,i)=>{
     const n=t.suno.candidates?.length||0;const inGame=t.suno.candidates?.some(c=>c.used_in_game);
     return <button key={t.track_id} className={'track-pick'+(i===tIdx?' selected':'')} aria-current={i===tIdx} onClick={()=>selectTrack(i)}>
      <strong>{t.title.replace(`${draft.name} - `,'')}</strong>
      <small>{human(t.status)} · {n} take{n===1?'':'s'}{inGame?' · in game':''}</small>
     </button>;
    })}
    <div className="track-picker-actions">
     <button disabled={busy} onClick={()=>addTrack(activeArch)}><Plus size={14}/> Add song slot</button>
     <select aria-label="Add theme variation from archetype" value="" disabled={busy} onChange={e=>{if(e.target.value)addTrack(e.target.value,e.target.value)}}>
      <option value="">+ Theme variation…</option>
      <optgroup label="Biome / theme styles">{BIOME_STYLES.map(a=><option key={a} value={a}>{a} ({ARCHETYPES[a].bpm} BPM)</option>)}</optgroup>
      <optgroup label="Standard families">{STANDARD_FAMILIES.map(a=><option key={a} value={a}>{a} ({ARCHETYPES[a].bpm} BPM)</option>)}</optgroup>
     </select>
     <button disabled={busy} title="Replace all tracks with fresh A/B/C prompt templates for the selected archetype" onClick={()=>{
      update({archetype:activeArch, setting:activeSetting, tracks:generateTracksForArchetype(draft.game_id, draft.name, activeArch, activeSetting, draft.tracks, 3)});
     }}><Sparkles size={14}/> Regenerate A/B/C</button>
    </div>
   </aside>

   {track ? <section className="panel track-editor" key={track.track_id}>
    <div className="track-head">
     <input className="track-title" aria-label={`Song title ${track.track_id}`} value={track.title} onChange={e=>updateTrack(tIdx,{title:e.target.value})}/>
     <label className="compact-field"><span>Status</span>
      <select aria-label={`Track status ${track.track_id}`} value={track.status} onChange={e=>updateTrack(tIdx,{status:e.target.value})}>{TRACK_STATUSES.map(s=><option key={s} value={s}>{human(s)}</option>)}</select>
     </label>
     <label className="compact-field"><span>Vocals</span>
      <select aria-label={`Vocals mode ${track.track_id}`} value={track.vocals} onChange={e=>updateTrack(tIdx,{vocals:e.target.value})}>{VOCALS.map(v=><option key={v} value={v}>{v}</option>)}</select>
     </label>
     <Pill>{track.bpm} BPM</Pill>
    </div>

    <div className="tabs track-panes" role="tablist" aria-label="Track details">
     {([['takes','Takes',track.suno.candidates?.length||0],['prompt','Prompt',null],['stems','Stems',track.stems_requested.length],['files','Files',track.files.length]] as [TrackPane,string,number|null][]).map(([id,lbl,n])=>
      <button key={id} role="tab" aria-selected={pane===id} className={pane===id?'selected':''} onClick={()=>setPane(id)}>{lbl}{n!==null&&<span>{n}</span>}</button>)}
    </div>

    {pane==='prompt'&&<div className="prompt-grid">
     <div>
      <label className="field"><span className="field-head">Style of music <button className="link-button" onClick={()=>void copyText(`${track.track_id}-style`, track.style_prompt)}><Copy size={12}/> {copied===`${track.track_id}-style`?'Copied':'Copy'}</button></span>
       <textarea aria-label={`Style prompt ${track.track_id}`} rows={5} value={track.style_prompt} onChange={e=>updateTrack(tIdx,{style_prompt:e.target.value})}/>
      </label>
      <label className="field"><span>Production / stem notes</span>
       <textarea aria-label={`Notes ${track.track_id}`} rows={3} value={track.notes} placeholder="Loop bar boundaries, listening review notes…" onChange={e=>updateTrack(tIdx,{notes:e.target.value})}/>
      </label>
      <div className="form-row">
       <label className="field"><span>Suno song URL</span>
        <input aria-label={`Suno URL ${track.track_id}`} value={track.suno.url} placeholder="https://suno.com/song/..." onChange={e=>updateTrack(tIdx,{suno:{...track.suno,url:e.target.value}})}/>
       </label>
       <label className="field"><span>Suno clip ID / model</span>
        <input aria-label={`Suno clip ID ${track.track_id}`} value={track.suno.clip_id} placeholder="clip UUID or v4" onChange={e=>updateTrack(tIdx,{suno:{...track.suno,clip_id:e.target.value}})}/>
       </label>
      </div>
     </div>
     <label className="field"><span className="field-head">{track.vocals==='sung'?'Lyrics & section tags':'Lyrics box · adaptive sections'} <button className="link-button" onClick={()=>void copyText(`${track.track_id}-lyrics`, track.lyrics)}><Copy size={12}/> {copied===`${track.track_id}-lyrics`?'Copied':'Copy'}</button></span>
      <textarea aria-label={`Lyrics ${track.track_id}`} rows={14} value={track.lyrics} onChange={e=>updateTrack(tIdx,{lyrics:e.target.value})}/>
     </label>
    </div>}

    {pane==='stems'&&<>
     <p className="muted small">Suno Advanced Split options only. Checked stems are isolated; unchecked ones are filler. Use <strong>Synth Pad</strong> for pads and separate <strong>Rhythm Electric Guitar</strong> / <strong>Lead Guitar</strong>.</p>
     <div className="stem-grid">
      {track.instruments.map((inst,i)=>(
       <div className={'stem-row'+(inst.keep?'':' filler')} key={i}>
        <input type="checkbox" aria-label={`Keep ${inst.stem}`} checked={inst.keep} onChange={e=>{const next=track.instruments.map((x,j)=>j===i?{...x,keep:e.target.checked}:x);updateTrack(tIdx,{instruments:next,stems_requested:keepList(next)})}}/>
        <select aria-label={`Suno instrument ${track.track_id} ${i}`} value={inst.stem} onChange={e=>{const val=e.target.value;const next=track.instruments.map((x,j)=>j===i?{...x,name:val,stem:val}:x);updateTrack(tIdx,{instruments:next,stems_requested:keepList(next)})}}>
         <optgroup label="Standard">{SUNO_STANDARD_OPTIONS.map(s=><option key={s} value={s}>{s}</option>)}</optgroup>
         <optgroup label="Beta">{SUNO_BETA_OPTIONS.map(s=><option key={s} value={s}>{s}</option>)}</optgroup>
        </select>
        <Pill tone={SUNO_STANDARD_OPTIONS.includes(inst.stem)?'green':'warm'}>{SUNO_STANDARD_OPTIONS.includes(inst.stem)?'Std':'Beta'}</Pill>
        {track.instruments.length>1&&<button className="icon-button" aria-label={`Remove ${inst.name}`} onClick={()=>{const next=track.instruments.filter((_,j)=>j!==i);updateTrack(tIdx,{instruments:next,stems_requested:keepList(next)})}}><X size={13}/></button>}
       </div>
      ))}
     </div>
     <div className="inline" style={{marginTop:12}}>
      <select aria-label={`Add Suno instrument to ${track.track_id}`} value="" onChange={e=>{const val=e.target.value;if(!val||track.instruments.some(x=>x.stem===val))return;const next=[...track.instruments,{name:val,stem:val,keep:true}];updateTrack(tIdx,{instruments:next,stems_requested:keepList(next)})}}>
       <option value="">+ Add instrument…</option>
       <optgroup label="Standard">{SUNO_STANDARD_OPTIONS.filter(s=>!track.instruments.some(x=>x.stem===s)).map(s=><option key={s} value={s}>{s}</option>)}</optgroup>
       <optgroup label="Beta">{SUNO_BETA_OPTIONS.filter(s=>!track.instruments.some(x=>x.stem===s)).map(s=><option key={s} value={s}>{s}</option>)}</optgroup>
      </select>
      <span className="small muted"><strong>Split targets:</strong> {track.stems_requested.join(', ') || 'none'}</span>
     </div>
    </>}

    {pane==='takes'&&<>
     {track.suno.analysis && <div className="tag-list" style={{marginBottom:12}}>
      <Pill tone="green">{track.suno.analysis.bpm_detected} BPM detected</Pill>
      <Pill>{track.suno.analysis.key_detected}</Pill>
      <Pill>{track.suno.analysis.bars_detected} bars ({track.suno.analysis.time_signature}/4)</Pill>
      {track.suno.analysis.recommended_loop_start_s!==undefined && <Pill tone="warm">Loop: bar {track.suno.analysis.recommended_loop_start_bar} ({track.suno.analysis.recommended_loop_start_s}s–{track.suno.analysis.recommended_loop_end_s}s)</Pill>}
      {track.suno.stem_group_id && <Pill>Stems: {track.suno.stem_group_id}</Pill>}
     </div>}
     {!(track.suno.candidates?.length) && <p className="muted">No takes yet. Generate in Suno with the Prompt tab, then record the URL or attach a Suno match.</p>}
     <div className="take-list">
      {(track.suno.candidates||[]).map(cand=><TakeRow key={cand.clip_id} cand={cand} track={track} copied={copied}
       onCopy={()=>void copyText(`url-${cand.clip_id}`, cand.url)}
       onPatch={patch=>updateTrack(tIdx,{suno:{...track.suno,candidates:(track.suno.candidates||[]).map(c=>c.clip_id===cand.clip_id?{...c,...patch}:c)}})}
       onUse={()=>updateTrack(tIdx,{suno:{...track.suno,url:cand.url,clip_id:cand.clip_id,recommended_take:cand.take,candidates:(track.suno.candidates||[]).map(c=>({...c,used_in_game:c.clip_id===cand.clip_id}))}})}
       onOpenPath={openFolderForPath}/>)}
     </div>
    </>}

    {pane==='files'&&(track.files.length ? <div className="file-links">
     {track.files.map((f,fi)=><button key={f.path+fi} type="button" className="file-link" disabled={!native} title={f.path} onClick={()=>openFolderForPath(f.path)}>{f.path}<FolderOpen size={12}/></button>)}
    </div> : <p className="muted">No local pipeline files recorded for this track.</p>)}
   </section> : <section className="panel"><p className="muted">No tracks yet. Use Regenerate A/B/C to create prompt templates.</p></section>}
  </div>}

  {section==='matches'&&<section className="panel">
   <p className="muted small">Suno library clips matched by title. Attach a match to the selected track as a new take, or dismiss false matches.</p>
   <div className="take-list">
    {matches.map(rel=>{
     const target = draft.tracks[tIdx];
     const attached = draft.tracks.some(t=>t.suno.candidates?.some(c=>c.clip_id===rel.clip_id));
     return <div className="take-row" key={rel.clip_id}>
      <div className="take-main">
       <div className="inline"><strong>{rel.title}</strong>
        <Pill tone={rel.match_confidence==='ambiguous'?'warm':'green'}>{rel.match_confidence}</Pill>
        {rel.liked && <Pill tone="warm">Liked</Pill>}{rel.duration_s && <Pill>{rel.duration_s}s</Pill>}{rel.model && <Pill>{rel.model}</Pill>}
       </div>
       <small className="muted">Matched: {rel.matched_terms.join(', ')}{rel.match_candidates && rel.match_candidates.length>1 ? ` · Possible games: ${rel.match_candidates.join(', ')}` : ''}{rel.style ? ` · ${rel.style.slice(0,120)}${rel.style.length>120?'…':''}` : ''}</small>
      </div>
      <div className="inline take-actions">
       <a className="button" href={rel.url} target="_blank" rel="noreferrer">Open <ArrowUpRight size={13}/></a>
       <button onClick={()=>void copyText(`rel-${rel.clip_id}`, rel.url)}>{copied===`rel-${rel.clip_id}`?<Check size={13}/>:<Copy size={13}/>}</button>
       {target && !attached && <button className="primary" onClick={()=>{
        const take=(target.suno.candidates?.length||0)+1;
        const cand:SunoCandidate={take,clip_id:rel.clip_id,url:rel.url,duration_s:rel.duration_s||0,bpm_detected:target.bpm,key_detected:'Unanalyzed',time_signature:4,bars_detected:0,sections_count:0,quality_score:0,liked:rel.liked,listen_notes:`Attached from related Suno library (${rel.title})`};
        updateTrack(tIdx,{suno:{...target.suno,candidates:[...(target.suno.candidates||[]),cand]}});
       }}>Attach to {target.title.replace(`${draft.name} - `,'')}</button>}
       {attached && <Pill tone="green">Attached</Pill>}
       <button aria-label={`Dismiss ${rel.title}`} onClick={()=>update({related_suno_tracks:(draft.related_suno_tracks||[]).map(x=>x.clip_id===rel.clip_id?{...x,dismissed:true}:x)})}><X size={13}/> Dismiss</button>
      </div>
     </div>;
    })}
   </div>
  </section>}
 </div>;
}

function TakeRow({cand,track,copied,onCopy,onPatch,onUse,onOpenPath}:{cand:SunoCandidate;track:MusicTrack;copied:string;onCopy:()=>void;onPatch:(p:Partial<SunoCandidate>)=>void;onUse:()=>void;onOpenPath:(p?:string)=>void}){
 const isSelected = track.suno.clip_id===cand.clip_id;
 const instPct = cand.labels?.['arrangement:instrumental'] !== undefined ? Math.round(cand.labels['arrangement:instrumental']*100) : null;
 const meta = [`${cand.duration_s}s`,`${cand.bpm_detected} BPM`,cand.key_detected,`${cand.bars_detected} bars`,`${cand.sections_count} sections`,
  instPct!==null?`instrumental ${instPct}%`:'',cand.recommended_loop_start_s!==undefined?`loop ${cand.recommended_loop_start_s}s–${cand.recommended_loop_end_s}s`:'',
  cand.terms?.length?cand.terms.slice(0,4).join(', '):''].filter(Boolean).join(' · ');
 return <div className={'take-row'+(cand.used_in_game?' in-game':'')}>
  <div className="take-main">
   <div className="inline">
    <strong>Take {cand.take}</strong>
    {cand.used_in_game && <Pill tone="green">In game</Pill>}
    {isSelected && !cand.used_in_game && <Pill tone="green">Selected</Pill>}
    {cand.take===track.suno.recommended_take && <Pill>Recommended</Pill>}
    <Pill>Score {cand.quality_score}</Pill>
   </div>
   <small className="muted">{meta}</small>
   {cand.midi_files && cand.midi_files.length>0 && <details className="midi">
    <summary>MIDI stems ({cand.midi_files.length})</summary>
    <div className="file-links">{cand.midi_files.map((m,mi)=>m.path
     ?<button key={m.audio_id||mi} type="button" className="file-link" disabled={!native} title={m.path} onClick={()=>onOpenPath(m.path)}>{m.stem} ({m.notes_count ?? 0} notes)<FolderOpen size={12}/></button>
     :<span key={m.audio_id||mi}>{m.stem} ({m.notes_count ?? 0} notes)</span>)}</div>
   </details>}
  </div>
  <div className="take-review">
   <select aria-label={`Listen rating ${cand.clip_id}`} value={cand.listen_rating ?? ''} onChange={e=>onPatch({listen_rating:e.target.value?Number(e.target.value):undefined})}>
    <option value="">Rate…</option>{[5,4,3,2,1].map(n=><option key={n} value={n}>{n} / 5</option>)}
   </select>
   <input aria-label={`Listen notes ${cand.clip_id}`} value={cand.listen_notes || ''} placeholder="Listen notes: mix, loop seam, bleed…" onChange={e=>onPatch({listen_notes:e.target.value})}/>
  </div>
  <div className="inline take-actions">
   <button className={'icon-button'+(cand.liked?' liked':'')} aria-label={cand.liked?'Unlike':'Like'} aria-pressed={!!cand.liked} title={cand.liked?'Liked':'Like'} onClick={()=>onPatch({liked:!cand.liked})}><Star size={14} fill={cand.liked?'currentColor':'none'}/></button>
   <a className="button" href={cand.url} target="_blank" rel="noreferrer" title="Open in Suno">Listen <ArrowUpRight size={13}/></a>
   <button className="icon-button" aria-label="Copy URL" title="Copy URL" onClick={onCopy}>{copied===`url-${cand.clip_id}`?<Check size={13}/>:<Copy size={13}/>}</button>
   <button className={cand.used_in_game?'':'primary'} disabled={!!cand.used_in_game} onClick={onUse}>{cand.used_in_game?'In game':'Use in game'}</button>
  </div>
 </div>;
}

export function fallbackMusicRecords():MusicDesignRecord[]{
 return structuredClone(seedRecords as unknown as MusicDesignRecord[]);
}
