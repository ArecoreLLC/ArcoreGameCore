import {chromium} from '@playwright/test';
import {spawn,execFileSync} from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(import.meta.dirname,'..'),output=path.join(root,'test-results','roadmap-export-'+Date.now());await fs.mkdir(output,{recursive:true});
const exe=process.env.GAMECORE_TEST_EXE||path.join(root,'src-tauri','target-json-export','release','gamecore-library.exe');
const app=spawn(exe,[],{windowsHide:true,stdio:'ignore',env:{...process.env,GAMECORE_DATA_DIR:path.join(output,'library'),WEBVIEW2_USER_DATA_FOLDER:path.join(output,'webview'),WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:'--remote-debugging-port=9451'}});let browser;
try{
 for(let i=0;i<150;i++){try{browser=await chromium.connectOverCDP('http://127.0.0.1:9451');break}catch{await new Promise(r=>setTimeout(r,400))}}
 assert.ok(browser);const page=browser.contexts()[0].pages()[0];const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.getByRole('heading',{name:'Small worlds. Big potential.'}).waitFor({timeout:45000});
 const invoke=(command,args={})=>page.evaluate(({command,args})=>window.__TAURI_INTERNALS__.invoke(command,args),{command,args});
 await page.getByRole('button',{name:'Game roadmap',exact:true}).click();await page.waitForFunction(()=>document.querySelectorAll('.roadmap-card').length===50);
 await page.getByLabel('Search roadmap').fill('Lantern Heist');await page.getByRole('button',{name:'Export JSON',exact:true}).click();
 let raw=await page.getByLabel('Roadmap JSON',{exact:true}).inputValue();let doc=JSON.parse(raw);assert.equal(doc.games.length,50);assert.equal(doc.capabilities.length,146);assert.equal(doc.summary.target_assignments,330);assert.deepEqual(doc.integrity.missing_definitions,[]);assert.deepEqual(doc.integrity.single_consumer_capabilities,[]);assert.ok(doc.games.every(g=>g.creative_direction&&g.visual_direction));assert.equal(doc.games.find(g=>g.id==='gravity-parcel').title,'Relic Rematch');assert.equal(doc.games.find(g=>g.id==='salvage-submersible').title,'Relic Gallery');assert.equal(doc.review_context.larger_game_combinations.length,4);
 await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.copiedRoadmap=text}}}));
 await page.getByRole('button',{name:'Copy JSON',exact:true}).click();assert.equal(await page.evaluate(()=>window.copiedRoadmap),raw);
 await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw new Error('Clipboard unavailable')}}}));
 await page.getByRole('button',{name:'Copy JSON',exact:true}).click();assert.equal(await page.getByLabel('Roadmap JSON',{exact:true}).evaluate(el=>el.selectionEnd-el.selectionStart),raw.length);
 const file=await invoke('export_roadmap_json',{directory:output,document:doc});assert.deepEqual(JSON.parse(await fs.readFile(file,'utf8')),doc);
 const second=await invoke('export_roadmap_json',{directory:output,document:doc});assert.notEqual(file,second);
 await page.getByRole('button',{name:'Close export'}).click();await page.locator('.roadmap-card').click();await page.getByLabel('Owner',{exact:true}).fill('Unsaved export owner');
 await page.getByRole('button',{name:'Export JSON',exact:true}).click();raw=await page.getByLabel('Roadmap JSON',{exact:true}).inputValue();doc=JSON.parse(raw);
 assert.deepEqual(doc.snapshot.unsaved_game_ids,['lantern-heist']);assert.equal(doc.games.find(g=>g.id==='lantern-heist').owner,'Unsaved export owner');
 assert.equal((await invoke('roadmap')).find(g=>g.id==='lantern-heist').owner,'');
 await page.screenshot({path:path.join(output,'export-dialog.png'),fullPage:false});assert.deepEqual(errors,[]);
 const report={status:'passed',checks:['All 50 games exported despite list filter','Self-contained capability and donor definitions plus larger-game review context','Copy handler payload and manual-selection fallback (system clipboard untouched)','Native UTF-8 JSON files round-trip and use unique filenames','Unsaved edits labeled and exported without saving to SQLite','No page errors'],output};
 await fs.writeFile(path.join(output,'result.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
}catch(e){console.error(e);process.exitCode=1;}finally{if(browser)await browser.close();if(app.pid)execFileSync('taskkill',['/PID',String(app.pid),'/T','/F'],{windowsHide:true,stdio:'ignore'});}
