import type {Game,Library,MusicDesignRecord,Taxon} from './types';
import type {RoadmapGame} from './roadmap';
import {mainGenreById,subGenreById,ORTHOGONAL_FACETS} from './genreTaxonomy';
import {ARCHETYPES,parentArchetypeFor,subArchetypeFor} from './music';

export const GAME_EXPORT_FORMAT='gamecore.games-export';
export type ExportSource='catalog'|'pipeline';

const clean=(v:unknown)=>typeof v==='string'?v.trim():v;
const present=(v:unknown)=>v!==undefined&&v!==null&&!(typeof v==='string'&&!v.trim())&&!(Array.isArray(v)&&!v.length);
/** Drop empty strings/arrays so exports stay compact and readable. */
function compact<T extends Record<string,unknown>>(o:T):Partial<T>{return Object.fromEntries(Object.entries(o).map(([k,v])=>[k,clean(v)]).filter(([,v])=>present(v))) as Partial<T>}

function genreBlock(genre?:string,sub?:string){
 const main=mainGenreById(genre),s=subGenreById(sub);
 const parent=s?.parent_genre&&s.parent_genre!==genre?mainGenreById(s.parent_genre):undefined;
 const m=main||parent;
 return compact({main:m?{id:m.id,label:m.label}:genre?{id:genre,label:genre}:undefined,sub:s?{id:s.id,label:s.label}:sub?{id:sub,label:sub}:undefined});
}

function taxonRef(t:Taxon|undefined,id:string){return t?compact({id,label:t.label,family:t.family,group:t.group,level:t.level,parent_id:t.parent_id}):{id,label:id,family:'unknown'}}

function musicBlock(rec?:MusicDesignRecord):Record<string,string|number|undefined>|undefined{
 if(!rec) return undefined;
 const eff=rec.archetype||rec.recommended_archetype||'';
 if(!eff) return compact({status:rec.status});
 const info=(ARCHETYPES as Record<string,{genre:string;bpm:number;mood:string}>)[eff];
 return compact({archetype:eff,parent_archetype:parentArchetypeFor(eff),sub_archetype:subArchetypeFor(eff),music_genre:info?.genre,bpm:info?.bpm,mood:info?.mood,setting:rec.setting||rec.recommended_setting,status:rec.status});
}

/** Free-text placeholders ("Not measured", "See project README…") stay in `classification` but are not tags. */
const PLACEHOLDER=/^(not |see |unknown|unclassified|n\/a|none|tbd)/i;
const isTagValue=(v:unknown)=>{const t=typeof v==='string'?v.trim():'';return !!t&&t.length<=40&&!PLACEHOLDER.test(t)};
const slug=(s:string)=>s.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
/** Flat, de-duplicated "namespace:value" tags for search, filters or other tools. */
function tagList(groups:Record<string,(string|undefined|null)[]>){
 const out=new Set<string>();
 for(const [ns,values] of Object.entries(groups)) for(const v of values) if(isTagValue(v)) out.add(`${ns}:${slug(String(v))}`);
 return [...out];
}

const facetKeys=()=>Object.keys(ORTHOGONAL_FACETS as Record<string,unknown>);

export function catalogGameExport(g:Game,lib:Library,music?:MusicDesignRecord){
 const tax=(id:string)=>lib.taxonomy.find(t=>t.id===id);
 const cl=g.classification||{};
 const facets=compact(Object.fromEntries(Object.entries(cl).filter(([k])=>k!=='genre'&&k!=='sub_genre')));
 const capIds=[...new Set([...g.capabilities.map(c=>c.id),...g.mechanics.map(m=>m.capability).filter(Boolean)])];
 const mus=musicBlock(music);
 return {
  id:g.id,name:g.name,source:'catalog' as const,
  overview:compact({tagline:g.marketing?.tagline,description:g.description,pitch:g.marketing?.pitch,audience:g.marketing?.audience,engine:g.engine,dimension:g.dimension,kind:g.kind,maturity:g.maturity,release_status:g.marketing?.release_status,build_status:g.build_status,playtest_status:g.playtest_status,languages:g.languages,path:g.path,core_logic:g.logic,limitations:g.limitations,subgames:g.subgames?.map(s=>s.name)}),
  genre:genreBlock(cl.genre,cl.sub_genre),
  classification:facets,
  mechanics:g.mechanics.map(m=>compact({id:m.id,name:m.name,capability:m.capability,capability_label:tax(m.capability)?.label,state:m.state,rules:m.rules,reuse_boundary:m.reuse_boundary})),
  capabilities:g.capabilities.map(c=>({...taxonRef(tax(c.id),c.id),state:c.state})),
  taxonomy:capIds.map(id=>taxonRef(tax(id),id)),
  music:mus,
  modules:g.module_keys||[],
  tags:tagList({
   genre:[cl.genre],'sub-genre':[cl.sub_genre],
   ...Object.fromEntries(Object.entries(facets).map(([k,v])=>[k.replaceAll('_','-'),[String(v)]])),
   engine:[g.engine.split(' / ')[0].split(' ')[0]],'engine-version':[g.engine.split(' / ')[0]],dimension:[g.dimension],kind:[g.kind],maturity:[g.maturity],
   language:g.languages||[],module:g.module_keys||[],
   family:capIds.map(id=>tax(id)?.family),group:capIds.map(id=>tax(id)?.group),
   capability:capIds,mechanic:g.mechanics.map(m=>m.name),
   archetype:[mus?.archetype as string|undefined,mus?.parent_archetype as string|undefined],
  }),
 };
}

