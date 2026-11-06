import {WIDTH,HEIGHT,STAGES,clamp,phaseAt,phaseProgress,random,ellipse,line,spiderGuides,genericGuides,analyzePixels,traceEdges,makeStrokes,validateLesson} from './core.mjs';
const $=s=>document.querySelector(s),canvas=$('#drawing'),ctx=canvas.getContext('2d');
let guides=spiderGuides(),defaultGuides=spiderGuides(),imageDataURL='',isSpider=true,progress=.155,playing=false,lastTime=0,tool='view',draft=null,history=[],busy=false,loadingID=0,preview=true;
let layers=[],operations=[],cursor=[640,349],paper=null,activeIndex=-1,activeCount=0,activeLayer=null;
const reference=document.createElement('canvas');reference.width=WIDTH;reference.height=HEIGHT;
const rctx=reference.getContext('2d',{willReadFrequently:true});
const makeCanvas=()=>{const c=document.createElement('canvas');c.width=WIDTH;c.height=HEIGHT;return c;};
const say=message=>{$('#status').textContent=message;};
const pause=()=>{playing=false;$('#play').textContent='▶';$('#play').setAttribute('aria-label','Play drawing');};
const genericCopy=[
  ['Place the largest masses. Compare their width, height and overlap.','Look for the simple shape underneath a complicated silhouette.'],
  ['Add axes and smaller shapes to locate the important features.','Check spacing and angles before committing to details.'],
  ['Trace the main silhouette and the strongest internal edges.','Automatic edges are a starting point. Add your own contours for a clearer lesson.'],
  ['Build shadows with hatching. Leave the light areas open.','Group dark values together so the form stays readable.'],
  ['Lay in the large color masses with broad brush strokes.','Start broad and compare neighboring colors before adding detail.'],
  ['Refine the small strokes and highlights.','Choose a focal point and let the surrounding detail stay softer.']
];
function stageCopy(i){return isSpider?[STAGES[i].text,STAGES[i].tip]:genericCopy[i];}
$('#stages').innerHTML=STAGES.map((s,i)=>`<button class="stage" data-stage="${i}"><span class="number">0${i+1}</span><span><strong>${s.title}</strong><small>${s.short}</small></span></button>`).join('');
function buildPaper(){paper=makeCanvas();const p=paper.getContext('2d');p.fillStyle='#faf8f1';p.fillRect(0,0,WIDTH,HEIGHT);const rng=random(18);for(let i=0;i<95000;i++){p.fillStyle=`rgba(106,93,69,${rng()*.055})`;p.fillRect(rng()*WIDTH,rng()*HEIGHT,.6+rng()*.8,.6+rng()*.8);}}
buildPaper();

