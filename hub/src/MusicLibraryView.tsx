import React,{useMemo,useState} from 'react';
import {invoke,convertFileSrc} from '@tauri-apps/api/core';
import {ArrowUpRight,Copy,Check,FolderOpen,Search,SlidersHorizontal,Music2} from 'lucide-react';
import type {MusicDesignRecord} from './types';
import {ARCHETYPES,PARENT_ARCHETYPE_IDS,SUB_ARCHETYPE_IDS,archetypeLabel} from './music';
import {MUSIC_LIBRARY,filterLibrary,groupByTaxonomy,libraryFilePath,formatDuration,type LibraryTrack,type MusicLibraryIndex} from './musicLibrary';
import './music-library.css';

type Pane='tracks'|'coverage';
const human=(s:string)=>s.replaceAll('_',' ').replaceAll('-',' ');
const archInfo=(id:string)=>(ARCHETYPES as Record<string,{genre:string;bpm:number;mood:string;parent_archetype?:string}>)[id];

function Pill({children,tone=''}:{children:React.ReactNode;tone?:string}){return <span className={'pill '+tone}>{children}</span>}

export function MusicLibraryView({records,native,openGameMusic,library=MUSIC_LIBRARY}:{
 records:MusicDesignRecord[];
 native:boolean;
 openGameMusic:(gameId:string)=>void;
 library?:MusicLibraryIndex;
}){
 const [pane,setPane]=useState<Pane>('tracks');
 const [query,setQuery]=useState('');
 const [parent,setParent]=useState('');
 const [archetype,setArchetype]=useState('');
 const [state,setState]=useState('');
 const [context,setContext]=useState('');
 const [includeRelated,setIncludeRelated]=useState(false);
 const [copied,setCopied]=useState('');

 const filtered=useMemo(()=>filterLibrary(library.tracks,{query,parent,archetype,state,context,includeRelated}),[library,query,parent,archetype,state,context,includeRelated]);
 // Related matches are filed under their own archetype; show them in the group being browsed instead.
 const grouped=useMemo(()=>{
  if(!includeRelated||(!archetype&&!parent)) return groupByTaxonomy(filtered);
  const target=archetype||parent;
  return groupByTaxonomy(filtered.map(t=>t.archetype===target||(!archetype&&t.parent_archetype===parent)?t:{...t,archetype:target,parent_archetype:archInfo(target)?.parent_archetype||target}));
 },[filtered,includeRelated,archetype,parent]);
 const gamesByArch=useMemo(()=>{
  const m=new Map<string,MusicDesignRecord[]>();
  for(const r of records){if(r.status==='excluded')continue;const a=r.archetype||r.recommended_archetype;if(!a)continue;m.set(a,[...(m.get(a)||[]),r])}
  return m;
 },[records]);
 const totalSeconds=library.tracks.reduce((n,t)=>n+(t.duration_s||0),0);
 const covered=library.coverage.filter(c=>c.primary_tracks>0).length;
 const gaps=library.coverage.reduce((n,c)=>n+c.missing_states.length,0);

 async function copy(key:string,text:string){try{await navigator.clipboard.writeText(text);setCopied(key);setTimeout(()=>setCopied(''),1800)}catch{setCopied('')}}
 function clear(){setQuery('');setParent('');setArchetype('');setState('');setContext('');setIncludeRelated(false)}

 return <div className="music-library">
  <div className="page-heading compact"><div><h1>Music library</h1><p>Reusable cues for any game, organized by the adaptive-music archetype taxonomy. Files stay in <code>{library.library_root}</code>.</p></div></div>
  <div className="stats">
   <div><strong>{library.tracks.length}</strong><span>Library tracks · {Math.round(totalSeconds/60)} min</span></div>
   <div><strong>{covered}/{library.coverage.length}</strong><span>Archetypes with a primary track</span></div>
   <div><strong>{library.folders.length}</strong><span>Source folders</span></div>
   <div><strong>{gaps}</strong><span>Archetype × game-state gaps</span></div>
  </div>

  <div className="tabs" role="tablist" aria-label="Music library sections">
   {([['tracks','Browse by archetype',filtered.length],['coverage','Coverage',gaps]] as [Pane,string,number][]).map(([id,lbl,n])=><button key={id} role="tab" aria-selected={pane===id} className={pane===id?'selected':''} onClick={()=>setPane(id)}>{lbl}<span>{n}</span></button>)}
  </div>

  {pane==='tracks'&&<>
   <div className="filterbar">
    <div className="search"><Search size={18}/><input aria-label="Search music library" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search titles, uses, instruments…"/></div>
    <select aria-label="Filter archetype family" value={parent} onChange={e=>{setParent(e.target.value);setArchetype('')}}><option value="">All families</option>{PARENT_ARCHETYPE_IDS.map(id=><option key={id} value={id}>{archetypeLabel(id)}</option>)}</select>
    <select aria-label="Filter archetype" value={archetype} onChange={e=>setArchetype(e.target.value)}><option value="">All archetypes</option>{[...(parent?[parent]:PARENT_ARCHETYPE_IDS),...SUB_ARCHETYPE_IDS.filter(id=>!parent||archInfo(id)?.parent_archetype===parent)].map(id=><option key={id} value={id}>{archetypeLabel(id)}</option>)}</select>
    <select aria-label="Filter game state" value={state} onChange={e=>setState(e.target.value)}><option value="">Any game state</option>{library.game_states.map(s=><option key={s} value={s}>{s}</option>)}</select>
    <select aria-label="Filter context" value={context} onChange={e=>setContext(e.target.value)}><option value="">Any context</option>{library.contexts.map(c=><option key={c} value={c}>{human(c)}</option>)}</select>
    <label className="inline related-toggle"><input type="checkbox" checked={includeRelated} onChange={e=>setIncludeRelated(e.target.checked)}/> Include related sounds</label>
    <button className="icon-button" title="Clear filters" aria-label="Clear music filters" onClick={clear}><SlidersHorizontal size={18}/></button>
   </div>
   {!grouped.length&&<div className="empty"><Music2 size={35}/><h2>No matching tracks</h2><p>Clear a filter, or add cues to the library and rebuild the index.</p></div>}
   {grouped.map(fam=><section className="ml-family" key={fam.parent} aria-label={`${archetypeLabel(fam.parent)} family`}>
    <div className="ml-family-head"><div className="eyebrow">{archetypeLabel(fam.parent)} family</div><small className="muted">{archInfo(fam.parent)?.genre}</small></div>
    {fam.groups.map(g=>{
     const info=archInfo(g.archetype);const cov=library.coverage.find(c=>c.archetype===g.archetype);const games=gamesByArch.get(g.archetype)||[];
     return <section className="panel ml-group" key={g.archetype}>
      <div className="section-heading tight">
       <div>
        <h2>{archetypeLabel(g.archetype)} {info?.parent_archetype&&<Pill>biome style</Pill>}</h2>
        <p className="muted small">{info?.genre} · {info?.mood} · {info?.bpm} BPM reference</p>
       </div>
       <div className="tag-list">
        <Pill tone="green">{g.tracks.length} track{g.tracks.length===1?'':'s'}</Pill>
        {cov&&cov.missing_states.length>0&&<Pill tone="warm">Missing: {cov.missing_states.join(', ')}</Pill>}
       </div>
      </div>
      {games.length>0&&<div className="ml-games"><small className="muted">Catalog games on this archetype:</small>{games.slice(0,8).map(r=><button key={r.game_id} className="link-button" onClick={()=>openGameMusic(r.game_id)}>{r.name}</button>)}{games.length>8&&<small className="muted">+{games.length-8} more</small>}</div>}
      <div className="ml-tracks">{g.tracks.map(t=><TrackRow key={t.id} t={t} root={library.library_root} native={native} copied={copied} onCopy={copy} filedUnder={g.archetype}/>)}</div>
     </section>;
    })}
   </section>)}
  </>}

  {pane==='coverage'&&<section className="panel">
   <div className="section-heading tight"><div><h2>Archetype × game-state coverage</h2><p className="muted small">Counts of primary library tracks per energy state. Empty cells are the next cues worth generating. Rebuild with <code>python tools/music_library.py build</code>.</p></div></div>
   <div className="ml-matrix" role="table" aria-label="Music library coverage">
    <div role="row" className="ml-row head"><span role="columnheader">Archetype</span>{library.game_states.map(s=><span role="columnheader" key={s}>{s}</span>)}<span role="columnheader">Related</span><span role="columnheader">Games</span></div>
    {library.coverage.map(c=><div role="row" className={'ml-row'+(c.archetype===c.parent_archetype?' parent':'')} key={c.archetype}>
     <span role="rowheader">{archetypeLabel(c.archetype)}</span>
     {library.game_states.map(s=>{const n=library.tracks.filter(t=>t.archetype===c.archetype&&t.status==='library'&&t.game_states.includes(s)).length;return <span role="cell" key={s} className={n?'have':'gap'}>{n||'—'}</span>})}
     <span role="cell">{c.related_tracks}</span>
     <span role="cell">{(gamesByArch.get(c.archetype)||[]).length}</span>
    </div>)}
   </div>
  </section>}
 </div>;
}

