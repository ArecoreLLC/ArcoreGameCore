import test from 'node:test';
import assert from 'node:assert/strict';
import {STAGES,phaseAt,phaseProgress,random,spiderGuides,ellipse,analyzePixels,traceEdges,makeStrokes,validateLesson} from './core.mjs';

test('timeline boundaries include six complete stages without overrun',()=>{
  assert.equal(STAGES.length,6);assert.equal(phaseAt(0),0);assert.equal(phaseAt(1),5);assert.equal(phaseAt(2),5);assert.equal(phaseAt(-1),0);
  for(let i=0;i<6;i++){assert.equal(phaseProgress(i/6,i),0);assert.equal(phaseProgress((i+1)/6,i),1);}
});
test('spider guide geometry is finite, inside the paper, and construction precedes contours',()=>{
  const guides=spiderGuides();assert.ok(guides.length>35);assert.ok(guides.some(g=>g.stage===0));assert.ok(guides.some(g=>g.stage===1));
  for(const g of guides)for(const [x,y]of g.points){assert.ok(Number.isFinite(x)&&x>=0&&x<=1280);assert.ok(Number.isFinite(y)&&y>=0&&y<=698);}
  const circle=ellipse(100,100,20,10);assert.ok(Math.hypot(circle.points[0][0]-circle.points.at(-1)[0],circle.points[0][1]-circle.points.at(-1)[1])<1e-8);
});
function fixture(){const w=80,h=60,pixels=new Uint8ClampedArray(w*h*4);for(let y=0;y<h;y++)for(let x=0;x<w;x++){const value=x>=20&&x<60&&y>=15&&y<45?50:230;pixels.set([value,value,value,255],(y*w+x)*4);}return {w,h,pixels};}
test('edge detector finds the silhouette and suppresses flat fields',()=>{
  const {w,h,pixels}=fixture(),a=analyzePixels(pixels,w,h);assert.equal(a.edge[30*w+40],0);assert.ok(a.edge[30*w+20]>100);const paths=traceEdges(a.edge,w,h);assert.ok(paths.length>0);assert.ok(paths.some(p=>p.points.length>20));
});
test('painting excludes flat reference background and produces repeatable stroke layers',()=>{
  const {w,h,pixels}=fixture(),a=analyzePixels(pixels,w,h),strokes=makeStrokes(pixels,w,h,a);assert.deepEqual(strokes,makeStrokes(pixels,w,h,a));assert.ok(strokes.hatch.length>0);assert.ok(strokes.fine.length>strokes.broad.length);
  for(const layer of Object.values(strokes))for(const s of layer){assert.ok(s.x>=20*1280/w&&s.x<60*1280/w);assert.ok(s.y>=15*698/h&&s.y<45*698/h);assert.ok(s.width>0);assert.ok(s.alpha>0&&s.alpha<=1);}
});
test('blank image creates no false outlines, shadows, or paint',()=>{
  const pixels=new Uint8ClampedArray(30*30*4).fill(255),a=analyzePixels(pixels,30,30);assert.deepEqual(traceEdges(a.edge,30,30),[]);assert.deepEqual(makeStrokes(pixels,30,30,a),{hatch:[],broad:[],fine:[]});
});
test('lesson survives JSON roundtrip and rejects unsafe or malformed inputs',()=>{
  const lesson={version:1,name:'Spider',image:'data:image/jpeg;base64,AAAA',guides:spiderGuides()};assert.deepEqual(validateLesson(JSON.parse(JSON.stringify(lesson))),lesson);
  for(const patch of [{version:2},{image:'https://example.com/image.jpg'},{guides:[{type:'line',stage:1,points:[[NaN,0],[2,3]]}]},{guides:[{type:'line',stage:9,points:[[1,0],[2,3]]}]},{guides:Array(501).fill(ellipse(10,10,5,5))}])assert.throws(()=>validateLesson({...lesson,...patch}));
});
test('random stream is deterministic and bounded',()=>{const a=random(),b=random();for(let i=0;i<1000;i++){const n=a();assert.equal(n,b());assert.ok(n>=0&&n<1);}});
