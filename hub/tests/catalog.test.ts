import {describe,it,expect} from 'vitest';
import {matches,coverage,mediaReadiness} from '../src/catalog';
import catalog from '../data/catalog.json';
import taxonomy from '../data/taxonomy.json';
import type {Game,Media} from '../src/types';
const games=catalog as unknown as Game[];
describe('catalog discovery and filtering',()=>{
 it('includes all 16 Games-folder consumers and separate VR runtime',()=>{
  expect(games.filter(g=>g.path.startsWith('X:/Projects/Games/'))).toHaveLength(16);
  expect(games.some(g=>g.path.endsWith('/ShammyVerse/vr-demo'))).toBe(true);
 });
 it('finds mechanics across descriptions and respects engine/capability filters',()=>{
  const raft=games.find(g=>g.name==='Flotsam Citadel')!;
  expect(matches(raft,'buoyancy','Unreal','construction')).toBe(true);
  expect(matches(raft,'buoyancy','Godot','')).toBe(false);
 });
 it('never equates implementation candidates with verified coverage',()=>{
  const rows=coverage(games,taxonomy);
  expect(rows.find(t=>t.id==='buoyancy')!.donors.length).toBeGreaterThanOrEqual(2);
  expect(rows.find(t=>t.id==='buoyancy')!.verified).toHaveLength(0);
  expect(rows.find(t=>t.id==='rollback')!.donors).toHaveLength(0);
 });
 it('all mechanics, IDs and tags are valid and games contain reuse context',()=>{
  expect(new Set(games.map(g=>g.id)).size).toBe(games.length);
  for(const g of games){expect(g.description.length).toBeGreaterThan(20);expect(g.logic.length).toBeGreaterThan(30);expect(g.reuse.length).toBeGreaterThan(20);expect(g.assets.length).toBeGreaterThan(20);expect(g.mechanics.length).toBeGreaterThan(0);
   for(const c of g.capabilities)expect(taxonomy.some(t=>t.id===c.id)).toBe(true);
   for(const m of g.mechanics)expect(taxonomy.some(t=>t.id===m.capability)).toBe(true);
  }
 });
 it('records all 21 registered arcade games without inventing playtest passes',()=>{
  const quest=games.find(g=>g.name==='ShammieQuest')!;
  expect(quest.subgames).toHaveLength(21);expect(quest.subgames.every(s=>s.source_present&&s.validation.includes('not_run'))).toBe(true);
 });
 it('counts independent capabilities without inheriting broad coverage',()=>{
  const leaves=taxonomy.filter(t=>t.level==='capability');
  expect(leaves).toHaveLength(243);
  const rows=coverage(games,leaves);
  expect(rows.filter(t=>t.donors.length)).toHaveLength(97);
  expect(rows.filter(t=>!t.donors.length)).toHaveLength(146);
  expect(rows.find(t=>t.id==='cap-sampled-buoyant-lift')!.donors.map(g=>g.id)).toEqual(['flotsam-citadel']);
  expect(rows.find(t=>t.id==='cap-fluid-displacement')!.donors).toHaveLength(0);
  expect(rows.every(t=>t.verified.length===0)).toBe(true);
 });
 it('keeps reference captures, asset clips, trailers and clearance distinct',()=>{
  const base={status:'draft',curation:'selected',sort_order:0} as Media;
  const reference={...base,kind:'screenshot',curation:'reference'};
  const asset={...base,kind:'video',content_role:'asset-demo'};
  expect(mediaReadiness([reference,asset])).toMatchObject({referenceOnly:true,needsScreenshot:true,needsGameplay:true,needsTrailer:true,needsClearance:true});
  expect(mediaReadiness([{...base,kind:'screenshot'},{...base,kind:'video',content_role:'gameplay'},{...base,kind:'trailer'}])).toMatchObject({needsScreenshot:false,needsGameplay:false,needsTrailer:false,needsClearance:true});
  expect(mediaReadiness([{...base,kind:'screenshot',status:'retired'}]).needsScreenshot).toBe(true);
 });
});