function TrackRow({t,root,native,copied,onCopy,filedUnder}:{t:LibraryTrack;root:string;native:boolean;copied:string;onCopy:(k:string,v:string)=>void;filedUnder:string}){
 const path=libraryFilePath(t,root);
 const r=t.review;
 return <div className="ml-track">
  <div className="ml-track-main">
   <div className="inline"><strong>{t.title}</strong><small className="muted">{t.id}</small>{t.archetype!==filedUnder&&<Pill tone="accent">related · {archetypeLabel(t.archetype)}</Pill>}</div>
   <small className="muted">{[t.use,formatDuration(t.duration_s),t.bpm_target?`${t.bpm_target} BPM`:'',t.world_flavor?human(t.world_flavor):'',t.vocals!=='none'?`${t.vocals} vocals`:''].filter(Boolean).join(' · ')}</small>
   <div className="tag-list">
    {t.game_states.map(s=><Pill key={s} tone="green">{s}</Pill>)}
    {t.contexts.filter(c=>!t.game_states.includes(c)).map(c=><Pill key={c}>{human(c)}</Pill>)}
    {t.secondary_archetypes.filter(a=>a!==filedUnder).map(a=><Pill key={a} tone="accent">+ {archetypeLabel(a)}</Pill>)}
   </div>
  </div>
  <div className="ml-track-side">
   {native?<audio controls preload="none" src={convertFileSrc(path)} aria-label={`Play ${t.title}`}/>:<small className="muted">Playback in the desktop app</small>}
   <div className="inline">
    {r&&<small className="muted" title={r.notes}>Review {r.brief_match??'–'}/{r.musicality??'–'}/{r.melody??'–'}</small>}
    {t.suno?.url&&<a className="button" href={t.suno.url} target="_blank" rel="noreferrer">Suno <ArrowUpRight size={13}/></a>}
    <button className="icon-button" aria-label={`Copy path for ${t.title}`} title="Copy file path" onClick={()=>onCopy(t.id,path)}>{copied===t.id?<Check size={14}/>:<Copy size={14}/>}</button>
    <button className="icon-button" aria-label={`Open folder for ${t.title}`} title="Open folder" disabled={!native} onClick={()=>void invoke('open_folder_for_path',{path})}><FolderOpen size={14}/></button>
   </div>
  </div>
 </div>;
}

