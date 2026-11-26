import {it,expect} from 'vitest';
import {catalogGameExport,pipelineGameExport,gamesExportDocument,GAME_EXPORT_FORMAT} from '../src/gameExport';
import {previewRoadmap} from '../src/roadmap';
import seed from '../data/capability-roadmap.json';
import projects from '../data/catalog.json';
import taxonomy from '../data/taxonomy.json';
import type {Game,Library} from '../src/types';

const lib={projects,taxonomy,storage:'PRIVATE-STORAGE',schema_version:1} as unknown as Library;

it('exports catalog games with overview, genre, mechanics, taxonomy and tags',()=>{
 const g={...(projects[0] as unknown as Game),classification:{genre:'action',sub_genre:'',perspective:'top-down'}};
 const row=catalogGameExport(g,lib);
 expect(row).toMatchObject({id:g.id,name:g.name,source:'catalog',genre:{main:{id:'action'}},classification:{perspective:'top-down'}});
 expect(row.overview.description).toBe(g.description.trim());
 expect(row.mechanics).toHaveLength(g.mechanics.length);
 expect(row.taxonomy.every(t=>t.id&&t.label)).toBe(true);
 expect(row.tags).toContain('genre:action');
 expect(row.tags).toContain('perspective:top-down');
 expect(new Set(row.tags).size).toBe(row.tags.length);
 const doc=JSON.parse(JSON.stringify(gamesExportDocument('catalog',[row],lib,{scope:'selected',total:projects.length})));
 expect(doc).toMatchObject({format:GAME_EXPORT_FORMAT,schema_version:1,source:'catalog',summary:{games:1}});
 expect(doc.taxonomy_definitions.length).toBe(new Set(row.taxonomy.map(t=>t.id)).size);
 expect(JSON.stringify(doc)).not.toContain('PRIVATE-STORAGE');
});

it('exports pipeline games with staged target capabilities as mechanics',()=>{
 const rows=previewRoadmap(seed.projects);
 const row=pipelineGameExport(rows[0],lib);
 expect(row).toMatchObject({id:rows[0].id,name:rows[0].title,source:'pipeline'});
 expect(row.mechanics).toHaveLength(rows[0].capability_ids.length);
 expect(row.mechanics.every(m=>['first_slice','later','unstaged'].includes(m.stage as string))).toBe(true);
 expect(row.tags.some(t=>t.startsWith('capability:'))).toBe(true);
 const doc=gamesExportDocument('pipeline',rows.map(r=>pipelineGameExport(r,lib)),lib,{scope:'all',total:rows.length});
 expect(doc.summary.games).toBe(rows.length);
});
