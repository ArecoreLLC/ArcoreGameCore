import {describe,it,expect} from 'vitest';
import {MUSIC_LIBRARY,filterLibrary,groupByTaxonomy,libraryTracksForArchetype,libraryFilePath,formatDuration,type LibraryTrack} from '../src/musicLibrary';
import {ARCHETYPE_IDS,PARENT_ARCHETYPE_IDS,parentArchetypeFor} from '../src/music';

const t=(id:string,archetype:string,extra:Partial<LibraryTrack>={}):LibraryTrack=>({id,title:id,file:`${id}.mp3`,folder:'f',path:`f/${id}.mp3`,archetype,parent_archetype:parentArchetypeFor(archetype),secondary_archetypes:[],game_states:['explore'],contexts:[],vocals:'none',status:'library',...extra});

describe('shared music library index',()=>{
 it('only uses archetypes and game states from the adaptive-music taxonomy',()=>{
  expect(MUSIC_LIBRARY.tracks.length).toBeGreaterThan(0);
  for(const tr of MUSIC_LIBRARY.tracks){
   expect(ARCHETYPE_IDS).toContain(tr.archetype as never);
   expect(tr.parent_archetype).toBe(parentArchetypeFor(tr.archetype));
   tr.secondary_archetypes.forEach(a=>expect(ARCHETYPE_IDS).toContain(a as never));
   tr.game_states.forEach(s=>expect(MUSIC_LIBRARY.game_states).toContain(s));
  }
  expect(MUSIC_LIBRARY.coverage.map(c=>c.archetype).sort()).toEqual([...ARCHETYPE_IDS].sort());
  expect(new Set(MUSIC_LIBRARY.tracks.map(x=>x.id)).size).toBe(MUSIC_LIBRARY.tracks.length);
 });

 it('groups tracks family-first in taxonomy order',()=>{
  const groups=groupByTaxonomy([t('a','nautical-folk'),t('b','cozy'),t('c','horror')]);
  expect(groups.map(g=>g.parent)).toEqual(PARENT_ARCHETYPE_IDS.filter(p=>p==='cozy'||p==='horror'));
  expect(groups.find(g=>g.parent==='cozy')!.groups.map(g=>g.archetype)).toEqual(['cozy','nautical-folk']);
 });

 it('filters by family, archetype, state, context and text, optionally including related sounds',()=>{
  const tracks=[t('a','cozy',{contexts:['town']}),t('b','horror',{secondary_archetypes:['cozy'],game_states:['tension']}),t('c','nautical-folk',{use:'pirate sailing'}),t('d','cozy',{status:'retired'})];
  expect(filterLibrary(tracks,{archetype:'cozy'}).map(x=>x.id)).toEqual(['a']);
  expect(filterLibrary(tracks,{archetype:'cozy',includeRelated:true}).map(x=>x.id)).toEqual(['a','b']);
  expect(filterLibrary(tracks,{parent:'cozy'}).map(x=>x.id)).toEqual(['a','c']);
  expect(filterLibrary(tracks,{state:'tension'}).map(x=>x.id)).toEqual(['b']);
  expect(filterLibrary(tracks,{context:'town'}).map(x=>x.id)).toEqual(['a']);
  expect(filterLibrary(tracks,{query:'PIRATE'}).map(x=>x.id)).toEqual(['c']);
 });

 it('lists reusable cues for a game archetype, primary matches first',()=>{
  const tracks=[t('rel','horror',{secondary_archetypes:['cozy']}),t('main','cozy'),t('old','cozy',{status:'retired'})];
  expect(libraryTracksForArchetype('cozy',tracks).map(x=>x.id)).toEqual(['main','rel']);
  expect(libraryTracksForArchetype('',tracks)).toEqual([]);
 });

 it('builds absolute file paths and readable durations',()=>{
  expect(libraryFilePath(t('a','cozy'),'X:/Lib/')).toBe('X:/Lib/f/a.mp3');
  expect(formatDuration(224.88)).toBe('3:45');
  expect(formatDuration(239.8)).toBe('4:00');
  expect(formatDuration(undefined)).toBe('');
 });
});