/** Compact list for a game's Music tab: library cues that already fit its archetype. */
export function LibraryMatches({tracks,archetype,native,onBrowse}:{tracks:LibraryTrack[];archetype:string;native:boolean;onBrowse?:()=>void}){
 if(!archetype) return null;
 return <section className="panel ml-matches">
  <div className="section-heading tight">
   <div><div className="eyebrow">SHARED MUSIC LIBRARY</div><h2>{tracks.length} reusable cue{tracks.length===1?'':'s'} for {archetypeLabel(archetype)}</h2>
    <p className="muted small">Filed under this archetype first, then cues that list it as a related sound. Use them as extra region, menu or state tracks without generating new music.</p></div>
   {onBrowse&&<button onClick={onBrowse}>Open Music library <ArrowUpRight size={14}/></button>}
  </div>
  {tracks.length?<div className="ml-tracks">{tracks.slice(0,6).map(t=><div className="ml-track compact" key={t.id}>
   <div className="ml-track-main"><div className="inline"><strong>{t.title}</strong><small className="muted">{t.id} · {formatDuration(t.duration_s)}</small>{t.archetype!==archetype&&<Pill tone="accent">related</Pill>}</div>
    <div className="tag-list">{t.game_states.map(s=><Pill key={s} tone="green">{s}</Pill>)}{t.contexts.filter(c=>!t.game_states.includes(c)).map(c=><Pill key={c}>{human(c)}</Pill>)}</div></div>
   <div className="ml-track-side">{native?<audio controls preload="none" src={convertFileSrc(libraryFilePath(t))} aria-label={`Play ${t.title}`}/>:t.suno?.url?<a className="button" href={t.suno.url} target="_blank" rel="noreferrer">Suno <ArrowUpRight size={13}/></a>:null}</div>
  </div>)}{tracks.length>6&&<small className="muted">+{tracks.length-6} more in the Music library</small>}</div>
  :<p className="muted small">No library cues for this archetype yet. The Coverage view lists what to generate.</p>}
 </section>;
}
