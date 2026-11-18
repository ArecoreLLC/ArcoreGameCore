import type {Game,Media,MusicDesignRecord,MusicTrack} from './types';
import {applyArchetypeToRecord,pipelineStage} from './music';

/**
 * One inbox for every decision that waits on a person.
 *
 * Each source keeps its own state (music records, media rows). This module only reads that
 * state into a common shape and translates a decision back into the source's own fields.
 * The `approval_history` table adds the audit trail and "changes requested" marker.
 */
export type ApprovalKind='music_direction'|'music_take'|'media';
export type Decision='approved'|'changes_requested'|'rejected';
/** `reopened` is written by Undo / Reopen and returns an item to the queue. */
export type HistoryDecision=Decision|'reopened';
export type ApprovalState='pending'|'changes_requested'|'approved'|'rejected';
export type ApprovalEntry={id:string;kind:ApprovalKind;subject_id:string;item_id:string;item_label?:string;decision:HistoryDecision;note:string;decided_at:string};
export type ApprovalItem={
 key:string; kind:ApprovalKind; subjectId:string; subjectName:string; itemId:string;
 title:string; summary:string; state:ApprovalState;
 /** Hard requirements: Approve stays disabled until these are resolved. */
 blockers:string[];
 /** Soft reminders shown next to the decision buttons. */
 hints:string[];
 updatedAt:string; scope:string; lastDecision?:ApprovalEntry;
};

export const KIND_LABELS:Record<ApprovalKind,string>={music_direction:'Music direction',music_take:'Music take',media:'Media'};
export const STATE_LABELS:Record<ApprovalState,string>={pending:'Needs decision',changes_requested:'Changes requested',approved:'Approved',rejected:'Rejected'};
export const IMAGE_KINDS=['screenshot','logo','icon','marketing'];
const REVIEWABLE_TRACK=['generated','stems_split'];

export const itemKey=(kind:ApprovalKind,itemId:string)=>`${kind}:${itemId}`;
export const isOpen=(s:ApprovalState)=>s==='pending'||s==='changes_requested';

/** Latest decision per item; `history` may be in any order. */
export function latestDecisions(history:ApprovalEntry[]):Map<string,ApprovalEntry>{
 const out=new Map<string,ApprovalEntry>();
 for(const e of history){
  const k=itemKey(e.kind,e.item_id),prev=out.get(k);
  if(!prev||e.decided_at>prev.decided_at)out.set(k,e);
 }
 return out;
}

/** Open items wait on a person; a recorded "changes requested" marks them as sent back. */
function openState(last?:ApprovalEntry):ApprovalState{return last?.decision==='changes_requested'?'changes_requested':'pending'}

export function mediaBlockers(m:Pick<Media,'title'|'caption'|'rights'|'alt_text'|'kind'>):string[]{
 const b:string[]=[];
 if(!m.title.trim())b.push('Add a title');
 if(!m.caption.trim())b.push('Add a caption');
 if(!m.rights.trim())b.push('Record rights / license clearance');
 if(IMAGE_KINDS.includes(m.kind)&&!m.alt_text.trim())b.push('Add alt text');
 return b;
}

export function trackSummary(t:MusicTrack):string{
 const a=t.suno.analysis,n=t.suno.candidates?.length||0;
 return [a?`${a.bpm_detected} BPM · ${a.key_detected}`:`${t.bpm} BPM target`,n?`${n} take${n===1?'':'s'}`:'',t.status.replace('_',' ')].filter(Boolean).join(' · ');
}