function guideOps(g){const result=[];for(let i=1;i<g.points.length;i++){result.push({kind:'pencil',a:g.points[i-1],b:g.points[i],construction:g.stage<2});}return result;}
function paintOperation(c,op,n=0){
  if(op.kind==='pencil'){
    const [ax,ay]=op.a,[bx,by]=op.b;const jitter=Math.sin(n*17.71)*.55;
    c.lineCap='round';c.lineJoin='round';c.strokeStyle=op.construction?'rgba(112,107,87,.43)':'rgba(63,59,50,.57)';c.lineWidth=op.construction?.85:1.05;
    c.beginPath();c.moveTo(ax+jitter,ay);c.lineTo(bx,by+jitter);c.stroke();
    c.strokeStyle=op.construction?'rgba(115,109,89,.13)':'rgba(63,59,50,.15)';c.lineWidth=.5;c.beginPath();c.moveTo(ax+1,ay-1);c.lineTo(bx+1.3,by-.5);c.stroke();cursor=op.b;
  }else{
    c.globalAlpha=op.alpha;c.strokeStyle=op.color;c.lineWidth=op.width;c.lineCap='round';c.beginPath();c.moveTo(op.x-op.dx*.5,op.y-op.dy*.5);c.quadraticCurveTo(op.x+Math.sin(n)*1.2,op.y,op.x+op.dx*.5,op.y+op.dy*.5);c.stroke();c.globalAlpha=1;cursor=[op.x+op.dx*.5,op.y+op.dy*.5];
  }
}
let extracted=null;
function rebuild(){
  operations=[guides.filter(g=>g.stage===0).flatMap(guideOps),guides.filter(g=>g.stage===1).flatMap(guideOps),[...guides.filter(g=>g.stage===2),...extracted.contours].flatMap(guideOps),extracted.hatch,extracted.broad,extracted.fine];
  layers=operations.map(ops=>{const layer=makeCanvas(),c=layer.getContext('2d');ops.forEach((op,n)=>paintOperation(c,op,n));return layer;});
  activeIndex=-1;activeCount=0;render();
}
function stageLayer(i,fraction){
  if(fraction>=1)return layers[i];
  const count=Math.floor(operations[i].length*fraction);
  if(activeIndex!==i||count<activeCount){activeIndex=i;activeCount=0;activeLayer=makeCanvas();}
  const c=activeLayer.getContext('2d');for(let n=activeCount;n<count;n++)paintOperation(c,operations[i][n],n);activeCount=count;
  if(count){const op=operations[i][count-1];cursor=op.b||[op.x+op.dx*.5,op.y+op.dy*.5];}
  return activeLayer;
}
function composite(c,p,{tip=false,editing=false}={}){
  c.clearRect(0,0,WIDTH,HEIGHT);c.drawImage(paper,0,0);
  if(editing){c.globalAlpha=.22;c.drawImage(reference,0,0);c.globalAlpha=1;}
  for(let i=0;i<6;i++){const f=phaseProgress(p,i);if(f<=0)continue;
    // Lift construction graphite as the drawing develops; optional ghost lines remain.
    let alpha=1;
    if(i<2&&p>2/6)alpha=$('#guides-visible').checked?Math.max(.20,1-(p-2/6)*1.6):Math.max(0,1-(p-2/6)*6);
    if(i===2&&p>4/6)alpha=1-(p-4/6)*2.1;
    c.globalAlpha=alpha;c.drawImage(stageLayer(i,f),0,0);c.globalAlpha=1;
  }
  if(draft&&editing){const ops=guideOps(draft);ops.forEach((op,n)=>paintOperation(c,op,n));}
  if($('#guides-visible').checked&&p>5/6){c.globalAlpha=.12;c.drawImage(layers[0],0,0);c.drawImage(layers[1],0,0);c.globalAlpha=1;}
  if(tip&&p>0&&p<1&&operations[phaseAt(p)].length){c.save();c.translate(...cursor);c.rotate(-.6);c.fillStyle=phaseAt(p)<4?'#bb996a':'#547366';c.strokeStyle='#574937';c.lineWidth=.7;c.beginPath();c.moveTo(0,0);c.lineTo(5,-15);c.lineTo(3,-72);c.lineTo(-3,-72);c.lineTo(-4,-15);c.closePath();c.fill();c.stroke();c.fillStyle='#423f35';c.beginPath();c.moveTo(0,0);c.lineTo(2,-7);c.lineTo(-2,-7);c.closePath();c.fill();c.restore();}
}
function render(){
  if(!layers.length)return;
  composite(ctx,progress,{tip:playing&&$('#cursor-visible').checked,editing:tool!=='view'});
  const i=phaseAt(progress),s=STAGES[i];
  $('#timeline').value=Math.round(progress*1000);$('#elapsed').textContent=`0:${String(Math.floor(progress*60)).padStart(2,'0')}`;if(progress===1)$('#elapsed').textContent='1:00';
  $('#phase-status').textContent=s.title;$('#medium-label').textContent=`0${i+1} / ${s.title}`;$('#paper-note').textContent=i<4?'HB PENCIL · WARM PRESS PAPER':'COLOR STUDY · WARM PRESS PAPER';
  $('#lesson-tip').textContent=stageCopy(i)[1];
  document.querySelectorAll('.stage').forEach((b,j)=>{b.classList.toggle('active',j===i);b.setAttribute('aria-current',j===i?'step':'false');b.querySelector('small').textContent=j===i?stageCopy(j)[0]:isSpider?STAGES[j].short:['Find the big shapes','Place features & axes','Follow the silhouette','Build light and shadow','Block in color','Refine the focal point'][j];});
}
function seek(p){pause();preview=false;progress=clamp(p);render();}
function animate(time){if(playing&&!busy){const delta=Math.min(100,time-lastTime||0);progress=clamp(progress+delta/60000*Number($('#speed').value));if(progress>=1){if($('#loop').checked){progress=0;activeIndex=-1;}else pause();}render();}lastTime=time;requestAnimationFrame(animate);}
requestAnimationFrame(animate);
async function loadImage(src,{name='My reference study',sample=false,newGuides=null}={}){
  const id=++loadingID;pause();busy=true;$('#loading').hidden=false;setDisabled(true);
  try{
    const candidate=new Image();candidate.src=src;await candidate.decode();if(id!==loadingID)return;
    if(candidate.width*candidate.height>40000000)throw Error('Please choose an image smaller than 40 megapixels.');
    // Letterbox all inputs to a fixed lesson coordinate space without stretching.
    rctx.fillStyle='#faf8f1';rctx.fillRect(0,0,WIDTH,HEIGHT);const fit=Math.min(WIDTH/candidate.width,HEIGHT/candidate.height),w=candidate.width*fit,h=candidate.height*fit;rctx.drawImage(candidate,(WIDTH-w)/2,(HEIGHT-h)/2,w,h);
    imageDataURL=reference.toDataURL('image/jpeg',.94);$('#reference-overlay').src=imageDataURL;
    const low=document.createElement('canvas');low.width=640;low.height=349;const lctx=low.getContext('2d',{willReadFrequently:true});lctx.drawImage(reference,0,0,640,349);const pixels=lctx.getImageData(0,0,640,349).data;
    // Yield before the CPU work so the loading status is painted.
    await new Promise(resolve=>setTimeout(resolve,30));if(id!==loadingID)return;
    const a=analyzePixels(pixels,640,349),strokes=makeStrokes(pixels,640,349,a);extracted={...strokes,contours:traceEdges(a.edge,640,349)};
    isSpider=sample;guides=newGuides??(sample?spiderGuides():genericGuides());defaultGuides=structuredClone(guides);history=[];$('#study-name').textContent=name;$('.study-tag').textContent=sample?'GUIDED STUDY':'CUSTOM STUDY';
    if(!sample){STAGES[0].title='Gesture & proportion';$('.lesson-panel h2').textContent='From reference to drawing';$('.panel-intro').textContent='Add your guides. Make the study your own.';}else{$('.lesson-panel h2').textContent='From shape to character';$('.panel-intro').textContent='Six small steps. One curious little friend.';}
    progress=.155;preview=true;$('#reference-overlay').hidden=true;$('#reference-toggle').textContent='Compare reference';$('#reference-toggle').setAttribute('aria-pressed','false');setTool('view');rebuild();say(sample?'Spider study ready. Press play, or choose a step.':'Reference ready. Use Ellipse, Axis and Contour to plan a drawing lesson.');
  }catch(error){say(`Could not open reference: ${error.message}`);}finally{if(id===loadingID){busy=false;$('#loading').hidden=true;setDisabled(false);}}
}
function setDisabled(disabled){document.querySelectorAll('button,input,select').forEach(el=>el.disabled=disabled);document.querySelectorAll('label[for]').forEach(el=>el.style.pointerEvents=disabled?'none':'');}
function setTool(next){pause();tool=next;draft=null;canvas.style.cursor=next==='view'?'default':'crosshair';document.querySelectorAll('[data-tool]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.tool===next)));if(next!=='view'){progress=next==='contour'?.499:.332;$('#reference-overlay').hidden=true;$('#reference-toggle').setAttribute('aria-pressed','false');$('#reference-toggle').textContent='Compare reference';}$('#edit-hint').textContent=next==='view'?'Reference stays on your device. Other images use automatic edge and tone studies; construction shapes are yours to place.':`Drag on the paper to ${next==='contour'?'trace a contour':next==='ellipse'?'place an ellipse':'place an axis'}. Undo removes the last change. Return to View to play.`;render();}
function pointerPoint(event){const r=canvas.getBoundingClientRect();return [clamp((event.clientX-r.left)/r.width)*WIDTH,clamp((event.clientY-r.top)/r.height)*HEIGHT];}
let start=null;
canvas.addEventListener('pointerdown',e=>{if(tool==='view'||busy)return;start=pointerPoint(e);draft=line([start,start],tool==='contour'?2:1);canvas.setPointerCapture(e.pointerId);});
canvas.addEventListener('pointermove',e=>{if(!start||!draft)return;const point=pointerPoint(e);if(tool==='ellipse'){draft=ellipse((start[0]+point[0])/2,(start[1]+point[1])/2,Math.abs(point[0]-start[0])/2,Math.abs(point[1]-start[1])/2);}else if(tool==='line')draft=line([start,point]);else if(Math.hypot(point[0]-draft.points.at(-1)[0],point[1]-draft.points.at(-1)[1])>2)draft.points.push(point);render();});
canvas.addEventListener('pointerup',()=>{if(!draft)return;const points=draft.points;if(points.some(p=>Math.hypot(p[0]-points[0][0],p[1]-points[0][1])>4)){if(guides.length>=500){say('This lesson has reached its 500-guide limit.');}else{history.push(structuredClone(guides));guides.push(draft);}}draft=null;start=null;rebuild();});
canvas.addEventListener('pointercancel',()=>{draft=null;start=null;render();});
document.querySelectorAll('[data-tool]').forEach(b=>b.onclick=()=>setTool(b.dataset.tool));
$('#undo').onclick=()=>{if(history.length){guides=history.pop();rebuild();say('Last guide change undone.');}else say('No guide changes to undo.');};
$('#reset-guides').onclick=()=>{history.push(structuredClone(guides));guides=structuredClone(defaultGuides);rebuild();say('Original guides restored. Undo is available.');};
$('#play').onclick=()=>{if(tool!=='view')setTool('view');if(playing){pause();render();}else{if(progress>=1||preview)progress=0;preview=false;playing=true;lastTime=performance.now();$('#play').textContent='Ⅱ';$('#play').setAttribute('aria-label','Pause drawing');}};
$('#restart').onclick=()=>seek(0);$('#timeline').oninput=e=>seek(Number(e.target.value)/1000);
document.querySelectorAll('[data-stage]').forEach(b=>b.onclick=()=>{setTool('view');seek((Number(b.dataset.stage)+1)/6-.00001);});
$('#guides-visible').onchange=render;$('#cursor-visible').onchange=render;
$('#reference-toggle').onclick=()=>{const on=$('#reference-overlay').hidden;$('#reference-overlay').hidden=!on;$('#reference-toggle').textContent=on?'Back to drawing':'Compare reference';$('#reference-toggle').setAttribute('aria-pressed',String(on));};
$('#sample').onclick=()=>loadImage('./assets/spider-reference.jpg',{name:'Little woodland spider',sample:true});
function readFile(file){return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=()=>reject(Error('File could not be read.'));reader.readAsDataURL(file);});}
$('#reference-file').onchange=async e=>{const file=e.target.files[0];if(!file)return;try{if(file.size>12000000)throw Error('Choose an image under 12 MB.');if(!['image/jpeg','image/png','image/webp'].includes(file.type))throw Error('Choose a JPEG, PNG or WebP image.');await loadImage(await readFile(file),{name:file.name.replace(/\.[^.]+$/,'').slice(0,150)});}catch(error){say(error.message);}finally{e.target.value='';}};
$('#lesson-file').onchange=async e=>{const file=e.target.files[0];if(!file)return;try{if(file.size>18000000)throw Error('Lesson file must be under 18 MB.');const data=validateLesson(JSON.parse(await file.text()));await loadImage(data.image,{name:data.name,sample:data.study==='spider',newGuides:data.guides});}catch(error){say(`Could not open lesson: ${error.message}`);}finally{e.target.value='';}};
function download(blob,name){const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);}
function saveCanvas(c,name){c.toBlob(blob=>{if(blob){download(blob,name);say(`Saved ${name}.`);}else say('Image export failed. Try again.');},'image/png');}
$('#export-png').onclick=()=>{const c=makeCanvas();composite(c.getContext('2d'),progress);saveCanvas(c,'drawing-atelier-frame.png');render();};
$('#save-lesson').onclick=()=>{download(new Blob([JSON.stringify({version:1,name:$('#study-name').textContent,study:isSpider?'spider':'custom',image:imageDataURL,guides},null,2)],{type:'application/json'}),'drawing-atelier-lesson.json');say('Saved editable lesson, including its reference image and construction guides.');};
function wrapText(c,text,x,y,width,lineHeight){let row='';for(const word of text.split(' ')){const trial=row+word+' ';if(c.measureText(trial).width>width&&row){c.fillText(row,x,y);row=word+' ';y+=lineHeight;}else row=trial;}c.fillText(row,x,y);return y+lineHeight;}
$('#export-sheet').onclick=()=>{
  const sheet=document.createElement('canvas');sheet.width=1800;sheet.height=2370;const c=sheet.getContext('2d');c.fillStyle='#faf8f1';c.fillRect(0,0,sheet.width,sheet.height);c.fillStyle='#334d3d';c.font='18px sans-serif';c.fillText('DRAWING ATELIER  /  A SIX-STEP STUDY',80,65);c.font='44px Georgia';c.fillText($('#study-name').textContent.slice(0,65),80,123);c.font='21px Georgia';c.fillStyle='#727969';c.fillText('Observe the shapes. Draw lightly. Build the details a little at a time.',80,170);
  for(let i=0;i<6;i++){
    const x=80+(i%2)*850,y=215+Math.floor(i/2)*690;c.fillStyle='#e2e3d8';c.fillRect(x,y,790,433);const frame=makeCanvas();composite(frame.getContext('2d'),(i+1)/6-.000001);c.drawImage(frame,x+2,y+2,786,429);c.fillStyle='#334d3d';c.font='28px Georgia';c.fillText(`0${i+1}  ${STAGES[i].title}`,x,y+477);c.font='19px sans-serif';c.fillStyle='#697061';wrapText(c,stageCopy(i)[0],x,y+515,770,29);
  }
  c.font='17px sans-serif';c.fillStyle='#697061';c.fillText('Practice space: try the construction again without looking at the finished drawing.',80,2310);c.fillText('Reference-driven simulation · Drawing Atelier',80,2343);saveCanvas(sheet,'drawing-atelier-six-step-sheet.png');activeIndex=-1;render();
};
document.addEventListener('keydown',e=>{if(busy||['INPUT','SELECT','TEXTAREA','BUTTON'].includes(document.activeElement.tagName)||e.ctrlKey||e.metaKey||e.altKey)return;if(e.code==='Space'){e.preventDefault();$('#play').click();}else if(e.code==='ArrowRight'){e.preventDefault();seek((phaseAt(progress)+2)/6-.00001);}else if(e.code==='ArrowLeft'){e.preventDefault();seek(Math.max(0,phaseAt(progress))/6-.00001);}});
loadImage('./assets/spider-reference.jpg',{name:'Little woodland spider',sample:true});
