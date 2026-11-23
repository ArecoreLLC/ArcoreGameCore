import libraryDoc from '../data/music-library/index.json';
import {ARCHETYPES,PARENT_ARCHETYPE_IDS,parentArchetypeFor} from './music';

/** One reusable cue from the shared music library (tools/music_library.py → hub/data/music-library/index.json). */
export interface LibraryTrack{
 id:string;
 title:string;
 file:string;
 folder:string;
 path:string;
 format?:string;
 duration_s?:number;
 bpm_target?:number;
 archetype:string;
 parent_archetype:string;
 secondary_archetypes:string[];
 game_states:string[];
 contexts:string[];
 world_flavor?:string|null;
 vocals:string;
 loopable?:boolean;
 use?:string;
 style_prompt?:string;
 status:string;
 suno?:{clip_id:string;url:string;alternate_clip_id?:string;model?:string;generated_on?:string};
 review?:{method?:string;brief_match?:number|null;musicality?:number|null;melody?:number|null;notes?:string};
 rights_note?:string;
}
export interface LibraryCoverage{archetype:string;parent_archetype:string;primary_tracks:number;related_tracks:number;missing_states:string[]}
export interface LibraryFolder{folder:string;label:string;description:string;track_count:number}
export interface MusicLibraryIndex{
 schema:string;
 generated_at:string;
 library_root:string;
 game_states:string[];
 contexts:string[];
 families:{archetype:string;sub_archetypes:string[]}[];
 folders:LibraryFolder[];
 coverage:LibraryCoverage[];
 tracks:LibraryTrack[];
}

export const MUSIC_LIBRARY = libraryDoc as unknown as MusicLibraryIndex;

export interface LibraryFilter{query?:string;parent?:string;archetype?:string;state?:string;context?:string;includeRelated?:boolean}

/** True when the track is filed under the archetype, or (with includeRelated) lists it as a secondary sound. */
export function trackMatchesArchetype(t:LibraryTrack, archetype:string, includeRelated=true):boolean{
 return t.archetype===archetype || (includeRelated && t.secondary_archetypes.includes(archetype));
}

export function filterLibrary(tracks:LibraryTrack[], f:LibraryFilter):LibraryTrack[]{
 const q=(f.query||'').trim().toLowerCase();
 return tracks.filter(t=>{
  if(t.status==='retired') return false;
  if(f.archetype && !trackMatchesArchetype(t,f.archetype,Boolean(f.includeRelated))) return false;
  if(!f.archetype && f.parent && t.parent_archetype!==f.parent && !(f.includeRelated && t.secondary_archetypes.some(s=>parentArchetypeFor(s)===f.parent))) return false;
  if(f.state && !t.game_states.includes(f.state)) return false;
  if(f.context && !t.contexts.includes(f.context)) return false;
  if(q){
   const hay=[t.id,t.title,t.use,t.folder,t.archetype,t.world_flavor,t.style_prompt,...t.contexts].filter(Boolean).join(' ').toLowerCase();
   if(!hay.includes(q)) return false;
  }
  return true;
 });
}

/** Tracks grouped family → archetype (parent first, then its biome styles), in taxonomy order. */
export function groupByTaxonomy(tracks:LibraryTrack[]):{parent:string;groups:{archetype:string;tracks:LibraryTrack[]}[]}[]{
 return PARENT_ARCHETYPE_IDS.map(parent=>{
  const ids=[parent,...Object.keys(ARCHETYPES).filter(a=>(ARCHETYPES as Record<string,{parent_archetype?:string}>)[a].parent_archetype===parent)];
  return {parent,groups:ids.map(archetype=>({archetype,tracks:tracks.filter(t=>t.archetype===archetype)})).filter(g=>g.tracks.length)};
 }).filter(f=>f.groups.length);
}

/** Library cues a catalog game can reuse: filed under its archetype first, then ones listing it as a secondary sound. */
export function libraryTracksForArchetype(archetype:string, tracks:LibraryTrack[]=MUSIC_LIBRARY.tracks):LibraryTrack[]{
 if(!archetype) return [];
 const live=tracks.filter(t=>t.status!=='retired');
 return [...live.filter(t=>t.archetype===archetype),...live.filter(t=>t.archetype!==archetype&&t.secondary_archetypes.includes(archetype))];
}

export function libraryFilePath(t:LibraryTrack, root=MUSIC_LIBRARY.library_root):string{
 return `${root.replace(/[\\/]+$/,'')}/${t.path}`;
}

export function formatDuration(s?:number):string{
 if(!s && s!==0) return '';
 const total=Math.round(s), m=Math.floor(total/60), r=total%60;
 return `${m}:${String(r).padStart(2,'0')}`;
}
