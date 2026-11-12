import {chromium} from '@playwright/test';
import {spawn,execFileSync} from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(import.meta.dirname,'..');
const output=path.join(root,'test-results','marketing-'+Date.now());
await fs.mkdir(output,{recursive:true});
const source=process.env.GAMECORE_SOURCE_LIBRARY||path.join(process.env.APPDATA,'com.arcore.gamecore');
const copy=path.join(output,'library');
// Online snapshot into an isolated test library. No write to the user's library.
execFileSync('python',['-c',`import sqlite3,sys,json,shutil; from pathlib import Path
src=Path(sys.argv[1]);dst=Path(sys.argv[2]);(dst/'media').mkdir(parents=True)
a=sqlite3.connect((src/'catalog.sqlite3').as_uri()+'?mode=ro',uri=True);b=sqlite3.connect(dst/'catalog.sqlite3');a.backup(b)
for (raw,) in b.execute('SELECT data FROM media'):
 m=json.loads(raw);p=Path(m['stored_path']);shutil.copy2(p,dst/'media'/p.name)
a.close();b.close()`,source,copy]);
const exe=process.env.GAMECORE_TEST_EXE||path.join(root,'src-tauri','target','release','gamecore-library.exe');
const app=spawn(exe,[],{windowsHide:true,stdio:'ignore',env:{...process.env,GAMECORE_DATA_DIR:copy,WEBVIEW2_USER_DATA_FOLDER:path.join(output,'webview'),WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:'--remote-debugging-port=9448'}});
let browser;const checks=[];
try{
 for(let i=0;i<100;i++){try{browser=await chromium.connectOverCDP('http://127.0.0.1:9448');break;}catch{await new Promise(r=>setTimeout(r,400));}}
 assert.ok(browser,'Native WebView started');
 const page=browser.contexts()[0].pages()[0];const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.getByRole('heading',{name:'Small worlds. Big potential.'}).waitFor({timeout:45000});
 const invoke=(command,args={})=>page.evaluate(({command,args})=>window.__TAURI_INTERNALS__.invoke(command,args),{command,args});
 let lib=await invoke('library');assert.equal(lib.media.length,44);assert.equal(lib.taxonomy.filter(t=>t.level==='capability').length,240);
 assert.ok(lib.media.every(m=>m.stored_path.startsWith(copy)&&m.status==='draft'));
 await page.getByRole('button',{name:'Marketing library'}).click();
 await page.waitForFunction(()=>[...document.querySelectorAll('.cover-image')].every(i=>i.naturalWidth>0));
 assert.equal(await page.locator('.cover-image').count(),19);
 await page.screenshot({path:path.join(output,'marketing-library.png'),fullPage:false});
 await page.getByLabel('Marketing readiness').selectOption('needsScreenshot');assert.equal(await page.locator('.game-card').count(),12);
 await page.getByLabel('Marketing readiness').selectOption('needsGameplay');assert.equal(await page.locator('.game-card').count(),30);
 await page.getByLabel('Marketing readiness').selectOption('needsTrailer');assert.equal(await page.locator('.game-card').count(),31);
 checks.push('44 managed assets; 19 cover images decoded; 12 screenshot/reshoot, 30 gameplay/scene and 31 trailer gaps');
 await page.getByLabel('Marketing readiness').selectOption('');
 await page.locator('.game-card').filter({hasText:'Gully Giants'}).click();
 await page.getByText('Needs screenshot reshoot',{exact:true}).waitFor();
 await page.getByRole('button',{name:'Back to library'}).click();
 await page.locator('.game-card').filter({has:page.getByRole('heading',{name:'ShammyVerse',exact:true})}).click();
 assert.equal(await page.locator('.media-card').count(),8);
 await page.screenshot({path:path.join(output,'shammyverse-media.png'),fullPage:false});
 await page.locator('.media-card').filter({hasText:'Sailing to meet Plumpy'}).click();
 await page.waitForFunction(()=>{const v=document.querySelector('video');return v&&v.readyState>=2&&v.videoWidth>0;});
 await page.locator('video').evaluate(async v=>{v.muted=true;await v.play();});
 await page.waitForFunction(()=>document.querySelector('video')?.currentTime>0.3);
 await page.locator('video').evaluate(v=>v.pause());
 await page.screenshot({path:path.join(output,'video-review.png'),fullPage:false});
 await page.getByLabel('Title',{exact:true}).fill('QA selection edit');
 await page.getByRole('button',{name:'Save review',exact:true}).click();
 await page.getByText('Media review saved',{exact:true}).waitFor();
 const edited=(await invoke('list_media',{projectId:'shammyverse'})).find(m=>m.title==='QA selection edit');
 assert.equal(edited.curation,'selected');assert.equal(edited.content_role,'gameplay');assert.ok(edited.review_notes.includes('sampled frames'));
 checks.push('Native video decoded and played; editorial metadata survives review save');
 await page.getByRole('button',{name:'Capability atlas'}).click();
 await page.getByLabel('Capability evidence').selectOption('gap');
 assert.equal(await page.locator('.atlas-card').count(),143);
 await page.getByLabel('Capability group').selectOption('Water and buoyancy');
 assert.equal(await page.locator('.atlas-card').count(),3);
 await page.screenshot({path:path.join(output,'specific-capability-gaps.png'),fullPage:false});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 assert.deepEqual(errors,[]);
 checks.push('143 specific gaps; buoyancy does not cover flooding, currents or fluid displacement; no JS errors or horizontal overflow');
 await fs.writeFile(path.join(output,'result.json'),JSON.stringify({status:'passed',checks,output,exe},null,2));
 console.log(JSON.stringify({status:'passed',checks,output},null,2));
}catch(e){await fs.writeFile(path.join(output,'result.json'),JSON.stringify({status:'failed',checks,error:String(e)},null,2));console.error(e);process.exitCode=1;}
finally{if(browser)await browser.close().catch(()=>{});if(app.pid)execFileSync('taskkill',['/PID',String(app.pid),'/T','/F'],{windowsHide:true,stdio:'ignore'});}
