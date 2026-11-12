import { chromium } from '@playwright/test';
import { spawn } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(import.meta.dirname,'..');
const output=path.join(root,'test-results','native-'+Date.now());
await fs.mkdir(output,{recursive:true});
const exe=process.env.GAMECORE_TEST_EXE||path.join(root,'src-tauri','target','debug','gamecore-library.exe');
const env={...process.env,GAMECORE_DATA_DIR:path.join(output,'library'),WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:'--remote-debugging-port=9447',WEBVIEW2_USER_DATA_FOLDER:path.join(output,'webview')};
let app,browser;
async function start(){
 app=spawn(exe,[],{env,windowsHide:true,stdio:'ignore'});
 for(let i=0;i<100;i++){
  try{browser=await chromium.connectOverCDP('http://127.0.0.1:9447');break;}catch{await new Promise(r=>setTimeout(r,400))}
 }
 if(!browser)throw new Error('Native WebView did not expose the test debug port');
 const page=browser.contexts()[0].pages()[0];
 await page.getByRole('heading',{name:'Small worlds. Big potential.'}).waitFor({timeout:45000});
 return page;
}
function stop(){if(app?.pid)spawn('taskkill',['/PID',String(app.pid),'/T','/F'],{windowsHide:true,stdio:'ignore'});}
const checks=[];
try{
 let page=await start();
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const invoke=(command,args={})=>page.evaluate(({command,args})=>window.__TAURI_INTERNALS__.invoke(command,args),{command,args});
 const lib=await invoke('library');assert.equal(lib.projects.length,31);checks.push('31 projects seeded into native SQLite');
 assert.equal(await page.locator('.game-card').count(),31);
 await page.screenshot({path:path.join(output,'library.png'),fullPage:false});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth),false);
 await page.getByRole('textbox',{name:'Search game library'}).fill('buoyancy');
 assert.ok(await page.locator('.game-card').count()>=2);checks.push('Native UI search and layout');
 await page.locator('.game-card').filter({hasText:'Flotsam Citadel'}).click();
 await page.getByRole('tab',{name:/Mechanics/}).click();
 await page.getByRole('heading',{name:'Raft mass and buoyancy',exact:true}).waitFor();
 await page.screenshot({path:path.join(output,'mechanics.png'),fullPage:false});
 await page.getByRole('button',{name:'Edit project',exact:true}).click();
 await page.getByRole('tab',{name:'Marketing',exact:true}).click();
 await page.getByLabel('tagline',{exact:true}).fill('QA isolated press kit');
 await page.getByLabel('pitch',{exact:true}).fill('A tiny raft, a big storm.');
 await page.getByRole('button',{name:'Save changes',exact:true}).click();
 await page.getByText('Project saved to SQLite',{exact:true}).waitFor();checks.push('Project editing through native UI');
 await page.getByRole('tab',{name:'Assets',exact:true}).click();
 await page.getByLabel('File type').selectOption('source');
 await page.getByRole('textbox',{name:'Search indexed files'}).fill('RaftSimulation');
 await page.locator('.file-table code').filter({hasText:'RaftSimulation.h'}).waitFor();checks.push('SQLite source-file search');
 const game=lib.projects.find(g=>g.name==='Flotsam Citadel');
 const item=await invoke('import_media',{projectId:game.id,path:path.join(root,'src-tauri','icons','icon.png'),kind:'screenshot'});
 assert.equal(item.status,'draft');
 await page.getByRole('button',{name:'Back to library'}).click();
 await page.locator('.game-card').filter({hasText:'Flotsam Citadel'}).click();
 await page.getByRole('tab',{name:/^Media/}).click();
 await page.locator('.media-card').first().click();
 await page.locator('.media-preview img').waitFor();
 await page.waitForFunction(()=>{const img=document.querySelector('.media-preview img');return img?.naturalWidth===256});
 await page.getByLabel('Title',{exact:true}).fill('QA fixture image');
 await page.getByLabel('Caption',{exact:true}).fill('Test fixture only, not game artwork.');
 await page.getByLabel('Alt text / visual description').fill('Three outlined boxes');
 await page.getByLabel('Rights / license clearance').fill('Original app icon; QA only');
 await page.getByLabel('Review status').selectOption('approved');
 await page.getByRole('button',{name:'Save review',exact:true}).click();
 await page.getByText('Media review saved',{exact:true}).waitFor();
 const media=await invoke('list_media',{projectId:game.id});assert.equal(media[0].width,256);assert.equal(media[0].status,'approved');
 const presskit=await invoke('export_presskit',{projectId:game.id,directory:output});
 const exported=JSON.parse(await fs.readFile(path.join(presskit,'press-kit.json'),'utf8'));
 assert.equal(exported.media.length,1);assert.equal(exported.marketing.tagline,'QA isolated press kit');assert.equal(exported.marketing.notes,undefined);assert.equal(exported.path,undefined);
 checks.push('Native managed-media preview, dimensions, approval and press-kit export');
 const backup=await invoke('backup_library',{directory:output});await fs.access(path.join(backup,'catalog.sqlite3'));checks.push('Native SQLite/media backup');
 await page.getByRole('button',{name:'Capability atlas'}).click();
 await page.getByRole('textbox',{name:'Find a capability'}).fill('rollback');
 await page.getByRole('heading',{name:'Rollback simulation',exact:true}).waitFor();
 await page.screenshot({path:path.join(output,'capability-gap.png'),fullPage:false});
 assert.deepEqual(errors,[]);checks.push('Capability gap view; no JavaScript page errors');
 await browser.close();browser=null;stop();await new Promise(r=>setTimeout(r,1500));
 page=await start();
 const reopened=await invoke('library');assert.equal(reopened.projects.find(g=>g.id===game.id).marketing.tagline,'QA isolated press kit');
 assert.equal((await invoke('list_media',{projectId:game.id}))[0].status,'approved');checks.push('Edits and media review survive native process restart');
 await fs.writeFile(path.join(output,'result.json'),JSON.stringify({status:'passed',checks,exe,output},null,2));
 console.log(JSON.stringify({status:'passed',checks,output},null,2));
}catch(e){await fs.writeFile(path.join(output,'result.json'),JSON.stringify({status:'failed',checks,error:String(e)},null,2));console.error(e);process.exitCode=1;}
finally{if(browser)await browser.close().catch(()=>{});stop();}
