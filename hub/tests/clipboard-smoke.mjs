import {chromium} from '@playwright/test';
import {spawn,execFileSync} from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(import.meta.dirname,'..'),output=path.join(root,'test-results','clipboard-'+Date.now());
await fs.mkdir(output,{recursive:true});
const exe=process.env.GAMECORE_TEST_EXE||path.join(root,'src-tauri','target','release','gamecore-library.exe');
const app=spawn(exe,[],{windowsHide:true,stdio:'ignore',env:{...process.env,GAMECORE_DATA_DIR:path.join(output,'library'),WEBVIEW2_USER_DATA_FOLDER:path.join(output,'webview'),WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:'--remote-debugging-port=9453'}});
let browser;
try{
 for(let i=0;i<100;i++){try{browser=await chromium.connectOverCDP('http://127.0.0.1:9453');break}catch{await new Promise(r=>setTimeout(r,400))}}
 assert.ok(browser);const page=browser.contexts()[0].pages()[0];
 await page.locator('.game-card').first().waitFor({timeout:45000});
 const invoke=(command,args={})=>page.evaluate(({command,args})=>window.__TAURI_INTERNALS__.invoke(command,args),{command,args});
 await page.locator('.game-card').first().click();
 await page.getByRole('tab',{name:/^Media/}).click();
 // Exercise clipboard image handling without replacing the person's system clipboard.
 await page.evaluate(async()=>{
  const canvas=document.createElement('canvas');canvas.width=80;canvas.height=60;
  canvas.getContext('2d').fillRect(0,0,80,60);
  window.testImage=await new Promise(r=>canvas.toBlob(r,'image/png'));
  Object.defineProperty(navigator,'clipboard',{configurable:true,value:{read:async()=>[{types:['image/png'],getType:async()=>window.testImage}]}});
 });
 await page.getByRole('button',{name:'Paste screenshot',exact:true}).click();
 await page.getByRole('dialog',{name:'Review media'}).waitFor();
 await page.getByText('80 × 60',{exact:true}).waitFor();
 let lib=await invoke('library');assert.equal(lib.media.length,1);
 const media=lib.media[0];assert.equal(media.status,'draft');assert.equal(media.source_path,'clipboard');
 await fs.access(media.stored_path);
 await page.getByRole('dialog').locator('textarea').first().fill('Keep text paste working');
 const prevented=await page.getByRole('dialog').locator('textarea').first().evaluate(el=>{
  const data=new DataTransfer();data.items.add(new File([window.testImage],'paste.png',{type:'image/png'}));
  const event=new ClipboardEvent('paste',{clipboardData:data,bubbles:true,cancelable:true});el.dispatchEvent(event);return event.defaultPrevented;
 });assert.equal(prevented,false);
 await page.getByRole('button',{name:'Close media review'}).click();
 await page.evaluate(()=>{
  const data=new DataTransfer();data.items.add(new File([window.testImage],'paste.png',{type:'image/png'}));
  document.dispatchEvent(new ClipboardEvent('paste',{clipboardData:data,bubbles:true,cancelable:true}));
 });
 await page.getByRole('dialog',{name:'Review media'}).waitFor();
 lib=await invoke('library');assert.equal(lib.media.length,2);
 assert.equal(lib.media[0].sha256,lib.media[1].sha256);
 await page.getByRole('button',{name:'Close media review'}).click();
 await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{read:async()=>[]}}));
 await page.getByRole('button',{name:'Paste screenshot',exact:true}).click();
 await page.getByText(/No screenshot on the clipboard/).waitFor();
 assert.equal((await invoke('library')).media.length,2);
 await assert.rejects(()=>invoke('import_clipboard_image',{projectId:media.project_id,bytes:[1,2,3]}));
 await assert.rejects(()=>invoke('import_clipboard_image',{projectId:'missing',bytes:[137,80,78,71,13,10,26,10]}));
 await page.locator('.media-card').first().getByText(/at import/).waitFor();
 await page.locator('.media-card').first().click();
 await page.getByText(/Checkout observed when imported/).waitFor();
 await page.getByRole('button',{name:'Set as thumbnail',exact:true}).click();
 await page.getByRole('button',{name:'Game thumbnail',exact:true}).waitFor();
 lib=await invoke('library');assert.equal(lib.media.filter(m=>m.is_thumbnail).length,1);
 assert.equal(lib.media.find(m=>m.is_thumbnail).status,'draft');
 await page.getByRole('button',{name:'Close media review'}).click();
 await page.locator('.media-card').getByText('Game thumbnail',{exact:true}).waitFor();
 const emitDrop=(event,paths)=>invoke('plugin:event|emit',{event,payload:{paths,position:{x:300,y:300}}});
 await emitDrop('tauri://drag-enter',[media.stored_path]);
 await page.locator('.screenshot-dropzone.dragging').waitFor();
 await emitDrop('tauri://drag-drop',[media.stored_path,media.stored_path,path.join(output,'skip.txt')]);
 await page.getByText('2 screenshots imported as drafts. Unsupported files skipped.',{exact:true}).waitFor();
 lib=await invoke('library');assert.equal(lib.media.length,4);
 assert.equal(lib.media.filter(m=>m.is_thumbnail).length,1);
 // Allow the asynchronous native subscription to reattach after the import finishes.
 await page.waitForTimeout(250);
 await emitDrop('tauri://drag-drop',[path.join(output,'skip.txt')]);
 await page.getByText(/Drop PNG, JPEG or WebP screenshots here/).waitFor();
 assert.equal((await invoke('library')).media.length,4);
 await page.screenshot({path:path.join(output,'media.png')});
 const report={status:'passed',checks:['Paste button imports PNG as draft with decoded dimensions','Image paste event imports screenshot','Text fields and review dialog do not intercept image paste','Empty clipboard gives actionable error without importing','Invalid payload and missing project rejected','Content-addressed files preserved','Explicit draft thumbnail and gallery badge','Native drag events highlight target and import multiple screenshots','Unsupported drops do not create media'],output};
 await fs.writeFile(path.join(output,'result.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
}finally{if(browser)await browser.close();if(app.pid)execFileSync('taskkill',['/PID',String(app.pid),'/T','/F'],{windowsHide:true,stdio:'ignore'});}
