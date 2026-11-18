import React,{useState,useEffect} from 'react';
import {invoke,isTauri} from '@tauri-apps/api/core';
import {Music2,Check,Copy,FolderOpen,ArrowUpRight,Plus,Save,Search,Sparkles,X} from 'lucide-react';
import type {Game,MusicDesignRecord,MusicTrack,ProviderCatalogs} from './types';
import {ARCHETYPE_IDS,ARCHETYPES,SUNO_STANDARD_OPTIONS,SUNO_BETA_OPTIONS,applyArchetypeToRecord,generateTracksForArchetype,pipelineStage} from './music';
import seedRecords from '../data/music-design/index.json';

const native = isTauri();
const GAME_STATUSES = ['unassigned','recommended','excluded','planned','in_progress','approved'];
const TRACK_STATUSES = ['prompt_ready','generated','stems_split','approved','rejected'];
const IN_GAME_STATUSES = ['not_integrated','stems_downloaded','sonic_alchemist_sliced','wired_in_engine'];
const VOCALS = ['none','wordless','sung'];

function Pill({children,tone=''}:{children:React.ReactNode;tone?:string}){return <span className={'pill '+tone}>{children}</span>}

export function GameMusicPanel({
 game, record, providerCatalogs, onSaveRecord, onUpdateGameLink, onOpenFolder, busy
}:{
 game:Game;
 record:MusicDesignRecord;
 providerCatalogs:ProviderCatalogs;
 onSaveRecord:(rec:MusicDesignRecord)=>Promise<void>;
 onUpdateGameLink:(provider:string, assetId:string)=>Promise<void>;
 onOpenFolder:(provider:string|null)=>void;
 busy:boolean;
}){
 const [draft,setDraft] = useState<MusicDesignRecord>(()=>structuredClone(record));
 const [dirty,setDirty] = useState(false);
 const [copied,setCopied] = useState('');

 useEffect(()=>{setDraft(structuredClone(record));setDirty(false)},[record]);

 function openFolderForPath(path?:string){
  if(!path || !native) return;
  void invoke('open_folder_for_path', { path });
 }

 function update(patch:Partial<MusicDesignRecord>){
  setDraft(prev=>({...prev,...patch}));
  setDirty(true);
 }

 function updateTrack(idx:number, patch:Partial<MusicTrack>){
  setDraft(prev=>({
   ...prev,
   tracks: prev.tracks.map((t,i)=>i===idx?{...t,...patch}:t)
  }));
  setDirty(true);
 }

 async function copyText(key:string, text:string){
  try{
   await navigator.clipboard.writeText(text);
   setCopied(key);
   setTimeout(()=>setCopied(''),2000);
  }catch{
   setCopied('');
  }
 }

 const activeArch = draft.archetype || draft.recommended_archetype || 'cozy';
 const activeSetting = draft.setting || draft.recommended_setting || '';
 const saList = providerCatalogs['ArcoreSonicAlchemist']?.projects || [];
 const scList = providerCatalogs['ArcoreSoundCore']?.projects || [];
 const mfList = providerCatalogs['ArcoreModelForge']?.projects || [];

 const saLink = game.provider_links.find(p=>p.provider==='ArcoreSonicAlchemist')?.asset_id || draft.sonic_alchemist_project || '';
 const scLink = game.provider_links.find(p=>p.provider==='ArcoreSoundCore')?.asset_id || draft.soundcore_project || '';
 const mfLink = game.provider_links.find(p=>p.provider==='ArcoreModelForge')?.asset_id || draft.modelforge_project || '';
 const activeTrack = draft.tracks.find(t=>t.suno.candidates?.some(c=>c.used_in_game)) || draft.tracks[0];
 const activeSuno = activeTrack?.suno;
 const activeCand = activeSuno?.candidates?.find(c=>c.used_in_game) || activeSuno?.candidates?.find(c=>c.clip_id===activeSuno.clip_id);
 const activeStage = pipelineStage(draft);
 const dbFilePath = `hub/data/music-design/${draft.game_id}.json`;

 return <div className="music-tab">
  <div className="section-heading">
   <div>
    <h2>Adaptive music & Suno stem design</h2>
    <p>Organize Suno takes, 0-credit analysis, listen ratings, stem groups, MIDI exports, and active in-game audio wiring.</p>
   </div>
   <div className="inline">
    <Pill tone={activeStage==='wired_in_engine'||draft.status==='approved'?'green':'warm'}>{activeStage}</Pill>
    <Pill tone={draft.status==='approved'||draft.status==='planned'?'green':'warm'}>{draft.status}</Pill>
    <button className="primary" disabled={!native||busy||!dirty} onClick={()=>onSaveRecord(draft)}><Save size={16}/> Save music design</button>
   </div>
  </div>

  {activeTrack && (
   <section className="panel">
    <div className="section-heading">
     <div>
      <div className="eyebrow">CURRENTLY SELECTED & IN-GAME MUSIC</div>
      <h2>{activeTrack.title}</h2>
      <div className="tag-list" style={{marginTop:6}}>
       <Pill tone={activeSuno?.in_game_status==='wired_in_engine'?'green':'warm'}>
        In-Game: {activeSuno?.in_game_status || 'not_integrated'}
       </Pill>
       {activeCand && <Pill tone="green">Take {activeCand.take}{activeCand.used_in_game ? ' · Used in game' : ''}</Pill>}
       {activeSuno?.analysis && (
        <>
         <Pill>{activeSuno.analysis.bpm_detected} BPM</Pill>
         <Pill>{activeSuno.analysis.key_detected}</Pill>
         <Pill>{activeSuno.analysis.bars_detected} bars</Pill>
        </>
       )}
       {activeSuno?.in_game_loop_s && <Pill tone="green">Loop: {activeSuno.in_game_loop_s}s</Pill>}
       {activeSuno?.stem_group_id && <Pill>Stem group: {activeSuno.stem_group_id}</Pill>}
      </div>
     </div>
     <div className="inline">
      {activeSuno?.url && (
       <a className="button" href={activeSuno.url} target="_blank" rel="noreferrer">
        Open in Suno <ArrowUpRight size={14}/>
       </a>
      )}
      <button onClick={()=>void copyText('db-file', dbFilePath)}>
       <Copy size={14}/> {copied==='db-file'?'Copied DB path!':'Copy DB JSON path'}
      </button>
     </div>
    </div>

    <div className="form-row">
     <label className="field">
      <span>In-game integration status</span>
      <select
       aria-label="In-game integration status"
       value={activeSuno?.in_game_status || 'not_integrated'}
       onChange={e=>{
        const idx = Math.max(0, draft.tracks.findIndex(t=>t.track_id===activeTrack.track_id));
        updateTrack(idx,{suno:{...activeTrack.suno, in_game_status:e.target.value}});
       }}
      >
       {IN_GAME_STATUSES.map(s=><option key={s} value={s}>{s}</option>)}
      </select>
     </label>
     <label className="field">
      <span>Engine audio path (e.g. /Game/Audio/Music)</span>
      <input
       aria-label="Engine audio path"
       value={activeSuno?.engine_asset_path || ''}
       placeholder="/Game/Audio/Music"
       onChange={e=>{
        const idx = Math.max(0, draft.tracks.findIndex(t=>t.track_id===activeTrack.track_id));
        updateTrack(idx,{suno:{...activeTrack.suno, engine_asset_path:e.target.value}});
       }}
      />
     </label>
     <label className="field">
      <span>In-game loop length (s)</span>
      <input
       aria-label="In-game loop length"
       type="number"
       step="0.01"
       value={activeSuno?.in_game_loop_s ?? ''}
       placeholder="e.g. 54.86"
       onChange={e=>{
        const idx = Math.max(0, draft.tracks.findIndex(t=>t.track_id===activeTrack.track_id));
        const val = e.target.value ? Number(e.target.value) : undefined;
        updateTrack(idx,{suno:{...activeTrack.suno, in_game_loop_s:val}});
       }}
      />
     </label>
    </div>

    <div className="small muted" style={{marginTop:8}}>
     <strong>Music DB file:</strong> <code>{dbFilePath}</code>
     {activeSuno?.clip_id && <> · <strong>Active Clip:</strong> <code>{activeSuno.clip_id}</code></>}
     {(activeSuno?.in_game_stems?.length ? activeSuno.in_game_stems : activeTrack.stems_requested).length > 0 && (
      <> · <strong>Active Stems:</strong> {(activeSuno?.in_game_stems?.length ? activeSuno.in_game_stems : activeTrack.stems_requested).join(', ')}</>
     )}
    </div>
   </section>
  )}

  <section className="panel">
   <div className="section-heading">
    <div>
     <div className="eyebrow">RECOMMENDED BIOME / ARCHETYPE</div>
     <h2>{draft.recommended_archetype || 'Unassigned'} {draft.recommended_setting ? `· ${draft.recommended_setting}` : ''}</h2>
     <p className="muted">{draft.recommendation_reason || 'Select an archetype and setting to generate 2–3 adaptive tracks with locked instrumentation.'}</p>
    </div>
    {draft.recommended_archetype && draft.status !== 'excluded' && (
     <button className="primary" disabled={!native||busy} onClick={()=>{
      const next = applyArchetypeToRecord(draft, draft.recommended_archetype!, draft.recommended_setting || draft.setting, true);
      setDraft(next);
      void onSaveRecord(next);
     }}>
      <Check size={16}/> Approve recommended ({draft.recommended_archetype})
     </button>
    )}
   </div>

   <div className="form-row">
    <label className="field">
     <span>Music status</span>
     <select aria-label="Music status" value={draft.status} onChange={e=>update({status:e.target.value})}>
      {GAME_STATUSES.map(s=><option key={s} value={s}>{s}</option>)}
     </select>
    </label>
    <label className="field">
     <span>Selected archetype</span>
     <select aria-label="Selected archetype" value={draft.archetype||''} onChange={e=>{
      const arch = e.target.value || null;
      if(arch){
       setDraft(prev=>applyArchetypeToRecord(prev, arch, prev.setting || prev.recommended_setting, false));
       setDirty(true);
      }else{
       update({archetype:null});
      }
     }}>
      <option value="">(Use recommendation: {draft.recommended_archetype||'none'})</option>
      <optgroup label="Standard Families (6)">
       {ARCHETYPE_IDS.filter(a=>!('parent_archetype' in ARCHETYPES[a])).map(a=><option key={a} value={a}>{a} — {ARCHETYPES[a].genre} ({ARCHETYPES[a].bpm} BPM)</option>)}
      </optgroup>
      <optgroup label="Granular Biome / Theme Styles (10)">
       {ARCHETYPE_IDS.filter(a=>'parent_archetype' in ARCHETYPES[a]).map(a=><option key={a} value={a}>{a} [{(ARCHETYPES[a] as {parent_archetype?:string}).parent_archetype}] — {ARCHETYPES[a].genre} ({ARCHETYPES[a].bpm} BPM)</option>)}
      </optgroup>
     </select>
    </label>
   </div>

   <div className="form-row">
    <label className="field">
     <span>Biome / atmosphere setting</span>
     <input aria-label="Biome / atmosphere setting" value={draft.setting} placeholder={draft.recommended_setting||'e.g. neon grid, sunken crypt, breezy harbor'} onChange={e=>update({setting:e.target.value})}/>
    </label>
    <label className="field">
     <span>Exclusion note (if already scored)</span>
     <input aria-label="Exclusion note" value={draft.exclusion_reason} placeholder="Leave blank unless game already has music" onChange={e=>update({exclusion_reason:e.target.value})}/>
    </label>
   </div>

   <div className="inline">
    <button disabled={busy} onClick={()=>{
     const tracks = generateTracksForArchetype(draft.game_id, draft.name, activeArch, activeSetting, draft.tracks, 3);
     update({archetype:activeArch, setting:activeSetting, tracks});
    }}><Sparkles size={15}/> Regenerate prompt templates (A/B/C)</button>
    <button disabled={busy} onClick={()=>{
     const letter = String.fromCharCode(65 + draft.tracks.length);
     const extra = generateTracksForArchetype(draft.game_id, draft.name, activeArch, activeSetting, [], 1)[0];
     if(extra){
      update({tracks:[...draft.tracks,{...extra, track_id:`${draft.game_id}-${letter}`, title:`${draft.name} - Track ${letter}`}]});
     }
    }}><Plus size={15}/> Add song slot</button>
    <select aria-label="Add theme variation from archetype" value="" disabled={busy} onChange={e=>{
     const arch = e.target.value;
     if(!arch) return;
     const letter = String.fromCharCode(65 + draft.tracks.length);
     const extra = generateTracksForArchetype(draft.game_id, draft.name, arch, activeSetting, [], 1)[0];
     if(extra){
      update({tracks:[...draft.tracks,{...extra, track_id:`${draft.game_id}-${letter}`, title:`${draft.name} - ${arch}`}]});
     }
    }}>
     <option value="">+ Add theme variation from archetype…</option>
     <optgroup label="Granular Biome / Theme Styles (10)">
      {ARCHETYPE_IDS.filter(a=>'parent_archetype' in ARCHETYPES[a]).map(a=><option key={a} value={a}>{a} ({ARCHETYPES[a].bpm} BPM)</option>)}
     </optgroup>
     <optgroup label="Standard Families (6)">
      {ARCHETYPE_IDS.filter(a=>!('parent_archetype' in ARCHETYPES[a])).map(a=><option key={a} value={a}>{a} ({ARCHETYPES[a].bpm} BPM)</option>)}
     </optgroup>
    </select>
   </div>
  </section>

  <section className="panel">
   <h2>Ecosystem library links (SoundAlchemist · SoundCore · ModelForge)</h2>
   <p className="muted">Link this game directly to its adaptive music project in Sonic Alchemist, its sound effects gallery in SoundCore, and its 3D asset project in ModelForge.</p>
   <div className="provider-grid">
    <div className="panel provider">
     <Music2 size={20}/>
     <h3>ArcoreSonicAlchemist</h3>
     <p className="muted">Adaptive music production, stem splitting, and state-machine arrangements.</p>
     <label className="field">
      <span>Linked Sonic Alchemist project</span>
      <select aria-label="Sonic Alchemist project" value={saLink} onChange={e=>{
       const val = e.target.value;
       update({sonic_alchemist_project:val});
       void onUpdateGameLink('ArcoreSonicAlchemist', val);
      }}>
       <option value="">Not linked — pick a project or composition…</option>
       {saList.map(p=><option key={p.id} value={p.id}>{p.label}</option>)}
       <option value={game.id}>Create / link '{game.id}'</option>
      </select>
     </label>
     <button disabled={!native} onClick={()=>onOpenFolder('ArcoreSonicAlchemist')}>Open Sonic Alchemist <ArrowUpRight size={14}/></button>
    </div>

    <div className="panel provider">
     <Music2 size={20}/>
     <h3>ArcoreSoundCore</h3>
     <p className="muted">Sound effects catalog, provenance, and game audio delivery manifests.</p>
     <label className="field">
      <span>Linked SoundCore project / collection</span>
      <select aria-label="SoundCore project" value={scLink} onChange={e=>{
       const val = e.target.value;
       update({soundcore_project:val});
       void onUpdateGameLink('ArcoreSoundCore', val);
      }}>
       <option value="">Not linked — pick a collection or category…</option>
       {scList.map(p=><option key={p.id} value={p.id}>{p.label}</option>)}
       <option value={game.id}>Project: {game.id}</option>
      </select>
     </label>
     <button disabled={!native} onClick={()=>onOpenFolder('ArcoreSoundCore')}>Open SoundCore gallery <ArrowUpRight size={14}/></button>
    </div>

    <div className="panel provider">
     <FolderOpen size={20}/>
     <h3>ArcoreModelForge</h3>
     <p className="muted">Versioned 3D models, rigs, materials, and texture lab assets.</p>
     <label className="field">
      <span>Linked ModelForge project</span>
      <select aria-label="ModelForge project" value={mfLink} onChange={e=>{
       const val = e.target.value;
       update({modelforge_project:val});
       void onUpdateGameLink('ArcoreModelForge', val);
      }}>
       <option value="">Not linked — pick a 3D project…</option>
       {mfList.map(p=><option key={p.id} value={p.id}>{p.label}</option>)}
       <option value={game.name}>Project: {game.name}</option>
      </select>
     </label>
     <button disabled={!native} onClick={()=>onOpenFolder('ArcoreModelForge')}>Open ModelForge <ArrowUpRight size={14}/></button>
    </div>
   </div>
  </section>

  {draft.tracks.map((t,idx)=>(
   <section className="panel track-card" key={t.track_id}>
    <div className="section-heading">
     <div className="inline">
      <Pill tone={t.status==='approved'?'green':'warm'}>{t.track_id}</Pill>
      <h2>{t.title}</h2>
      <Pill>{t.bpm} BPM</Pill>
      <Pill>Vocals: {t.vocals}</Pill>
     </div>
     <div className="inline">
      <button onClick={()=>void copyText(`${t.track_id}-style`, t.style_prompt)}>
       <Copy size={14}/> {copied===`${t.track_id}-style`?'Copied style!':'Copy Style Box'}
      </button>
      <button onClick={()=>void copyText(`${t.track_id}-lyrics`, t.lyrics)}>
       <Copy size={14}/> {copied===`${t.track_id}-lyrics`?'Copied lyrics!':'Copy Lyrics Box'}
      </button>
     </div>
    </div>

    <div className="form-row">
     <label className="field">
      <span>Song title</span>
      <input aria-label={`Song title ${t.track_id}`} value={t.title} onChange={e=>updateTrack(idx,{title:e.target.value})}/>
     </label>
     <div className="form-row">
      <label className="field">
       <span>Track status</span>
       <select aria-label={`Track status ${t.track_id}`} value={t.status} onChange={e=>updateTrack(idx,{status:e.target.value})}>
        {TRACK_STATUSES.map(s=><option key={s} value={s}>{s}</option>)}
       </select>
      </label>
      <label className="field">
       <span>Vocals mode</span>
       <select aria-label={`Vocals mode ${t.track_id}`} value={t.vocals} onChange={e=>updateTrack(idx,{vocals:e.target.value})}>
        {VOCALS.map(v=><option key={v} value={v}>{v}</option>)}
       </select>
      </label>
     </div>
    </div>

    <label className="field">
     <span>Suno Style of Music prompt (includes genre, mood, BPM & explicit instruments for stem split)</span>
     <textarea aria-label={`Style prompt ${t.track_id}`} rows={3} value={t.style_prompt} onChange={e=>updateTrack(idx,{style_prompt:e.target.value})}/>
    </label>

    <div className="two-col">
     <div>
      <label className="field">
       <span>{t.vocals==='sung'?'Suno Lyrics & Adaptive Section Tags (sung vocals + section cues)':'Suno Lyrics Box — Adaptive Architecture (Intro → Explore → Tension → Combat → Boss → Outro)'}</span>
       <textarea aria-label={`Lyrics ${t.track_id}`} rows={11} value={t.lyrics} onChange={e=>updateTrack(idx,{lyrics:e.target.value})}/>
      </label>
     </div>
     <div>
      <h3>Suno Advanced Split instruments (22 Standard · 68 Beta)</h3>
      <p className="muted small">Restricted to Suno’s exact stem separation options. Check core hero stems to isolate in Advanced Split; use <strong>Synth Pad</strong> for pads and separate <strong>Rhythm Electric Guitar</strong> / <strong>Lead Guitar</strong>.</p>
      <div className="stem-table">
       {t.instruments.map((inst,i)=>(
        <div className="classification" key={i}>
         <label className="inline" style={{minWidth:70}}>
          <input type="checkbox" checked={inst.keep} onChange={e=>{
           const nextInst = t.instruments.map((x,j)=>j===i?{...x,keep:e.target.checked}:x);
           const nextKeep = [...new Set(nextInst.filter(x=>x.keep).map(x=>x.stem))].sort();
           updateTrack(idx,{instruments:nextInst, stems_requested:nextKeep});
          }}/>
          <small>{inst.keep?'Keep':'Filler'}</small>
         </label>
         <select aria-label={`Suno instrument ${t.track_id} ${i}`} value={inst.stem} style={{flex:1}} onChange={e=>{
          const val = e.target.value;
          const nextInst = t.instruments.map((x,j)=>j===i?{...x,name:val,stem:val}:x);
          const nextKeep = [...new Set(nextInst.filter(x=>x.keep).map(x=>x.stem))].sort();
          updateTrack(idx,{instruments:nextInst, stems_requested:nextKeep});
         }}>
          <optgroup label="Standard options (22)">
           {SUNO_STANDARD_OPTIONS.map(s=><option key={s} value={s}>{s} (Standard)</option>)}
          </optgroup>
          <optgroup label="Beta options (68)">
           {SUNO_BETA_OPTIONS.map(s=><option key={s} value={s}>{s} (Beta)</option>)}
          </optgroup>
         </select>
         <Pill tone={SUNO_STANDARD_OPTIONS.includes(inst.stem)?'green':'warm'}>{SUNO_STANDARD_OPTIONS.includes(inst.stem)?'Standard':'Beta'}</Pill>
         {t.instruments.length>1&&(
          <button aria-label={`Remove ${inst.name}`} onClick={()=>{
           const nextInst = t.instruments.filter((_,j)=>j!==i);
           const nextKeep = [...new Set(nextInst.filter(x=>x.keep).map(x=>x.stem))].sort();
           updateTrack(idx,{instruments:nextInst, stems_requested:nextKeep});
          }}><X size={14}/></button>
         )}
        </div>
       ))}
      </div>
      <div className="inline" style={{margin:'10px 0'}}>
       <select aria-label={`Add Suno instrument to ${t.track_id}`} value="" onChange={e=>{
        const val = e.target.value;
        if(!val || t.instruments.some(x=>x.stem===val)) return;
        const nextInst = [...t.instruments, {name:val, stem:val, keep:true}];
        const nextKeep = [...new Set(nextInst.filter(x=>x.keep).map(x=>x.stem))].sort();
        updateTrack(idx,{instruments:nextInst, stems_requested:nextKeep});
       }}>
        <option value="">+ Add Suno instrument (22 Standard / 68 Beta)…</option>
        <optgroup label="Standard options (22)">
         {SUNO_STANDARD_OPTIONS.filter(s=>!t.instruments.some(x=>x.stem===s)).map(s=><option key={s} value={s}>{s} (Standard)</option>)}
        </optgroup>
        <optgroup label="Beta options (68)">
         {SUNO_BETA_OPTIONS.filter(s=>!t.instruments.some(x=>x.stem===s)).map(s=><option key={s} value={s}>{s} (Beta)</option>)}
        </optgroup>
       </select>
      </div>
      <p className="small"><strong>Target Advanced Split Stems:</strong> {t.stems_requested.join(', ') || 'none'}</p>
      <div className="form-row">
       <label className="field">
        <span>Suno song URL</span>
        <input aria-label={`Suno URL ${t.track_id}`} value={t.suno.url} placeholder="https://suno.com/song/..." onChange={e=>updateTrack(idx,{suno:{...t.suno,url:e.target.value}})}/>
       </label>
       <label className="field">
        <span>Suno clip ID / model</span>
        <input aria-label={`Suno clip ID ${t.track_id}`} value={t.suno.clip_id} placeholder="clip UUID or v4" onChange={e=>updateTrack(idx,{suno:{...t.suno,clip_id:e.target.value}})}/>
       </label>
      </div>
      <label className="field">
       <span>Production / stem notes</span>
       <input aria-label={`Notes ${t.track_id}`} value={t.notes} placeholder="Loop bar boundaries, listening review notes…" onChange={e=>updateTrack(idx,{notes:e.target.value})}/>
      </label>
      {(t.suno.analysis || (t.suno.candidates && t.suno.candidates.length>0) || t.files.length>0) && (
       <div style={{marginTop:12,padding:12,border:'1px solid var(--border, #2a333d)',borderRadius:8}}>
        <div className="eyebrow">SUNO MCP ANALYSIS, LISTEN STATS & ALL GENERATED TAKES ({t.suno.candidates?.length || 0})</div>
        {t.suno.analysis && (
         <div className="tag-list" style={{margin:'8px 0'}}>
          <Pill tone="green">Detected {t.suno.analysis.bpm_detected} BPM</Pill>
          <Pill>{t.suno.analysis.key_detected}</Pill>
          <Pill>{t.suno.analysis.bars_detected} bars ({t.suno.analysis.time_signature}/4)</Pill>
          {t.suno.analysis.recommended_loop_start_s!==undefined && (
           <Pill tone="warm">32-Bar Loop: Bar {t.suno.analysis.recommended_loop_start_bar} ({t.suno.analysis.recommended_loop_start_s}s–{t.suno.analysis.recommended_loop_end_s}s)</Pill>
          )}
          {t.suno.stem_group_id && <Pill>Stems: {t.suno.stem_group_id}</Pill>}
         </div>
        )}
        {t.suno.candidates && t.suno.candidates.map(cand=>{
         const isSelected = t.suno.clip_id===cand.clip_id;
         const instPct = cand.labels?.['arrangement:instrumental'] !== undefined ? Math.round(cand.labels['arrangement:instrumental']*100) : null;
         const updateCand = (patch:Partial<typeof cand>)=>{
          const nextCands = (t.suno.candidates||[]).map(c=>c.clip_id===cand.clip_id?{...c,...patch}:c);
          updateTrack(idx,{suno:{...t.suno, candidates:nextCands}});
         };
         return (
          <div key={cand.clip_id} style={{marginTop:8,padding:10,border:'1px solid var(--border, #2a333d)',borderRadius:6}}>
           <div className="section-heading">
            <div className="inline">
             <strong>Take {cand.take}</strong>
             {cand.used_in_game && <Pill tone="green">USED IN GAME</Pill>}
             {isSelected && <Pill tone="green">SELECTED</Pill>}
             {cand.liked && <Pill tone="warm">LIKED</Pill>}
             {cand.take===t.suno.recommended_take && <Pill>Recommended</Pill>}
             <Pill>Score {cand.quality_score}</Pill>
            </div>
            <div className="inline">
             <a className="button" href={cand.url} target="_blank" rel="noreferrer">Open <ArrowUpRight size={13}/></a>
             <button onClick={()=>void copyText(`url-${cand.clip_id}`, cand.url)}>
              {copied===`url-${cand.clip_id}`?<Check size={13}/>:<Copy size={13}/>} Copy URL
             </button>
             <button className={isSelected?'primary':''} onClick={()=>{
              const nextCands = (t.suno.candidates||[]).map(c=>({...c, used_in_game:c.clip_id===cand.clip_id}));
              updateTrack(idx,{suno:{...t.suno, url:cand.url, clip_id:cand.clip_id, recommended_take:cand.take, candidates:nextCands}});
             }}>
              {cand.used_in_game?'Used in game':isSelected?'Mark Used in Game':'Use Take '+cand.take}
             </button>
            </div>
           </div>
           <small className="muted" style={{display:'block',margin:'4px 0'}}>
            {cand.duration_s}s · {cand.bpm_detected} BPM · {cand.key_detected} · {cand.bars_detected} bars · {cand.sections_count} sections
            {instPct!==null ? ` · Instrumental ${instPct}%` : ''}
            {cand.recommended_loop_start_s!==undefined ? ` · Loop ${cand.recommended_loop_start_s}s–${cand.recommended_loop_end_s}s` : ''}
            {cand.terms?.length ? ` · ${cand.terms.slice(0,4).join(', ')}` : ''}
           </small>
           <div className="form-row" style={{marginTop:6}}>
            <label className="field" style={{maxWidth:120}}>
             <span>Listen rating</span>
             <select aria-label={`Listen rating ${cand.clip_id}`} value={cand.listen_rating ?? ''} onChange={e=>updateCand({listen_rating:e.target.value?Number(e.target.value):undefined})}>
              <option value="">Unrated</option>
              {[5,4,3,2,1].map(n=><option key={n} value={n}>{n} / 5</option>)}
             </select>
            </label>
            <label className="field">
             <span>Listen / QA notes</span>
             <input aria-label={`Listen notes ${cand.clip_id}`} value={cand.listen_notes || ''} placeholder="Mix balance, loop seam, vocal bleed…" onChange={e=>updateCand({listen_notes:e.target.value})}/>
            </label>
            <div className="inline" style={{alignSelf:'flex-end'}}>
             <button onClick={()=>updateCand({liked:!cand.liked})}>{cand.liked?'Liked ★':'Like'}</button>
            </div>
           </div>
           {cand.midi_files && cand.midi_files.length>0 && (
            <div className="small muted" style={{marginTop:6,display:'flex',flexWrap:'wrap',gap:6,alignItems:'center'}}>
             <strong>MIDI stems ({cand.midi_files.length}):</strong>
             {cand.midi_files.map((m,mi)=>m.path?(
              <button key={m.audio_id||mi} type="button" className="file-link" disabled={!native} title={m.path} onClick={()=>openFolderForPath(m.path)}>
               {m.stem} ({m.notes_count ?? 0} notes)<FolderOpen size={12}/>
              </button>
             ):(
              <span key={m.audio_id||mi}>{m.stem} ({m.notes_count ?? 0} notes)</span>
             ))}
            </div>
           )}
          </div>
         );
        })}
        {t.files.length>0 && (
         <div className="small muted" style={{marginTop:8,display:'flex',flexWrap:'wrap',gap:6,alignItems:'center'}}>
          <strong>Local pipeline files ({t.files.length}):</strong>
          {t.files.map((f,fi)=>(
           <button key={f.path+fi} type="button" className="file-link" disabled={!native} title={f.path} onClick={()=>openFolderForPath(f.path)}>
            {f.path}<FolderOpen size={12}/>
           </button>
          ))}
         </div>
        )}
       </div>
      )}
     </div>
    </div>
   </section>
  ))}

  {(draft.related_suno_tracks || []).some(r=>!r.dismissed) && (
   <section className="panel">
    <div className="section-heading">
     <div>
      <div className="eyebrow">SUNO LIBRARY TITLE MATCHES</div>
      <h2>Related Suno tracks ({(draft.related_suno_tracks || []).filter(r=>!r.dismissed).length})</h2>
      <p className="muted">Library clips matched by title (ignoring generic words like "3D" alone). Attach a match to Track A or dismiss false/ambiguous matches.</p>
     </div>
    </div>
    {(draft.related_suno_tracks || []).filter(r=>!r.dismissed).map(rel=>(
     <div key={rel.clip_id} style={{marginTop:8,padding:10,border:'1px solid var(--border, #2a333d)',borderRadius:6}}>
      <div className="section-heading">
       <div className="inline">
        <strong>{rel.title}</strong>
        <Pill tone={rel.match_confidence==='ambiguous'?'warm':'green'}>{rel.match_confidence} match</Pill>
        {rel.liked && <Pill tone="warm">LIKED</Pill>}
        {rel.duration_s && <Pill>{rel.duration_s}s</Pill>}
        {rel.model && <Pill>{rel.model}</Pill>}
       </div>
       <div className="inline">
        <a className="button" href={rel.url} target="_blank" rel="noreferrer">Open <ArrowUpRight size={13}/></a>
        <button onClick={()=>void copyText(`rel-${rel.clip_id}`, rel.url)}>
         {copied===`rel-${rel.clip_id}`?<Check size={13}/>:<Copy size={13}/>} Copy URL
        </button>
        {draft.tracks[0] && !draft.tracks[0].suno.candidates?.some(c=>c.clip_id===rel.clip_id) && (
         <button className="primary" onClick={()=>{
          const t0 = draft.tracks[0];
          const nextTake = (t0.suno.candidates?.length || 0) + 1;
          const newCand = {
           take: nextTake,
           clip_id: rel.clip_id,
           url: rel.url,
           duration_s: rel.duration_s || 0,
           bpm_detected: t0.bpm,
           key_detected: 'Unanalyzed',
           time_signature: 4,
           bars_detected: 0,
           sections_count: 0,
           quality_score: 0,
           liked: rel.liked,
           listen_notes: `Attached from related Suno library (${rel.title})`,
          };
          updateTrack(0,{suno:{...t0.suno, candidates:[...(t0.suno.candidates||[]), newCand]}});
         }}>Attach to Track A</button>
        )}
        <button onClick={()=>{
         update({related_suno_tracks:(draft.related_suno_tracks||[]).map(x=>x.clip_id===rel.clip_id?{...x,dismissed:true}:x)});
        }}><X size={13}/> Dismiss</button>
       </div>
      </div>
      <small className="muted" style={{display:'block',marginTop:4}}>
       Clip: <code>{rel.clip_id}</code> · Matched: {rel.matched_terms.join(', ')}
       {rel.match_candidates && rel.match_candidates.length>1 ? ` · Possible games: ${rel.match_candidates.join(', ')}` : ''}
       {rel.style ? ` · ${rel.style.slice(0,140)}${rel.style.length>140?'…':''}` : ''}
      </small>
     </div>
    ))}
   </section>
  )}
 </div>;
}

export function fallbackMusicRecords():MusicDesignRecord[]{
 return structuredClone(seedRecords as unknown as MusicDesignRecord[]);
}
