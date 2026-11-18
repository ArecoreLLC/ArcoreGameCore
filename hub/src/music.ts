import type {MusicDesignRecord,MusicTrack} from './types';
import archetypesDoc from '../../workflows/adaptive-music-stems/archetypes.json';

export const ARCHETYPE_IDS = Object.keys(archetypesDoc.archetypes) as (keyof typeof archetypesDoc.archetypes)[];
export const ARCHETYPES = archetypesDoc.archetypes;
export const PARENT_ARCHETYPE_IDS = ARCHETYPE_IDS.filter(id => !(ARCHETYPES[id] as {parent_archetype?:string}).parent_archetype);
export const SUB_ARCHETYPE_IDS = ARCHETYPE_IDS.filter(id => Boolean((ARCHETYPES[id] as {parent_archetype?:string}).parent_archetype));
export function parentArchetypeFor(archId:string|null|undefined):string{
 if(!archId) return '';
 const info = (ARCHETYPES as Record<string, {parent_archetype?:string}>)[archId];
 return info?.parent_archetype || archId;
}
export function subArchetypeFor(archId:string|null|undefined):string{
 if(!archId) return '';
 const info = (ARCHETYPES as Record<string, {parent_archetype?:string}>)[archId];
 return info?.parent_archetype ? archId : '';
}
export function archetypeLabel(id:string):string{
 return id.split('-').map(w=>w.charAt(0).toUpperCase()+w.slice(1)).join(' ');
}
export function matchesArchetypeFilter(effArch:string|null|undefined, parentFilter:string, subFilter:string):boolean{
 if(subFilter) return effArch === subFilter;
 if(parentFilter) return parentArchetypeFor(effArch) === parentFilter;
 return true;
}
export const SUNO_STANDARD_OPTIONS = archetypesDoc.suno_standard_options;
export const SUNO_BETA_OPTIONS = archetypesDoc.suno_beta_options;
export const SUNO_STEMS = archetypesDoc.suno_stem_categories;
export const SECTIONS = archetypesDoc.sections;

const BPM_STEPS = [0, -8, 10];
const VARIANTS = [
 ['A', 'main theme', 'memorable repeating melodic motif'],
 ['B', 'alternate region', 'different key, blended sub-archetype palette, new motif'],
 ['C', 'late-game variation', 'darker harmony, hybrid escalation palette, motif reprised'],
] as const;

const V2_SUBCATEGORY_BLENDS:Record<string,[string,string,string]> = {
 'cozy': ['nautical-folk', 'storybook-orchestral', 'cosmic-ambient'],
 'nautical-folk': ['storybook-orchestral', 'modern-tactics', 'noir-mystery'],
 'lofi-workshop': ['nautical-folk', 'neon-synthfunk', 'storybook-orchestral'],
 'storybook-orchestral': ['lofi-workshop', 'cosmic-ambient', 'medieval-siege'],
 'dark-fantasy': ['medieval-siege', 'cosmic-ambient', 'mech-industrial'],
 'medieval-siege': ['storybook-orchestral', 'modern-tactics', 'dark-fantasy'],
 'cosmic-ambient': ['noir-mystery', 'mech-industrial', 'dark-fantasy'],
 'cyberpunk': ['neon-synthfunk', 'mech-industrial', 'modern-tactics'],
 'neon-synthfunk': ['lofi-workshop', 'retro-chiptune-rock', 'mech-industrial'],
 'mech-industrial': ['neon-synthfunk', 'modern-tactics', 'horror'],
 'arcade': ['retro-chiptune-rock', 'neon-synthfunk', 'mech-industrial'],
 'retro-chiptune-rock': ['neon-synthfunk', 'mech-industrial', 'modern-tactics'],
 'horror': ['noir-mystery', 'cosmic-ambient', 'mech-industrial'],
 'noir-mystery': ['lofi-workshop', 'mech-industrial', 'dark-fantasy'],
 'action-rock': ['modern-tactics', 'mech-industrial', 'retro-chiptune-rock'],
 'modern-tactics': ['mech-industrial', 'medieval-siege', 'noir-mystery'],
};

