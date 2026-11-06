// CLI bridge: reuse the browser's deterministic geometry and image analysis.
import {readFileSync,writeFileSync} from 'node:fs';
import {STAGES,spiderGuides,genericGuides,analyzePixels,traceEdges,makeStrokes,validateLesson} from './core.mjs';
const [pixelsPath,outputPath,study='spider',lessonPath]=process.argv.slice(2);
if(!pixelsPath||!outputPath)throw Error('Usage: node export-strokes.mjs pixels.rgba output.json spider|custom [lesson.json]');
const pixels=readFileSync(pixelsPath),width=640,height=349;
if(pixels.length!==width*height*4)throw Error('Expected a 640 x 349 RGBA image.');
const guides=lessonPath?validateLesson(JSON.parse(readFileSync(lessonPath,'utf8'))).guides:study==='spider'?spiderGuides():genericGuides();
const analysis=analyzePixels(pixels,width,height),strokes=makeStrokes(pixels,width,height,analysis);
// Suppress neighboring Sobel responses so a soft boundary becomes a pencil line.
const thin=new Float32Array(analysis.edge.length);
for(let y=2;y<height-2;y++)for(let x=2;x<width-2;x++){
  const i=y*width+x,a=analysis.angles[i]-Math.PI/2,dx=Math.round(Math.cos(a)),dy=Math.round(Math.sin(a)),d=dy*width+dx;
  if(analysis.edge[i]>=analysis.edge[i+d]&&analysis.edge[i]>=analysis.edge[i-d])thin[i]=analysis.edge[i];
}
const tones=strokes.fine.map(op=>{const rgb=op.color.slice(4,-1).split(',').map(Number),luma=(rgb[0]*.299+rgb[1]*.587+rgb[2]*.114)/255;return {...op,color:'#454138',alpha:(1-luma)*.55,width:op.width*1.2};});
const segments=guide=>guide.points.slice(1).map((b,i)=>({kind:'pencil',a:guide.points[i],b,construction:guide.stage<2,opacity:guide.segment_opacity?.[i]??1}));
const stages=[guides.filter(g=>g.stage===0).flatMap(segments),guides.filter(g=>g.stage===1).flatMap(segments),[...guides.filter(g=>g.stage===2),...traceEdges(thin,width,height,22)].flatMap(segments),[...tones,...strokes.hatch],strokes.broad,strokes.fine];
const genericText=['Find the largest masses and compare their proportions.','Use axes and simple shapes to place the smaller features.','Follow the main silhouette and the strongest internal edges.','Build shadows with hatching, leaving the light areas open.','Block in the large color masses with broad brush strokes.','Refine the smaller strokes, edges and highlights.'];
writeFileSync(outputPath,JSON.stringify({stages,guides,study,instructions:STAGES.map((s,i)=>({title:s.title,text:study==='spider'?s.text:genericText[i]}))}));