export function buildApprovalItems(records:MusicDesignRecord[],media:Media[],games:Game[],history:ApprovalEntry[]):ApprovalItem[]{
 const last=latestDecisions(history);
 const name=(id:string)=>games.find(g=>g.id===id)?.name||records.find(r=>r.game_id===id)?.name||id;
 const items:ApprovalItem[]=[];
 for(const r of records){
  const scope=r.scope||'catalog';
  // Music direction: the archetype/setting recommendation for a game.
  const dirKey=itemKey('music_direction',r.game_id),dirLast=last.get(dirKey);
  let dirState:ApprovalState|null=null;
  if(r.status==='recommended')dirState=openState(dirLast);
  else if(['approved','in_progress','planned'].includes(r.status))dirState='approved';
  else if(r.status==='unassigned'&&dirLast?.decision==='rejected')dirState='rejected';
  if(dirState){
   const arch=r.archetype||r.recommended_archetype;
   items.push({key:dirKey,kind:'music_direction',subjectId:r.game_id,subjectName:r.name,itemId:r.game_id,
    title:arch?`${arch}${(r.setting||r.recommended_setting)?` · ${r.setting||r.recommended_setting}`:''}`:'No archetype recommended',
    summary:r.recommendation_reason||'',state:dirState,blockers:arch?[]:['Choose an archetype'],hints:[],
    updatedAt:r.updated_at||'',scope,lastDecision:dirLast});
  }
  // Music takes: each generated track needs a listen before it is used.
  for(const t of r.tracks){
   let st:ApprovalState|null=null;const k=itemKey('music_take',t.track_id),l=last.get(k);
   if(REVIEWABLE_TRACK.includes(t.status))st=openState(l);
   else if(t.status==='approved')st='approved';
   else if(t.status==='rejected')st='rejected';
   if(!st)continue;
   const rated=(t.suno.candidates||[]).some(c=>c.listen_rating);
   items.push({key:k,kind:'music_take',subjectId:r.game_id,subjectName:r.name,itemId:t.track_id,title:t.title,
    summary:trackSummary(t),state:st,blockers:t.suno.url.trim()?[]:['Add the Suno song URL'],
    hints:rated||!t.suno.candidates?.length?[]:['No take has a listen rating yet'],updatedAt:t.suno.generated_at||r.updated_at||'',scope,lastDecision:l});
  }
 }
 for(const m of media){
  const k=itemKey('media',m.id),l=last.get(k);
  const st:ApprovalState=m.status==='approved'?'approved':m.status==='retired'?'rejected':openState(l);
  items.push({key:k,kind:'media',subjectId:m.project_id,subjectName:name(m.project_id),itemId:m.id,
   title:m.title||'Untitled '+m.kind,summary:[m.kind,m.caption].filter(Boolean).join(' · '),state:st,
   blockers:st==='approved'?[]:mediaBlockers(m),hints:[],updatedAt:m.created_at,scope:'catalog',lastDecision:l});
 }
 return items;
}

/** Open items first (sent-back before new), then most recently updated. */
export function sortApprovals(items:ApprovalItem[]):ApprovalItem[]{
 const rank:Record<ApprovalState,number>={changes_requested:0,pending:1,approved:2,rejected:3};
 return [...items].sort((a,b)=>rank[a.state]-rank[b.state]||b.updatedAt.localeCompare(a.updatedAt)||a.subjectName.localeCompare(b.subjectName));
}

// --- Decisions translated back into each source's own fields -------------------------------

export function decideMusicDirection(r:MusicDesignRecord,d:Decision):MusicDesignRecord{
 if(d==='approved'){
  const arch=r.archetype||r.recommended_archetype;
  if(!arch)throw new Error(`${r.name}: choose an archetype before approving`);
  return applyArchetypeToRecord(r,arch,r.setting||r.recommended_setting,true);
 }
 if(d==='rejected')return {...r,status:'unassigned'};
 return r; // changes requested: the history entry carries the note; status stays recommended
}

export function reopenMusicDirection(r:MusicDesignRecord):MusicDesignRecord{return {...r,status:'recommended'}}

function setTrack(r:MusicDesignRecord,trackId:string,fn:(t:MusicTrack)=>MusicTrack):MusicDesignRecord{
 if(!r.tracks.some(t=>t.track_id===trackId))throw new Error(`Track ${trackId} not found`);
 return {...r,tracks:r.tracks.map(t=>t.track_id===trackId?fn(t):t)};
}
export function decideMusicTake(r:MusicDesignRecord,trackId:string,d:Decision):MusicDesignRecord{
 if(d==='changes_requested')return r;
 return setTrack(r,trackId,t=>{
  if(d==='approved'&&!t.suno.url.trim())throw new Error(`${t.title}: add the Suno song URL before approving`);
  return {...t,status:d};
 });
}
export function reopenMusicTake(r:MusicDesignRecord,trackId:string):MusicDesignRecord{
 return setTrack(r,trackId,t=>({...t,status:t.suno.stem_group_id?'stems_split':'generated'}));
}

export function decideMedia(m:Media,d:Decision,note=''):Media{
 if(d==='approved'){
  const b=mediaBlockers(m);
  if(b.length)throw new Error(`${m.title||'Media'}: ${b.join(', ')}`);
  return {...m,status:'approved'};
 }
 if(d==='rejected')return {...m,status:'retired'};
 const stamp=`Changes requested: ${note.trim()}`;
 return {...m,status:'draft',review_notes:m.review_notes?.trim()?`${m.review_notes.trim()}\n${stamp}`:stamp};
}
export function reopenMedia(m:Media):Media{return {...m,status:'draft'}}

export function pipelineLabel(r:MusicDesignRecord){return pipelineStage(r).replaceAll('_',' ')}