export function generateTracksForArchetype(gameId:string, gameName:string, archetypeId:string, setting:string, existing:MusicTrack[]=[], count=3):MusicTrack[]{
 const archMap = ARCHETYPES as Record<string, typeof ARCHETYPES['cozy']>;
 const arch = archMap[archetypeId];
 if(!arch) return existing;
 const result:MusicTrack[] = [];
 const blend = V2_SUBCATEGORY_BLENDS[archetypeId];
 for(let i=0;i<count;i++){
  const [letter,label,motif] = VARIANTS[i % VARIANTS.length];
  const tid = `${gameId}-${letter}`;
  const prev = existing.find(t=>t.track_id===tid);
  if(prev && (prev.suno?.url || prev.status !== 'prompt_ready')){
   result.push(prev);
   continue;
  }
  const varArch = (i===1 && blend && archMap[blend[0]]) ? archMap[blend[0]] : (i===2 && blend && archMap[blend[1]]) ? archMap[blend[1]] : arch;
  const accentArch = (i===2 && blend && archMap[blend[2]]) ? archMap[blend[2]] : undefined;
  const bpm = (i>0 && varArch!==arch) ? varArch.bpm : arch.bpm + BPM_STEPS[i % BPM_STEPS.length];
  const instNames = [...varArch.instruments.map(x=>x.name)];
  if(accentArch){
   for(const ai of accentArch.instruments){
    if(!instNames.includes(ai.name) && instNames.length < 7) instNames.push(ai.name);
   }
  }
  const genreText = accentArch ? `${varArch.genre} blended with ${accentArch.genre}` : varArch.genre;
  const settingPart = setting.trim() ? `, ${setting.trim()} atmosphere` : '';
  const style = `${genreText}, clean mix, dry studio recording, minimalist frequency separation, ${varArch.mood}${settingPart}, ${instNames.join(', ')}, ${bpm} BPM, strict quantize, steady 4/4 rhythm, ${motif}, instrumental`;
  const cues = varArch.section_cues as Record<string,string>;
  const bassInst = varArch.instruments.find(x=>x.name.includes('Bass') || x.name==='808')?.name || varArch.instruments[0]?.name || 'Bass';
  const lyrics = [
   '[Instrumental]',
   `[Tempo: ${bpm} BPM, strict quantize, steady rhythm]`,
   '',
   '[Intro - Bass Stem Only]',
   `[Deep pulsing ${bassInst}, clean low-end drone, minimal]`,
   '',
   '[Part 1 - Add Percussion Stem]',
   `[${cues['[Verse 1 - Exploration Layer]'] || 'Crisp dry percussion and rhythm layer'}, steady 4/4 rhythm]`,
   '',
   '[Part 2 - Add Melody Stem]',
   `[${cues['[Pre-Chorus - Tension Build]'] || 'Sharp melodic ostinato'}, high frequency separation, dry studio]`,
   '',
   '[Part 3 - Add Combat & Climax Layer]',
   `[${cues['[Chorus - Combat Layer]'] || 'Full tactical intensity'}; ${cues['[Bridge - Danger / Boss State]'] || 'tight separated stabs'}]`,
   '',
   '[Outro - Strip Back]',
   '[Sub-bass pulse and distant percussion fade out]',
  ].join('\n');
  const keepStems = [...new Set(varArch.instruments.filter(x=>x.core).map(x=>x.stem))].sort();
  result.push({
   track_id: tid,
   title: `${gameName} - ${label}`,
   status: 'prompt_ready',
   vocals: prev?.vocals || 'none',
   bpm,
   style_prompt: style,
   lyrics: prev?.vocals === 'sung' && prev.lyrics ? prev.lyrics : lyrics,
   instruments: varArch.instruments.map(x=>({name:x.name, stem:x.stem, keep:x.core})),
   stems_requested: keepStems,
   states: SECTIONS.map(s=>({state:s.state, section:s.tag})),
   suno: prev?.suno || {url:'', clip_id:'', model:'', generated_at:''},
   files: prev?.files || [],
   notes: prev?.notes || '',
  });
 }
 return result;
}

export function applyArchetypeToRecord(rec:MusicDesignRecord, archetypeId:string, setting:string, approve=true):MusicDesignRecord{
 const tracks = generateTracksForArchetype(rec.game_id, rec.name, archetypeId, setting, rec.tracks, 3);
 return {
  ...rec,
  archetype: archetypeId,
  setting,
  // Approving is a decision: it records `approved`. Work already under way keeps `in_progress`.
  status: approve ? (rec.status === 'in_progress' ? rec.status : 'approved') : rec.status,
  tracks,
  updated_at: new Date().toISOString(),
 };
}

/** Production progress, separate from the approval decision held in `status`. */
export function pipelineStage(r:MusicDesignRecord):string{
 if(r.status === 'excluded') return 'excluded';
 const t0 = r.tracks[0];
 const suno = t0?.suno;
 if(suno?.in_game_status === 'wired_in_engine') return 'wired_in_engine';
 if(t0?.status === 'stems_split' || Boolean(suno?.stem_group_id)) return 'stems_split';
 if(t0?.status === 'generated' || Boolean(suno?.analysis) || Boolean(suno?.clip_id)) return 'generated';
 return 'prompt_ready';
}

export type MediaCategory = 'all' | 'image' | 'video' | 'music' | 'branding' | 'sfx';

export function mediaCategoryForKind(kind:string, contentRole=''):MediaCategory{
 if(kind==='logo' || kind==='icon' || kind==='marketing' || contentRole==='branding' || contentRole==='logo' || contentRole==='icon') return 'branding';
 if(kind==='music') return 'music';
 if(kind==='sfx') return 'sfx';
 if(kind==='video' || kind==='trailer') return 'video';
 return 'image';
}

export function indexedAssetCategory(path:string):MediaCategory | null{
 const lower = path.toLowerCase();
 const ext = lower.slice(lower.lastIndexOf('.'));
 if(['.wav','.ogg','.mp3','.flac','.m4a'].includes(ext)){
  if(/music|song|bgm|theme|ost|shanty|chorus|stems|adaptive/i.test(lower)) return 'music';
  return 'sfx';
 }
 if(['.mp4','.webm','.mov'].includes(ext)) return 'video';
 if(['.png','.jpg','.jpeg','.webp','.svg','.ico'].includes(ext)){
  if(/logo|icon|banner|capsule|keyart|marketing|cover|brand|splash/i.test(lower)) return 'branding';
  return 'image';
 }
 return null;
}
