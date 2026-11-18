import {describe,it,expect} from 'vitest';
import seedRecords from '../data/music-design/index.json';
import type {Media,MusicDesignRecord} from '../src/types';
import {buildApprovalItems,sortApprovals,decideMusicDirection,decideMusicTake,decideMedia,reopenMusicTake,mediaBlockers,latestDecisions,type ApprovalEntry} from '../src/approvals';

const records=structuredClone(seedRecords as unknown as MusicDesignRecord[]);
const media=(over:Partial<Media>={}):Media=>({id:'m1',project_id:'g1',kind:'screenshot',title:'Arena',caption:'Fight',alt_text:'Two robots',rights:'Original',credit:'',status:'draft',source_path:'',stored_path:'',sha256:'',created_at:'2026-11-01T00:00:00Z',approved_at:null,sort_order:0,width:null,height:null,duration_seconds:null,...over});
const entry=(over:Partial<ApprovalEntry>):ApprovalEntry=>({id:'e',kind:'media',subject_id:'g1',item_id:'m1',decision:'approved',note:'',decided_at:'2026-11-02T00:00:00Z',...over});

describe('approvals inbox',()=>{
 it('queues recommended music directions, generated takes and draft media',()=>{
  const items=buildApprovalItems(records,[media(),media({id:'m2',status:'approved'})],[],[]);
  const open=items.filter(i=>i.state==='pending');
  expect(open.filter(i=>i.kind==='music_direction')).toHaveLength(records.filter(r=>r.status==='recommended').length);
  expect(open.filter(i=>i.kind==='music_take')).toHaveLength(records.flatMap(r=>r.tracks).filter(t=>['generated','stems_split'].includes(t.status)).length);
  expect(items.find(i=>i.itemId==='m1')!.state).toBe('pending');
  expect(items.find(i=>i.itemId==='m2')!.state).toBe('approved');
  expect(items.some(i=>i.kind==='music_take'&&records.flatMap(r=>r.tracks).find(t=>t.track_id===i.itemId)!.status==='prompt_ready')).toBe(false);
 });

 it('marks sent-back items and sorts them first; reopened returns to pending',()=>{
  const sent=entry({decision:'changes_requested',note:'Reshoot at night'});
  let items=sortApprovals(buildApprovalItems([], [media({id:'m0',created_at:'2026-11-05T00:00:00Z'}),media()],[],[sent]));
  expect(items[0].itemId).toBe('m1');
  expect(items[0].state).toBe('changes_requested');
  items=buildApprovalItems([], [media()],[],[sent,entry({decision:'reopened',decided_at:'2026-11-03T00:00:00Z'})]);
  expect(items[0].state).toBe('pending');
  expect(latestDecisions([sent,entry({decided_at:'2026-11-01T00:00:00Z'})]).get('media:m1')!.decision).toBe('changes_requested');
 });

 it('lists media approval requirements matching the native rule',()=>{
  expect(mediaBlockers(media())).toEqual([]);
  expect(mediaBlockers(media({title:' ',alt_text:'',rights:''}))).toEqual(['Add a title','Record rights / license clearance','Add alt text']);
  expect(mediaBlockers(media({kind:'video',alt_text:''}))).toEqual([]);
  expect(()=>decideMedia(media({caption:''}),'approved')).toThrow(/caption/);
 });

 it('translates media decisions into status and review notes',()=>{
  expect(decideMedia(media(),'approved').status).toBe('approved');
  expect(decideMedia(media(),'rejected').status).toBe('retired');
  const sent=decideMedia(media({status:'approved',review_notes:'Nice'}),'changes_requested','Crop the HUD');
  expect(sent.status).toBe('draft');
  expect(sent.review_notes).toBe('Nice\nChanges requested: Crop the HUD');
 });

 it('approves a music direction as `approved` and rejects it back to unassigned',()=>{
  const rec=structuredClone(records.find(r=>r.status==='recommended')!);
  expect(decideMusicDirection(rec,'approved').status).toBe('approved');
  expect(decideMusicDirection(rec,'rejected').status).toBe('unassigned');
  expect(decideMusicDirection(rec,'changes_requested')).toBe(rec);
  expect(()=>decideMusicDirection({...rec,archetype:null,recommended_archetype:null},'approved')).toThrow(/archetype/);
 });

 it('approves, rejects and reopens a single take without touching sibling tracks',()=>{
  const rec=structuredClone(records.find(r=>r.tracks.some(t=>t.status==='stems_split'))!);
  const t=rec.tracks.find(x=>x.status==='stems_split')!;
  const approved=decideMusicTake(rec,t.track_id,'approved');
  expect(approved.tracks.find(x=>x.track_id===t.track_id)!.status).toBe('approved');
  expect(approved.tracks.filter(x=>x.track_id!==t.track_id)).toEqual(rec.tracks.filter(x=>x.track_id!==t.track_id));
  expect(reopenMusicTake(approved,t.track_id).tracks.find(x=>x.track_id===t.track_id)!.status).toBe(t.suno.stem_group_id?'stems_split':'generated');
  expect(()=>decideMusicTake(rec,'missing','approved')).toThrow();
  const noUrl=structuredClone(rec);noUrl.tracks.find(x=>x.track_id===t.track_id)!.suno.url='';
  expect(()=>decideMusicTake(noUrl,t.track_id,'approved')).toThrow(/Suno/);
 });
});
