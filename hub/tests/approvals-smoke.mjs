// Native Approvals inbox smoke test against an isolated, freshly seeded library.
// Usage (from hub/): node tests/approvals-smoke.mjs   (GAMECORE_TEST_EXE selects the build; default release)
import { chromium } from '@playwright/test';
import { spawn } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(import.meta.dirname,'..');
const output=path.join(root,'test-results','approvals-'+Date.now());
await fs.mkdir(output,{recursive:true});
const exe=process.env.GAMECORE_TEST_EXE||path.join(root,'src-tauri','target','release','gamecore-library.exe');
const env={...process.env,GAMECORE_DATA_DIR:path.join(output,'library'),WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:'--remote-debugging-port=40124',WEBVIEW2_USER_DATA_FOLDER:path.join(output,'webview')};
let app,browser;const checks=[];
async function start(){
 app=spawn(exe,[],{env,windowsHide:true,stdio:'ignore'});
 for(let i=0;i<100;i++){try{browser=await chromium.connectOverCDP('http://127.0.0.1:40124');break}catch{await new Promise(r=>setTimeout(r,400))}}
 assert.ok(browser,'Native WebView exposed the test debug port');
 const page=browser.contexts()[0].pages()[0];
 await page.setViewportSize({width:1440,height:900}).catch(()=>{});
 await page.getByRole('heading',{name:'Game library',exact:true}).waitFor({timeout:45000});
 return page;
}
async function stop(){await browser?.close().catch(()=>{});app?.kill();await new Promise(r=>setTimeout(r,1500));browser=undefined}
const invoke=(page,command,args={})=>page.evaluate(({command,args})=>window.__TAURI_INTERNALS__.invoke(command,args),{command,args});
try{
 let page=await start();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 let before=await invoke(page,'music_designs');
 // The seed may have no directions awaiting review; queue three in this isolated library.
 if(before.filter(r=>r.status==='recommended').length<3){
  for(const r of before.filter(r=>r.status!=='excluded'&&r.recommended_archetype&&r.status!=='recommended').slice(0,3))await invoke(page,'save_music_design',{record:{...r,status:'recommended'}});
  await page.getByRole('button',{name:'Refresh library'}).click();await page.waitForTimeout(800);
  before=await invoke(page,'music_designs');
 }
 const recommended=before.filter(r=>r.status==='recommended');
 const reviewable=before.flatMap(r=>r.tracks).filter(t=>['generated','stems_split'].includes(t.status));
 assert.ok(recommended.length>1&&reviewable.length>0,'Seed has recommended directions and generated takes');

 await page.getByRole('button',{name:/^Approvals/}).click();
 await page.getByRole('heading',{name:'Approvals',exact:true}).waitFor();
 const badge=Number(await page.locator('nav .count.attention').textContent());
 assert.equal(badge,recommended.length+reviewable.length);
 checks.push(`Sidebar badge ${badge} = ${recommended.length} directions + ${reviewable.length} takes`);
 await page.screenshot({path:path.join(output,'approvals-queue.png')});

 // Approve one music direction.
 await page.getByRole('tab',{name:/^Music direction/}).click();
 const first=page.locator('.approval-row').first();
 const dirName=(await first.locator('strong').textContent()).trim();
 await first.click();
 await page.locator('.approval-detail').getByRole('button',{name:'Approve',exact:true}).click();
 await page.locator('.undo-bar').waitFor();
 let recs=await invoke(page,'music_designs');
 const dirRec=recs.find(r=>r.name===dirName);
 assert.equal(dirRec.status,'approved');
 let log=await invoke(page,'approval_history');
 assert.equal(log[0].kind,'music_direction');assert.equal(log[0].decision,'approved');assert.equal(log[0].item_id,dirRec.game_id);
 checks.push(`Approved music direction for ${dirName}: status approved, history logged`);

 // Undo restores the record and logs `reopened`.
 await page.locator('.undo-bar').getByRole('button',{name:/Undo/}).click();
 await page.waitForFunction(()=>!document.querySelector('.undo-bar'));
 await page.waitForTimeout(400);
 recs=await invoke(page,'music_designs');
 assert.equal(recs.find(r=>r.game_id===dirRec.game_id).status,'recommended');
 log=await invoke(page,'approval_history');assert.equal(log[0].decision,'reopened');
 checks.push('Undo restored recommended status and appended a reopened entry');

 // Request changes on a take: note required, status unchanged, row marked.
 await page.getByRole('tab',{name:/^Music take/}).click();
 const take=page.locator('.approval-row').first();const takeName=(await take.locator('strong').textContent()).trim();
 await take.click();
 const detail=page.locator('.approval-detail');
 assert.ok(await detail.getByRole('button',{name:'Request changes'}).isDisabled(),'Request changes needs a note');
 await detail.getByRole('textbox').last().fill('Loop seam clicks at bar 32');
 await detail.getByRole('button',{name:'Request changes'}).click();
 await page.locator('.approval-row').filter({hasText:takeName}).getByText('Changes requested').waitFor();
 log=await invoke(page,'approval_history');
 assert.equal(log[0].decision,'changes_requested');assert.equal(log[0].note,'Loop seam clicks at bar 32');
 checks.push(`Requested changes on ${takeName} take; row moved to Changes requested`);

 // Bulk approve two directions through the confirmation dialog.
 await page.getByRole('tab',{name:/^Music direction/}).click();
 const boxes=page.locator('.approval-row input[type=checkbox]');
 await boxes.nth(0).check();await boxes.nth(1).check();
 await page.getByRole('button',{name:'Approve selected (2)'}).click();
 const dialog=page.getByRole('dialog',{name:'Confirm approvals'});
 assert.equal(await dialog.locator('li').count(),2);
 await page.screenshot({path:path.join(output,'approvals-bulk-confirm.png')});
 await dialog.getByRole('button',{name:'Approve 2'}).click();
 await page.locator('.undo-bar').getByText('Approved 2 items').waitFor();
 recs=await invoke(page,'music_designs');
 assert.equal(recs.filter(r=>r.status==='recommended').length,recommended.length-2);
 checks.push('Bulk approval confirmed 2 listed items and saved both');

 // Media: draft import is blocked until fields are complete, then approved.
 const game=(await invoke(page,'library')).projects.find(g=>g.name==='Flotsam Citadel');
 const item=await invoke(page,'import_media',{projectId:game.id,path:path.join(root,'src-tauri','icons','icon.png'),kind:'screenshot'});
 await page.getByRole('button',{name:'Refresh library'}).click();
 await page.getByRole('tab',{name:/^Media/}).click();
 await page.locator('.approval-row').first().click();
 assert.ok(await detail.getByRole('button',{name:'Approve',exact:true}).isDisabled(),'Approve disabled while requirements are missing');
 await detail.getByLabel('Caption').fill('Raft at dusk');
 await detail.getByLabel('Alt text').fill('A small raft on dark water');
 await detail.getByLabel('Rights / license clearance').fill('Original studio capture');
 await detail.getByRole('button',{name:'Approve',exact:true}).click();
 await page.locator('.undo-bar').waitFor();
 const media=(await invoke(page,'list_media',{projectId:game.id})).find(m=>m.id===item.id);
 assert.equal(media.status,'approved');assert.equal(media.caption,'Raft at dusk');assert.ok(media.approved_at);
 checks.push('Media approve stayed disabled until caption/alt/rights were filled, then saved approved');
 await page.screenshot({path:path.join(output,'approvals-media.png')});

 // Persistence across restart.
 await stop();page=await start();
 log=await invoke(page,'approval_history');
 assert.ok(log.length>=6,'History survived restart');
 await page.getByRole('button',{name:/^Approvals/}).click();
 await page.getByRole('tab',{name:/^Music take/}).click();
 await page.locator('.approval-row').filter({hasText:takeName}).getByText('Changes requested').waitFor();
 checks.push(`History (${log.length} entries) and changes-requested marker survived restart`);
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({passed:checks,output},null,1));
}catch(e){console.error(e);process.exitCode=1}finally{await stop()}