export function pipelineGameExport(g:RoadmapGame,lib:Library,music?:MusicDesignRecord){
 const tax=(id:string)=>lib.taxonomy.find(t=>t.id===id);
 const stage=(id:string)=>g.first_slice_capabilities.includes(id)?'first_slice':g.later_capabilities.includes(id)?'later':'unstaged';
 const facets=compact({perspective:g.perspective,networking:g.networking,scale_density:g.scale_density,art_pipeline:g.art_pipeline});
 const mus=musicBlock(music);
 return {
  id:g.id,name:g.title,source:'pipeline' as const,
  overview:compact({pitch:g.pitch,creative_direction:g.creative_direction,visual_direction:g.visual_direction,creative_scope:g.creative_scope,priority:g.priority,wave:g.wave,status:g.status,owner:g.owner,preferred_runtime:g.preferred_runtime,technical_risk:g.technical_risk,priority_reason:g.priority_reason,acceptance:g.acceptance,reusable_outputs:g.reusable_outputs,depends_on:g.depends_on,donor_projects:g.donors.map(d=>d.project_id)}),
  genre:genreBlock(g.genre,g.sub_genre),
  classification:facets,
  /** Planned games have no documented mechanics yet; their target capabilities stand in, staged and with progress. */
  mechanics:g.capability_ids.map(id=>compact({capability:id,name:tax(id)?.label||id,stage:stage(id),state:g.target_progress[id]?.state||'planned',description:tax(id)?.description})),
  capabilities:g.capability_ids.map(id=>({...taxonRef(tax(id),id),stage:stage(id),state:g.target_progress[id]?.state||'planned'})),
  taxonomy:g.capability_ids.map(id=>taxonRef(tax(id),id)),
  music:mus,
  modules:[] as string[],
  tags:tagList({
   genre:[g.genre],'sub-genre':[g.sub_genre],
   ...Object.fromEntries(Object.entries(facets).map(([k,v])=>[k.replaceAll('_','-'),[String(v)]])),
   runtime:[g.preferred_runtime],risk:[g.technical_risk],wave:[String(g.wave)],status:[g.status],
   family:g.capability_ids.map(id=>tax(id)?.family),group:g.capability_ids.map(id=>tax(id)?.group),
   capability:g.capability_ids,
   archetype:[mus?.archetype as string|undefined,mus?.parent_archetype as string|undefined],
  }),
 };
}

type ExportedGame=ReturnType<typeof catalogGameExport>|ReturnType<typeof pipelineGameExport>;

export function gamesExportDocument(source:ExportSource,games:ExportedGame[],lib:Library,meta:{scope:'filtered'|'all'|'selected';filters?:Record<string,string>;total:number}){
 const ids=new Set(games.flatMap(g=>g.taxonomy.map(t=>t.id)));
 const genres=new Set(games.map(g=>g.genre.main?.id).filter(Boolean));
 return {
  format:GAME_EXPORT_FORMAT,schema_version:1,exported_at:new Date().toISOString(),source,
  scope:{...meta,filters:meta.filters?compact(meta.filters):undefined,exported:games.length},
  summary:{games:games.length,genres:[...genres],unique_capabilities:ids.size,mechanics:games.reduce((n,g)=>n+g.mechanics.length,0)},
  taxonomy_definitions:lib.taxonomy.filter(t=>ids.has(t.id)).map(t=>compact({id:t.id,label:t.label,family:t.family,group:t.group,level:t.level,parent_id:t.parent_id,description:t.description})),
  classification_facets:Object.fromEntries(facetKeys().map(k=>[k,(ORTHOGONAL_FACETS as Record<string,unknown>)[k]])),
  games,
 };
}

export function exportFileName(source:ExportSource,scope:string){return `gamecore-${source}-${scope}-${new Date().toISOString().slice(0,10)}.json`}
