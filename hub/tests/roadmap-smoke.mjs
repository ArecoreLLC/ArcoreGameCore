import {chromium} from '@playwright/test';
import {spawn,execFileSync} from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(import.meta.dirname,'..'),output=path.join(root,'test-results','roadmap-'+Date.now());
await fs.mkdir(output,{recursive:true});
const source=path.join(process.env.APPDATA,'com.arcore.gamecore'),copy=path.join(output,'library');
execFileSync('python',['-c',`import sqlite3,sys,json,shutil;from pathlib import Path
src=Path(sys.argv[1]);dst=Path(sys.argv[2]);(dst/'media').mkdir(parents=True)
a=sqlite3.connect((src/'catalog.sqlite3').as_uri()+'?mode=ro',uri=True);b=sqlite3.connect(dst/'catalog.sqlite3');a.backup(b)
for (raw,) in b.execute('SELECT data FROM media'):
 p=Path(json.loads(raw)['stored_path']);shutil.copy2(p,dst/'media'/p.name)
a.close();b.close()`,source,copy]);
const exe=process.env.GAMECORE_TEST_EXE||path.join(root,'src-tauri','target-json-export','release','gamecore-library.exe');let app,browser;
const checks=[];
async function start(){app=spawn(exe,[],{windowsHide:true,stdio:'ignore',env:{...process.env,GAMECORE_DATA_DIR:copy,WEBVIEW2_USER_DATA_FOLDER:path.join(output,'webview'),WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:'--remote-debugging-port=9449'}});for(let i=0;i<100;i++){try{browser=await chromium.connectOverCDP('http://127.0.0.1:9449');break}catch{await new Promise(r=>setTimeout(r,400))}}assert.ok(browser);const page=browser.contexts()[0].pages()[0];await page.getByRole('heading',{name:'Small worlds. Big potential.'}).waitFor({timeout:45000});return page;}
function stop(){if(app?.pid)execFileSync('taskkill',['/PID',String(app.pid),'/T','/F'],{windowsHide:true,stdio:'ignore'});app=null;}
try{
 let page=await start();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const invoke=(command,args={})=>page.evaluate(({command,args})=>window.__TAURI_INTERNALS__.invoke(command,args),{command,args});
 const before=await invoke('library');assert.ok(before.projects.length>=31);assert.ok(before.media.length>=44);
 await page.getByRole('button',{name:'Game roadmap',exact:true}).click();
 await page.getByRole('heading',{name:'Game roadmap',exact:true}).waitFor();
 await page.waitForFunction(()=>document.querySelectorAll('.roadmap-card').length===50);
 let rows=await invoke('roadmap');assert.equal(rows.length,50);assert.equal(new Set(rows.flatMap(g=>g.capability_ids)).size,146);
 await page.screenshot({path:path.join(output,'roadmap.png'),fullPage:false});checks.push(`Existing ${before.projects.length} projects and ${before.media.length} media retained; 50 roadmap tracks and all 146 gaps seeded`);
 await page.getByLabel('Roadmap wave').selectOption('6');assert.equal(await page.locator('.roadmap-card').count(),14);
 await page.getByLabel('Roadmap wave').selectOption('');
 await page.getByLabel('Search roadmap').fill('Lantern Heist');await page.locator('.roadmap-card').click();
 await page.getByLabel('Priority',{exact:true}).fill('2');await page.getByLabel('Owner',{exact:true}).fill('QA owner');
 await page.getByLabel('Game status').selectOption('active');
 await page.getByLabel('Target state').selectOption('in_progress');
 await page.getByLabel('Target notes / blockers').fill('QA source inspection complete');
 await page.getByRole('button',{name:'Save roadmap',exact:true}).click();await page.getByText('Roadmap saved to SQLite',{exact:true}).waitFor();
 await page.getByLabel('Search donor files').fill('.cpp');
 await page.locator('.reference-files > div').first().waitFor();
 const sourcePath=await page.locator('.reference-files .file-link').first().innerText();
 await page.locator('.reference-files > div').first().getByRole('button',{name:'Pin to target'}).click();
 await page.getByLabel('Reference kind').selectOption('asset');await page.getByLabel('Search donor files').fill('');
 await page.locator('.reference-files > div').first().waitFor();
 await page.locator('.reference-files > div').first().getByRole('button',{name:'Pin to target'}).click();
 await page.getByLabel('Target state').selectOption('verified');
 await page.getByRole('button',{name:'Save roadmap',exact:true}).click();
 await page.getByRole('alert').filter({hasText:'require revision'}).waitFor();
 await page.getByLabel('Revision / build').fill('qa-fixture-revision');await page.getByLabel('Platform / hardware').fill('Windows / test fixture');
 await page.getByLabel('Test command or procedure').fill('QA only: validate roadmap state persistence');
 await page.getByLabel('Evidence path / result').fill('Isolated test evidence; not a game acceptance claim');
 await page.getByRole('button',{name:'Save roadmap',exact:true}).click();
 await page.waitForFunction(()=>!document.querySelector('[role=alert]'));
 await page.getByLabel('Add prerequisite game').selectOption('clockwork-courier');
 await page.getByLabel('Tire friction',{exact:true}).uncheck();
 await page.getByLabel('Dependency stage clockwork-courier cap-suspension-solver',{exact:true}).selectOption('later');
 await page.getByRole('button',{name:'Save roadmap',exact:true}).click();
 await page.waitForFunction(()=>!document.querySelector('[role=alert]'));
 rows=await invoke('roadmap');let lantern=rows.find(g=>g.id==='lantern-heist'),cap=lantern.capability_ids[0];
 assert.equal(lantern.dependency_requirements['clockwork-courier'].length,2);assert.equal(lantern.dependency_stages['clockwork-courier']['cap-suspension-solver'],'later');assert.equal(lantern.priority,2);assert.equal(lantern.owner,'QA owner');assert.equal(lantern.target_progress[cap].state,'verified');
 assert.equal(lantern.target_progress[cap].reuse_links.length,2);assert.equal(lantern.target_progress[cap].reuse_links[0].path,sourcePath.trim());
 await page.screenshot({path:path.join(output,'roadmap-detail.png'),fullPage:false});
 await page.locator('.target-editor').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(output,'roadmap-target.png'),fullPage:false});
 checks.push('UI priority, owner, status and capability evidence saved; source and asset files pinned; evidence-free verification rejected');
 const cycle=structuredClone(lantern);cycle.dependency_requirements={'prism-patrol':['cap-dynamic-path-replanning']};
 await assert.rejects(()=>invoke('save_roadmap',{project:cycle}),/cycle/);
 const conflict=structuredClone(lantern);conflict.version=-1;await assert.rejects(()=>invoke('save_roadmap',{project:conflict}),/another window/);
 const after=await invoke('library');assert.deepEqual(after.projects,before.projects);assert.deepEqual(after.taxonomy,before.taxonomy);assert.deepEqual(after.media,before.media);
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.deepEqual(errors,[]);
 const backup=await invoke('backup_library',{directory:output});
 const count=execFileSync('python',['-c','import sqlite3,sys; c=sqlite3.connect(sys.argv[1]);print(c.execute("SELECT COUNT(*) FROM roadmap").fetchone()[0]);c.close()',path.join(backup,'catalog.sqlite3')],{encoding:'utf8'});assert.equal(Number(count.trim()),50);
 checks.push('Cycles and stale writes rejected; roadmap progress leaves atlas unchanged; backup includes roadmap');
 await browser.close();browser=null;stop();await new Promise(r=>setTimeout(r,700));page=await start();
 rows=await invoke('roadmap');lantern=rows.find(g=>g.id==='lantern-heist');assert.equal(lantern.owner,'QA owner');assert.equal(lantern.target_progress[cap].reuse_links.length,2);
 checks.push('Priority, evidence and references survive native restart without seed overwrite');
 await fs.writeFile(path.join(output,'result.json'),JSON.stringify({status:'passed',checks,output,exe},null,2));console.log(JSON.stringify({status:'passed',checks,output},null,2));
}catch(e){await fs.writeFile(path.join(output,'result.json'),JSON.stringify({status:'failed',checks,error:String(e)},null,2));console.error(e);process.exitCode=1;}
finally{if(browser)await browser.close().catch(()=>{});stop();}
