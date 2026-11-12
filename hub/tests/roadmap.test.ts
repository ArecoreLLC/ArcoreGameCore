import {describe,it,expect} from 'vitest';
import {previewRoadmap,progress,unmet} from '../src/roadmap';
import seed from '../data/capability-roadmap.json';
import catalog from '../data/catalog.json';
import taxonomy from '../data/taxonomy.json';
describe('roadmap coverage and milestone progress',()=>{
 it('assigns all original gaps across 50 valid game tracks',()=>{
  const rows=previewRoadmap(seed.projects);expect(rows).toHaveLength(50);
  const covered=new Set(catalog.flatMap(g=>g.capabilities.filter(c=>c.state!=='planned').map(c=>c.id)));
  const gaps=taxonomy.filter(t=>t.level==='capability'&&!covered.has(t.id)).map(t=>t.id);
  const assigned=new Set(rows.flatMap(g=>g.capability_ids));expect(gaps).toHaveLength(146);
  expect(gaps.every(id=>assigned.has(id))).toBe(true);expect(rows.reduce((n,g)=>n+g.capability_ids.length,0)).toBe(330);
  expect(rows.every(g=>g.donors.every(d=>catalog.some(p=>p.id===d.project_id)))).toBe(true);
  expect(new Set(rows.map(g=>g.id)).size).toBe(50);
 });
 it('separates first-slice gates from later milestones and removes unrelated gates',()=>{
  const rows=previewRoadmap(seed.projects);
  expect(unmet(rows.find(g=>g.id==='pocket-expedition')!,rows)).toHaveLength(0);
  expect(unmet(rows.find(g=>g.id==='canopy-courier')!,rows)).toHaveLength(0);
  const g=rows.find(g=>g.id==='shadow-couriers')!;
  expect(g.dependency_requirements['arena-relay']).toContain('cap-client-prediction-reconciliation');
  expect(unmet(g,rows,'later').length).toBeGreaterThan(0);
  for(const {id,target} of unmet(g,rows))rows.find(x=>x.id===id)!.target_progress[target].state='verified';
  expect(unmet(g,rows)).toHaveLength(0);expect(unmet(g,rows,'later').length).toBeGreaterThan(0);
 });
 it('has two consumers per capability and an acyclic producer graph with valid stages',()=>{
  const rows=previewRoadmap(seed.projects);
  for(const id of new Set(rows.flatMap(g=>g.capability_ids)))expect(rows.filter(g=>g.capability_ids.includes(id)).length).toBeGreaterThanOrEqual(2);
  for(const g of rows){
   expect(g.creative_direction).toBeTruthy();expect(g.visual_direction).toBeTruthy();
   for(const [dep,targets] of Object.entries(g.dependency_requirements)){
    const donor=rows.find(x=>x.id===dep)!;expect(donor.priority).toBeLessThan(g.priority);
    for(const target of targets){expect(donor.capability_ids).toContain(target);expect(['first_slice','later']).toContain(g.dependency_stages?.[dep]?.[target]);}
   }
  }
 });
 it('keeps planned and blocked targets out of accepted progress',()=>{
  const g=previewRoadmap(seed.projects)[0];g.target_progress[g.capability_ids[0]].state='blocked';
  expect(progress(g)).toMatchObject({total:9,accepted:0,blocked:1,first:0});
 });
});
