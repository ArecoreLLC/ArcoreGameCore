import React,{useEffect,useState} from 'react';
import {invoke,isTauri} from '@tauri-apps/api/core';
import type {Game,Taxon} from './types';
import {LANGUAGES,REUSE,examplesFromGuide,type ModuleEntry,type ModuleResults} from './moduleCatalog';
import './modules.css';

export default function ModulesView({taxonomy,games,onTagged}:{taxonomy:Taxon[];games:Game[];onTagged:()=>Promise<void>}){
 const [query,setQuery]=useState(''),[language,setLanguage]=useState(''),[capability,setCapability]=useState(''),[reuse,setReuse]=useState(''),[offset,setOffset]=useState(0);
 const [results,setResults]=useState<ModuleResults|null>(null),[loading,setLoading]=useState(false),[error,setError]=useState(''),[retry,setRetry]=useState(0);
 const [key,setKey]=useState(''),[detail,setDetail]=useState<ModuleEntry|null>(null),[guide,setGuide]=useState(''),[detailError,setDetailError]=useState(''),[detailLoading,setDetailLoading]=useState(false);
 const [gameId,setGameId]=useState(''),[saving,setSaving]=useState(false),[tagNotice,setTagNotice]=useState('');
 useEffect(()=>{
  let cancelled=false;setLoading(true);setError('');
  const timer=setTimeout(()=>{
   if(!isTauri()){setError('Open the desktop app to browse the current module catalogs.');setLoading(false);return;}
   invoke<ModuleResults>('search_modules',{arguments:{...(query?{query}:{}),...(language?{language}:{}),...(capability?{capability}:{}),...(reuse?{reuse}:{}),offset,limit:12}})
    .then(value=>{if(!cancelled)setResults(value)}).catch(e=>{if(!cancelled)setError(String(e))}).finally(()=>{if(!cancelled)setLoading(false)});
  },180);
  return()=>{cancelled=true;clearTimeout(timer)};
 },[query,language,capability,reuse,offset,retry]);
 useEffect(()=>{
  let cancelled=false;setDetail(null);setGuide('');setDetailError('');setTagNotice('');
  if(!key)return;setDetailLoading(true);
  (async()=>{
   try{
    const value=await invoke<ModuleResults>('search_modules',{arguments:{key,details:true}});
    if(cancelled)return;setDetail(value.entries[0]||null);
    const text=await invoke<string>('module_guide',{key});if(!cancelled)setGuide(text);
   }catch(e){if(!cancelled)setDetailError(String(e))}finally{if(!cancelled)setDetailLoading(false)}
  })();return()=>{cancelled=true};
 },[key]);
 const label=(id:string)=>taxonomy.find(t=>t.id===id)?.label||id;
 const linked=games.find(g=>g.id===gameId)?.module_keys?.includes(key)||false;
 async function tag(){setSaving(true);setTagNotice('');try{await invoke('tag_game_module',{projectId:gameId,key,add:!linked});await onTagged();setTagNotice(linked?'Module tag removed. Language tags retained.':'Module and language tags saved.')}catch(e){setTagNotice(String(e))}finally{setSaving(false)}}
 const source=detail?.source_entry;
 return <section className="module-browser">
  <h1>Modules</h1><p>Find shared code, inspect examples, and understand what stays in the game.</p>
  <div className="module-filters">
   <label>Search modules<input aria-label="Search modules" placeholder="Terrain, painting, cues…" value={query} onChange={e=>{setQuery(e.target.value);setOffset(0)}}/></label>
   <label>Language<select aria-label="Module language" value={language} onChange={e=>{setLanguage(e.target.value);setOffset(0)}}><option value="">All languages</option>{['cpp','csharp','gdscript','python'].map(id=><option key={id} value={id}>{LANGUAGES[id]}</option>)}</select></label>
   <label>Capability<select aria-label="Module capability" value={capability} onChange={e=>{setCapability(e.target.value);setOffset(0)}}><option value="">All capabilities</option>{results?.capabilities.map(id=><option key={id} value={id}>{label(id)}</option>)}</select></label>
   <label>Reuse status<select aria-label="Module reuse status" value={reuse} onChange={e=>{setReuse(e.target.value);setOffset(0)}}><option value="">All statuses</option>{Object.entries(REUSE).map(([id,label])=><option key={id} value={id}>{label}</option>)}</select></label>
   <button onClick={()=>{setQuery('');setLanguage('');setCapability('');setReuse('');setOffset(0)}}>Clear module filters</button>
  </div>
  <p className="muted">Reusable source still needs consumer testing. Legacy and game-specific entries are not ready-to-install modules. Capability coverage is partial; unclassified modules appear under All capabilities.</p>
  {error?<div role="alert">{error} <button onClick={()=>setRetry(v=>v+1)}>Retry search</button></div>:<>
   <p role="status">{loading?'Searching…':`${results?.total||0} modules`}</p>
   <div className="module-layout"><div aria-busy={loading}>
    <div className="module-cards">{!loading&&results?.entries.map(entry=><button className={'module-card '+(key===entry.key?'chosen':'')} key={entry.key} onClick={()=>setKey(entry.key)}>
     <span className={'module-status '+entry.reuse}>{REUSE[entry.reuse]}</span><h2>{entry.name}</h2><span>{entry.languages.map(l=>LANGUAGES[l]||l).join(' · ')} · {entry.engine}</span><small>{entry.capability_ids.map(label).join(' · ')||'Capability not classified'}</small><small>{entry.state} · {entry.key}</small>
    </button>)}</div>
    {!loading&&results?.total===0&&<p>No modules match these filters. Try a broader search or clear filters.</p>}
    <div className="module-pages"><button disabled={loading||offset===0} onClick={()=>setOffset(Math.max(0,offset-12))}>Previous modules</button><span>Page {Math.floor(offset/12)+1}</span><button disabled={loading||results?.next_offset==null} onClick={()=>setOffset(results!.next_offset!)}>Next modules</button></div>
   </div>
   <aside className="module-detail" aria-label="Module details">
    {!key?<p>Select a module to see its boundary, examples and game references.</p>:<>
     {detailLoading&&<p role="status">Loading module details…</p>}
     {detail&&<><span className={'module-status '+detail.reuse}>{REUSE[detail.reuse]}</span><h2>{detail.name}</h2><code>{detail.key}</code>
      <h3>Reuse boundary</h3><p>{source?.limitations||source?.validation_note||'Review the guide and consumer tests before adoption.'}</p><p>Version: {source?.version||source?.bundle_version||'Not recorded'} · State: {detail.state}</p>
      {source?.review_decision&&<p>Review decision: {source.review_decision}</p>}
      <h3>Source and consumer examples</h3>{[...(source?.files||[]),...(source?.source?[source.source]:[]),...(source?.consumer_paths||[]),...(source?.tests||[])].map(path=><div className="module-path" key={path}>{path}</div>)}
      <p>Source projects: {detail.source_project_ids.map(id=>games.find(g=>g.id===id)?.name||id).join(', ')||'See module guide'}</p>
      <h3>Examples from the guide</h3>{examplesFromGuide(guide).map((example,i)=><div key={i}><small>{example.language||'Example'}</small><pre>{example.code}</pre></div>)}
      {!detailLoading&&guide&&!examplesFromGuide(guide).length&&<p>No inline code example is recorded. See the source references and guide below.</p>}
      <details><summary>Read module guide · {detail.guide}</summary><pre className="module-guide">{guide}</pre></details>
      <h3>Game catalog tags</h3><p>Link a game for discovery. This records a reference, not an installed or verified dependency.</p>
      <label>Game to tag<select aria-label="Game to tag" value={gameId} onChange={e=>{setGameId(e.target.value);setTagNotice('')}}><option value="">Choose a game</option>{games.map(g=><option value={g.id} key={g.id}>{g.name}</option>)}</select></label>
      <button disabled={!gameId||saving} onClick={tag}>{saving?'Saving…':linked?'Remove module tag':'Add module tag'}</button><p role="status">{tagNotice}</p>
      <p>Tagged games: {games.filter(g=>g.module_keys?.includes(key)).map(g=>g.name).join(', ')||'None yet'}</p>
     </>}{detailError&&<p role="alert">{detailError}</p>}
    </>}
   </aside></div>
  </>}
 </section>;
}
