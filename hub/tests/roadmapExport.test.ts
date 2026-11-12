import {it,expect} from 'vitest';
import {roadmapReviewExport} from '../src/roadmapExport';
import {previewRoadmap} from '../src/roadmap';
import seed from '../data/capability-roadmap.json';
import projects from '../data/catalog.json';
import taxonomy from '../data/taxonomy.json';
import type {Library} from '../src/types';
it('exports a self-contained review of current edits with deduplicated definitions',()=>{
 const rows=previewRoadmap(seed.projects);rows[0].priority=99;rows[0].notes='Current unsaved note';
 const id=rows[0].capability_ids[0];rows[0].target_progress[id].state='blocked';rows[0].target_progress[id].notes='Needs source review';
 const doc=roadmapReviewExport(rows,{projects,taxonomy,storage:'PRIVATE-STORAGE',schema_version:1} as unknown as Library,{unsavedGameId:rows[0].id});
 const roundTrip=JSON.parse(JSON.stringify(doc));expect(roundTrip.summary).toMatchObject({games:50,unique_capabilities:146,target_assignments:330});
 expect(roundTrip.snapshot.unsaved_game_ids).toEqual([rows[0].id]);
 expect(roundTrip.games.find((g:{id:string})=>g.id===rows[0].id)).toMatchObject({priority:99,notes:'Current unsaved note',target_progress:{[id]:{state:'blocked',notes:'Needs source review'}}});
 expect(roundTrip.capabilities).toHaveLength(146);expect(JSON.stringify(doc)).not.toContain('PRIVATE-STORAGE');
 expect(roundTrip.games.every((g:{donor_project_ids:string[]})=>g.donor_project_ids.every(id=>roundTrip.donor_projects.some((d:{id:string})=>d.id===id)))).toBe(true);
});
