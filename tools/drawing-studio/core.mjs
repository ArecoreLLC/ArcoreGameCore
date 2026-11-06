export const WIDTH = 1280, HEIGHT = 698;
export const STAGES = [
  {title:'Gesture & proportion',short:'Find the big shapes',text:'Place the round head and the larger abdomen behind it. Keep the head low and leave room for the feet.',tip:'Draw lightly from your shoulder. These first shapes are a scaffold, so they don’t need to be perfect.'},
  {title:'Construction lines',short:'Give the shapes structure',text:'Add the face axes, eye circles and jointed leg shapes. Check their angles before adding details.',tip:'Compare distances: the two largest eyes take up most of the face. Small circles help you place the other eyes.'},
  {title:'Confident contours',short:'Find the character inside',text:'Follow the silhouette, define the eyes and connect the leg joints. Use short, searching pencil strokes.',tip:'Let the outline overlap at the joints. An interrupted line often describes a soft, furry edge better than a hard border.'},
  {title:'Graphite & texture',short:'Turn shapes into volume',text:'Shade underneath the body and between the legs. Build the darker eyes and suggest fur with light hatching.',tip:'Keep your lightest lights clean. Dark values under the head and legs make the body feel round and grounded.'},
  {title:'Underpainting',short:'Lay in the color families',text:'Block in mossy browns and soft greens with broad strokes. Work from the large color masses toward the details.',tip:'Squint at the reference. Paint the large patches you see before thinking about individual strands of fur.'},
  {title:'Fur, light & finish',short:'Let the little details shine',text:'Refine the strokes, deepen the eyes and pick out soft highlights. Leave a little of the drawing visible.',tip:'Save the sharpest contrast for the eyes. A few well-placed highlights do more than detailing every surface.'}
];
export const clamp = (n,a=0,b=1)=>Math.max(a,Math.min(b,n));
export const phaseAt = p => Math.min(5,Math.floor(clamp(p)*6));
export const phaseProgress = (p,i) => clamp(p*6-i);
export function random(seed=3741){return ()=>{seed|=0;seed=seed+0x6D2B79F5|0;let t=Math.imul(seed^seed>>>15,1|seed);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
export function ellipse(cx,cy,rx,ry,rotation=0,stage=1){const points=[];for(let i=0;i<=90;i++){const a=i/90*Math.PI*2;points.push([cx+Math.cos(a)*rx*Math.cos(rotation)-Math.sin(a)*ry*Math.sin(rotation),cy+Math.cos(a)*rx*Math.sin(rotation)+Math.sin(a)*ry*Math.cos(rotation)]);}return {type:'ellipse',stage,points};}
export const line=(points,stage=1)=>({type:'line',stage,points});
export function spiderGuides(){return [
  ellipse(821,248,199,157,-.15,0),ellipse(623,303,200,151,.04,0),
  line([[273,573],[1022,590]],0),line([[626,152],[616,448]]),line([[439,266],[481,283],[545,294],[619,305],[696,310],[788,307]]),
  ellipse(512,294,51,57,-.14),ellipse(640,304,59,63,.10),ellipse(445,255,19,29,.27),ellipse(744,278,28,32,.13),
  ...[[487,208,13,16],[551,210,15,17],[610,215,16,17],[698,223,15,18]].map(([x,y,rx,ry])=>ellipse(x,y,rx,ry)),
  ...[[267,356,62,27,-.55],[227,428,24,45,.29],[377,337,23,53,-.7],[362,448,24,57,.1],[349,542,20,41,.1],[426,462,21,52,-.1],[426,526,18,35,.15],[490,436,33,61,-.48],[502,513,18,30,.23],[639,449,32,63,.45],[789,384,37,55,.23],[750,489,35,66,.29],[718,586,23,50,.27],[876,413,38,47,-.1],[894,497,26,62,-.15],[900,584,24,44,-.16],[939,358,53,30,.68],[972,440,27,58,-.39],[974,546,21,56,-.1],[1002,370,55,24,.84],[1032,462,22,54,-.15],[1055,534,23,39,-.4]].map(([x,y,rx,ry,r])=>ellipse(x,y,rx,ry,r)),
  line([[361,323],[270,359],[228,428],[210,478]]),line([[411,335],[369,414],[352,491],[339,574]]),line([[784,343],[782,400],[752,477],[712,615]]),line([[852,358],[880,406],[896,492],[902,609]]),line([[908,297],[946,355],[977,432],[977,582]]),line([[935,279],[1007,368],[1034,463],[1067,555]])
];}
export function genericGuides(){return [ellipse(640,349,370,260,0,0),line([[640,80],[640,620]]),line([[210,349],[1070,349]])];}

// Two box-blur passes suppress fur noise before finding structural contours.
export function analyzePixels(rgba,w,h){
  const gray=new Float32Array(w*h);for(let i=0;i<gray.length;i++)gray[i]=rgba[i*4]*.299+rgba[i*4+1]*.587+rgba[i*4+2]*.114;
  let smooth=gray;
  for(let pass=0;pass<2;pass++){const next=new Float32Array(smooth);for(let y=1;y<h-1;y++)for(let x=1;x<w-1;x++){let sum=0;for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++)sum+=smooth[(y+dy)*w+x+dx];next[y*w+x]=sum/9;}smooth=next;}
  const edge=new Float32Array(w*h),angles=new Float32Array(w*h);
  for(let y=1;y<h-1;y++)for(let x=1;x<w-1;x++){const i=y*w+x;const gx=-smooth[i-w-1]+smooth[i-w+1]-2*smooth[i-1]+2*smooth[i+1]-smooth[i+w-1]+smooth[i+w+1];const gy=-smooth[i-w-1]-2*smooth[i-w]-smooth[i-w+1]+smooth[i+w-1]+2*smooth[i+w]+smooth[i+w+1];edge[i]=Math.hypot(gx,gy);angles[i]=Math.atan2(gy,gx)+Math.PI/2;}
  return {gray,smooth,edge,angles};
}
export function traceEdges(edge,w,h,threshold=28){
  const used=new Uint8Array(w*h),paths=[];const neighbors=[-1,1,-w,w,-w-1,-w+1,w-1,w+1];
  for(let y=2;y<h-2;y++)for(let x=2;x<w-2;x++){let i=y*w+x;if(used[i]||edge[i]<threshold)continue;const points=[];for(let j=0;j<500;j++){used[i]=1;points.push([i%w*WIDTH/w,Math.floor(i/w)*HEIGHT/h]);let best=-1,score=0;for(const d of neighbors){const n=i+d,nx=n%w,ny=Math.floor(n/w);if(nx<2||nx>=w-2||ny<2||ny>=h-2||used[n]||edge[n]<threshold)continue;if(edge[n]>score){score=edge[n];best=n;}}if(best<0)break;i=best;}if(points.length>5)paths.push({type:'contour',stage:2,points});}
  return paths.sort((a,b)=>b.points.length-a.points.length);
}
export function makeStrokes(rgba,w,h,analysis){
  const rng=random(),bg=[rgba[0],rgba[1],rgba[2]],sx=WIDTH/w,sy=HEIGHT/h;
  const sample=(x,y)=>{const i=(Math.min(h-1,Math.max(0,y|0))*w+Math.min(w-1,Math.max(0,x|0)))*4;return [rgba[i],rgba[i+1],rgba[i+2]];};
  const foreground=(rgb)=>Math.hypot(rgb[0]-bg[0],rgb[1]-bg[1],rgb[2]-bg[2])>24;
  const hatch=[],broad=[],fine=[];
  for(let y=2;y<h-2;y+=3)for(let x=2;x<w-2;x+=3){const px=x+rng()*2,py=y+rng()*2,rgb=sample(px,py),i=(py|0)*w+(px|0);if(!foreground(rgb))continue;const darkness=1-analysis.gray[i]/255;if(darkness>.12){const length=3+rng()*7;hatch.push({x:px*sx,y:py*sy,dx:length*.7,dy:-length,width:.5+rng()*.6,alpha:darkness*.29,color:'#454138'});if(darkness>.55)hatch.push({x:px*sx,y:py*sy,dx:-length*.6,dy:-length,width:.6,alpha:darkness*.25,color:'#454138'});}}
  for(const [step,list,size] of [[6,broad,13],[2,fine,3.8]])for(let y=1;y<h-1;y+=step)for(let x=1;x<w-1;x+=step){const px=x+rng()*step,py=y+rng()*step,rgb=sample(px,py),i=Math.min(h-1,py|0)*w+Math.min(w-1,px|0);if(!foreground(rgb))continue;const a=analysis.edge[i]>12?analysis.angles[i]:-.9+Math.sin(px*.02)*.6;const len=(size+rng()*size)*.75;list.push({x:px*sx,y:py*sy,dx:Math.cos(a)*len,dy:Math.sin(a)*len,width:size*(.65+rng()*.5),alpha:list===broad?.86:.92,color:`rgb(${rgb.join(',')})`});}
  // Sweep across forms rather than reveal rectangular image tiles.
  for(const list of [hatch,broad,fine])list.sort((a,b)=>(a.y*.65+a.x*.35+Math.sin(a.x*.03)*28)-(b.y*.65+b.x*.35+Math.sin(b.x*.03)*28));
  return {hatch,broad,fine};
}
export function validateLesson(data){
  if(!data||data.version!==1||typeof data.name!=='string'||data.name.length>150||!/^data:image\/(png|jpeg|webp);base64,/.test(data.image)||data.image.length>16000000||!Array.isArray(data.guides)||data.guides.length>500)throw Error('This is not a supported Drawing Atelier lesson.');
  for(const g of data.guides){if(!['ellipse','line','contour'].includes(g.type)||!Number.isInteger(g.stage)||g.stage<0||g.stage>2||!Array.isArray(g.points)||g.points.length<2||g.points.length>10000||g.points.some(p=>!Array.isArray(p)||p.length!==2||p.some(n=>!Number.isFinite(n)||n<0||n>1280)))throw Error('The lesson contains an invalid construction guide.');}
  return data;
}
