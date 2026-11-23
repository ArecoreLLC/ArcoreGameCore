// Regression: the release UI must load without the development web server.
import {chromium} from '@playwright/test';
import {spawn,execFileSync} from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import net from 'node:net';
import assert from 'node:assert/strict';
const root=path.resolve(import.meta.dirname,'..');
const output=path.join(root,'test-results','standalone-'+Date.now());
await fs.mkdir(output,{recursive:true});
const port=9448;
async function isListening(port){return new Promise(resolve=>{const s=net.connect({host:'127.0.0.1',port});s.setTimeout(500);s.once('connect',()=>{s.destroy();resolve(true)});s.once('error',()=>resolve(false));s.once('timeout',()=>{s.destroy();resolve(false)})});}
assert.equal(await isListening(1437),false,'Stop the dev server before testing standalone assets');
assert.equal(await isListening(port),false,'Test debugging port already occupied');
const source=path.join(process.env.APPDATA,'com.arcore.gamecore','catalog.sqlite3');
const copy=path.join(output,'library');await fs.mkdir(copy);
execFileSync('python',['-c',`import sqlite3,sys;from pathlib import Path
a=sqlite3.connect(Path(sys.argv[1]).as_uri()+'?mode=ro',uri=True);b=sqlite3.connect(sys.argv[2]);a.backup(b);a.close();b.close()`,source,path.join(copy,'catalog.sqlite3')]);
let app,browser;
try {
 app=spawn(path.join(root,'src-tauri','target','release','gamecore-library.exe'),[],{windowsHide:true,stdio:'ignore',env:{...process.env,GAMECORE_DATA_DIR:copy,WEBVIEW2_USER_DATA_FOLDER:path.join(output,'webview'),WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:`--remote-debugging-port=${port}`}});
 for(let i=0;i<100;i++){try{browser=await chromium.connectOverCDP(`http://127.0.0.1:${port}`);break}catch{await new Promise(r=>setTimeout(r,300))}}
 assert.ok(browser,'WebView debugging endpoint unavailable');
 const page=browser.contexts()[0].pages()[0];
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.getByRole('heading',{name:'Game library',exact:true}).waitFor({timeout:30000});
 assert.ok(!page.url().includes(':1437'),'UI still depends on Vite');
 const library=await page.evaluate(()=>window.__TAURI_INTERNALS__.invoke('library'));
 assert.ok(library.projects.length>=31,'Existing catalog not loaded');
 assert.equal(errors.length,0,errors.join('\n'));
 await page.screenshot({path:path.join(output,'library.png')});
 const result={status:'passed',url:page.url(),dev_server:false,projects:library.projects.length,media:library.media.length,errors,library:'isolated SQLite backup; original unchanged'};
 await fs.writeFile(path.join(output,'result.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify({...result,evidence:output}));
} finally {
 await browser?.close();
 if(app?.pid)try{execFileSync('taskkill',['/PID',String(app.pid),'/T','/F'],{windowsHide:true,stdio:'ignore'})}catch{}
}
