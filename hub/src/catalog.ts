import type {Game,Taxon,Media} from './types';
export function matches(g:Game,q:string,engine:string,capability:string){
 const haystack=[g.name,g.description,g.logic,g.reuse,g.assets,...g.mechanics.map(m=>`${m.name} ${m.rules}`),...g.capabilities.map(c=>c.id)].join(' ').toLowerCase();
 return (!q||haystack.includes(q.toLowerCase()))&&(!engine||g.engine.startsWith(engine))&&(!capability||g.capabilities.some(c=>c.id===capability)||g.mechanics.some(m=>m.capability===capability));
}
export function coverage(games:Game[],taxa:Taxon[]){return taxa.map(t=>({...t,donors:games.filter(g=>g.capabilities.some(c=>c.id===t.id&&c.state!=='planned')||g.mechanics.some(m=>m.capability===t.id&&m.state!=='planned')),verified:games.filter(g=>g.capabilities.some(c=>c.id===t.id&&['verified','reused'].includes(c.state))||g.mechanics.some(m=>m.capability===t.id&&['verified','reused'].includes(m.state)))}));}
export function mediaReadiness(items:Media[]){
 const active=items.filter(m=>m.status!=='retired');
 const selected=active.filter(m=>m.curation==='selected'||m.status==='approved');
 const screenshots=selected.filter(m=>m.kind==='screenshot');
 const videos=selected.filter(m=>m.kind==='video');
 const trailers=selected.filter(m=>m.kind==='trailer');
 return {total:active.length,screenshots:screenshots.length,videos:videos.length,trailers:trailers.length,
  needsScreenshot:!screenshots.length,needsGameplay:!videos.some(m=>['gameplay','environment-showcase'].includes(m.content_role||'')),needsTrailer:!trailers.length,
  needsClearance:active.some(m=>m.status!=='approved'),cover:screenshots.sort((a,b)=>a.sort_order-b.sort_order)[0],
  referenceOnly:active.some(m=>m.kind==='screenshot')&&!screenshots.length};
}
