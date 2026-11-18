import {describe,it,expect} from 'vitest';
import {ARCHETYPE_IDS,generateTracksForArchetype,applyArchetypeToRecord,mediaCategoryForKind,indexedAssetCategory} from '../src/music';
import seedRecords from '../data/music-design/index.json';
import type {MusicDesignRecord} from '../src/types';

const records = seedRecords as unknown as MusicDesignRecord[];

describe('music design recommendations and adaptive prompt generation',()=>{
 it('covers all 31 catalog games and 50 roadmap tracks (81 total)',()=>{
  expect(records).toHaveLength(81);
  expect(records.filter(r=>r.scope==='catalog')).toHaveLength(31);
  expect(records.filter(r=>r.scope==='roadmap')).toHaveLength(50);
  expect(records.filter(r=>r.status==='excluded')).toHaveLength(5);
  // Records move through statuses as work proceeds; every status must be valid and
  // non-excluded records keep a recommendation to fall back on.
  const valid=['unassigned','recommended','excluded','planned','in_progress','approved'];
  expect(records.every(r=>valid.includes(r.status))).toBe(true);
  expect(records.filter(r=>r.status!=='excluded').every(r=>Boolean(r.recommended_archetype))).toBe(true);
 });

 it('generates 3 adaptive tracks with explicit instruments and valid Suno stems',()=>{
  const tracks = generateTracksForArchetype('test-game','Test Game','cyberpunk','neon grid',[],3);
  expect(tracks).toHaveLength(3);
  expect(tracks[0].style_prompt).toContain('neon grid atmosphere');
  expect(tracks[0].style_prompt).toContain('Synth Bass');
  expect(tracks[0].style_prompt).toContain('Synth Pad');
  // Lyrics build the arrangement one stem at a time so Suno's split stays clean.
  expect(tracks[0].lyrics).toContain('[Instrumental]');
  expect(tracks[0].lyrics).toContain('[Intro - Bass Stem Only]');
  expect(tracks[0].lyrics).toContain('[Part 3 - Add Combat & Climax Layer]');
  expect(tracks[0].stems_requested).toEqual(['Arpeggiator','Drums','Synth Bass','Synth Lead']);
 });

 it('approves recommended archetype and preserves recorded Suno URLs',()=>{
  const rec = structuredClone(records.find(r=>r.game_id==='beast-bistro-express')!);
  rec.tracks[0].suno.url = 'https://suno.com/song/123';
  const approved = applyArchetypeToRecord({...rec,status:'recommended'}, 'cyberpunk', 'cyber kitchen', true);
  expect(approved.status).toBe('approved');
  const underway = applyArchetypeToRecord({...rec,status:'in_progress'}, 'cyberpunk', 'cyber kitchen', true);
  expect(underway.status).toBe('in_progress');
  expect(approved.archetype).toBe('cyberpunk');
  expect(approved.tracks[0].suno.url).toBe('https://suno.com/song/123');
  expect(approved.tracks[1].style_prompt).toContain('cyber kitchen atmosphere');
 });

 it('classifies media into image, video, music, branding and sfx',()=>{
  expect(mediaCategoryForKind('screenshot','')).toBe('image');
  expect(mediaCategoryForKind('screenshot','branding')).toBe('branding');
  expect(mediaCategoryForKind('logo','')).toBe('branding');
  expect(mediaCategoryForKind('video','')).toBe('video');
  expect(mediaCategoryForKind('music','')).toBe('music');
  expect(mediaCategoryForKind('sfx','')).toBe('sfx');
  expect(indexedAssetCategory('Assets/Music/Theme.mp3')).toBe('music');
  expect(indexedAssetCategory('Assets/Audio/jump.wav')).toBe('sfx');
  expect(indexedAssetCategory('UI/Icons/app_logo.png')).toBe('branding');
 });
});
